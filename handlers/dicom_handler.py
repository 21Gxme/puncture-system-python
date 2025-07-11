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
        """Load DICOM images from a folder, convert to Hounsfield Units, and create 3D volume"""
        path = "./dicom-folder/" + folder_name
        ct_images = os.listdir(path)
        slices = [dicom.read_file(os.path.join(path, s), force=True) for s in ct_images]
        slices = sorted(slices, key=lambda x: x.ImagePositionPatient[2], reverse=True)

        img_shape = list(slices[0].pixel_array.shape)
        img_shape.append(len(slices))
        self.volume3d = np.zeros(img_shape, dtype=np.float32) # Use float for HU values

        for i, s in enumerate(slices):
            # === CHANGED: Apply Rescale Slope and Intercept to get Hounsfield Units (HU) ===
            # This ensures that the pixel values are in a standardized, comparable scale.
            
            # Get slope and intercept, with defaults if they don't exist
            slope = getattr(s, 'RescaleSlope', 1)
            intercept = getattr(s, 'RescaleIntercept', 0)

            # Convert raw pixel array to HU
            array2D = s.pixel_array.astype(np.float32)
            array2D = array2D * slope + intercept
            
            self.volume3d[:, :, i] = array2D

        self.X_init = img_shape[0]
        self.Y_init = img_shape[1]
        self.Z_init = img_shape[2]

        return self.volume3d, img_shape

    # === CHANGED ===: Updated to a better contrast algorithm
    def make_2d_image(self, image_2d, brightness=0, contrast=1.0):
        """Convert 2D array to PIL Image with brightness/contrast adjustment"""
        # Normalize to 0-255 first
        if image_2d.max() - image_2d.min() != 0:
            normalized_image = ((image_2d - image_2d.min()) / (image_2d.max() - image_2d.min()) * 255)
        else:
            normalized_image = np.zeros(image_2d.shape)

        # Apply brightness and contrast using a standard formula
        # Convert to float for calculation
        adjusted_image = normalized_image.astype(np.float32)
        adjusted_image = contrast * (adjusted_image - 128) + 128 + brightness

        # Clip values to be in 0-255 range
        adjusted_image = np.clip(adjusted_image, 0, 255)

        # Convert to uint8 for image creation
        adjusted_image = adjusted_image.astype(np.uint8)

        # Create PIL image
        image = Image.fromarray(adjusted_image)
        return image