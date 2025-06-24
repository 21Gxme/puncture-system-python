import os
import numpy as np
from tkinter import  Menu, filedialog, END
import shutil
from vispy import scene
import tkinter.messagebox as messagebox

from data_structures import Vector3D
from handlers.dicom_handler import DicomHandler
from handlers.visualization_handler import VisualizationHandler
from handlers.csv_handler import CSVHandler
from gui.gui_components import GUIComponents

class MainPage:
    def __init__(self, root):
        """
        The `__init__` function initializes various handlers, variables, and GUI components for a
        CT-Guided Puncture Assistance System in Python.
        
        :param root: The `root` parameter in the `__init__` method appears to be a reference to the root
        window or main application window of the GUI application. It is used to set the title, geometry,
        and initialize various GUI components and handlers within the application
        """
        self.root = root
        self.root.title("CT-Guided Puncture Assistance System")
        self.root.geometry("1200x800")

        # Initialize handlers
        self.dicom_handler = DicomHandler()
        self.visualization_handler = VisualizationHandler()
        self.csv_handler = CSVHandler(self.draw_realtime_line)
        self.gui_components = GUIComponents(root, self)

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
        
        self.pan_xy = [0, 0]  # [x_offset, y_offset]
        self.pan_yz = [0, 0]
        self.pan_xz = [0, 0]
        
        # Store original needle coordinates in image space (0-512 range)
        self.original_needle_coords = {
            'xy': {'start': None, 'end': None},
            'yz': {'start': None, 'end': None}, 
            'xz': {'start': None, 'end': None}
        }
        
        # Initialize GUI
        self.gui_components.init_toolbar()
        self.gui_components.init_sidebar()
        self.gui_components.init_main_view()

        self.view = scene.SceneCanvas(keys='interactive', show=False).central_widget.add_view()

    def zoom_in_xy(self):
        """Zoom in XY plane centered on needle"""
        if self.zoom_xy < self.max_zoom:
            self.zoom_xy = min(self.zoom_xy + self.zoom_step, self.max_zoom)
            self.update_images()

    def zoom_out_xy(self):
        """Zoom out XY plane centered on needle"""
        if self.zoom_xy > self.min_zoom:
            self.zoom_xy = max(self.zoom_xy - self.zoom_step, self.min_zoom)
            self.update_images()

    def zoom_in_yz(self):
        """Zoom in YZ plane centered on needle"""
        if self.zoom_yz < self.max_zoom:
            self.zoom_yz = min(self.zoom_yz + self.zoom_step, self.max_zoom)
            self.update_images()

    def zoom_out_yz(self):
        """Zoom out YZ plane centered on needle"""
        if self.zoom_yz > self.min_zoom:
            self.zoom_yz = max(self.zoom_yz - self.zoom_step, self.min_zoom)
            self.update_images()

    def zoom_in_xz(self):
        """Zoom in XZ plane centered on needle"""
        if self.zoom_xz < self.max_zoom:
            self.zoom_xz = min(self.zoom_xz + self.zoom_step, self.max_zoom)
            self.update_images()

    def zoom_out_xz(self):
        """Zoom out XZ plane centered on needle"""
        if self.zoom_xz > self.min_zoom:
            self.zoom_xz = max(self.zoom_xz - self.zoom_step, self.min_zoom)
            self.update_images()

    def zoom_in_all(self):
        """Zoom in all planes centered on needle"""
        if self.zoom_all < self.max_zoom:
            self.zoom_all = min(self.zoom_all + self.zoom_step, self.max_zoom)
            self.zoom_xy = self.zoom_yz = self.zoom_xz = self.zoom_all
            self.update_images()

    def zoom_out_all(self):
        """Zoom out all planes centered on needle"""
        if self.zoom_all > self.min_zoom:
            self.zoom_all = max(self.zoom_all - self.zoom_step, self.min_zoom)
            self.zoom_xy = self.zoom_yz = self.zoom_xz = self.zoom_all
            self.update_images()

    def get_needle_center_xy(self):
        """Get the center point of the needle in XY plane coordinates"""
        if self.point_start and self.point_end:
            center_x = (self.point_start[0] + self.point_end[0]) / 2
            center_y = (self.point_start[1] + self.point_end[1]) / 2
            return [center_x, center_y]
        return None

    def get_needle_center_yz(self):
        """Get the center point of the needle in YZ plane coordinates"""
        if self.point_start and self.point_end:
            center_y = (self.point_start[1] + self.point_end[1]) / 2
            center_z = (self.point_start[2] + self.point_end[2]) / 2 if len(self.point_start) > 2 else self.Z_for_axis
            return [center_y, 390 - center_z]
        return None

    def get_needle_center_xz(self):
        """Get the center point of the needle in XZ plane coordinates"""
        if self.point_start and self.point_end:
            center_x = (self.point_start[0] + self.point_end[0]) / 2
            center_z = (self.point_start[2] + self.point_end[2]) / 2 if len(self.point_start) > 2 else self.Z_for_axis
            return [center_x, 390 - center_z]
        return None

    def reset_zoom_xy(self):
        """Reset XY plane zoom to 1.0"""
        self.zoom_xy = 1.0
        self.update_images()

    def reset_zoom_yz(self):
        """Reset YZ plane zoom to 1.0"""
        self.zoom_yz = 1.0
        self.update_images()

    def reset_zoom_xz(self):
        """Reset XZ plane zoom to 1.0"""
        self.zoom_xz = 1.0
        self.update_images()

    def reset_zoom_all(self):
        """Reset all planes zoom to 1.0"""
        self.zoom_xy = self.zoom_yz = self.zoom_xz = self.zoom_all = 1.0
        self.update_images()

    def get_zoom_for_panel(self, panel_num):
        """Get zoom factor for specific panel"""
        if panel_num == 0:  # XY plane
            return self.zoom_xy
        elif panel_num == 1:  # YZ plane
            return self.zoom_yz
        elif panel_num == 2:  # XZ plane
            return self.zoom_xz
        return 1.0

    def slider_changed(self, name, value):
        """Handle slider value changes"""
        # z_ratio = 512 / (self.Z_init)
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
            if hasattr(self.visualization_handler, 'view') and self.visualization_handler.view:
                self.visualization_handler.view.camera.elevation = float(value)
        elif name == "Y Rotation":
            if hasattr(self.visualization_handler, 'view') and self.visualization_handler.view:
                self.visualization_handler.view.camera.azimuth = float(value)
        elif name == "Z Rotation":
            if hasattr(self.visualization_handler, 'view') and self.visualization_handler.view:
                self.visualization_handler.view.camera.roll = float(value)
        self.update_images()
        self.draw_realtime_line()
        self.visualization_handler.update_realtime_line_vispy(self.csv_handler.realtime_points, self.realtime_line_deleted)

    def toggle_sidebar(self):
        """Toggle sidebar visibility"""
        if self.gui_components.sidebar.winfo_viewable():
            self.gui_components.sidebar.pack_forget()
        else:
            self.gui_components.sidebar.pack(side="left", fill="y")

    def show_file_menu(self):
        """Show file menu"""
        menu = Menu(self.root, tearoff=0)
        menu.add_command(label="DICOM Folder", command=self.input_button_click)
        menu.add_command(label="Puncture Planned Route CSV", command=self.input_plan_coor_data)
        menu.add_command(label="Puncture Real-Time Route CSV", command=self.select_realtime_csv)
        menu.post(self.root.winfo_pointerx(), self.root.winfo_pointery())

    def select_realtime_csv(self):
        """Select CSV file for real-time monitoring"""
        file_path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
        if file_path:
            self.csv_handler.set_csv_file(file_path)
            self.realtime_line_deleted = False
            print(f"Selected CSV file: {file_path}")

    def input_button_click(self):
        """Handle DICOM folder selection"""
        folder = filedialog.askdirectory(title="Select a Folder")
        if folder:
            self.load_folder(folder)

    def load_folder(self, folder):
        """Load DICOM folder"""
        folder_name = os.path.basename(folder)
        destination = os.path.join(os.getcwd() + "/dicom-folder", folder_name)
        if not os.path.exists(destination):
            shutil.copytree(folder, destination)
        self.dataList.append(destination)
        self.gui_components.list_view.insert(END, folder_name)

    def list_view_item_click(self, event):
        """Handle list view item selection"""
        selected_indices = self.gui_components.list_view.curselection()
        if selected_indices:
            self.selectedItem = self.gui_components.list_view.get(selected_indices[0])
            self.IsSelectedItem = 1
            self.load_dicom_images(self.selectedItem)

    def load_dicom_images(self, folder_name):
        """Load DICOM images"""
        volume3d, img_shape = self.dicom_handler.load_dicom_images(folder_name)
        self.volume3d = volume3d
        self.X_init = img_shape[0]
        self.Y_init = img_shape[1]
        self.Z_init = img_shape[2]
        self.X = img_shape[0] // 2
        self.Y = img_shape[1] // 2
        self.Z = img_shape[2] // 2

    def btnLoadPictures_Click(self):
        """Load and display pictures"""
        if self.IsSelectedItem == 0:
            return
        for num, pa in enumerate(self.gui_components.panels):
            self.load_panel_image(pa, num)
        self.visualization_handler.visualize_vispy(self.volume3d)

    def load_panel_image(self, pa, num):
        """Load image for a specific panel with zoom support"""
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
        
        # Get zoom for this panel
        zoom = self.get_zoom_for_panel(num)
        
        self.gui_components.update_panel_image(pa, image_2d, zoom)
        
        # Draw axes with zoom consideration
        if pa == self.gui_components.panel2:
            self.draw_axes_value_change(pa, "magenta", "yellow", self.Y, self.X)
        elif pa == self.gui_components.panel3:
            self.draw_axes_value_change(pa, "blue", "magenta", self.X, self.Z_for_axis)
        elif pa == self.gui_components.panel4:
            self.draw_axes_value_change(pa, "blue", "yellow", self.Y, self.Z_for_axis)
            
        try:
            if not self.is_clear:
                self.draw_needle_plan()
        except AttributeError:
            pass

    def draw_axes_value_change(self, panel, x_color, y_color, x_axis, y_axis):
        """Draw axes on panel with zoom and pan support"""
        panel.canvas.delete("axes")
        
        # Determine plane type based on panel
        if panel == self.gui_components.panel2:
            plane_type = 'xy'
        elif panel == self.gui_components.panel3:
            plane_type = 'yz'
        elif panel == self.gui_components.panel4:
            plane_type = 'xz'
        else:
            return
        
        # Transform axis coordinates
        if y_axis == self.Z_for_axis:
            x_pos, _ = self.get_canvas_coordinates(panel, x_axis, 0, plane_type)
            _, y_pos = self.get_canvas_coordinates(panel, 0, y_axis, plane_type)
        else:
            x_pos, _ = self.get_canvas_coordinates(panel, x_axis, 0, plane_type)
            _, y_pos = self.get_canvas_coordinates(panel, 0, y_axis, plane_type)
        
        width = panel.canvas.winfo_width()
        height = panel.canvas.winfo_height()
        
        # Draw axes lines
        panel.canvas.create_line(0, y_pos, width, y_pos, fill=x_color, tags="axes")
        panel.canvas.create_line(x_pos, 0, x_pos, height, fill=y_color, tags="axes")

    def update_images(self):
        """Update all panel images"""
        for num, pa in enumerate(self.gui_components.panels):
            self.load_panel_image(pa, num)

    def get_canvas_coordinates(self, panel, image_x, image_y, plane_type):
        canvas_width = panel.canvas.winfo_width() or 512
        canvas_height = panel.canvas.winfo_height() or 512

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
        """Reset pan for all planes"""
        self.pan_xy = [0, 0]
        self.pan_yz = [0, 0]
        self.pan_xz = [0, 0]
        self.update_images()

    def reset_pan_xy(self):
        """Reset XY plane pan"""
        self.pan_xy = [0, 0]
        self.update_images()

    def reset_pan_yz(self):
        """Reset YZ plane pan"""
        self.pan_yz = [0, 0]
        self.update_images()

    def reset_pan_xz(self):
        """Reset XZ plane pan"""
        self.pan_xz = [0, 0]
        self.update_images()

    def update_single_panel(self, panel_num):
        if panel_num < len(self.gui_components.panels):
            self.load_panel_image(self.gui_components.panels[panel_num], panel_num)
        # Draw new lines
        self.draw_realtime_line()
        self.draw_needle_plan()

    def get_pan_for_panel(self, panel_num):
        """Get pan offset for specific panel"""
        if panel_num == 0:  # XY plane
            return tuple(self.pan_xy)
        elif panel_num == 1:  # YZ plane
            return tuple(self.pan_yz)
        elif panel_num == 2:  # XZ plane
            return tuple(self.pan_xz)
        return (0, 0)

    def input_plan_coor_data(self):
        """Load planned coordinates from CSV"""
        file_path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
        if not file_path:
            return
        
        self.point_start, self.point_end = self.csv_handler.load_plan_coordinates(file_path)
        if self.point_start is None or self.point_end is None:
            return
        
        # Store original needle coordinates in image space
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
        self.visualization_handler.draw_needle_plan_vispy(self.point_start, self.point_end, self.plan_line_deleted)

    def draw_needle_plan(self):
        """Draw planned needle path with proper coordinate transformation"""
        if self.plan_line_deleted or not self.original_needle_coords['xy']['start']:
            return
        
        try:
            # Draw on all relevant panels
            panels_and_planes = [
                (self.gui_components.panel2, "xy"),
                (self.gui_components.panel3, "yz"), 
                (self.gui_components.panel4, "xz")
            ]
            
            for panel, plane in panels_and_planes:
                # Get original coordinates for this plane
                start_coords = self.original_needle_coords[plane]['start']
                end_coords = self.original_needle_coords[plane]['end']
                
                if start_coords is None or end_coords is None:
                    continue
                
                # Transform to canvas coordinates
                x0_screen, y0_screen = self.get_canvas_coordinates(panel, start_coords[0], start_coords[1], plane)
                x1_screen, y1_screen = self.get_canvas_coordinates(panel, end_coords[0], end_coords[1], plane)
                
                # Clear previous needle lines for this panel
                panel.canvas.delete("needle")
                
                # Draw the needle line
                self.create_dash_line(panel.canvas, x0_screen, y0_screen, x1_screen, y1_screen, fill="green", tags="needle")
            
        except (AttributeError, TypeError) as e:
            print(f"Error drawing needle plan: {e}")

    def create_dash_line(self, canvas, x0, y0, x1, y1, fill, tags):
        """Create dashed line on canvas"""
        dash_length = 5
        gap_length = 3
        line_width = 3
        total_length = ((x1 - x0)**2 + (y1 - y0)**2) ** 0.5
        if total_length == 0:
            return
        num_dashes = int(total_length // (dash_length + gap_length))
        for i in range(num_dashes):
            start_x = x0 + (x1 - x0) * (i * (dash_length + gap_length)) / total_length
            start_y = y0 + (y1 - y0) * (i * (dash_length + gap_length)) / total_length
            end_x = start_x + (x1 - x0) * dash_length / total_length
            end_y = start_y + (y1 - y0) * dash_length / total_length
            canvas.create_line(start_x, start_y, end_x, end_y, fill=fill, tags=tags, width=line_width)

    def start_realtime_data(self):
        """Start real-time data monitoring"""
        self.csv_handler.start_realtime_monitoring()

    def stop_realtime_data(self):
        """Stop real-time data monitoring"""
        self.csv_handler.stop_realtime_monitoring()

    def draw_realtime_line(self):
        """Draw real-time line with proper coordinate transformation"""
        if self.realtime_line_deleted or not hasattr(self.csv_handler, 'realtime_points'):
            return
        
        # Draw on all panels
        panels_and_planes = [
            (self.gui_components.panel2, "xy"),
            (self.gui_components.panel3, "yz"),
            (self.gui_components.panel4, "xz")
        ]
        
        for panel, plane in panels_and_planes:
            panel.canvas.delete("realtime")
            
            for i in range(1, len(self.csv_handler.realtime_points)):
                # Get original coordinates
                if plane == "xy":
                    x0, y0 = self.csv_handler.realtime_points[i-1][:2]
                    x1, y1 = self.csv_handler.realtime_points[i][:2]
                    
                    # Transform to canvas coordinates
                    x0_screen, y0_screen = self.get_canvas_coordinates(panel, x0, y0, plane)
                    x1_screen, y1_screen = self.get_canvas_coordinates(panel, x1, y1, plane)
                    
                elif plane == "yz":
                    point0 = self.csv_handler.realtime_points[i-1]
                    point1 = self.csv_handler.realtime_points[i]
                    y0 = point0[1] if len(point0) > 1 else 256
                    z0 = point0[2] if len(point0) > 2 else self.Z_for_axis
                    y1 = point1[1] if len(point1) > 1 else 256
                    z1 = point1[2] if len(point1) > 2 else self.Z_for_axis

                    # Make needle slightly higher
                    x0_screen, y0_screen = self.get_canvas_coordinates(panel, y0, 390-z0, plane)
                    x1_screen, y1_screen = self.get_canvas_coordinates(panel, y1, 390-z1, plane)

                elif plane == "xz":
                    point0 = self.csv_handler.realtime_points[i-1]
                    point1 = self.csv_handler.realtime_points[i]
                    x0 = point0[0] if len(point0) > 0 else 256
                    z0 = point0[2] if len(point0) > 2 else self.Z_for_axis
                    x1 = point1[0] if len(point1) > 0 else 256
                    z1 = point1[2] if len(point1) > 2 else self.Z_for_axis
                    
                    # Make needle slightly higher
                    x0_screen, y0_screen = self.get_canvas_coordinates(panel, x0, 390-z0, plane)
                    x1_screen, y1_screen = self.get_canvas_coordinates(panel, x1, 390-z1, plane)
                                
                # Draw the line segment
                self.create_dash_line(panel.canvas, x0_screen, y0_screen, x1_screen, y1_screen, fill="red", tags="realtime")

        # Update 3D visualization
        if hasattr(self.visualization_handler, 'update_realtime_line_vispy'):
            self.visualization_handler.update_realtime_line_vispy(self.csv_handler.realtime_points, self.realtime_line_deleted)

    def clear_needle(self):
        """Clear all needle visualizations"""
        self.is_clear = True
        self.plan_line_deleted = True
        self.realtime_line_deleted = True
        for panel in self.gui_components.panels:
            panel.canvas.delete("needle")
            panel.canvas.delete("realtime")
        self.visualization_handler.clear_lines()

    def delete_plan_line(self):
        """Delete planned line"""
        self.plan_line_deleted = True
        self.gui_components.panel2.canvas.delete("needle")
        if hasattr(self.visualization_handler, 'dash_line'):
            self.visualization_handler.dash_line.set_data(np.array([]))

    def delete_realtime_line(self):
        """Delete real-time line"""
        self.realtime_line_deleted = True
        self.gui_components.panel2.canvas.delete("realtime")
        if hasattr(self.visualization_handler, 'realtime_line_vispy'):
            self.visualization_handler.realtime_line_vispy.set_data(np.array([]))
    # Modify the load_panel_image method to include pan support:
    def load_panel_image(self, pa, num):
        """Load image for a specific panel with zoom and pan support"""
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
        
        # Get zoom and pan for this panel
        zoom = self.get_zoom_for_panel(num)
        pan_offset = self.get_pan_for_panel(num)
        
        self.gui_components.update_panel_image(pa, image_2d, zoom, pan_offset)
        
        # Draw axes with zoom and pan consideration
        if pa == self.gui_components.panel2:
            self.draw_axes_value_change(pa, "magenta", "yellow", self.Y, self.X)
        elif pa == self.gui_components.panel3:
            self.draw_axes_value_change(pa, "blue", "magenta", self.X, self.Z_for_axis)
        elif pa == self.gui_components.panel4:
            self.draw_axes_value_change(pa, "blue", "yellow", self.Y, self.Z_for_axis)
        
        try:
            if not self.is_clear:
                self.draw_needle_plan()
        except AttributeError:
            pass

    # Update the get_canvas_coordinates method to include pan offset:
    def get_canvas_coordinates(self, panel, image_x, image_y, plane_type):
        """Transform image coordinates to canvas coordinates with proper zoom and pan handling"""
        # Get canvas dimensions
        canvas_width = panel.canvas.winfo_width() or 512
        canvas_height = panel.canvas.winfo_height() or 512
        
        # Get current zoom factor and pan offset for the plane
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
        
        # Calculate zoomed image size
        zoomed_width = 512 * zoom_factor
        zoomed_height = 512 * zoom_factor
        
        # Center the zoomed image in canvas and apply pan offset
        offset_x = (canvas_width - zoomed_width) / 2 + pan_offset[0]
        offset_y = (canvas_height - zoomed_height) / 2 + pan_offset[1]
        
        # Transform coordinates
        canvas_x = offset_x + (image_x * zoom_factor)
        canvas_y = offset_y + (image_y * zoom_factor)
        
        return canvas_x, canvas_y
    
    def zoom_xy_slider_changed(self, value):
        """Handle XY zoom slider value changes"""
        self.zoom_xy = float(value)
        self.update_images()

    def zoom_yz_slider_changed(self, value):
        """Handle YZ zoom slider value changes"""
        self.zoom_yz = float(value)
        self.update_images()

    def zoom_xz_slider_changed(self, value):
        """Handle XZ zoom slider value changes"""
        self.zoom_xz = float(value)
        self.update_images()
        
    def delete_selected_file(self):
        selected_indices = self.gui_components.list_view.curselection()
        if not selected_indices:
            messagebox.showwarning("No Selection", "Please select a file to delete.")
            return

        idx = selected_indices[0]
        folder_name = self.gui_components.list_view.get(idx)
        folder_path = os.path.join(os.getcwd(), "dicom-folder", folder_name)

        confirm = messagebox.askyesno("Delete File", f"Are you sure you want to delete '{folder_name}'?")
        if confirm:
            try:
                if os.path.exists(folder_path):
                    shutil.rmtree(folder_path)
                self.gui_components.list_view.delete(idx)
                if folder_path in self.dataList:
                    self.dataList.remove(folder_path)
                self.selectedItem = None
                self.IsSelectedItem = 0
                self.clear_needle()           # Clear overlays
                self.clear_all_canvases()     # Clear images and everything
                messagebox.showinfo("Deleted", f"'{folder_name}' has been deleted.")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete '{folder_name}': {e}")
                
    def clear_all_canvases(self):
        """Clear all images and overlays from all panels."""
        for panel in self.gui_components.panels:
            panel.canvas.delete("all")
            panel.image = None