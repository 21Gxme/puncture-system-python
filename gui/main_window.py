import os
import numpy as np
from tkinter import  Menu, filedialog, END
import shutil
from vispy import scene

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
        
        # Initialize GUI
        self.gui_components.init_toolbar()
        self.gui_components.init_sidebar()
        self.gui_components.init_main_view()

        self.view = scene.SceneCanvas(keys='interactive', show=False).central_widget.add_view()

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
        """Load image for a specific panel"""
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
        
        self.gui_components.update_panel_image(pa, image_2d)
        
        # Draw axes
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
        """Draw axes on panel"""
        panel.canvas.delete("axes")
        width = panel.canvas.winfo_width()
        height = panel.canvas.winfo_height()
        width_ratio = 512 / width
        height_ratio = 512 / height
        if y_axis == self.Z_for_axis:
            panel.canvas.create_line(0, (height - (y_axis / height_ratio)), width, (height - (y_axis / height_ratio)), fill=x_color, tags="axes")
            panel.canvas.create_line(x_axis / width_ratio, 0, x_axis / width_ratio, height, fill=y_color, tags="axes")
        else:
            panel.canvas.create_line(0, y_axis / height_ratio, width, y_axis / height_ratio, fill=x_color, tags="axes")
            panel.canvas.create_line(x_axis / width_ratio, 0, x_axis / width_ratio, height, fill=y_color, tags="axes")

    def update_images(self):
        """Update all panel images"""
        for num, pa in enumerate(self.gui_components.panels):
            self.load_panel_image(pa, num)

    def input_plan_coor_data(self):
        """Load planned coordinates from CSV"""
        file_path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
        if not file_path:
            return
        
        self.point_start, self.point_end = self.csv_handler.load_plan_coordinates(file_path)
        if self.point_start is None or self.point_end is None:
            return
            
        self.is_clear = False
        self.plan_line_deleted = False
        self.draw_needle_plan()
        self.visualization_handler.draw_needle_plan_vispy(self.point_start, self.point_end, self.plan_line_deleted)

    def draw_needle_plan(self):
        """Draw planned needle path"""
        if self.plan_line_deleted or not self.point_start or not self.point_end:
            return
        try:
            for panel, plane in zip([self.gui_components.panel2], ["xy"]):
                if plane == "xy":
                    x0, y0 = self.point_start[0], self.point_start[1]
                    x1, y1 = self.point_end[0], self.point_end[1]
                x0 = x0 * (panel.canvas.winfo_width() / 512)
                y0 = y0 * (panel.canvas.winfo_height() / 512)
                x1 = x1 * (panel.canvas.winfo_width() / 512)
                y1 = y1 * (panel.canvas.winfo_height() / 512)
                self.create_dash_line(panel.canvas, x0, y0, x1, y1, fill="green", tags="needle")
        except AttributeError:
            pass

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
        """Draw real-time line"""
        if self.realtime_line_deleted:
            return
        # Draw on XY-plane
        self.gui_components.panel2.canvas.delete("realtime")
        for i in range(1, len(self.csv_handler.realtime_points)):
            x0, y0 = self.csv_handler.realtime_points[i-1][:2]
            x1, y1 = self.csv_handler.realtime_points[i][:2]
            self.create_dash_line(self.gui_components.panel2.canvas, x0, y0, x1, y1, fill="red", tags="realtime")

        # Update 3D visualization
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
