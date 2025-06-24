from tkinter import Frame, Label, Button, Listbox, Scale, HORIZONTAL, Canvas, Scrollbar, VERTICAL, DoubleVar
from PIL import Image, ImageTk
import numpy as np


class GUIComponents:
    def __init__(self, root, main_app):
        """
        The function initializes an object with root and main_app attributes along with an empty list
        for panels.
        
        :param root: The `root` parameter typically refers to the root window or main container of a
        graphical user interface (GUI) application. It serves as the parent widget for all other widgets
        in the application
        :param main_app: The `main_app` parameter likely refers to the main application or main window
        of the program. It is being passed to the `__init__` method along with the `root` parameter. The
        `root` parameter could be a reference to the root widget or main container of the GUI
        application,
        """
        self.root = root
        self.main_app = main_app
        self.panels = []
        
        # Initialize drag state variables
        self.drag_data = {
            'dragging': False,
            'start_x': 0,
            'start_y': 0,
            'panel_index': -1
        }
        
    def init_toolbar(self):
        """Initialize the toolbar"""
        self.toolbar = Frame(self.root)
        self.toolbar.pack(side="top", fill="x")

        menu_button = Button(self.toolbar, text="Menu", command=self.main_app.toggle_sidebar)
        menu_button.pack(side="left")

        file_button = Button(self.toolbar, text="File", command=self.main_app.show_file_menu)
        file_button.pack(side="left")

        load_button = Button(self.toolbar, text="Load", command=self.main_app.btnLoadPictures_Click)
        load_button.pack(side="left")

        start_button = Button(self.toolbar, text="Start Real-Time Route", command=self.main_app.start_realtime_data)
        start_button.pack(side="left")
        
        stop_button = Button(self.toolbar, text="Stop Real-Time Route", command=self.main_app.stop_realtime_data)
        stop_button.pack(side="left")

        # Add reset pan button
        reset_pan_button = Button(self.toolbar, text="Reset Pan", command=self.main_app.reset_pan_all, bg="lightyellow")
        reset_pan_button.pack(side="left")

        # Add zoom control buttons
        zoom_frame = Frame(self.toolbar)
        zoom_frame.pack(side="right", padx=10)

        # In GUIComponents class, inside init_sidebar (after self.list_view is created)
        delete_button = Button(self.toolbar, text="Delete File", command=self.main_app.delete_selected_file, bg="salmon")
        delete_button.pack(side="left")

        # All planes zoom controls
        Label(zoom_frame, text="All Planes:").grid(row=0, column=0, padx=2)
        Button(zoom_frame, text="Reset All", command=self.main_app.reset_zoom_all, bg="lightblue").grid(row=0, column=3, padx=1)

    def init_sidebar(self):
        """Initialize the sidebar"""
        self.sidebar = Frame(self.root)
        self.sidebar.pack(side="left", fill="y")

        self.list_view = Listbox(self.sidebar)
        self.list_view.pack(fill="both", expand=True)
        self.list_view.bind("<<ListboxSelect>>", self.main_app.list_view_item_click)

        self.init_sliders()
        self.init_zoom_controls()

    def init_zoom_controls(self):
        """Initialize individual plane zoom controls"""
        zoom_frame = Frame(self.sidebar)
        zoom_frame.pack(fill="x", padx=5, pady=5)

        Label(zoom_frame, text="Zoom Controls", font=("Arial", 10, "bold")).pack()

        # XY Plane controls
        xy_frame = Frame(zoom_frame)
        xy_frame.pack(fill="x", pady=2)
        Label(xy_frame, text="XY Plane:", fg="purple").pack(side="left")
        self.xy_zoom_var = DoubleVar(value=self.main_app.zoom_xy)
        xy_slider = Scale(xy_frame, from_=self.main_app.min_zoom, to=self.main_app.max_zoom, orient=HORIZONTAL, command=self.main_app.zoom_xy_slider_changed, variable=self.xy_zoom_var, resolution=0.1)
        xy_slider.pack(side="left", padx=1)
        Button(xy_frame, text="Reset", command=self.main_app.reset_zoom_xy, width=5, bg="lightblue").pack(side="left", padx=1)

        # YZ Plane controls
        yz_frame = Frame(zoom_frame)
        yz_frame.pack(fill="x", pady=2)
        Label(yz_frame, text="YZ Plane:", fg="blue").pack(side="left")
        self.yz_zoom_var = DoubleVar(value=self.main_app.zoom_yz)
        yz_slider = Scale(yz_frame, from_=self.main_app.min_zoom, to=self.main_app.max_zoom, orient=HORIZONTAL, command=self.main_app.zoom_yz_slider_changed, variable=self.yz_zoom_var, resolution=0.1)
        yz_slider.pack(side="left", padx=1)
        Button(yz_frame, text="Reset", command=self.main_app.reset_zoom_yz, width=5, bg="lightblue").pack(side="left", padx=1)

        # XZ Plane controls
        xz_frame = Frame(zoom_frame)
        xz_frame.pack(fill="x", pady=2)
        Label(xz_frame, text="XZ Plane:", fg="orange").pack(side="left")
        self.xz_zoom_var = DoubleVar(value=self.main_app.zoom_xz)
        xz_slider = Scale(xz_frame, from_=self.main_app.min_zoom, to=self.main_app.max_zoom, orient=HORIZONTAL, command=self.main_app.zoom_xz_slider_changed, variable=self.xz_zoom_var, resolution=0.1)
        xz_slider.pack(side="left", padx=1)
        Button(xz_frame, text="Reset", command=self.main_app.reset_zoom_xz, width=5, bg="lightblue").pack(side="left", padx=1)

        # Zoom level display
        self.zoom_info_frame = Frame(zoom_frame)
        self.zoom_info_frame.pack(fill="x", pady=5)
        self.zoom_info_label = Label(self.zoom_info_frame, text="Zoom: XY=1.0 YZ=1.0 XZ=1.0", font=("Arial", 8))
        self.zoom_info_label.pack()

        # Pan info display
        self.pan_info_label = Label(self.zoom_info_frame, text="Pan: XY=(0,0) YZ=(0,0) XZ=(0,0)", font=("Arial", 8))
        self.pan_info_label.pack()

    def update_zoom_info(self):
        """Update zoom level display with needle information"""
        zoom_text = f"Zoom: XY={self.main_app.zoom_xy:.1f} YZ={self.main_app.zoom_yz:.1f} XZ={self.main_app.zoom_xz:.1f}"
        
        # Add needle center information if available
        needle_center_xy = self.main_app.get_needle_center_xy()
        if needle_center_xy:
            needle_text = f"\nNeedle Center: ({needle_center_xy[0]:.1f}, {needle_center_xy[1]:.1f})"
            zoom_text += needle_text
        
        self.zoom_info_label.config(text=zoom_text)
        
        # Update pan info
        pan_text = f"Pan: XY=({self.main_app.pan_xy[0]:.0f},{self.main_app.pan_xy[1]:.0f}) YZ=({self.main_app.pan_yz[0]:.0f},{self.main_app.pan_yz[1]:.0f}) XZ=({self.main_app.pan_xz[0]:.0f},{self.main_app.pan_xz[1]:.0f})"
        self.pan_info_label.config(text=pan_text)

    def init_sliders(self):
        """Initialize control sliders"""
        sliders_frame = Frame(self.sidebar)
        sliders_frame.pack(fill="both", expand=True)

        self.add_slider(sliders_frame, "X Value", 512, 256, lambda value: self.main_app.slider_changed("X Value", value))
        self.add_slider(sliders_frame, "Y Value", 512, 256, lambda value: self.main_app.slider_changed("Y Value", value))
        self.add_slider(sliders_frame, "Z Value", 512, 256, lambda value: self.main_app.slider_changed("Z Value", value))
        self.add_slider(sliders_frame, "X Rotation", 180, 90, lambda value: self.main_app.slider_changed("X Rotation", value))
        self.add_slider(sliders_frame, "Y Rotation", 360, 180, lambda value: self.main_app.slider_changed("Y Rotation", value))
        self.add_slider(sliders_frame, "Z Rotation", 360, 180, lambda value: self.main_app.slider_changed("Z Rotation", value))

    def add_slider(self, parent, label_text, maximum, initial_value, command):
        """Add a slider with label"""
        label = Label(parent, text=label_text)
        label.pack()
        slider = Scale(parent, from_=0, to=maximum, orient=HORIZONTAL, command=command)
        slider.set(initial_value)
        slider.pack()

    def init_main_view(self):
        """Initialize the main view area"""
        self.main_view_frame = Frame(self.root)
        self.main_view_frame.pack(side="right", fill="both", expand=True)

        self.canvas = Canvas(self.main_view_frame)
        self.canvas.grid(row=0, column=0, sticky="nsew")

        self.scrollbar_y = Scrollbar(self.main_view_frame, orient=VERTICAL, command=self.canvas.yview)
        self.scrollbar_y.grid(row=0, column=1, sticky="ns")

        self.scrollbar_x = Scrollbar(self.main_view_frame, orient=HORIZONTAL, command=self.canvas.xview)
        self.scrollbar_x.grid(row=1, column=0, sticky="ew")

        self.main_view_frame.grid_rowconfigure(0, weight=1)
        self.main_view_frame.grid_columnconfigure(0, weight=1)

        self.canvas.configure(xscrollcommand=self.scrollbar_x.set, yscrollcommand=self.scrollbar_y.set)
        self.canvas.bind('<Configure>', lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))

        self.content_frame = Frame(self.canvas)
        self.canvas.create_window((0, 0), window=self.content_frame, anchor="nw")

        self.init_panels()

    def init_panels(self):
        """Initialize image display panels"""
        self.panel2 = self.create_panel("XY", "magenta", "yellow")
        self.panel3 = self.create_panel("YZ", "blue", "magenta")
        self.panel4 = self.create_panel("XZ", "blue", "yellow")

        self.panel2.grid(row=0, column=0, sticky="nsew", padx=1, pady=1)
        self.panel3.grid(row=0, column=1, sticky="nsew", padx=1, pady=1)
        self.panel4.grid(row=1, column=0, sticky="nsew", padx=1, pady=1)

        self.content_frame.grid_columnconfigure(0, weight=1, minsize=512)
        self.content_frame.grid_columnconfigure(1, weight=1, minsize=512)
        self.content_frame.grid_rowconfigure(0, weight=1, minsize=512)
        self.content_frame.grid_rowconfigure(1, weight=1, minsize=512)

        self.panels.extend([self.panel2, self.panel3, self.panel4])

        # Add mouse wheel zoom support to panels
        self.setup_mouse_zoom()
        # Add drag support to panels
        self.setup_drag_support()

    def setup_mouse_zoom(self):
        """Setup mouse wheel zoom for panels"""
        def on_mouse_wheel(event, panel_num):
            # Store old zoom values for pan calculation
            old_zoom = None
            if panel_num == 0:
                old_zoom = self.main_app.zoom_xy
            elif panel_num == 1:
                old_zoom = self.main_app.zoom_yz
            elif panel_num == 2:
                old_zoom = self.main_app.zoom_xz
            
            if event.delta > 0:
                if panel_num == 0:
                    self.main_app.zoom_in_xy()
                elif panel_num == 1:
                    self.main_app.zoom_in_yz()
                elif panel_num == 2:
                    self.main_app.zoom_in_xz()
            else:
                if panel_num == 0:
                    self.main_app.zoom_out_xy()
                elif panel_num == 1:
                    self.main_app.zoom_out_yz()
                elif panel_num == 2:
                    self.main_app.zoom_out_xz()
            
            self.update_zoom_info()

        # Bind mouse wheel events to each panel
        for i, panel in enumerate(self.panels):
            panel.canvas.bind("<MouseWheel>", lambda event, num=i: on_mouse_wheel(event, num))
            # For Linux systems
            panel.canvas.bind("<Button-4>", lambda event, num=i: on_mouse_wheel(type('MockEvent', (), {'delta': 120})(), num))
            panel.canvas.bind("<Button-5>", lambda event, num=i: on_mouse_wheel(type('MockEvent', (), {'delta': -120})(), num))

    def setup_drag_support(self):
        """Setup drag support for all panels"""
        for i, panel in enumerate(self.panels):
            # Bind mouse events for dragging
            panel.canvas.bind("<Button-1>", lambda event, num=i: self.start_drag(event, num))
            panel.canvas.bind("<B1-Motion>", lambda event, num=i: self.on_drag(event, num))
            panel.canvas.bind("<ButtonRelease-1>", lambda event, num=i: self.end_drag(event, num))
            
            # Change cursor when hovering over canvas
            panel.canvas.bind("<Enter>", lambda event: event.widget.config(cursor="hand2"))
            panel.canvas.bind("<Leave>", lambda event: event.widget.config(cursor=""))

    def start_drag(self, event, panel_num):
        """Start dragging operation"""
        self.drag_data['dragging'] = True
        self.drag_data['start_x'] = event.x
        self.drag_data['start_y'] = event.y
        self.drag_data['panel_index'] = panel_num
        
        # Change cursor to indicate dragging
        self.panels[panel_num].canvas.config(cursor="fleur")

    def on_drag(self, event, panel_num):
        """Handle drag motion"""
        if not self.drag_data['dragging'] or self.drag_data['panel_index'] != panel_num:
            return
        
        # Calculate drag distance
        dx = event.x - self.drag_data['start_x']
        dy = event.y - self.drag_data['start_y']
        
        # Update pan offset for the specific panel
        if panel_num == 0:  # XY plane
            self.main_app.pan_xy[0] += dx
            self.main_app.pan_xy[1] += dy
        elif panel_num == 1:  # YZ plane
            self.main_app.pan_yz[0] += dx
            self.main_app.pan_yz[1] += dy
        elif panel_num == 2:  # XZ plane
            self.main_app.pan_xz[0] += dx
            self.main_app.pan_xz[1] += dy
        
        # Update the display
        self.main_app.update_single_panel(panel_num)
        
        # Update drag start position for next motion
        self.drag_data['start_x'] = event.x
        self.drag_data['start_y'] = event.y
        
        # Update info display
        self.update_zoom_info()

    def end_drag(self, event, panel_num):
        """End dragging operation"""
        self.drag_data['dragging'] = False
        self.drag_data['panel_index'] = -1
        
        # Reset cursor
        self.panels[panel_num].canvas.config(cursor="hand2")

    def create_panel(self, label_text, x_color, y_color):
        """Create a display panel"""
        panel = Frame(self.content_frame, bg="black", width=512, height=512)
        panel.pack_propagate(False)
        panel.canvas = Canvas(panel, bg="black")
        panel.canvas.pack(fill="both", expand=True, anchor="center")
        
        # Add plane label
        panel.plane_label = label_text
        
        return panel
        
    def update_panel_image(self, panel, image_data, zoom=1.0, pan_offset=(0, 0)):
        """Update image in a panel with zoom and pan support"""
        if image_data is None:
            return
        
        # Create PIL image from data
        image = self.main_app.dicom_handler.make_2d_image(image_data) if hasattr(self.main_app.dicom_handler, 'make_2d_image') else self.create_image_from_array(image_data)
        
        if image is None:
            return
        
        # Apply zoom transformation
        if zoom != 1.0:
            new_width = int(image.width * zoom)
            new_height = int(image.height * zoom)
            image = image.resize((new_width, new_height), Image.LANCZOS)
        
        photo = ImageTk.PhotoImage(image=image)
        
        # Clear previous content but keep needle and realtime lines
        panel.canvas.delete("images")
        
        if photo:
            canvas_width = panel.canvas.winfo_width() or 512
            canvas_height = panel.canvas.winfo_height() or 512
            image_width = photo.width()
            image_height = photo.height()
            
            # Center the image in canvas and apply pan offset
            x = (canvas_width - image_width) // 2 + pan_offset[0]
            y = (canvas_height - image_height) // 2 + pan_offset[1]
            
            panel.canvas.create_image(x, y, image=photo, anchor='nw', tags="images")
            panel.canvas.image = photo  # Keep a reference
        
        # Ensure needle and realtime lines are drawn on top
        panel.canvas.tag_raise("needle")
        panel.canvas.tag_raise("realtime")
        panel.canvas.tag_raise("axes")
        
        # Update zoom info display
        self.update_zoom_info()

    def create_image_from_array(self, array):
        """Create PIL Image from numpy array"""
        try:
            # Normalize the array to 0-255 range
            if array.dtype != np.uint8:
                array_normalized = ((array - array.min()) / (array.max() - array.min()) * 255).astype(np.uint8)
            else:
                array_normalized = array
            
            # Create PIL Image
            image = Image.fromarray(array_normalized, mode='L')  # 'L' for grayscale
            return image
        except Exception as e:
            print(f"Error creating image from array: {e}")
            return None