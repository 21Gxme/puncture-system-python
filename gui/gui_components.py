from tkinter import Frame, Label, Button, Listbox, Scale, HORIZONTAL, Canvas, Scrollbar, VERTICAL 
from PIL import ImageTk


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

    def create_panel(self, label_text, x_color, y_color):
        """Create a display panel"""
        panel = Frame(self.content_frame, bg="black", width=512, height=512)
        panel.pack_propagate(False)
        panel.canvas = Canvas(panel, bg="black")
        panel.canvas.pack(fill="both", expand=True, anchor="center")
        return panel
        
    def update_panel_image(self, panel, image_data):
        """Update image in a panel"""
        image = self.main_app.dicom_handler.make_2d_image(image_data) if image_data is not None else None
        photo = ImageTk.PhotoImage(image=image) if image_data is not None else None
        panel.canvas.delete("axes")
        panel.canvas.delete("images")

        if photo:
            canvas_width = panel.canvas.winfo_width()
            canvas_height = panel.canvas.winfo_height()
            image_width = photo.width()
            image_height = photo.height()
            x = (canvas_width - image_width) // 2
            y = (canvas_height - image_height) // 2
            panel.canvas.create_image(x, y, image=photo, anchor='nw')
            panel.canvas.image = photo
