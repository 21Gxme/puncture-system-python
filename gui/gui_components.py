from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QPushButton, QLabel, QListWidget, QSlider, QScrollArea, QComboBox, QCheckBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPainter, QPen, QPixmap, QColor
from PIL import Image, ImageQt
import numpy as np
from handlers.visualization_handler import VisualizationHandler

class ImagePanel(QLabel):
    def __init__(self, plane_name, gui_components, parent=None):
        super().__init__(parent)
        self.plane_name = plane_name
        self.gui_components = gui_components
        self.setMinimumSize(300, 300)
        self.setStyleSheet("background-color: black; border: 1px solid gray;")
        self.setAlignment(Qt.AlignCenter)
        self.image_data = None
        self.current_pixmap = None
        self.needle_line = None
        self.realtime_lines = []
        self.axes_lines = []
        self.locked = False
        self.dragging = False
        self.last_pos = None
        self.setMouseTracking(True)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        if self.current_pixmap:
            panel_index = self.gui_components.panels.index(self) if self in self.gui_components.panels else -1
            pan_offset = self.gui_components.main_app.get_pan_for_panel(panel_index)
            x = (self.width() - self.current_pixmap.width()) // 2 + pan_offset[0]
            y = (self.height() - self.current_pixmap.height()) // 2 + pan_offset[1]
            painter.drawPixmap(x, y, self.current_pixmap)
        for axis in self.axes_lines:
            pen = QPen(QColor(axis['color']), 2)
            painter.setPen(pen)
            if axis['type'] == 'horizontal':
                painter.drawLine(0, int(axis['y']), self.width(), int(axis['y']))
            elif axis['type'] == 'vertical':
                painter.drawLine(int(axis['x']), 0, int(axis['x']), self.height())
        if self.needle_line:
            pen = QPen(QColor(self.needle_line['color']), 3)
            pen.setStyle(Qt.DashLine)
            painter.setPen(pen)
            start, end = self.needle_line['start'], self.needle_line['end']
            painter.drawLine(int(start[0]), int(start[1]), int(end[0]), int(end[1]))
        for line in self.realtime_lines:
            pen = QPen(QColor(line['color']), 3)
            pen.setStyle(Qt.DashLine)
            painter.setPen(pen)
            start, end = line['start'], line['end']
            painter.drawLine(int(start[0]), int(start[1]), int(end[0]), int(end[1]))

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragging = True
            self.last_pos = event.pos()
            self.setCursor(Qt.ClosedHandCursor)

    def mouseMoveEvent(self, event):
        if self.dragging and self.last_pos:
            dx = event.x() - self.last_pos.x()
            dy = event.y() - self.last_pos.y()
            panel_index = self.gui_components.panels.index(self) if self in self.gui_components.panels else -1
            if panel_index >= 0:
                self.gui_components.handle_panel_drag(panel_index, dx, dy)
            self.last_pos = event.pos()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragging = False
            self.setCursor(Qt.ArrowCursor)

    def wheelEvent(self, event):
        panel_index = self.gui_components.panels.index(self) if self in self.gui_components.panels else -1
        if panel_index >= 0:
            delta = event.angleDelta().y()
            self.gui_components.handle_panel_zoom(panel_index, delta > 0)

