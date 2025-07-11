from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,  # type: ignore
                             QPushButton, QLabel, QListWidget, QSlider, QScrollArea) # === ADDED: Import QScrollArea ===
from PyQt5.QtCore import Qt # type: ignore
from PyQt5.QtGui import QPainter, QPen, QPixmap, QColor # type: ignore
from PIL import Image, ImageQt # type: ignore
import numpy as np # type: ignore
# === ADDED ===: Import the handler to be used instead of the old panel class
from handlers.visualization_handler import VisualizationHandler

class ImagePanel(QLabel):
    """Custom widget for displaying medical images with overlays"""

    def __init__(self, plane_name, gui_components, parent=None):
        super().__init__(parent)
        self.plane_name = plane_name
        self.gui_components = gui_components  # Store reference to gui_components
        self.setMinimumSize(300, 300)  # Reduced from 512x512 to 300x300
        self.setStyleSheet("background-color: black; border: 1px solid gray;")
        self.setAlignment(Qt.AlignCenter)

        # Data for drawing
        self.image_data = None
        self.needle_line = None
        self.realtime_lines = []
        self.axes_lines = []

        # Mouse interaction
        self.dragging = False
        self.last_pos = None

        # Enable mouse tracking
        self.setMouseTracking(True)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Draw the image first with pan offset applied
        if hasattr(self, 'current_pixmap') and self.current_pixmap:
            # Get pan offset for this panel
            panel_index = -1
            if self in self.gui_components.panels:
                panel_index = self.gui_components.panels.index(self)

            pan_offset = self.gui_components.main_app.get_pan_for_panel(panel_index)

            # Calculate image position with pan offset
            canvas_width = self.width()
            canvas_height = self.height()
            image_width = self.current_pixmap.width()
            image_height = self.current_pixmap.height()

            # Center the image and apply pan offset
            x = (canvas_width - image_width) // 2 + pan_offset[0]
            y = (canvas_height - image_height) // 2 + pan_offset[1]

            painter.drawPixmap(x, y, self.current_pixmap)

        # Draw axes (these should move with the image)
        for axis in self.axes_lines:
            if axis['type'] == 'horizontal':
                pen = QPen(QColor(axis['color']), 2)
                painter.setPen(pen)
                painter.drawLine(0, int(axis['y']), self.width(), int(axis['y']))
            elif axis['type'] == 'vertical':
                pen = QPen(QColor(axis['color']), 2)
                painter.setPen(pen)
                painter.drawLine(int(axis['x']), 0, int(axis['x']), self.height())

        # Draw needle line (planned) - these should move with the image
        if self.needle_line:
            pen = QPen(QColor(self.needle_line['color']), 3)
            pen.setStyle(Qt.DashLine)
            painter.setPen(pen)
            start = self.needle_line['start']
            end = self.needle_line['end']
            painter.drawLine(int(start[0]), int(start[1]), int(end[0]), int(end[1]))

        # Draw realtime lines - these should move with the image
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
            # Calculate drag distance
            dx = event.x() - self.last_pos.x()
            dy = event.y() - self.last_pos.y()

            # Get panel index (adjust for 3D panel)
            panel_index = -1
            if self in self.gui_components.panels:
                panel_index = self.gui_components.panels.index(self)

            # Call drag handler
            if panel_index >= 0:
                self.gui_components.handle_panel_drag(panel_index, dx, dy)

            self.last_pos = event.pos()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragging = False
            self.setCursor(Qt.ArrowCursor)

    def wheelEvent(self, event):
        # Handle zoom with mouse wheel
        panel_index = -1
        if self in self.gui_components.panels:
            panel_index = self.gui_components.panels.index(self)

        if panel_index >= 0:
            delta = event.angleDelta().y()
            self.gui_components.handle_panel_zoom(panel_index, delta > 0)

# === DELETED ===: The entire VisPy3DPanel class has been removed.

