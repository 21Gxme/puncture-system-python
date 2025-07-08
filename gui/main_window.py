import os
import numpy as np # type: ignore
import shutil
# === CHANGED ===: QWidget and QVBoxLayout are used for the 3D panel container
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QFileDialog, QMessageBox)  # type: ignore
from PyQt5.QtWidgets import QMenu # type: ignore
from PyQt5.QtCore import QTimer # type: ignore
from data_structures import Vector3D
from handlers.dicom_handler import DicomHandler
from handlers.csv_handler import CSVHandler
from gui.gui_components import GUIComponents
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QFileDialog, QMessageBox, QLabel)  # type: ignore
from PyQt5.QtCore import Qt   # type: ignore


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CT-Guided Puncture Assistance System")
        self.setGeometry(100, 100, 800, 600)
        
        # Initialize handlers
        self.dicom_handler = DicomHandler()
        self.csv_handler = CSVHandler(self.draw_realtime_line)
        
        # Initialize variables
        self.X_init = 256
        self.Y_init = 256
        self.Z_init = 256
        self.X = 256
        self.Y = 256
        self.Z = 256
        self.Z_for_axis = 256

        self.thetaX = 0
        self.thetaY = 0
        self.thetaZ = 0

        # Initialize zoom factors for each plane
        self.zoom_xy = 1.0
        self.zoom_yz = 1.0
        self.zoom_xz = 1.0
        self.zoom_all = 1.0
        self.min_zoom = 0.1
        self.max_zoom = 5.0
        self.zoom_step = 0.1

        self.CenterPoint = Vector3D(0, 0, 0)
        self.NeedleMatrix3D = np.zeros((512, 512, 512), dtype=np.int16)
        self.NowMatrix3D = np.zeros((512, 512, 512), dtype=np.int16)

        self.IsSelectedItem = 0
        self.y_end = 512
        self.ImageStride = 512 * 2
        self.ImagePixelSize = 512 * 512 * 2
        self.MaxCTvalue = 0
        self.CT_Adjust = -1000

        self.needleVector = []
        self.ok = 0
        self._count = 0
        self.timer = None
        self.selectedItem = None

        self.is_clear = False
        self.plan_line_deleted = False
        self.realtime_line_deleted = False
        
        self.dataList = []
        self.point_start = None
        self.point_end = None
        
        self.pan_xy = [0, 0]
        self.pan_yz = [0, 0]
        self.pan_xz = [0, 0]
        
        # Store original needle coordinates in image space (0-512 range)
        self.original_needle_coords = {
            'xy': {'start': None, 'end': None},
            'yz': {'start': None, 'end': None}, 
            'xz': {'start': None, 'end': None}
        }
        
        # Cache for real-time needle coordinates in image space
        self.realtime_needle_coords = {
            'xy': [],
            'yz': [],
            'xz': []
        }
        
        # Smooth rendering timer for real-time updates
        self.smooth_render_timer = QTimer()
        self.smooth_render_timer.timeout.connect(self.smooth_render_update)
        self.smooth_render_timer.setSingleShot(True)
        
        # Initialize GUI
        self.gui_components = GUIComponents(self)
        self.init_ui()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        self.gui_components.init_toolbar()
        main_layout.addWidget(self.gui_components.toolbar)
        content_layout = QHBoxLayout()
        self.gui_components.init_sidebar()
        self.gui_components.init_main_view()
        content_layout.addWidget(self.gui_components.sidebar)
        content_layout.addWidget(self.gui_components.main_view_widget, 1)
        main_layout.addLayout(content_layout)

    def cache_realtime_coordinates(self):
        if not hasattr(self.csv_handler, 'realtime_points') or not self.csv_handler.realtime_points:
            return
        self.realtime_needle_coords = {'xy': [], 'yz': [], 'xz': []}
        for point in self.csv_handler.realtime_points:
            if len(point) >= 2:
                self.realtime_needle_coords['xy'].append((point[0], point[1]))
            if len(point) >= 3:
                y_coord = point[1] if len(point) > 1 else 256
                z_coord = 390 - (point[2] if len(point) > 2 else self.Z_for_axis)
                self.realtime_needle_coords['yz'].append((y_coord, z_coord))
            if len(point) >= 3:
                x_coord = point[0] if len(point) > 0 else 256
                z_coord = 390 - (point[2] if len(point) > 2 else self.Z_for_axis)
                self.realtime_needle_coords['xz'].append((x_coord, z_coord))

    def smooth_render_update(self):
        self.draw_realtime_line_optimized()

    def zoom_in_xy(self):
        if self.zoom_xy < self.max_zoom:
            self.zoom_xy = min(self.zoom_xy + self.zoom_step, self.max_zoom)
            self.update_images_smooth()

    def zoom_out_xy(self):
        if self.zoom_xy > self.min_zoom:
            self.zoom_xy = max(self.zoom_xy - self.zoom_step, self.min_zoom)
            self.update_images_smooth()

    def zoom_in_yz(self):
        if self.zoom_yz < self.max_zoom:
            self.zoom_yz = min(self.zoom_yz + self.zoom_step, self.max_zoom)
            self.update_images_smooth()

    def zoom_out_yz(self):
        if self.zoom_yz > self.min_zoom:
            self.zoom_yz = max(self.zoom_yz - self.zoom_step, self.min_zoom)
            self.update_images_smooth()

    def zoom_in_xz(self):
        if self.zoom_xz < self.max_zoom:
            self.zoom_xz = min(self.zoom_xz + self.zoom_step, self.max_zoom)
            self.update_images_smooth()

    def zoom_out_xz(self):
        if self.zoom_xz > self.min_zoom:
            self.zoom_xz = max(self.zoom_xz - self.zoom_step, self.min_zoom)
            self.update_images_smooth()

    def zoom_in_all(self):
        if self.zoom_all < self.max_zoom:
            self.zoom_all = min(self.zoom_all + self.zoom_step, self.max_zoom)
            self.zoom_xy = self.zoom_yz = self.zoom_xz = self.zoom_all
            self.update_images_smooth()

    def zoom_out_all(self):
        if self.zoom_all > self.min_zoom:
            self.zoom_all = max(self.zoom_all - self.zoom_step, self.min_zoom)
            self.zoom_xy = self.zoom_yz = self.zoom_xz = self.zoom_all
            self.update_images_smooth()

    def update_images_smooth(self):
        for num, panel in enumerate(self.gui_components.panels):
            self.load_panel_image(panel, num)
        self.smooth_render_timer.start(10)

    def get_needle_center_xy(self):
        if self.point_start and self.point_end:
            center_x = (self.point_start[0] + self.point_end[0]) / 2
            center_y = (self.point_start[1] + self.point_end[1]) / 2
            return [center_x, center_y]
        return None

    def get_needle_center_yz(self):
        if self.point_start and self.point_end:
            center_y = (self.point_start[1] + self.point_end[1]) / 2
            center_z = (self.point_start[2] + self.point_end[2]) / 2 if len(self.point_start) > 2 else self.Z_for_axis
            return [center_y, 390 - center_z]
        return None

    def get_needle_center_xz(self):
        if self.point_start and self.point_end:
            center_x = (self.point_start[0] + self.point_end[0]) / 2
            center_z = (self.point_start[2] + self.point_end[2]) / 2 if len(self.point_start) > 2 else self.Z_for_axis
            return [center_x, 390 - center_z]
        return None

    def reset_zoom_xy(self):
        self.zoom_xy = 1.0
        self.update_images_smooth()

    def reset_zoom_yz(self):
        self.zoom_yz = 1.0
        self.update_images_smooth()

    def reset_zoom_xz(self):
        self.zoom_xz = 1.0
        self.update_images_smooth()

    def reset_zoom_all(self):
        self.zoom_xy = self.zoom_yz = self.zoom_xz = self.zoom_all = 1.0
        self.update_images_smooth()

    def get_zoom_for_panel(self, panel_num):
        if panel_num == 0:
            return self.zoom_xy
        elif panel_num == 1:
            return self.zoom_yz
        elif panel_num == 2:
            return self.zoom_xz
        return 1.0

    def slider_changed(self, name, value):
        if name == "X Value":
            self.Y = int(value)
        elif name == "Y Value":
            self.X = int(value)
        elif name == "Z Value":
            self.Z_for_axis = int(value)
            low_end = 256 - (self.Z_init // 2)
            upper_end = 256 + (self.Z_init // 2)
            self.Z = int(value)
            if self.Z < low_end:
                self.Z = 1234
            elif self.Z > upper_end:
                self.Z = 1234
            else:
                self.Z = -int(int(value) - low_end)
            if self.Z == 0:
                self.Z = -1
        # === CHANGED ===: Now interacts with the handler's camera, with a check
        elif name == "X Rotation":
            if hasattr(self.gui_components.panel_3d_handler, 'view') and self.gui_components.panel_3d_handler.view:
                self.gui_components.panel_3d_handler.view.camera.elevation = float(value)
        elif name == "Y Rotation":
            if hasattr(self.gui_components.panel_3d_handler, 'view') and self.gui_components.panel_3d_handler.view:
                self.gui_components.panel_3d_handler.view.camera.azimuth = float(value)
        elif name == "Z Rotation":
            if hasattr(self.gui_components.panel_3d_handler, 'view') and self.gui_components.panel_3d_handler.view:
                self.gui_components.panel_3d_handler.view.camera.roll = float(value)

        self.update_images_smooth()

        # === FIXED ===: Add checks to ensure data exists before drawing
        # Check if plan data exists before trying to draw it
        if self.point_start and self.point_end:
            self.gui_components.panel_3d_handler.draw_needle_plan_vispy(self.point_start, self.point_end, self.plan_line_deleted)

        # Check if real-time data exists before trying to draw it
        if self.csv_handler.realtime_points:
            self.gui_components.panel_3d_handler.update_realtime_line_vispy(self.csv_handler.realtime_points, self.realtime_line_deleted)
    def toggle_sidebar(self):
        if self.gui_components.sidebar.isVisible():
            self.gui_components.sidebar.hide()
        else:
            self.gui_components.sidebar.show()

    def show_file_menu(self):
        menu = QMenu(self)
        menu.addAction("DICOM Folder", self.input_button_click)
        menu.addAction("Puncture Planned Route CSV", self.input_plan_coor_data)
        menu.addAction("Puncture Real-Time Route CSV", self.select_realtime_csv)
        menu.exec_(self.mapToGlobal(self.pos()))

    def select_realtime_csv(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select CSV File", "", "CSV files (*.csv)")
        if file_path:
            self.csv_handler.set_csv_file(file_path)
            self.realtime_line_deleted = False
            self.cache_realtime_coordinates()
            print(f"Selected CSV file: {file_path}")

    def input_button_click(self):
        folder = QFileDialog.getExistingDirectory(self, "Select a Folder")
        if folder:
            self.load_folder(folder)

    def load_folder(self, folder):
        folder_name = os.path.basename(folder)
        destination = os.path.join(os.getcwd() + "/dicom-folder", folder_name)
        if not os.path.exists(destination):
            shutil.copytree(folder, destination)
        self.dataList.append(destination)
        self.gui_components.list_view.addItem(folder_name)

    def list_view_item_click(self):
        current_item = self.gui_components.list_view.currentItem()
        if current_item:
            self.selectedItem = current_item.text()
            self.IsSelectedItem = 1
            self.load_dicom_images(self.selectedItem)

    def load_dicom_images(self, folder_name):
        volume3d, img_shape = self.dicom_handler.load_dicom_images(folder_name)
        self.volume3d = volume3d
        self.X_init = img_shape[0]
        self.Y_init = img_shape[1]
        self.Z_init = img_shape[2]
        self.X = img_shape[0] // 2
        self.Y = img_shape[1] // 2
        self.Z = img_shape[2] // 2

    def btnLoadPictures_Click(self):
        if self.IsSelectedItem == 0:
            return
        for num, panel in enumerate(self.gui_components.panels):
            self.load_panel_image(panel, num)
            
        # === CHANGED ===: Major change in how the 3D view is created and displayed
        # 1. Call the handler to create the visualization and the canvas
        self.gui_components.panel_3d_handler.visualize_vispy(self.volume3d)
        
        # 2. Get the layout of the container widget
        container_layout = self.gui_components.panel_3d_container.layout()
        
        # 3. Clear any old widgets from the container's layout
        while container_layout.count():
            child = container_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
                
        # 4. Add the newly created VisPy canvas to the container
        if self.gui_components.panel_3d_handler.canvas:
            container_layout.addWidget(self.gui_components.panel_3d_handler.canvas.native)

    def load_panel_image(self, panel, num):
        if self.IsSelectedItem == 0:
            return
        try:
            if num == 0:
                image_2d = self.volume3d[:, :, self.Z]
            elif num == 1:
                image_2d = np.flipud(np.rot90(self.volume3d[:, self.Y, :]))
            elif num == 2:
                image_2d = np.flipud(np.rot90(self.volume3d[self.X, :, :]))
            else:
                image_2d = np.zeros((512, 512), dtype=np.int16)
        except (IndexError, AttributeError):
            image_2d = np.zeros((512, 512), dtype=np.int16)
        zoom = self.get_zoom_for_panel(num)
        self.gui_components.update_panel_image(panel, image_2d, zoom)
        if panel == self.gui_components.panel_xy:
            self.draw_axes_value_change(panel, "magenta", "yellow", self.Y, self.X)
        elif panel == self.gui_components.panel_yz:
            self.draw_axes_value_change(panel, "blue", "magenta", self.X, self.Z_for_axis)
        elif panel == self.gui_components.panel_xz:
            self.draw_axes_value_change(panel, "blue", "yellow", self.Y, self.Z_for_axis)
        try:
            if not self.is_clear:
                self.draw_needle_plan()
        except AttributeError:
            pass

    def draw_axes_value_change(self, panel, x_color, y_color, x_axis, y_axis):
        panel.axes_lines = []
        if panel == self.gui_components.panel_xy:
            plane_type = 'xy'
        elif panel == self.gui_components.panel_yz:
            plane_type = 'yz'
        elif panel == self.gui_components.panel_xz:
            plane_type = 'xz'
        else:
            return
        if y_axis == self.Z_for_axis:
            x_pos, _ = self.get_canvas_coordinates(panel, x_axis, 0, plane_type)
            _, y_pos = self.get_canvas_coordinates(panel, 0, y_axis, plane_type)
        else:
            x_pos, _ = self.get_canvas_coordinates(panel, x_axis, 0, plane_type)
            _, y_pos = self.get_canvas_coordinates(panel, 0, y_axis, plane_type)
        width = panel.width()
        height = panel.height()
        panel.axes_lines = [
            {'type': 'horizontal', 'y': y_pos, 'color': x_color},
            {'type': 'vertical', 'x': x_pos, 'color': y_color}
        ]
        panel.update()

    def update_images(self):
        self.update_images_smooth()

    def get_canvas_coordinates(self, panel, image_x, image_y, plane_type):
        canvas_width = panel.width() or 300
        canvas_height = panel.height() or 300
        if plane_type == 'xy':
            zoom_factor = self.zoom_xy
            pan_offset = self.pan_xy
        elif plane_type == 'yz':
            zoom_factor = self.zoom_yz
            pan_offset = self.pan_yz
        elif plane_type == 'xz':
            zoom_factor = self.zoom_xz
            pan_offset = self.pan_xz
        else:
            zoom_factor = 1.0
            pan_offset = [0, 0]
        zoomed_width = 512 * zoom_factor
        zoomed_height = 512 * zoom_factor
        offset_x = (canvas_width - zoomed_width) / 2 + pan_offset[0]
        offset_y = (canvas_height - zoomed_height) / 2 + pan_offset[1]
        canvas_x = offset_x + (image_x * zoom_factor)
        canvas_y = offset_y + (image_y * zoom_factor)
        return canvas_x, canvas_y

    def reset_pan_all(self):
        self.pan_xy = [0, 0]
        self.pan_yz = [0, 0]
        self.pan_xz = [0, 0]
        self.update_images_smooth()

    def reset_pan_xy(self):
        self.pan_xy = [0, 0]
        self.update_images_smooth()

    def reset_pan_yz(self):
        self.pan_yz = [0, 0]
        self.update_images_smooth()

    def reset_pan_xz(self):
        self.pan_xz = [0, 0]
        self.update_images_smooth()

    def update_single_panel(self, panel_num):
        if panel_num < len(self.gui_components.panels):
            self.load_panel_image(self.gui_components.panels[panel_num], panel_num)
        self.smooth_render_timer.start(5)

    def get_pan_for_panel(self, panel_num):
        if panel_num == 0:
            return tuple(self.pan_xy)
        elif panel_num == 1:
            return tuple(self.pan_yz)
        elif panel_num == 2:
            return tuple(self.pan_xz)
        return (0, 0)

    def input_plan_coor_data(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select CSV File", "", "CSV files (*.csv)")
        if not file_path:
            return
        self.point_start, self.point_end = self.csv_handler.load_plan_coordinates(file_path)
        if self.point_start is None or self.point_end is None:
            return
        self.original_needle_coords = {
            'xy': {
                'start': (self.point_start[0], self.point_start[1]),
                'end': (self.point_end[0], self.point_end[1])
            },
            'yz': {
                'start': (self.point_start[1] if len(self.point_start) > 1 else 256,
                         390 - (self.point_start[2] if len(self.point_start) > 2 else self.Z_for_axis)), 
                'end': (self.point_end[1] if len(self.point_end) > 1 else 256,
                       390 - (self.point_end[2] if len(self.point_end) > 2 else self.Z_for_axis))
            },
            'xz': {
                'start': (self.point_start[0],
                         390 - (self.point_start[2] if len(self.point_start) > 2 else self.Z_for_axis)), 
                'end': (self.point_end[0],
                       390 - (self.point_end[2] if len(self.point_end) > 2 else self.Z_for_axis))
            }
        }
        self.is_clear = False
        self.plan_line_deleted = False
        self.draw_needle_plan()
        # === CHANGED ===: Calls method on panel_3d_handler with correct arguments
        self.gui_components.panel_3d_handler.draw_needle_plan_vispy(self.point_start, self.point_end, self.plan_line_deleted)

    def draw_needle_plan(self):
        if self.plan_line_deleted or not self.original_needle_coords['xy']['start']:
            return
        try:
            panels_and_planes = [
                (self.gui_components.panel_xy, "xy"),
                (self.gui_components.panel_yz, "yz"),
                (self.gui_components.panel_xz, "xz")
            ]
            for panel, plane in panels_and_planes:
                start_coords = self.original_needle_coords[plane]['start']
                end_coords = self.original_needle_coords[plane]['end']
                if start_coords is None or end_coords is None:
                    continue
                x0_screen, y0_screen = self.get_canvas_coordinates(panel, start_coords[0], start_coords[1], plane)
                x1_screen, y1_screen = self.get_canvas_coordinates(panel, end_coords[0], end_coords[1], plane)
                panel.needle_line = {
                    'start': (x0_screen, y0_screen),
                    'end': (x1_screen, y1_screen),
                    'color': 'green'
                }
                panel.update()
        except (AttributeError, TypeError) as e:
            print(f"Error drawing needle plan: {e}")

    def start_realtime_data(self):
        self.csv_handler.start_realtime_monitoring()

    def stop_realtime_data(self):
        self.csv_handler.stop_realtime_monitoring()

    def draw_realtime_line(self):
        if self.realtime_line_deleted:
            return
        self.cache_realtime_coordinates()
        self.draw_realtime_line_optimized()
        # === CHANGED ===: Calls method on panel_3d_handler with correct arguments
        self.gui_components.panel_3d_handler.update_realtime_line_vispy(self.csv_handler.realtime_points, self.realtime_line_deleted)

    def draw_realtime_line_optimized(self):
        if self.realtime_line_deleted or not self.realtime_needle_coords['xy']:
            return
        panels_and_planes = [
            (self.gui_components.panel_xy, "xy"),
            (self.gui_components.panel_yz, "yz"),
            (self.gui_components.panel_xz, "xz")
        ]
        for panel, plane in panels_and_planes:
            panel.realtime_lines = []
            cached_coords = self.realtime_needle_coords[plane]
            line_segments = []
            for i in range(1, len(cached_coords)):
                x0, y0 = cached_coords[i-1]
                x1, y1 = cached_coords[i]
                x0_screen, y0_screen = self.get_canvas_coordinates(panel, x0, y0, plane)
                x1_screen, y1_screen = self.get_canvas_coordinates(panel, x1, y1, plane)
                line_segments.append({
                    'start': (x0_screen, y0_screen),
                    'end': (x1_screen, y1_screen),
                    'color': 'red'
                })
            panel.realtime_lines = line_segments
            panel.update()

    def clear_needle(self):
        self.is_clear = True
        self.plan_line_deleted = True
        self.realtime_line_deleted = True
        self.realtime_needle_coords = {'xy': [], 'yz': [], 'xz': []}
        for panel in self.gui_components.panels:
            panel.needle_line = None
            panel.realtime_lines = []
            panel.update()
        # === CHANGED ===: Calls clear_lines on the handler
        self.gui_components.panel_3d_handler.clear_lines()

    def delete_plan_line(self):
        self.plan_line_deleted = True
        for panel in self.gui_components.panels:
            panel.needle_line = None
            panel.update()
        # === CHANGED ===: The handler's draw method will now do nothing due to the flag
        self.gui_components.panel_3d_handler.draw_needle_plan_vispy(None, None, self.plan_line_deleted)

    def delete_realtime_line(self):
        self.realtime_line_deleted = True
        self.realtime_needle_coords = {'xy': [], 'yz': [], 'xz': []}
        for panel in self.gui_components.panels:
            panel.realtime_lines = []
            panel.update()
        # === CHANGED ===: The handler's update method will now do nothing due to the flag
        self.gui_components.panel_3d_handler.update_realtime_line_vispy([], self.realtime_line_deleted)

    def zoom_xy_slider_changed(self, value):
        self.zoom_xy = float(value)
        self.update_images_smooth()

    def zoom_yz_slider_changed(self, value):
        self.zoom_yz = float(value)
        self.update_images_smooth()

    def zoom_xz_slider_changed(self, value):
        self.zoom_xz = float(value)
        self.update_images_smooth()

    def delete_selected_file(self):
        current_item = self.gui_components.list_view.currentItem()
        if not current_item:
            QMessageBox.warning(self, "No Selection", "Please select a file to delete.")
            return
        folder_name = current_item.text()
        folder_path = os.path.join(os.getcwd(), "dicom-folder", folder_name)
        reply = QMessageBox.question(self, "Delete File", f"Are you sure you want to delete '{folder_name}'?",
                                QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            try:
                if os.path.exists(folder_path):
                    shutil.rmtree(folder_path)
                row = self.gui_components.list_view.row(current_item)
                self.gui_components.list_view.takeItem(row)
                if folder_path in self.dataList:
                    self.dataList.remove(folder_path)
                self.selectedItem = None
                self.IsSelectedItem = 0
                self.volume3d = None  # <-- เพิ่มเข้ามา: ล้างข้อมูล Volume หลักทันที
                self.clear_needle()
                self.clear_all_canvases()
                QMessageBox.information(self, "Deleted", f"'{folder_name}' has been deleted.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to delete '{folder_name}': {e}")

    def clear_all_canvases(self):
        # --- ส่วนที่แก้ไข: เคลียร์ 2D panels ---
        for panel in self.gui_components.panels:
            panel.image_data = None
            panel.current_pixmap = None  # เคลียร์ pixmap ที่ใช้แสดงผล
            panel.needle_line = None
            panel.realtime_lines = []
            panel.axes_lines = []
            panel.update() # สั่งให้วาด panel ใหม่ (ตอนนี้จะว่างเปล่า)

        # --- ส่วนที่แก้ไข: เคลียร์ 3D visualization ---
        if hasattr(self.gui_components, 'panel_3d_handler'):
            self.gui_components.panel_3d_handler.clear_lines()
            # ตรวจสอบและลบ 3D volume ออกจาก scene
            if hasattr(self.gui_components.panel_3d_handler, 'volume') and self.gui_components.panel_3d_handler.volume is not None:
                self.gui_components.panel_3d_handler.volume.parent = None
                self.gui_components.panel_3d_handler.volume = None

        # --- ส่วนที่แก้ไข: คืนค่าหน้าจอ 3D view container ---
        container = self.gui_components.panel_3d_container
        if container and container.layout():
            layout = container.layout()
            # ลบ widget เก่า (VisPy canvas) ออกจาก layout
            while layout.count():
                child = layout.takeAt(0)
                if child.widget():
                    child.widget().deleteLater()
            
            # เพิ่ม placeholder label กลับเข้าไปใหม่
            placeholder_label = QLabel("3D View - Load DICOM data")
            placeholder_label.setAlignment(Qt.AlignCenter)
            placeholder_label.setStyleSheet("background-color: black; color: white;")
            layout.addWidget(placeholder_label)

        # ล้างข้อมูล volume หลักในหน่วยความจำ
        self.volume3d = None