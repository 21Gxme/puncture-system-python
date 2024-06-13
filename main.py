import sys
import os
import numpy as np
import pydicom as dicom
from tkinter import Tk, Frame, Label, Button, Menu, Listbox, filedialog, Scale, HORIZONTAL, END
from tkinter.ttk import Notebook
from PIL import Image, ImageTk
import shutil


class Vector3D:
    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z


class MainPage:
    def __init__(self, root):
        self.root = root
        self.root.title("MR_PunctureSystem")
        self.root.geometry("1200x800")

        self.panels = []
        self.X = 256
        self.Y = 256
        self.Z = 256

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
        self.CT_Ajust = -1000  # Example value, adjust accordingly

        self.init_toolbar()
        self.init_sidebar()
        self.init_main_view()

        self.dataList = []
        self.selectedItem = None

    def init_toolbar(self):
        self.toolbar = Frame(self.root)
        self.toolbar.pack(side="top", fill="x")

        menu_button = Button(self.toolbar, text="Menu", command=self.toggle_sidebar)
        menu_button.pack(side="left")

        file_button = Button(self.toolbar, text="File", command=self.show_file_menu)
        file_button.pack(side="left")

        load_button = Button(self.toolbar, text="Load", command=self.btnLoadPictures_Click)
        load_button.pack(side="left")

        add_button = Button(self.toolbar, text="Add", command=self.show_add_menu)
        add_button.pack(side="left")

        delete_button = Button(self.toolbar, text="Delete")
        delete_button.pack(side="left")

        exchange_button = Button(self.toolbar, text="Exchange")
        exchange_button.pack(side="left")

        zoom_in_button = Button(self.toolbar, text="ZoomIn", command=self.zoom_in)
        zoom_in_button.pack(side="left")

        zoom_out_button = Button(self.toolbar, text="ZoomOut", command=self.zoom_out)
        zoom_out_button.pack(side="left")

        load_pictures_button = Button(self.toolbar, text="Load Pictures", command=self.load_pictures)
        load_pictures_button.pack(side="left")

    def init_sidebar(self):
        self.sidebar = Frame(self.root)
        self.sidebar.pack(side="left", fill="y")

        self.list_view = Listbox(self.sidebar)
        self.list_view.pack(fill="both", expand=True)
        self.list_view.bind("<<ListboxSelect>>", self.list_view_item_click)

        self.init_sliders()

    def init_sliders(self):
        sliders_frame = Frame(self.sidebar)
        sliders_frame.pack(fill="both", expand=True)

        self.add_slider(sliders_frame, "X Value", 512, 256, lambda value: self.slider_changed("X Value", value))
        self.add_slider(sliders_frame, "Y Value", 512, 256, lambda value: self.slider_changed("Y Value", value))
        self.add_slider(sliders_frame, "Z Value", 512, 256, lambda value: self.slider_changed("Z Value", value))
        self.add_slider(sliders_frame, "X Rotation", 180, 90, lambda value: self.slider_changed("X Rotation", value))
        self.add_slider(sliders_frame, "Y Rotation", 180, 90, lambda value: self.slider_changed("Y Rotation", value))
        self.add_slider(sliders_frame, "Z Rotation", 180, 90, lambda value: self.slider_changed("Z Rotation", value))

    def add_slider(self, parent, label_text, maximum, initial_value, command):
        label = Label(parent, text=label_text)
        label.pack()
        slider = Scale(parent, from_=0, to=maximum, orient=HORIZONTAL, command=command)
        slider.set(initial_value)
        slider.pack()

    def slider_changed(self, name, value):
        if name == "X Value":
            self.Y = int(value)
        elif name == "Y Value":
            self.X = int(value)
        elif name == "Z Value":
            self.Z = int(int(value)/3.0843373494)
        self.update_images()
        print(f"Slider changed: {name} to {int(value)}")

    def init_main_view(self):
        self.main_view_frame = Frame(self.root)
        self.main_view_frame.pack(side="right", fill="both", expand=True)

        self.init_panels()

    def init_panels(self):
        self.panel1 = self.create_panel("3D")
        self.panel2 = self.create_panel("XY")
        self.panel3 = self.create_panel("YZ")
        self.panel4 = self.create_panel("XZ")

        self.panel1.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        self.panel2.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        self.panel3.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        self.panel4.grid(row=1, column=1, sticky="nsew", padx=10, pady=10)

        self.main_view_frame.grid_columnconfigure(0, weight=1)
        self.main_view_frame.grid_columnconfigure(1, weight=1)
        self.main_view_frame.grid_rowconfigure(0, weight=1)
        self.main_view_frame.grid_rowconfigure(1, weight=1)

        self.panels.extend([self.panel1, self.panel2, self.panel3, self.panel4])

    def create_panel(self, label_text):
        panel = Frame(self.main_view_frame, bg="black", width=512, height=512)
        panel.pack_propagate(False)  # Prevent the panel from resizing to fit its contents
        panel.canvas = Label(panel, bg="black")
        panel.canvas.pack(fill="both", expand=True)
        panel.bind("<Configure>", self.on_panel_resize)
        return panel

    def on_panel_resize(self, event):
        panel = event.widget
        size = min(panel.winfo_width(), panel.winfo_height())
        panel.config(width=size, height=size)

    def toggle_sidebar(self):
        if self.sidebar.winfo_viewable():
            self.sidebar.pack_forget()
        else:
            self.sidebar.pack(side="left", fill="y")

    def show_file_menu(self):
        menu = Menu(self.root, tearoff=0)
        menu.add_command(label="RAWデータ", command=self.input_button_click)
        menu.add_command(label="座標データ")
        menu.add_command(label="穿刺予定座標データ")
        menu.add_command(label="始点終点データ")
        menu.post(self.root.winfo_pointerx(), self.root.winfo_pointery())

    def input_button_click(self):
        folder = filedialog.askdirectory(title="Select a Folder")
        if folder:
            self.load_folder(folder)

    def load_folder(self, folder):
        folder_name = os.path.basename(folder)
        destination = os.path.join(os.getcwd() + "/dicom-folder", folder_name)
        if not os.path.exists(destination):
            shutil.copytree(folder, destination)
        self.dataList.append(destination)
        self.list_view.insert(END, folder_name)

    def list_view_item_click(self, event):
        selected_indices = self.list_view.curselection()
        if selected_indices:
            self.selectedItem = self.list_view.get(selected_indices[0])
            self.IsSelectedItem = 1
            self.load_dicom_images(self.selectedItem)
            self.update_images()

    def btnLoadPictures_Click(self):
        if self.IsSelectedItem == 0:
            return
        for num, pa in enumerate(self.panels):
            self.load_panel_image(pa, num)

    def load_panel_image(self, pa, num):
        if self.IsSelectedItem == 0:
            return
        try:
            if num == 1:  # Axial view XY
                image_2d = self.volume3d[:, :, self.Z]
            elif num == 2:  # Sagittal view YZ
                image_2d = np.flipud(np.rot90(self.volume3d[:, self.Y, :]))
            elif num == 3:  # Coronal view XZ
                image_2d = np.flipud(np.rot90(self.volume3d[self.X, :, :]))
            else:
                image_2d = np.zeros((512, 512), dtype=np.int16)  # Placeholder for the 3D view
        except IndexError:
            image_2d = np.zeros((512, 512), dtype=np.int16)  # Set the panel to black screen in case of error

        self.update_panel_image(pa, image_2d)

    def update_panel_image(self, panel, image_data):
        image = self.make_2d_image(image_data)
        photo = ImageTk.PhotoImage(image=image)
        panel.canvas.config(image=photo)
        panel.canvas.image = photo

    def load_dicom_images(self, folder_name):
        path = "./dicom-folder/" + folder_name
        ct_images = os.listdir(path)
        slices = [dicom.read_file(os.path.join(path, s), force=True) for s in ct_images]
        slices = sorted(slices, key=lambda x: x.ImagePositionPatient[2], reverse=True)

        pixel_spacing = slices[0].PixelSpacing
        slices_thickness = slices[0].SliceThickness

        img_shape = list(slices[0].pixel_array.shape)
        img_shape.append(len(slices))
        self.volume3d = np.zeros(img_shape)

        for i, s in enumerate(slices):
            array2D = s.pixel_array
            self.volume3d[:, :, i] = array2D

        self.X = img_shape[0] // 2
        self.Y = img_shape[1] // 2
        self.Z = img_shape[2] // 2
        print("X,Y,Z: ", self.X, self.Y, self.Z)
    def make_2d_image(self, image_2d):
        normalized_image = ((image_2d - image_2d.min()) / (image_2d.max() - image_2d.min()) * 255).astype(np.uint8)
        height, width = normalized_image.shape
        image = Image.fromarray(normalized_image)
        return image

    def update_images(self):
        for num, pa in enumerate(self.panels):
            self.load_panel_image(pa, num)

    def zoom_in(self):
        self.zoom(1.1)

    def zoom_out(self):
        self.zoom(0.9)

    def zoom(self, factor):
        pass  # Implement zoom functionality

    def show_add_menu(self):
        print("Show add menu")

    def load_pictures(self):
        pass  # Implement load pictures functionality


if __name__ == '__main__':
    root = Tk()
    app = MainPage(root)
    root.mainloop()
