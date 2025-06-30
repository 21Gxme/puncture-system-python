# สร้างไฟล์ gui_components.py แบบ PyQt5
gui_components_content = '''from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, 
                            QLabel, QPushButton, QSlider, QListWidget, QFrame, 
                            QGroupBox, QDoubleSpinBox, QSpinBox)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QPixmap, QImage, QPainter, QPen, QColor
from PIL import Image, ImageTk
import numpy as np

class GUIComponents(QWidget):
    def __init__(self, main_app):
        """
        Initialize GUI Components for PyQt5
        
        :param main_app: Reference to the main application window
        """
        super().__init__()
        self.main_app = main_app
        self.panels = []
        
        # Initialize drag state variables
        self.drag_data = {
            'dragging': False,
            'start_x': 0,
            'start_y': 0,
            'panel_index': -1
        }
        
        self.init_sidebar()

    def init_sidebar(self):
        """Initialize the sidebar with controls"""
        # Main sidebar layout
        sidebar_layout = QVBoxLayout(self)
        
        # File list section
        self.init_file_list(sidebar_layout)
        
        # Control sliders section
        self.init_sliders(sidebar_layout)
        
        # Zoom controls section
        self.init_zoom_controls(sidebar_layout)
        
        # Set fixed width for sidebar
        self.setFixedWidth(300)
        self.setStyleSheet("QWidget { background-color: #f0f0f0; }")

    def init_file_list(self, parent_layout):
        """Initialize file list widget"""
        # File list group
        file_group = QGroupBox("DICOM Files")
        file_layout = QVBoxLayout(file_group)
        
        # List widget for DICOM files
        self.list_view = QListWidget()
        self.list_view.itemClicked.connect(self.main_app.list_view_item_click)
        file_layout.addWidget(self.list_view)
        
        parent_layout.addWidget(file_group)

    def init_sliders(self, parent_layout):
        """Initialize control sliders"""
        sliders_group = QGroupBox("Image Controls")
        sliders_layout = QVBoxLayout(sliders_group)
        
        # X Value slider
        self.x_slider = self.add_slider(sliders_layout, "X Value", 0, 512, 256, 
                                       lambda value: self.main_app.slider_changed("X Value", value))
        
        # Y Value slider
        self.y_slider = self.add_slider(sliders_layout, "Y Value", 0, 512, 256,
                                       lambda value: self.main_app.slider_changed("Y Value", value))
        
        # Z Value slider
        self.z_slider = self.add_slider(sliders_layout, "Z Value", 0, 512, 256,
                                       lambda value: self.main_app.slider_changed("Z Value", value))
        
        # Rotation sliders
        rotation_group = QGroupBox("3D Rotation")
        rotation_layout = QVBoxLayout(rotation_group)
        
        # X Rotation slider
        self.x_rot_slider = self.add_slider(rotation_layout, "X Rotation", 0, 180, 90,
                                           lambda value: self.main_app.slider_changed("X Rotation", value))
        
        # Y Rotation slider
        self.y_rot_slider = self.add_slider(rotation_layout, "Y Rotation", 0, 360, 180,
                                           lambda value: self.main_app.slider_changed("Y Rotation", value))
        
        # Z Rotation slider
        self.z_rot_slider = self.add_slider(rotation_layout, "Z Rotation", 0, 360, 180,
                                           lambda value: self.main_app.slider_changed("Z Rotation", value))
        
        sliders_layout.addWidget(rotation_group)
        parent_layout.addWidget(sliders_group)

    def add_slider(self, parent_layout, label_text, minimum, maximum, initial_value, callback):
        """Add a slider with label to the layout"""
        # Container widget
        slider_widget = QWidget()
        slider_layout = QVBoxLayout(slider_widget)
        slider_layout.setContentsMargins(5, 5, 5, 5)
        
        # Label
        label = QLabel(label_text)
        slider_layout.addWidget(label)
        
        # Horizontal layout for slider and value display
        slider_row = QHBoxLayout()
        
        # Slider
        slider = QSlider(Qt.Horizontal)
        slider.setMinimum(minimum)
        slider.setMaximum(maximum)
        slider.setValue(initial_value)
        slider.valueChanged.connect(callback)
        slider_row.addWidget(slider)
        
        # Value display
        value_label = QLabel(str(initial_value))
        value_label.setFixedWidth(40)
        slider.valueChanged.connect(lambda v: value_label.setText(str(v)))
        slider_row.addWidget(value_label)
        
        slider_layout.addLayout(slider_row)
        parent_layout.addWidget(slider_widget)
        
        return slider

    def init_zoom_controls(self, parent_layout):
        """Initialize zoom control widgets"""
        zoom_group = QGroupBox("Zoom Controls")
        zoom_layout = QVBoxLayout(zoom_group)
        
        # XY Plane controls
        xy_frame = QWidget()
        xy_layout = QHBoxLayout(xy_frame)
        xy_layout.addWidget(QLabel("XY Plane:"))
        
        self.xy_zoom_spinbox = QDoubleSpinBox()
        self.xy_zoom_spinbox.setRange(self.main_app.min_zoom, self.main_app.max_zoom)
        self.xy_zoom_spinbox.setSingleStep(0.1)
        self.xy_zoom_spinbox.setValue(self.main_app.zoom_xy)
        self.xy_zoom_spinbox.valueChanged.connect(self.xy_zoom_changed)
        xy_layout.addWidget(self.xy_zoom_spinbox)
        
        xy_reset_btn = QPushButton("Reset")
        xy_reset_btn.clicked.connect(self.main_app.reset_zoom_xy)
        xy_layout.addWidget(xy_reset_btn)
        
        zoom_layout.addWidget(xy_frame)
        
        # YZ Plane controls
        yz_frame = QWidget()
        yz_layout = QHBoxLayout(yz_frame)
        yz_layout.addWidget(QLabel("YZ Plane:"))
        
        self.yz_zoom_spinbox = QDoubleSpinBox()
        self.yz_zoom_spinbox.setRange(self.main_app.min_zoom, self.main_app.max_zoom)
        self.yz_zoom_spinbox.setSingleStep(0.1)
        self.yz_zoom_spinbox.setValue(self.main_app.zoom_yz)
        self.yz_zoom_spinbox.valueChanged.connect(self.yz_zoom_changed)
        yz_layout.addWidget(self.yz_zoom_spinbox)
        
        yz_reset_btn = QPushButton("Reset")
        yz_reset_btn.clicked.connect(self.main_app.reset_zoom_yz)
        yz_layout.addWidget(yz_reset_btn)
        
        zoom_layout.addWidget(yz_frame)
        
        # XZ Plane controls
        xz_frame = QWidget()
        xz_layout = QHBoxLayout(xz_frame)
        xz_layout.addWidget(QLabel("XZ Plane:"))
        
        self.xz_zoom_spinbox = QDoubleSpinBox()
        self.xz_zoom_spinbox.setRange(self.main_app.min_zoom, self.main_app.max_zoom)
        self.xz_zoom_spinbox.setSingleStep(0.1)
        self.xz_zoom_spinbox.setValue(self.main_app.zoom_xz)
        self.xz_zoom_spinbox.valueChanged.connect(self.xz_zoom_changed)
        xz_layout.addWidget(self.xz_zoom_spinbox)
        
        xz_reset_btn = QPushButton("Reset")
        xz_reset_btn.clicked.connect(self.main_app.reset_zoom_xz)
        xz_layout.addWidget(xz_reset_btn)
        
        zoom_layout.addWidget(xz_frame)
        
        # Info display
        self.zoom_info_label = QLabel("Zoom: XY=1.0 YZ=1.0 XZ=1.0")
        self.zoom_info_label.setStyleSheet("font-size: 10px; color: #666;")
        zoom_layout.addWidget(self.zoom_info_label)
        
        self.pan_info_label = QLabel("Pan: XY=(0,0) YZ=(0,0) XZ=(0,0)")
        self.pan_info_label.setStyleSheet("font-size: 10px; color: #666;")
        zoom_layout.addWidget(self.pan_info_label)
        
        parent_layout.addWidget(zoom_group)

    def xy_zoom_changed(self, value):
        """Handle XY zoom spinbox changes"""
        self.main_app.zoom_xy = value
        self.main_app.update_images()
        self.update_zoom_info()

    def yz_zoom_changed(self, value):
        """Handle YZ zoom spinbox changes"""
        self.main_app.zoom_yz = value
        self.main_app.update_images()
        self.update_zoom_info()

    def xz_zoom_changed(self, value):
        """Handle XZ zoom spinbox changes"""
        self.main_app.zoom_xz = value
        self.main_app.update_images()
        self.update_zoom_info()

    def update_zoom_info(self):
        """Update zoom level display"""
        zoom_text = f"Zoom: XY={self.main_app.zoom_xy:.1f} YZ={self.main_app.zoom_yz:.1f} XZ={self.main_app.zoom_xz:.1f}"
        
        # Add needle center information if available
        if hasattr(self.main_app, 'get_needle_center_xy'):
            needle_center_xy = self.main_app.get_needle_center_xy()
            if needle_center_xy:
                needle_text = f"\\nNeedle Center: ({needle_center_xy[0]:.1f}, {needle_center_xy[1]:.1f})"
                zoom_text += needle_text
        
        self.zoom_info_label.setText(zoom_text)
        
        # Update pan info
        pan_text = f"Pan: XY=({self.main_app.pan_xy[0]:.0f},{self.main_app.pan_xy[1]:.0f}) YZ=({self.main_app.pan_yz[0]:.0f},{self.main_app.pan_yz[1]:.0f}) XZ=({self.main_app.pan_xz[0]:.0f},{self.main_app.pan_xz[1]:.0f})"
        self.pan_info_label.setText(pan_text)

    def update_zoom_spinboxes(self):
        """Update zoom spinbox values (called from main app)"""
        self.xy_zoom_spinbox.setValue(self.main_app.zoom_xy)
        self.yz_zoom_spinbox.setValue(self.main_app.zoom_yz)
        self.xz_zoom_spinbox.setValue(self.main_app.zoom_xz)

    def setup_mouse_zoom(self):
        """Setup mouse wheel zoom for panels (placeholder for future implementation)"""
        # TODO: Implement mouse wheel zoom for QLabel panels
        # This would require custom QLabel subclass with wheelEvent override
        pass

    def setup_drag_support(self):
        """Setup drag support for panels (placeholder for future implementation)"""
        # TODO: Implement drag support for QLabel panels
        # This would require custom QLabel subclass with mouse event overrides
        pass

    def create_image_from_array(self, array):
        """Create QImage from numpy array"""
        try:
            # Normalize the array to 0-255 range
            if array.dtype != np.uint8:
                array_normalized = ((array - array.min()) / (array.max() - array.min()) * 255).astype(np.uint8)
            else:
                array_normalized = array
            
            # Create QImage
            height, width = array_normalized.shape
            bytes_per_line = width
            q_image = QImage(array_normalized.data, width, height, bytes_per_line, QImage.Format_Grayscale8)
            return q_image
        except Exception as e:
            print(f"Error creating QImage from array: {e}")
            return None

    def update_panel_image(self, panel, image_data, zoom=1.0, pan_offset=(0, 0)):
        """Update image in a panel with zoom and pan support"""
        if image_data is None:
            return
        
        # Create QImage from numpy array
        q_image = self.create_image_from_array(image_data)
        if q_image is None:
            return
        
        # Apply zoom transformation
        if zoom != 1.0:
            new_width = int(q_image.width() * zoom)
            new_height = int(q_image.height() * zoom)
            q_image = q_image.scaled(new_width, new_height, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        
        # Convert to QPixmap
        pixmap = QPixmap.fromImage(q_image)
        
        # Apply pan offset (this would need custom implementation for proper panning)
        # For now, just scale to fit the panel
        scaled_pixmap = pixmap.scaled(panel.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        
        # Set pixmap to label
        panel.setPixmap(scaled_pixmap)
        
        # Update zoom info display
        self.update_zoom_info()

    def draw_overlay_on_panel(self, panel, lines, color="green"):
        """Draw overlay lines on a panel (for needle visualization)"""
        # Get current pixmap
        current_pixmap = panel.pixmap()
        if current_pixmap is None:
            return
        
        # Create a copy to draw on
        pixmap_copy = current_pixmap.copy()
        
        # Create painter
        painter = QPainter(pixmap_copy)
        
        # Set pen for drawing
        pen = QPen(QColor(color))
        pen.setWidth(3)
        painter.setPen(pen)
        
        # Draw lines
        for line in lines:
            if len(line) >= 4:  # x1, y1, x2, y2
                painter.drawLine(line[0], line[1], line[2], line[3])
        
        painter.end()
        
        # Set the modified pixmap back to the panel
        panel.setPixmap(pixmap_copy)

    def clear_panel_overlays(self, panel):
        """Clear overlays from a panel (redraw original image)"""
        # This would require storing the original pixmap separately
        # For now, this is a placeholder
        pass

# Custom QLabel class for advanced image display (optional enhancement)
class ImageDisplayLabel(QLabel):
    """Custom QLabel with mouse interaction support"""
    
    # Signals for mouse events
    mousePressed = pyqtSignal(int, int)  # x, y coordinates
    mouseMoved = pyqtSignal(int, int)
    mouseReleased = pyqtSignal(int, int)
    wheelScrolled = pyqtSignal(int)  # delta
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(512, 512)
        self.setStyleSheet("border: 1px solid gray; background-color: black;")
        self.setAlignment(Qt.AlignCenter)
        self.setScaledContents(False)
        
        # Mouse tracking
        self.setMouseTracking(True)
        self.dragging = False
        self.last_pos = None

    def mousePressEvent(self, event):
        """Handle mouse press events"""
        if event.button() == Qt.LeftButton:
            self.dragging = True
            self.last_pos = event.pos()
            self.mousePressed.emit(event.x(), event.y())
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        """Handle mouse move events"""
        if self.dragging and self.last_pos:
            self.mouseMoved.emit(event.x(), event.y())
            self.last_pos = event.pos()
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        """Handle mouse release events"""
        if event.button() == Qt.LeftButton:
            self.dragging = False
            self.last_pos = None
            self.mouseReleased.emit(event.x(), event.y())
        super().mouseReleaseEvent(event)

    def wheelEvent(self, event):
        """Handle mouse wheel events"""
        self.wheelScrolled.emit(event.angleDelta().y())
        super().wheelEvent(event)
'''

# บันทึกไฟล์
with open('gui_components_pyqt5.py', 'w', encoding='utf-8') as f:
    f.write(gui_components_content)

print("สร้างไฟล์ gui_components_pyqt5.py เรียบร้อยแล้ว!")