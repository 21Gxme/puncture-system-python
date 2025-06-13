# Fixed GUIComponents with better contrast and readability
gui_components_contrast_fix = '''import os
import shutil
from tkinter import Frame, Label, Button, Menu, Listbox, filedialog, Scale, HORIZONTAL, LEFT, END, Canvas, Scrollbar, VERTICAL, RIGHT, BOTTOM, X, Y, BOTH, TOP
from tkinter.ttk import Notebook
from PIL import ImageTk, Image

class GUIComponents:
    def __init__(self, root, main_app):
        self.root = root
        self.main_app = main_app
        self.panels = []
        
        # Zoom factors for each plane
        self.zoom_factors = {
            'xy': 1.0,
            'yz': 1.0,
            'xz': 1.0
        }
        
        # Pan offsets for each plane
        self.pan_offsets = {
            'xy': {'x': 0, 'y': 0},
            'yz': {'x': 0, 'y': 0},
            'xz': {'x': 0, 'y': 0}
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

    def init_sidebar(self):
        """Initialize the sidebar"""
        self.sidebar = Frame(self.root)
        self.sidebar.pack(side="left", fill="y")

        self.list_view = Listbox(self.sidebar)
        self.list_view.pack(fill="both", expand=True)
        self.list_view.bind("<<ListboxSelect>>", self.main_app.list_view_item_click)

        self.init_sliders()
        self.init_zoom_controls()

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

    def init_zoom_controls(self):
        """Initialize zoom control buttons with high contrast"""
        zoom_frame = Frame(self.sidebar, bg="white")
        zoom_frame.pack(fill="x", pady=10)
        
        # Title with better styling
        title_label = Label(zoom_frame, text="ZOOM CONTROLS", 
                          font=("Arial", 11, "bold"), 
                          bg="white", fg="black")
        title_label.pack(pady=(5, 8))
        
        # XY Plane controls
        xy_frame = Frame(zoom_frame, bg="white")
        xy_frame.pack(fill="x", pady=3)
        Label(xy_frame, text="XY Plane:", width=8, anchor="w", 
              bg="white", fg="black", font=("Arial", 9)).pack(side="left")
        Button(xy_frame, text="Zoom+", command=lambda: self.zoom_plane('xy', 1.2), 
               width=6, font=("Arial", 8), bg="lightblue", fg="black", 
               relief="raised", bd=2).pack(side="left", padx=1)
        Button(xy_frame, text="Zoom-", command=lambda: self.zoom_plane('xy', 0.8), 
               width=6, font=("Arial", 8), bg="lightcoral", fg="black", 
               relief="raised", bd=2).pack(side="left", padx=1)
        Button(xy_frame, text="Reset", command=lambda: self.reset_zoom('xy'), 
               width=5, font=("Arial", 8), bg="lightgray", fg="black", 
               relief="raised", bd=2).pack(side="left", padx=1)
        
        # YZ Plane controls
        yz_frame = Frame(zoom_frame, bg="white")
        yz_frame.pack(fill="x", pady=3)
        Label(yz_frame, text="YZ Plane:", width=8, anchor="w", 
              bg="white", fg="black", font=("Arial", 9)).pack(side="left")
        Button(yz_frame, text="Zoom+", command=lambda: self.zoom_plane('yz', 1.2), 
               width=6, font=("Arial", 8), bg="lightblue", fg="black", 
               relief="raised", bd=2).pack(side="left", padx=1)
        Button(yz_frame, text="Zoom-", command=lambda: self.zoom_plane('yz', 0.8), 
               width=6, font=("Arial", 8), bg="lightcoral", fg="black", 
               relief="raised", bd=2).pack(side="left", padx=1)
        Button(yz_frame, text="Reset", command=lambda: self.reset_zoom('yz'), 
               width=5, font=("Arial", 8), bg="lightgray", fg="black", 
               relief="raised", bd=2).pack(side="left", padx=1)
        
        # XZ Plane controls
        xz_frame = Frame(zoom_frame, bg="white")
        xz_frame.pack(fill="x", pady=3)
        Label(xz_frame, text="XZ Plane:", width=8, anchor="w", 
              bg="white", fg="black", font=("Arial", 9)).pack(side="left")
        Button(xz_frame, text="Zoom+", command=lambda: self.zoom_plane('xz', 1.2), 
               width=6, font=("Arial", 8), bg="lightblue", fg="black", 
               relief="raised", bd=2).pack(side="left", padx=1)
        Button(xz_frame, text="Zoom-", command=lambda: self.zoom_plane('xz', 0.8), 
               width=6, font=("Arial", 8), bg="lightcoral", fg="black", 
               relief="raised", bd=2).pack(side="left", padx=1)
        Button(xz_frame, text="Reset", command=lambda: self.reset_zoom('xz'), 
               width=5, font=("Arial", 8), bg="lightgray", fg="black", 
               relief="raised", bd=2).pack(side="left", padx=1)
        
        # Separator line
        separator = Frame(zoom_frame, height=3, bg="navy", relief="sunken")
        separator.pack(fill="x", pady=10)
        
        # Global controls label
        global_label = Label(zoom_frame, text="GLOBAL CONTROLS", 
                           font=("Arial", 10, "bold"), 
                           bg="white", fg="navy")
        global_label.pack(pady=(0, 5))
        
        # All planes controls with HIGH CONTRAST
        all_frame = Frame(zoom_frame, bg="white")
        all_frame.pack(fill="x", pady=2)
        
        # Zoom All In - Green with white text
        btn1 = Button(all_frame, 
                     text="ZOOM ALL IN",
                     command=self.zoom_all_in,
                     bg="#2E7D32",      # Dark green
                     fg="white",        # White text
                     font=("Arial", 10, "bold"),
                     width=18,
                     height=2,
                     relief="raised",
                     bd=3,
                     activebackground="#4CAF50",
                     activeforeground="white")
        btn1.pack(fill="x", pady=3)
        
        # Zoom All Out - Orange with black text
        btn2 = Button(all_frame,
                     text="ZOOM ALL OUT", 
                     command=self.zoom_all_out,
                     bg="#F57C00",      # Dark orange
                     fg="black",        # Black text
                     font=("Arial", 10, "bold"),
                     width=18,
                     height=2,
                     relief="raised",
                     bd=3,
                     activebackground="#FF9800",
                     activeforeground="black")
        btn2.pack(fill="x", pady=3)
        
        # Reset All - Red with white text
        btn3 = Button(all_frame,
                     text="RESET ALL ZOOM",
                     command=self.reset_all_zoom,
                     bg="#C62828",      # Dark red
                     fg="white",        # White text
                     font=("Arial", 10, "bold"),
                     width=18,
                     height=2,
                     relief="raised",
                     bd=3,
                     activebackground="#F44336",
                     activeforeground="white")
        btn3.pack(fill="x", pady=3)
        
        # Add zoom level display with better styling
        self.zoom_info_frame = Frame(zoom_frame, bg="white")
        self.zoom_info_frame.pack(fill="x", pady=8)
        
        self.zoom_info_label = Label(self.zoom_info_frame, 
                                   text="Zoom: XY=1.0x YZ=1.0x XZ=1.0x", 
                                   font=("Arial", 9, "bold"),
                                   fg="navy",
                                   bg="white")
        self.zoom_info_label.pack()

    def update_zoom_display(self):
        """Update the zoom level display"""
        zoom_text = f"Zoom: XY={self.zoom_factors['xy']:.1f}x YZ={self.zoom_factors['yz']:.1f}x XZ={self.zoom_factors['xz']:.1f}x"
        self.zoom_info_label.config(text=zoom_text)

    def zoom_plane(self, plane, factor):
        """Zoom a specific plane"""
        self.zoom_factors[plane] *= factor
        # Limit zoom range
        self.zoom_factors[plane] = max(0.1, min(self.zoom_factors[plane], 10.0))
        self.main_app.update_images()
        self.update_zoom_display()
        print(f"{plane.upper()} plane zoom: {self.zoom_factors[plane]:.2f}x")

    def reset_zoom(self, plane):
        """Reset zoom for a specific plane"""
        self.zoom_factors[plane] = 1.0
        self.pan_offsets[plane] = {'x': 0, 'y': 0}
        self.main_app.update_images()
        self.update_zoom_display()
        print(f"{plane.upper()} plane zoom reset")

    def zoom_all_in(self):
        """Zoom in all planes"""
        for plane in self.zoom_factors:
            self.zoom_factors[plane] *= 1.2
            self.zoom_factors[plane] = max(0.1, min(self.zoom_factors[plane], 10.0))
        self.main_app.update_images()
        self.update_zoom_display()
        print("All planes zoomed in")

    def zoom_all_out(self):
        """Zoom out all planes"""
        for plane in self.zoom_factors:
            self.zoom_factors[plane] *= 0.8
            self.zoom_factors[plane] = max(0.1, min(self.zoom_factors[plane], 10.0))
        self.main_app.update_images()
        self.update_zoom_display()
        print("All planes zoomed out")

    def reset_all_zoom(self):
        """Reset zoom for all planes"""
        for plane in self.zoom_factors:
            self.zoom_factors[plane] = 1.0
            self.pan_offsets[plane] = {'x': 0, 'y': 0}
        self.main_app.update_images()
        self.update_zoom_display()
        print("All planes zoom reset")

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
        
        # Add plane identifiers for zoom functionality
        self.panel2.plane_type = 'xy'
        self.panel3.plane_type = 'yz'
        self.panel4.plane_type = 'xz'
        
        # Bind mouse events for panning (optional enhancement)
        self.bind_mouse_events()

    def bind_mouse_events(self):
        """Bind mouse events for potential panning functionality"""
        for panel in self.panels:
            panel.canvas.bind("<Button-1>", lambda e, p=panel: self.start_pan(e, p))
            panel.canvas.bind("<B1-Motion>", lambda e, p=panel: self.do_pan(e, p))
            panel.canvas.bind("<ButtonRelease-1>", lambda e, p=panel: self.end_pan(e, p))
            
    def start_pan(self, event, panel):
        """Start panning operation"""
        panel.canvas.scan_mark(event.x, event.y)
        
    def do_pan(self, event, panel):
        """Perform panning"""
        panel.canvas.scan_dragto(event.x, event.y, gain=1)
        
    def end_pan(self, event, panel):
        """End panning operation"""
        pass

    def create_panel(self, label_text, x_color, y_color):
        """Create a display panel"""
        panel = Frame(self.content_frame, bg="black", width=512, height=512)
        panel.pack_propagate(False)
        panel.canvas = Canvas(panel, bg="black")
        panel.canvas.pack(fill="both", expand=True, anchor="center")
        return panel
        
    def update_panel_image(self, panel, image_data):
        """Update image in a panel with zoom support"""
        if image_data is None:
            return
            
        # Get zoom factor for this panel
        plane_type = getattr(panel, 'plane_type', 'xy')
        zoom_factor = self.zoom_factors.get(plane_type, 1.0)
        
        # Create and process image
        image = self.main_app.dicom_handler.make_2d_image(image_data)
        
        # Apply zoom
        if zoom_factor != 1.0:
            new_width = int(image.width * zoom_factor)
            new_height = int(image.height * zoom_factor)
            image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        photo = ImageTk.PhotoImage(image=image)
        
        # Clear previous content
        panel.canvas.delete("axes")
        panel.canvas.delete("images")

        if photo:
            canvas_width = panel.canvas.winfo_width()
            canvas_height = panel.canvas.winfo_height()
            image_width = photo.width()
            image_height = photo.height()
            
            # Center the image
            x = (canvas_width - image_width) // 2
            y = (canvas_height - image_height) // 2
            
            panel.canvas.create_image(x, y, image=photo, anchor='nw', tags="images")
            panel.canvas.image = photo
            
            # Update scroll region for panning
            panel.canvas.configure(scrollregion=panel.canvas.bbox("all"))

    def get_zoom_factor(self, plane):
        """Get zoom factor for a specific plane"""
        return self.zoom_factors.get(plane, 1.0)
'''

# Write the fixed file
with open('gui/gui_components.py', 'w') as f:
    f.write(gui_components_contrast_fix)

print("✅ HIGH CONTRAST fix applied!")
print("\n🎨 Visual improvements:")
print("- White background for zoom controls section")
print("- Dark colors with white/black text for maximum contrast")
print("- Bold fonts for better readability")
print("- Raised button relief with borders")
print("- Active states for button feedback")
print("\n🔘 Button color scheme:")
print("- ZOOM ALL IN: Dark Green (#2E7D32) + White text")
print("- ZOOM ALL OUT: Dark Orange (#F57C00) + Black text") 
print("- RESET ALL ZOOM: Dark Red (#C62828) + White text")
print("- Individual buttons: Light colors + Black text")
print("\n📏 Enhanced styling:")
print("- Larger font sizes (10pt for global, 8-9pt for individual)")
print("- 3D raised button effect with borders")
print("- Better spacing and padding")
print("- Navy blue accents for headers")