class GUIComponents(QWidget):
    def __init__(self, main_app):
        super().__init__()
        self.main_app = main_app
        self.panels = []
        # Store slider references for button controls
        self.sliders = {}

    def init_toolbar(self):
        """Initialize the toolbar"""
        self.toolbar = QWidget()
        self.toolbar.setStyleSheet("background-color: #f0f0f0; border-bottom: 1px solid #ccc; padding: 5px;")
        toolbar_layout = QHBoxLayout(self.toolbar)
        toolbar_layout.setContentsMargins(5, 5, 5, 5)

        # Menu and file buttons
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

        # Reset pan button
        reset_pan_button = QPushButton("Reset Pan")
        reset_pan_button.setStyleSheet("background-color: lightyellow;")
        reset_pan_button.clicked.connect(self.main_app.reset_pan_all)
        toolbar_layout.addWidget(reset_pan_button)

        # Delete button
        delete_button = QPushButton("Delete File")
        delete_button.setStyleSheet("background-color: salmon;")
        delete_button.clicked.connect(self.main_app.delete_selected_file)
        toolbar_layout.addWidget(delete_button)

        # Add separator
        toolbar_layout.addStretch()

        # Zoom controls
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
        """Initialize the sidebar"""
        # === CHANGED: Create a QScrollArea to hold the sidebar content ===
        self.sidebar = QScrollArea()
        self.sidebar.setWidgetResizable(True)
        self.sidebar.setFixedWidth(320) # Increased width slightly for scrollbar

        # Create a container widget for the actual content
        sidebar_content = QWidget()
        sidebar_layout = QVBoxLayout(sidebar_content)
        
        # File list
        self.list_view = QListWidget()
        self.list_view.itemClicked.connect(self.main_app.list_view_item_click)
        sidebar_layout.addWidget(self.list_view)
        
        # Sliders
        self.init_sliders(sidebar_layout)
        
        # Zoom controls
        self.init_zoom_controls(sidebar_layout)
        
        # Set the content widget for the scroll area
        self.sidebar.setWidget(sidebar_content)

    def init_sliders(self, parent_layout):
        """Initialize control sliders with increment/decrement buttons"""
        sliders_frame = QWidget()
        sliders_layout = QVBoxLayout(sliders_frame)

        # Add sliders with buttons
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
        
        # === REVERTED: Back to Brightness/Contrast sliders ===
        self.add_slider_with_buttons(sliders_layout, "Brightness", 200, 100,
                                   lambda value: self.main_app.brightness_changed(value - 100))
        # === CHANGED: Default contrast slider value set to 100 ===
        self.add_slider_with_buttons(sliders_layout, "Contrast", 200, 100,
                                   lambda value: self.main_app.contrast_changed(value))

        parent_layout.addWidget(sliders_frame)

    def add_slider_with_buttons(self, parent_layout, label_text, maximum, initial_value, callback):
        """Add a slider with label and increment/decrement buttons"""
        # Create container for this slider group
        slider_group = QWidget()
        slider_group_layout = QVBoxLayout(slider_group)
        slider_group_layout.setContentsMargins(0, 0, 0, 5)

        # Label
        label = QLabel(label_text)
        slider_group_layout.addWidget(label)

        # Container for slider and buttons
        controls_container = QWidget()
        controls_layout = QHBoxLayout(controls_container)
        controls_layout.setContentsMargins(0, 0, 0, 0)

        # Decrement button
        dec_button = QPushButton("-")
        dec_button.setFixedSize(25, 25)
        dec_button.setStyleSheet("font-weight: bold; background-color: #e0e0e0;")
        controls_layout.addWidget(dec_button)

        # Slider
        slider = QSlider(Qt.Horizontal)
        slider.setRange(0, maximum)
        slider.setValue(initial_value)
        slider.valueChanged.connect(callback)
        controls_layout.addWidget(slider)

        # Increment button
        inc_button = QPushButton("+")
        inc_button.setFixedSize(25, 25)
        inc_button.setStyleSheet("font-weight: bold; background-color: #e0e0e0;")
        controls_layout.addWidget(inc_button)

        # Value display label
        value_label = QLabel(str(initial_value))
        value_label.setFixedWidth(40)
        value_label.setAlignment(Qt.AlignCenter)
        value_label.setStyleSheet("border: 1px solid #ccc; padding: 2px;")
        controls_layout.addWidget(value_label)

        slider_group_layout.addWidget(controls_container)
        parent_layout.addWidget(slider_group)

        # Store slider reference
        self.sliders[label_text] = {
            'slider': slider,
            'label': value_label,
            'callback': callback
        }

        # Connect button events
        dec_button.clicked.connect(lambda: self.decrement_slider(label_text))
        inc_button.clicked.connect(lambda: self.increment_slider(label_text))

        # Update value label when slider changes
        slider.valueChanged.connect(lambda value: value_label.setText(str(value)))

    def increment_slider(self, slider_name):
        """Increment slider value by 1"""
        if slider_name in self.sliders:
            slider = self.sliders[slider_name]['slider']
            current_value = slider.value()
            max_value = slider.maximum()

            if current_value < max_value:
                new_value = current_value + 1
                slider.setValue(new_value)
                # The valueChanged signal will automatically trigger the callback

    def decrement_slider(self, slider_name):
        """Decrement slider value by 1"""
        if slider_name in self.sliders:
            slider = self.sliders[slider_name]['slider']
            current_value = slider.value()
            min_value = slider.minimum()

            if current_value > min_value:
                new_value = current_value - 1
                slider.setValue(new_value)
                # The valueChanged signal will automatically trigger the callback

    def add_slider(self, parent_layout, label_text, maximum, initial_value, callback):
        """Add a slider with label (legacy method - kept for compatibility)"""
        label = QLabel(label_text)
        parent_layout.addWidget(label)

        slider = QSlider(Qt.Horizontal)
        slider.setRange(0, maximum)
        slider.setValue(initial_value)
        slider.valueChanged.connect(callback)
        parent_layout.addWidget(slider)

    def init_zoom_controls(self, parent_layout):
        """Initialize individual plane zoom controls"""
        zoom_frame = QWidget()
        zoom_layout = QVBoxLayout(zoom_frame)

        zoom_label = QLabel("Zoom Controls")
        zoom_label.setStyleSheet("font-weight: bold;")
        zoom_layout.addWidget(zoom_label)

        # XY Plane controls
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

        # YZ Plane controls
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

        # XZ Plane controls
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

        # Info labels
        self.zoom_info_label = QLabel("Zoom: XY=1.0 YZ=1.0 XZ=1.0")
        self.zoom_info_label.setStyleSheet("font-size: 8pt;")
        zoom_layout.addWidget(self.zoom_info_label)

        self.pan_info_label = QLabel("Pan: XY=(0,0) YZ=(0,0) XZ=(0,0)")
        self.pan_info_label.setStyleSheet("font-size: 8pt;")
        zoom_layout.addWidget(self.pan_info_label)

        parent_layout.addWidget(zoom_frame)

    def update_zoom_info(self):
        """Update zoom level display with needle information"""
        zoom_text = f"Zoom: XY={self.main_app.zoom_xy:.1f} YZ={self.main_app.zoom_yz:.1f} XZ={self.main_app.zoom_xz:.1f}"

        # Add needle center information if available
        needle_center_xy = self.main_app.get_needle_center_xy()
        if needle_center_xy:
            needle_text = f"\nNeedle Center: ({needle_center_xy[0]:.1f}, {needle_center_xy[1]:.1f})"
            zoom_text += needle_text

        self.zoom_info_label.setText(zoom_text)

        # Update pan info
        pan_text = f"Pan: XY=({self.main_app.pan_xy[0]:.0f},{self.main_app.pan_xy[1]:.0f}) YZ=({self.main_app.pan_yz[0]:.0f},{self.main_app.pan_yz[1]:.0f}) XZ=({self.main_app.pan_xz[0]:.0f},{self.main_app.pan_xz[1]:.0f})"
        self.pan_info_label.setText(pan_text)

    def init_main_view(self):
        """Initialize the main view area with 3D panel in first position"""
        self.main_view_widget = QWidget()
        main_layout = QGridLayout(self.main_view_widget)

        # === CHANGED ===: Instantiate the handler and a container for the 3D view
        # 1. Create an instance of the visualization handler
        self.panel_3d_handler = VisualizationHandler()

        # 2. Create a standard QWidget to act as a container for the VisPy canvas
        self.panel_3d_container = QWidget()
        container_layout = QVBoxLayout(self.panel_3d_container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        # Add a placeholder label for better appearance before data is loaded
        placeholder_label = QLabel("3D View - Load DICOM data")
        placeholder_label.setAlignment(Qt.AlignCenter)
        placeholder_label.setStyleSheet("background-color: black; color: white;")
        container_layout.addWidget(placeholder_label)

        # Create 2D image panels
        self.panel_xy = ImagePanel("XY", self, self)  # XY plane
        self.panel_yz = ImagePanel("YZ", self, self)  # YZ plane
        self.panel_xz = ImagePanel("XZ", self, self)  # XZ plane

        # Add panels to grid: 3D container in top-left, then XY, YZ, XZ
        main_layout.addWidget(self.panel_3d_container, 0, 0) # Add the container, not the handler
        main_layout.addWidget(self.panel_xy, 0, 1)           # XY plane
        main_layout.addWidget(self.panel_yz, 1, 0)           # YZ plane
        main_layout.addWidget(self.panel_xz, 1, 1)           # XZ plane

        # Store panels for easy access (2D panels only)
        self.panels = [self.panel_xy, self.panel_yz, self.panel_xz]

        # Set equal column and row stretches
        main_layout.setColumnStretch(0, 1)
        main_layout.setColumnStretch(1, 1)
        main_layout.setRowStretch(0, 1)
        main_layout.setRowStretch(1, 1)

    def handle_panel_drag(self, panel_index, dx, dy):
        """Handle panel drag for panning (2D panels only)"""
        if panel_index == 0:  # XY plane
            self.main_app.pan_xy[0] += dx
            self.main_app.pan_xy[1] += dy
        elif panel_index == 1:  # YZ plane
            self.main_app.pan_yz[0] += dx
            self.main_app.pan_yz[1] += dy
        elif panel_index == 2:  # XZ plane
            self.main_app.pan_xz[0] += dx
            self.main_app.pan_xz[1] += dy

        # Update the display
        self.main_app.update_single_panel(panel_index)
        self.update_zoom_info()

    def handle_panel_zoom(self, panel_index, zoom_in):
        """Handle panel zoom with mouse wheel (2D panels only)"""
        if zoom_in:
            if panel_index == 0:
                self.main_app.zoom_in_xy()
            elif panel_index == 1:
                self.main_app.zoom_in_yz()
            elif panel_index == 2:
                self.main_app.zoom_in_xz()
        else:
            if panel_index == 0:
                self.main_app.zoom_out_xy()
            elif panel_index == 1:
                self.main_app.zoom_out_yz()
            elif panel_index == 2:
                self.main_app.zoom_out_xz()

        self.update_zoom_info()

    # === REVERTED: Function signature now takes brightness and contrast ===
    def update_panel_image(self, panel, image_data, zoom=1.0, brightness=0, contrast=1.0, pan_offset=(0, 0)):
        """Update image in a panel with zoom and pan support"""
        if image_data is None:
            return

        # === REVERTED: Pass brightness and contrast to the image creation function ===
        image = self.create_image_from_array(image_data, brightness, contrast)
        if image is None:
            return

        # Apply zoom transformation
        if zoom != 1.0:
            new_width = int(image.width * zoom)
            new_height = int(image.height * zoom)
            image = image.resize((new_width, new_height), Image.LANCZOS)

        # Convert to QPixmap
        qimage = ImageQt.ImageQt(image)
        pixmap = QPixmap.fromImage(qimage)

        # Store the pixmap for custom drawing (don't set it directly)
        panel.current_pixmap = pixmap
        panel.image_data = image_data

        # Clear the label pixmap so we can draw manually
        panel.setPixmap(QPixmap())

        # Trigger repaint
        panel.update()

        # Update zoom info display
        self.update_zoom_info()

    # === KEPT: Use global min/max for consistent normalization across all planes ===
    def create_image_from_array(self, array, brightness=0, contrast=1.0):
        """Create PIL Image from numpy array with brightness/contrast adjustment"""
        try:
            # Use global min/max from the main app for consistent normalization
            min_val = self.main_app.global_min
            max_val = self.main_app.global_max

            # Fallback to local slice min/max if global values aren't available
            if min_val is None or max_val is None:
                min_val, max_val = array.min(), array.max()

            # Normalize the array to 0-255 range based on the determined min/max
            if max_val - min_val > 0:
                # Clip array values to the normalization range to prevent artifacts
                array_clipped = np.clip(array, min_val, max_val)
                array_normalized = ((array_clipped - min_val) / (max_val - min_val) * 255)
            else:
                array_normalized = np.zeros(array.shape)

            # Apply brightness and contrast using a standard formula
            adjusted_array = array_normalized.astype(np.float32)
            adjusted_array = contrast * (adjusted_array - 128) + 128 + brightness

            # Clip final values to be in 0-255 range
            adjusted_array = np.clip(adjusted_array, 0, 255)
            adjusted_array = adjusted_array.astype(np.uint8)

            # Create PIL Image
            image = Image.fromarray(adjusted_array, mode='L')  # 'L' for grayscale
            return image
        except Exception as e:
            print(f"Error creating image from array: {e}")
            return None