class GUIComponents(QWidget):
    def __init__(self, main_app):
        super().__init__()
        self.main_app = main_app
        self.panels = []
        self.sliders = {}

    def init_toolbar(self):
        self.toolbar = QWidget()
        self.toolbar.setStyleSheet("background-color: #f0f0f0; border-bottom: 1px solid #ccc; padding: 5px;")
        toolbar_layout = QHBoxLayout(self.toolbar)
        toolbar_layout.setContentsMargins(5, 5, 5, 5)

        buttons = [
            ("Menu", self.main_app.toggle_sidebar),
            ("File", self.main_app.show_file_menu),
            ("Load", self.main_app.btnLoadPictures_Click),
            ("Start Real-Time Route", self.main_app.start_realtime_data),
            ("Stop Real-Time Route", self.main_app.stop_realtime_data),
            ("Reset Pan", self.main_app.reset_pan_all, "background-color: lightyellow;"),
            ("Delete File", self.main_app.delete_selected_file, "background-color: salmon;")
        ]
        for text, slot, *style in buttons:
            btn = QPushButton(text)
            if style:
                btn.setStyleSheet(style[0])
            btn.clicked.connect(slot)
            toolbar_layout.addWidget(btn)

        toolbar_layout.addStretch()

        zoom_frame = QWidget()
        zoom_layout = QHBoxLayout(zoom_frame)
        zoom_layout.setContentsMargins(0, 0, 0, 0)
        zoom_layout.addWidget(QLabel("All Planes:"))
        reset_all_button = QPushButton("Reset All")
        reset_all_button.setStyleSheet("background-color: lightblue;")
        reset_all_button.clicked.connect(self.main_app.reset_zoom_all)
        zoom_layout.addWidget(reset_all_button)
        toolbar_layout.addWidget(zoom_frame)

    def init_sidebar(self):
        self.sidebar = QScrollArea()
        self.sidebar.setWidgetResizable(True)
        self.sidebar.setFixedWidth(320)
        sidebar_content = QWidget()
        sidebar_layout = QVBoxLayout(sidebar_content)
        self.list_view = QListWidget()
        self.list_view.itemClicked.connect(self.main_app.list_view_item_click)
        sidebar_layout.addWidget(self.list_view)
        self.init_sliders(sidebar_layout)
        self.init_zoom_controls(sidebar_layout)
        self.sidebar.setWidget(sidebar_content)

    def init_sliders(self, parent_layout):
        sliders_frame = QWidget()
        sliders_layout = QVBoxLayout(sliders_frame)
        slider_configs = [
            ("X Value", 512, 256, lambda v: self.main_app.slider_changed("X Value", v)),
            ("Y Value", 512, 256, lambda v: self.main_app.slider_changed("Y Value", v)),
            ("Z Value", 512, 256, lambda v: self.main_app.slider_changed("Z Value", v)),
            ("X Rotation", 180, 90, lambda v: self.main_app.slider_changed("X Rotation", v)),
            ("Y Rotation", 360, 180, lambda v: self.main_app.slider_changed("Y Rotation", v)),
            ("Z Rotation", 360, 180, lambda v: self.main_app.slider_changed("Z Rotation", v)),
            ("Brightness", 200, 100, lambda v: self.main_app.brightness_changed(v - 100)),
            ("Contrast", 400, 100, lambda v: self.main_app.contrast_changed(v)),
        ]
        for label, maximum, initial, callback in slider_configs:
            self.add_slider_with_buttons(sliders_layout, label, maximum, initial, callback)
        parent_layout.addWidget(sliders_frame)

    def add_slider_with_buttons(self, parent_layout, label_text, maximum, initial_value, callback):
        slider_group = QWidget()
        slider_group_layout = QVBoxLayout(slider_group)
        slider_group_layout.setContentsMargins(0, 0, 0, 5)
        label = QLabel(label_text)
        slider_group_layout.addWidget(label)
        controls_container = QWidget()
        controls_layout = QHBoxLayout(controls_container)
        controls_layout.setContentsMargins(0, 0, 0, 0)
        dec_button = QPushButton("-")
        dec_button.setFixedSize(25, 25)
        dec_button.setStyleSheet("font-weight: bold; background-color: #e0e0e0;")
        controls_layout.addWidget(dec_button)
        slider = QSlider(Qt.Horizontal)
        slider.setRange(0, maximum)
        slider.setValue(initial_value)
        slider.valueChanged.connect(callback)
        controls_layout.addWidget(slider)
        inc_button = QPushButton("+")
        inc_button.setFixedSize(25, 25)
        inc_button.setStyleSheet("font-weight: bold; background-color: #e0e0e0;")
        controls_layout.addWidget(inc_button)
        value_label = QLabel(str(initial_value))
        value_label.setFixedWidth(40)
        value_label.setAlignment(Qt.AlignCenter)
        value_label.setStyleSheet("border: 1px solid #ccc; padding: 2px;")
        controls_layout.addWidget(value_label)
        slider_group_layout.addWidget(controls_container)
        parent_layout.addWidget(slider_group)
        self.sliders[label_text] = {'slider': slider, 'label': value_label, 'callback': callback}
        dec_button.clicked.connect(lambda: self.decrement_slider(label_text))
        inc_button.clicked.connect(lambda: self.increment_slider(label_text))
        slider.valueChanged.connect(lambda value: value_label.setText(str(value)))

    def increment_slider(self, slider_name):
        if slider_name in self.sliders:
            slider = self.sliders[slider_name]['slider']
            slider.setValue(slider.value() + 1)

    def decrement_slider(self, slider_name):
        if slider_name in self.sliders:
            slider = self.sliders[slider_name]['slider']
            slider.setValue(slider.value() - 1)

    def init_zoom_controls(self, parent_layout):
        zoom_frame = QWidget()
        zoom_layout = QVBoxLayout(zoom_frame)
        zoom_label = QLabel("Zoom Controls")
        zoom_label.setStyleSheet("font-weight: bold;")
        zoom_layout.addWidget(zoom_label)
        for plane, attr, reset_func in [
            ("XY", "zoom_xy", self.main_app.reset_zoom_xy),
            ("YZ", "zoom_yz", self.main_app.reset_zoom_yz),
            ("XZ", "zoom_xz", self.main_app.reset_zoom_xz),
        ]:
            frame = QWidget()
            layout = QHBoxLayout(frame)
            layout.addWidget(QLabel(f"{plane} Plane:"))
            slider = QSlider(Qt.Horizontal)
            slider.setRange(int(self.main_app.min_zoom * 10), int(self.main_app.max_zoom * 10))
            slider.setValue(int(getattr(self.main_app, attr) * 10))
            slider.valueChanged.connect(lambda v, a=attr: getattr(self.main_app, f"{a}_slider_changed")(v / 10.0))
            layout.addWidget(slider)
            reset_button = QPushButton("Reset")
            reset_button.clicked.connect(reset_func)
            layout.addWidget(reset_button)
            zoom_layout.addWidget(frame)
            setattr(self, f"{plane.lower()}_zoom_slider", slider)
        self.zoom_info_label = QLabel("Zoom: XY=1.0 YZ=1.0 XZ=1.0")
        self.zoom_info_label.setStyleSheet("font-size: 8pt;")
        zoom_layout.addWidget(self.zoom_info_label)
        self.pan_info_label = QLabel("Pan: XY=(0,0) YZ=(0,0) XZ=(0,0)")
        self.pan_info_label.setStyleSheet("font-size: 8pt;")
        zoom_layout.addWidget(self.pan_info_label)
        parent_layout.addWidget(zoom_frame)

    def update_zoom_info(self):
        zoom_text = f"Zoom: XY={self.main_app.zoom_xy:.1f} YZ={self.main_app.zoom_yz:.1f} XZ={self.main_app.zoom_xz:.1f}"
        self.zoom_info_label.setText(zoom_text)
        pan_text = (
            f"Pan: XY=({self.main_app.pan_xy[0]:.0f},{self.main_app.pan_xy[1]:.0f}) "
            f"YZ=({self.main_app.pan_yz[0]:.0f},{self.main_app.pan_yz[1]:.0f}) "
            f"XZ=({self.main_app.pan_xz[0]:.0f},{self.main_app.pan_xz[1]:.0f})"
        )
        self.pan_info_label.setText(pan_text)

    def init_main_view(self):
        self.main_view_widget = QWidget()
        main_layout = QGridLayout(self.main_view_widget)
        self.panel_3d_handler = VisualizationHandler()
        self.panel_3d_container = QWidget()
        container_layout = QVBoxLayout(self.panel_3d_container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        placeholder_label = QLabel("3D View - Load DICOM data")
        placeholder_label.setAlignment(Qt.AlignCenter)
        placeholder_label.setStyleSheet("background-color: black; color: white;")
        container_layout.addWidget(placeholder_label)

        def create_panel_with_selector(initial_plane, panel_index):
            panel = ImagePanel(initial_plane, self, self)
            controls_widget = QWidget()
            controls_layout = QHBoxLayout(controls_widget)
            controls_layout.setContentsMargins(0, 0, 0, 0)
            selector = QComboBox()
            selector.addItems(["XY", "YZ", "XZ"])
            selector.setCurrentText(initial_plane)
            selector.currentTextChanged.connect(
                lambda text, p=panel: self.main_app.on_plane_selection_changed(p, text)
            )
            lock_checkbox = QCheckBox("Lock")
            lock_checkbox.stateChanged.connect(
                lambda state, p=panel, s=selector: self.main_app.toggle_panel_lock(state, p, s)
            )
            controls_layout.addWidget(selector)
            controls_layout.addStretch()
            controls_layout.addWidget(lock_checkbox)
            container = QWidget()
            layout = QVBoxLayout(container)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(2)
            layout.addWidget(controls_widget)
            layout.addWidget(panel, 1)
            return container, panel, selector, lock_checkbox

        container1, self.panel1, self.selector1, self.lock1 = create_panel_with_selector("XY", 0)
        container2, self.panel2, self.selector2, self.lock2 = create_panel_with_selector("YZ", 1)
        container3, self.panel3, self.selector3, self.lock3 = create_panel_with_selector("XZ", 2)
        self.panels = [self.panel1, self.panel2, self.panel3]
        main_layout.addWidget(self.panel_3d_container, 0, 0)
        main_layout.addWidget(container1, 0, 1)
        main_layout.addWidget(container2, 1, 0)
        main_layout.addWidget(container3, 1, 1)
        main_layout.setColumnStretch(0, 1)
        main_layout.setColumnStretch(1, 1)
        main_layout.setRowStretch(0, 1)
        main_layout.setRowStretch(1, 1)

    def handle_panel_drag(self, panel_index, dx, dy):
        if panel_index == 0:
            self.main_app.pan_xy[0] += dx
            self.main_app.pan_xy[1] += dy
        elif panel_index == 1:
            self.main_app.pan_yz[0] += dx
            self.main_app.pan_yz[1] += dy
        elif panel_index == 2:
            self.main_app.pan_xz[0] += dx
            self.main_app.pan_xz[1] += dy
        self.main_app.update_single_panel(panel_index)
        self.update_zoom_info()

    def handle_panel_zoom(self, panel_index, zoom_in):
        if zoom_in:
            if panel_index == 0: self.main_app.zoom_in_xy()
            elif panel_index == 1: self.main_app.zoom_in_yz()
            elif panel_index == 2: self.main_app.zoom_in_xz()
        else:
            if panel_index == 0: self.main_app.zoom_out_xy()
            elif panel_index == 1: self.main_app.zoom_out_yz()
            elif panel_index == 2: self.main_app.zoom_out_xz()
        self.update_zoom_info()

    def update_panel_image(self, panel, image_data, zoom=1.0, brightness=0, contrast=1.0, pan_offset=(0, 0)):
        if image_data is None:
            panel.current_pixmap = None
            panel.update()
            return
        image = self.create_image_from_array(image_data, brightness, contrast)
        if image is None:
            return
        if zoom != 1.0:
            new_width = int(image.width * zoom)
            new_height = int(image.height * zoom)
            image = image.resize((new_width, new_height), Image.LANCZOS)
        qimage = ImageQt.ImageQt(image)
        pixmap = QPixmap.fromImage(qimage)
        panel.current_pixmap = pixmap
        panel.image_data = image_data
        panel.update()
        self.update_zoom_info()

    def create_image_from_array(self, array, brightness=0, contrast=1.0):
        try:
            min_val = self.main_app.global_min
            max_val = self.main_app.global_max
            if min_val is None or max_val is None:
                min_val, max_val = array.min(), array.max()
            if max_val - min_val > 0:
                array_clipped = np.clip(array, min_val, max_val)
                array_normalized = ((array_clipped - min_val) / (max_val - min_val) * 255)
            else:
                array_normalized = np.zeros(array.shape)
            adjusted_array = array_normalized.astype(np.float32)
            adjusted_array = contrast * (adjusted_array - 128) + 128 + brightness
            adjusted_array = np.clip(adjusted_array, 0, 255).astype(np.uint8)
            return Image.fromarray(adjusted_array, mode='L')
        except Exception as e:
            print(f"Error creating image from array: {e}")
            return None
