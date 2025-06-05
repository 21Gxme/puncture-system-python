import os
import numpy as np
import pydicom as dicom
from PIL import Image

class DicomHandler:
    def __init__(self):
        self.volume3d = None
        self.X_init = 256
        self.Y_init = 256
        self.Z_init = 256
        
    def load_dicom_images(self, folder_name):
        """Load DICOM images from a folder and create 3D volume"""
        path = "./dicom-folder/" + folder_name
        ct_images = os.listdir(path)
        slices = [dicom.read_file(os.path.join(path, s), force=True) for s in ct_images]
        slices = sorted(slices, key=lambda x: x.ImagePositionPatient[2], reverse=True)


        img_shape = list(slices[0].pixel_array.shape)
        img_shape.append(len(slices))
        self.volume3d = np.zeros(img_shape)

        for i, s in enumerate(slices):
            array2D = s.pixel_array
            self.volume3d[:, :, i] = array2D

        self.X_init = img_shape[0]
        self.Y_init = img_shape[1]
        self.Z_init = img_shape[2]
        
        return self.volume3d, img_shape
        
    def make_2d_image(self, image_2d):
        """Convert 2D array to PIL Image"""
        if image_2d.max() - image_2d.min() != 0:
            normalized_image = ((image_2d - image_2d.min()) / (image_2d.max() - image_2d.min()) * 255).astype(np.uint8)
        else:
            normalized_image = np.zeros(image_2d.shape, dtype=np.uint8)
        image = Image.fromarray(normalized_image)
        return image
