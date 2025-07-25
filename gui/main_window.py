import os
import numpy as np # type: ignore
import shutil
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QFileDialog, QMessageBox, QLabel, QPushButton) # type: ignore
from PyQt5.QtWidgets import QMenu # type: ignore
from PyQt5.QtCore import QTimer, Qt # type: ignore
from data_structures import Vector3D
from handlers.dicom_handler import DicomHandler
from handlers.csv_handler import CSVHandler
from gui.gui_components import GUIComponents


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

        self.brightness = 0
        self.contrast = 2.0

        # Global min/max for consistent normalization
        self.global_min = None
        self.global_max = None

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

        # Panel lock states
        self.panel_locks = [False, False, False]

        self.original_needle_coords = {
            'xy': {'start': None, 'end': None},
            'yz': {'start': None, 'end': None},
            'xz': {'start': None, 'end': None}
        }

        self.realtime_needle_coords = {
            'xy': [],
            'yz': [],
            'xz': []
        }

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
        self.realtime_needle_coords = {'xy': []}
        for point in self.csv_handler.realtime_points:
            if len(point) >= 2:
                self.realtime_needle_coords['xy'].append((point[0], point[1]))

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
    
    def on_plane_selection_changed(self, panel, plane_name):
        panel.plane_name = plane_name
        if self.volume3d is not None:
            try:
                panel_index = self.gui_components.panels.index(panel)
                self.load_panel_image(panel, panel_index)
            except ValueError:
                print(f"Error: Panel not found in the list.")

    def toggle_panel_lock(self, is_locked, panel, plane_buttons):
        """
        Handles the lock button toggle for a panel.
        """
        try:
            panel_index = self.gui_components.panels.index(panel)
            
            self.panel_locks[panel_index] = is_locked
            panel.locked = is_locked
            
            # Enable/disable the plane selection buttons
            if isinstance(plane_buttons, list):
                for button in plane_buttons:
                    button.setEnabled(not is_locked)
            
        except ValueError:
            print(f"Error: Could not find panel to toggle lock state.")

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
        elif name == "X Rotation":
            if hasattr(self.gui_components.panel_3d_handler, 'view') and self.gui_components.panel_3d_handler.view:
                self.gui_components.panel_3d_handler.view.camera.elevation = float(value)
        elif name == "Y Rotation":
            if hasattr(self.gui_components.panel_3d_handler, 'view') and self.gui_components.panel_3d_handler.view:
                self.gui_components.panel_3d_handler.view.camera.azimuth = float(value)
        elif name == "Z Rotation":
            if hasattr(self.gui_components.panel_3d_handler, 'view') and self.gui_components.panel_3d_handler.view:
                self.gui_components.panel_3d_handler.view.camera.roll = float(value)

        self.update_images()

    def brightness_changed(self, value):
        self.brightness = value
        self.update_images()

    def contrast_changed(self, value):
        self.contrast = value / 50.0
        self.update_images()

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

    # *** THIS IS THE FIRST FIX ***
    def list_view_item_click(self):
        """
        Only sets the selected item name. Does not load data.
        """
        current_item = self.gui_components.list_view.currentItem()
        if current_item:
            self.selectedItem = current_item.text()
            self.IsSelectedItem = 1
            # The line that called self.load_dicom_images() is removed.

    def load_dicom_images(self, folder_name):
        """
        Loads DICOM data from the specified folder into memory.
        """
        volume3d, img_shape = self.dicom_handler.load_dicom_images(folder_name)
        self.volume3d = volume3d
        self.X_init = img_shape[0]
        self.Y_init = img_shape[1]
        self.Z_init = img_shape[2]
        self.X = img_shape[0] // 2
        self.Y = img_shape[1] // 2
        self.Z = img_shape[2] // 2
        if self.volume3d is not None:
            self.global_min = self.volume3d.min()
            self.global_max = self.volume3d.max()
        # The call to update_images() is removed from here to prevent premature drawing.

    # *** THIS IS THE SECOND FIX ***
    def btnLoadPictures_Click(self):
        """
        Loads the selected DICOM data and then displays it.
        """
        if self.IsSelectedItem == 0 or self.selectedItem is None:
            QMessageBox.warning(self, "No Selection", "Please select a file from the list first.")
            return

        # Step 1: Load the data from the selected file
        self.load_dicom_images(self.selectedItem)

        # Step 2: Update all 2D panels with the new data
        self.update_images()

        # Step 3: Create or update the 3D visualization
        self.gui_components.panel_3d_handler.visualize_vispy(self.volume3d)
        container_layout = self.gui_components.panel_3d_container.layout()

        while container_layout.count():
            child = container_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        if self.gui_components.panel_3d_handler.canvas:
            container_layout.addWidget(self.gui_components.panel_3d_handler.canvas.native)


    def load_panel_image(self, panel, num):
        if self.IsSelectedItem == 0 or self.volume3d is None:
            return

        image_2d = None
        
        if self.panel_locks[num] and hasattr(panel, 'image_data') and panel.image_data is not None:
            image_2d = panel.image_data
        else:
            plane_name = panel.plane_name
            try:
                if plane_name == "XY":
                    image_2d = self.volume3d[:, :, self.Z]
                elif plane_name == "YZ":
                    image_2d = np.flipud(np.rot90(self.volume3d[:, self.Y, :]))
                elif plane_name == "XZ":
                    image_2d = np.flipud(np.rot90(self.volume3d[self.X, :, :]))
            except (IndexError, AttributeError):
                image_2d = np.zeros((512, 512), dtype=np.int16)
        
        if image_2d is None:
            return

        zoom = self.get_zoom_for_panel(num)
        self.gui_components.update_panel_image(panel, image_2d, zoom, self.brightness, self.contrast)
        
        plane_name = panel.plane_name
        if plane_name == "XY":
            self.draw_axes_value_change(panel, "magenta", "yellow", self.Y, self.X)
        elif plane_name == "YZ":
            self.draw_axes_value_change(panel, "blue", "magenta", self.X, self.Z_for_axis)
        elif plane_name == "XZ":
            self.draw_axes_value_change(panel, "blue", "yellow", self.Y, self.Z_for_axis)
            
        try:
            if not self.is_clear:
                self.draw_needle_plan()

        except AttributeError:
            pass

    def draw_axes_value_change(self, panel, x_color, y_color, x_axis, y_axis):
        panel.axes_lines = []
        plane_type = panel.plane_name.lower()
        
        if y_axis == self.Z_for_axis:
            x_pos, _ = self.get_canvas_coordinates(panel, x_axis, 0, plane_type)
            _, y_pos = self.get_canvas_coordinates(panel, 0, y_axis, plane_type)
        else:
            x_pos, _ = self.get_canvas_coordinates(panel, x_axis, 0, plane_type)
            _, y_pos = self.get_canvas_coordinates(panel, 0, y_axis, plane_type)
        
        panel.axes_lines = [
            {'type': 'horizontal', 'y': y_pos, 'color': x_color},
            {'type': 'vertical', 'x': x_pos, 'color': y_color}
        ]
        panel.update()

    def update_images(self):
        for num, panel in enumerate(self.gui_components.panels):
            self.load_panel_image(panel, num)

    def get_canvas_coordinates(self, panel, image_x, image_y, plane_type):
        canvas_width = panel.width() or 300
        canvas_height = panel.height() or 300
        
        try:
            panel_index = self.gui_components.panels.index(panel)
        except ValueError:
            panel_index = -1

        if panel_index == 0:
            zoom_factor = self.zoom_xy
            pan_offset = self.pan_xy
        elif panel_index == 1:
            zoom_factor = self.zoom_yz
            pan_offset = self.pan_yz
        elif panel_index == 2:
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
        self.update_images()

    def reset_pan_xy(self):
        self.pan_xy = [0, 0]
        self.update_images()

    def reset_pan_yz(self):
        self.pan_yz = [0, 0]
        self.update_images()

    def reset_pan_xz(self):
        self.pan_xz = [0, 0]
        self.update_images()

    def update_single_panel(self, panel_num):
        if panel_num < len(self.gui_components.panels):
            self.load_panel_image(self.gui_components.panels[panel_num], panel_num)

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
            }
        }
        self.is_clear = False
        self.plan_line_deleted = False
        self.draw_needle_plan()
        self.gui_components.panel_3d_handler.draw_needle_plan_vispy(self.point_start, self.point_end, self.plan_line_deleted)

    def draw_needle_plan(self):
        if self.plan_line_deleted or not self.original_needle_coords.get('xy') or not self.original_needle_coords['xy'].get('start'):
            return
        try:
            # วนหา panel ที่เป็น 'xy' โดยเฉพาะ
            for panel in self.gui_components.panels:
                if panel.plane_name.lower() == 'xy':
                    start_coords = self.original_needle_coords['xy']['start']
                    end_coords = self.original_needle_coords['xy']['end']

                    if start_coords is None or end_coords is None:
                        continue
                    
                    x0_screen, y0_screen = self.get_canvas_coordinates(panel, start_coords[0], start_coords[1], 'xy')
                    x1_screen, y1_screen = self.get_canvas_coordinates(panel, end_coords[0], end_coords[1], 'xy')
                    
                    panel.needle_line = {
                        'start': (x0_screen, y0_screen),
                        'end': (x1_screen, y1_screen),
                        'color': 'green'
                    }
                    panel.update()
                    break
        except (AttributeError, TypeError, KeyError) as e:
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
        self.gui_components.panel_3d_handler.update_realtime_line_vispy(self.csv_handler.realtime_points, self.realtime_line_deleted)

    def draw_realtime_line_optimized(self):
        if self.realtime_line_deleted or not self.realtime_needle_coords.get('xy'):
            return
        
        for panel in self.gui_components.panels:
            if panel.plane_name.lower() == 'xy':
                panel.realtime_lines = []
                
                cached_coords = self.realtime_needle_coords['xy']
                line_segments = []
                for i in range(1, len(cached_coords)):
                    x0, y0 = cached_coords[i-1]
                    x1, y1 = cached_coords[i]
                    x0_screen, y0_screen = self.get_canvas_coordinates(panel, x0, y0, 'xy')
                    x1_screen, y1_screen = self.get_canvas_coordinates(panel, x1, y1, 'xy')
                    line_segments.append({
                        'start': (x0_screen, y0_screen),
                        'end': (x1_screen, y1_screen),
                        'color': 'red'
                    })
                panel.realtime_lines = line_segments
                panel.update()
                break

    def clear_needle(self):
        self.is_clear = True
        self.plan_line_deleted = True
        self.realtime_line_deleted = True
        self.realtime_needle_coords = {'xy': [], 'yz': [], 'xz': []}
        for panel in self.gui_components.panels:
            panel.needle_line = None
            panel.realtime_lines = []
            panel.update()
        self.gui_components.panel_3d_handler.clear_lines()

    def delete_plan_line(self):
        self.plan_line_deleted = True
        for panel in self.gui_components.panels:
            panel.needle_line = None
            panel.update()
        self.gui_components.panel_3d_handler.draw_needle_plan_vispy(None, None, self.plan_line_deleted)

    def delete_realtime_line(self):
        self.realtime_line_deleted = True
        self.realtime_needle_coords = {'xy': [], 'yz': [], 'xz': []}
        for panel in self.gui_components.panels:
            panel.realtime_lines = []
            panel.update()
        self.gui_components.panel_3d_handler.update_realtime_line_vispy([], self.realtime_line_deleted)

    def zoom_xy_slider_changed(self, value):
        self.zoom_xy = float(value)
        self.update_images()

    def zoom_yz_slider_changed(self, value):
        self.zoom_yz = float(value)
        self.update_images()

    def zoom_xz_slider_changed(self, value):
        self.zoom_xz = float(value)
        self.update_images()

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
                self.volume3d = None
                self.clear_needle()
                self.clear_all_canvases()
                QMessageBox.information(self, "Deleted", f"'{folder_name}' has been deleted.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to delete '{folder_name}': {e}")

    def clear_all_canvases(self):
        for panel in self.gui_components.panels:
            panel.image_data = None
            panel.current_pixmap = None
            panel.needle_line = None
            panel.realtime_lines = []
            panel.axes_lines = []
            panel.update()

        if hasattr(self.gui_components, 'panel_3d_handler'):
            self.gui_components.panel_3d_handler.clear_lines()
            if hasattr(self.gui_components.panel_3d_handler, 'volume') and self.gui_components.panel_3d_handler.volume is not None:
                self.gui_components.panel_3d_handler.volume.parent = None
                self.gui_components.panel_3d_handler.volume = None

        container = self.gui_components.panel_3d_container
        if container and container.layout():
            layout = container.layout()
            while layout.count():
                child = layout.takeAt(0)
                if child.widget():
                    child.widget().deleteLater()

            placeholder_label = QLabel("3D View - Load DICOM data")
            placeholder_label.setAlignment(Qt.AlignCenter)
            placeholder_label.setStyleSheet("background-color: black; color: white;")
            layout.addWidget(placeholder_label)

        self.volume3d = None