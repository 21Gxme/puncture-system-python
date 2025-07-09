from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
                             QPushButton, QLabel, QListWidget, QSlider, QScrollArea,
                             QRadioButton, QGroupBox) # === ADDED: Import QRadioButton, QGroupBox ===
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPainter, QPen, QPixmap, QColor
from PIL import Image, ImageQt
import numpy as np
from handlers.visualization_handler import VisualizationHandler

class ImagePanel(QLabel):
    """Custom widget for displaying medical images with overlays"""

    def __init__(self, plane_name, gui_components, parent=None):
        super().__init__(parent)
        self.plane_name = plane_name
        self.gui_components = gui_components
        self.setMinimumSize(300, 300)
        self.setStyleSheet("background-color: black; border: 1px solid gray;")
        self.setAlignment(Qt.AlignCenter)
        self.image_data = None
        self.needle_line = None
        self.realtime_lines = []
        self.axes_lines = []
        self.dragging = False
        self.last_pos = None
        self.setMouseTracking(True)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        if hasattr(self, 'current_pixmap') and self.current_pixmap:
            panel_index = -1
            if self in self.gui_components.panels:
                panel_index = self.gui_components.panels.index(self)
            pan_offset = self.gui_components.main_app.get_pan_for_panel(panel_index)
            canvas_width = self.width()
            canvas_height = self.height()
            image_width = self.current_pixmap.width()
            image_height = self.current_pixmap.height()
            x = (canvas_width - image_width) // 2 + pan_offset[0]
            y = (canvas_height - image_height) // 2 + pan_offset[1]
            painter.drawPixmap(x, y, self.current_pixmap)

        for axis in self.axes_lines:
            if axis['type'] == 'horizontal':
                pen = QPen(QColor(axis['color']), 2)
                painter.setPen(pen)
                painter.drawLine(0, int(axis['y']), self.width(), int(axis['y']))
            elif axis['type'] == 'vertical':
                pen = QPen(QColor(axis['color']), 2)
                painter.setPen(pen)
                painter.drawLine(int(axis['x']), 0, int(axis['x']), self.height())

        if self.needle_line:
            pen = QPen(QColor(self.needle_line['color']), 3)
            pen.setStyle(Qt.DashLine)
            painter.setPen(pen)
            start = self.needle_line['start']
            end = self.needle_line['end']
            painter.drawLine(int(start[0]), int(start[1]), int(end[0]), int(end[1]))

        for line in self.realtime_lines:
            pen = QPen(QColor(line['color']), 3)
            pen.setStyle(Qt.DashLine)
            painter.setPen(pen)
            start = line['start']
            end = line['end']
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
            panel_index = -1
            if self in self.gui_components.panels:
                panel_index = self.gui_components.panels.index(self)
            if panel_index >= 0:
                self.gui_components.handle_panel_drag(panel_index, dx, dy)
            self.last_pos = event.pos()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragging = False
            self.setCursor(Qt.ArrowCursor)

    def wheelEvent(self, event):
        panel_index = -1
        if self in self.gui_components.panels:
            panel_index = self.gui_components.panels.index(self)
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
        menu_button = QPushButton("Menu")
        menu_button.clicked.connect(self.main_app.toggle_sidebar)
        toolbar_layout.addWidget(menu_button)
        file_button = QPushButton("File")
        file_button.clicked.connect(self.main_app.show_file_menu)
        toolbar_layout.addWidget(file_button)
        load_button = QPushButton("Load")
        load_button.clicked.connect(self.main_app.btnLoadPictures_Click)
        toolbar_layout.addWidget(load_button)
        start_button = QPushButton("Start Real-Time Route")
        start_button.clicked.connect(self.main_app.start_realtime_data)
        toolbar_layout.addWidget(start_button)
        stop_button = QPushButton("Stop Real-Time Route")
        stop_button.clicked.connect(self.main_app.stop_realtime_data)
        toolbar_layout.addWidget(stop_button)
        reset_pan_button = QPushButton("Reset Pan")
        reset_pan_button.setStyleSheet("background-color: lightyellow;")
        reset_pan_button.clicked.connect(self.main_app.reset_pan_all)
        toolbar_layout.addWidget(reset_pan_button)
        delete_button = QPushButton("Delete File")
        delete_button.setStyleSheet("background-color: salmon;")
        delete_button.clicked.connect(self.main_app.delete_selected_file)
        toolbar_layout.addWidget(delete_button)
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
        # === ADDED: Initialize new projection controls ===
        self.init_projection_controls(sidebar_layout)
        self.sidebar.setWidget(sidebar_content)

    def init_sliders(self, parent_layout):
        sliders_frame = QWidget()
        sliders_layout = QVBoxLayout(sliders_frame)
        self.add_slider_with_buttons(sliders_layout, "X Value", 512, 256,
                                   lambda value: self.main_app.slider_changed("X Value", value))
        self.add_slider_with_buttons(sliders_layout, "Y Value", 512, 256,
                                   lambda value: self.main_app.slider_changed("Y Value", value))
        self.add_slider_with_buttons(sliders_layout, "Z Value", 512, 256,
                                   lambda value: self.main_app.slider_changed("Z Value", value))
        self.add_slider_with_buttons(sliders_layout, "X Rotation", 180, 90,
                                   lambda value: self.main_app.slider_changed("X Rotation", value))
        self.add_slider_with_buttons(sliders_layout, "Y Rotation", 360, 180,
                                   lambda value: self.main_app.slider_changed("Y Rotation", value))
        self.add_slider_with_buttons(sliders_layout, "Z Rotation", 360, 180,
                                   lambda value: self.main_app.slider_changed("Z Rotation", value))
        self.add_slider_with_buttons(sliders_layout, "Brightness", 200, 100,
                                   lambda value: self.main_app.brightness_changed(value - 100))
        self.add_slider_with_buttons(sliders_layout, "Contrast", 200, 100,
                                   lambda value: self.main_app.contrast_changed(value))
        parent_layout.addWidget(sliders_frame)

    # === ADDED: Method to create projection mode controls ===
    def init_projection_controls(self, parent_layout):
        """Initialize projection mode controls"""
        projection_group = QGroupBox("Projection Mode")
        projection_group.setStyleSheet("font-weight: bold;")
        projection_layout = QVBoxLayout()

        modes = ["Slice", "MIP", "MinIP", "Average"]
        self.projection_buttons = {}

        for mode in modes:
            button = QRadioButton(mode)
            # Use a lambda with a default argument to capture the correct mode for each button
            button.toggled.connect(lambda checked, m=mode: self.main_app.projection_mode_changed(m, checked))
            projection_layout.addWidget(button)
            self.projection_buttons[mode] = button

        # Set the default selection
        self.projection_buttons["Slice"].setChecked(True)

        projection_group.setLayout(projection_layout)
        parent_layout.addWidget(projection_group)


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
        self.sliders[label_text] = {
            'slider': slider,
            'label': value_label,
            'callback': callback
        }
        dec_button.clicked.connect(lambda: self.decrement_slider(label_text))
        inc_button.clicked.connect(lambda: self.increment_slider(label_text))
        slider.valueChanged.connect(lambda value: value_label.setText(str(value)))

    def increment_slider(self, slider_name):
        if slider_name in self.sliders:
            slider = self.sliders[slider_name]['slider']
            current_value = slider.value()
            max_value = slider.maximum()
            if current_value < max_value:
                new_value = current_value + 1
                slider.setValue(new_value)

    def decrement_slider(self, slider_name):
        if slider_name in self.sliders:
            slider = self.sliders[slider_name]['slider']
            current_value = slider.value()
            min_value = slider.minimum()
            if current_value > min_value:
                new_value = current_value - 1
                slider.setValue(new_value)

    def add_slider(self, parent_layout, label_text, maximum, initial_value, callback):
        label = QLabel(label_text)
        parent_layout.addWidget(label)
        slider = QSlider(Qt.Horizontal)
        slider.setRange(0, maximum)
        slider.setValue(initial_value)
        slider.valueChanged.connect(callback)
        parent_layout.addWidget(slider)

    def init_zoom_controls(self, parent_layout):
        zoom_frame = QWidget()
        zoom_layout = QVBoxLayout(zoom_frame)
        zoom_label = QLabel("Zoom Controls")
        zoom_label.setStyleSheet("font-weight: bold;")
        zoom_layout.addWidget(zoom_label)
        xy_frame = QWidget()
        xy_layout = QHBoxLayout(xy_frame)
        xy_layout.addWidget(QLabel("XY Plane:"))
        self.xy_zoom_slider = QSlider(Qt.Horizontal)
        self.xy_zoom_slider.setRange(int(self.main_app.min_zoom * 10), int(self.main_app.max_zoom * 10))
        self.xy_zoom_slider.setValue(int(self.main_app.zoom_xy * 10))
        self.xy_zoom_slider.valueChanged.connect(lambda v: self.main_app.zoom_xy_slider_changed(v / 10.0))
        xy_layout.addWidget(self.xy_zoom_slider)
        xy_reset_button = QPushButton("Reset")
        xy_reset_button.setStyleSheet("background-color: lightblue;")
        xy_reset_button.clicked.connect(self.main_app.reset_zoom_xy)
        xy_layout.addWidget(xy_reset_button)
        zoom_layout.addWidget(xy_frame)
        yz_frame = QWidget()
        yz_layout = QHBoxLayout(yz_frame)
        yz_layout.addWidget(QLabel("YZ Plane:"))
        self.yz_zoom_slider = QSlider(Qt.Horizontal)
        self.yz_zoom_slider.setRange(int(self.main_app.min_zoom * 10), int(self.main_app.max_zoom * 10))
        self.yz_zoom_slider.setValue(int(self.main_app.zoom_yz * 10))
        self.yz_zoom_slider.valueChanged.connect(lambda v: self.main_app.zoom_yz_slider_changed(v / 10.0))
        yz_layout.addWidget(self.yz_zoom_slider)
        yz_reset_button = QPushButton("Reset")
        yz_reset_button.setStyleSheet("background-color: lightblue;")
        yz_reset_button.clicked.connect(self.main_app.reset_zoom_yz)
        yz_layout.addWidget(yz_reset_button)
        zoom_layout.addWidget(yz_frame)
        xz_frame = QWidget()
        xz_layout = QHBoxLayout(xz_frame)
        xz_layout.addWidget(QLabel("XZ Plane:"))
        self.xz_zoom_slider = QSlider(Qt.Horizontal)
        self.xz_zoom_slider.setRange(int(self.main_app.min_zoom * 10), int(self.main_app.max_zoom * 10))
        self.xz_zoom_slider.setValue(int(self.main_app.zoom_xz * 10))
        self.xz_zoom_slider.valueChanged.connect(lambda v: self.main_app.zoom_xz_slider_changed(v / 10.0))
        xz_layout.addWidget(self.xz_zoom_slider)
        xz_reset_button = QPushButton("Reset")
        xz_reset_button.setStyleSheet("background-color: lightblue;")
        xz_reset_button.clicked.connect(self.main_app.reset_zoom_xz)
        xz_layout.addWidget(xz_reset_button)
        zoom_layout.addWidget(xz_frame)
        self.zoom_info_label = QLabel("Zoom: XY=1.0 YZ=1.0 XZ=1.0")
        self.zoom_info_label.setStyleSheet("font-size: 8pt;")
        zoom_layout.addWidget(self.zoom_info_label)
        self.pan_info_label = QLabel("Pan: XY=(0,0) YZ=(0,0) XZ=(0,0)")
        self.pan_info_label.setStyleSheet("font-size: 8pt;")
        zoom_layout.addWidget(self.pan_info_label)
        parent_layout.addWidget(zoom_frame)

    def update_zoom_info(self):
        zoom_text = f"Zoom: XY={self.main_app.zoom_xy:.1f} YZ={self.main_app.zoom_yz:.1f} XZ={self.main_app.zoom_xz:.1f}"
        needle_center_xy = self.main_app.get_needle_center_xy()
        if needle_center_xy:
            needle_text = f"\nNeedle Center: ({needle_center_xy[0]:.1f}, {needle_center_xy[1]:.1f})"
            zoom_text += needle_text
        self.zoom_info_label.setText(zoom_text)
        pan_text = f"Pan: XY=({self.main_app.pan_xy[0]:.0f},{self.main_app.pan_xy[1]:.0f}) YZ=({self.main_app.pan_yz[0]:.0f},{self.main_app.pan_yz[1]:.0f}) XZ=({self.main_app.pan_xz[0]:.0f},{self.main_app.pan_xz[1]:.0f})"
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
        self.panel_xy = ImagePanel("XY", self, self)
        self.panel_yz = ImagePanel("YZ", self, self)
        self.panel_xz = ImagePanel("XZ", self, self)
        main_layout.addWidget(self.panel_3d_container, 0, 0)
        main_layout.addWidget(self.panel_xy, 0, 1)
        main_layout.addWidget(self.panel_yz, 1, 0)
        main_layout.addWidget(self.panel_xz, 1, 1)
        self.panels = [self.panel_xy, self.panel_yz, self.panel_xz]
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
        panel.setPixmap(QPixmap())
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
            adjusted_array = np.clip(adjusted_array, 0, 255)
            adjusted_array = adjusted_array.astype(np.uint8)
            image = Image.fromarray(adjusted_array, mode='L')
            return image
        except Exception as e:
            print(f"Error creating image from array: {e}")
            return None