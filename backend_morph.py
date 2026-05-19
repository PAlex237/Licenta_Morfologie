import cv2
import numpy as np
import os

class MorphoBackend:
    def __init__(self):
        self.image_original = None
        self.image_processed = None

    def load_image(self, file_path):
        """Citește imaginea în format Grayscale."""
        self.image_original = cv2.imread(file_path, cv2.IMREAD_GRAYSCALE)
        self.image_processed = None  
        return self.image_original is not None

    def save_image(self, file_path):
        """Salvează imaginea procesată pe disc."""
        if self.image_processed is not None:
            cv2.imwrite(file_path, self.image_processed)
            return True
        return False

    def get_original_image(self):
        return self.image_original

    def get_processed_image(self):
        return self.image_processed
    def convert_nii_volume(self, nii_path, output_folder="datasets/converted_2d"):
        """Citește un volum 3D (.nii/.nii.gz) și salvează feliile 2D în converted_2d."""
        try:
            import nibabel as nib
            img_3d = nib.load(nii_path)
            data = img_3d.get_fdata()
            num_slices = data.shape[2]
            
            os.makedirs(output_folder, exist_ok=True)
            
            for i in range(num_slices):
                slice_2d = data[:, :, i]
                if np.max(slice_2d) > 0:
                    slice_2d = (slice_2d - np.min(slice_2d)) / (np.max(slice_2d) - np.min(slice_2d))
                    slice_2d = slice_2d * 255.0
                slice_2d = slice_2d.astype(np.uint8)
                
                nume_fisier = f"slice_{i:03d}.png"
                cv2.imwrite(os.path.join(output_folder, nume_fisier), slice_2d)
                
            return True, num_slices
        except Exception as e:
            return False, str(e)

    def batch_process_folder(self, input_folder="datasets/converted_2d", output_folder="datasets/processed_2d", operator="", k_size=3):
        """Aplică operatorul morfologic pe toate pozele din input_folder și le salvează în output_folder."""
        if not os.path.exists(input_folder):
            return False, "Folderul de intrare nu există!"
            
        files = [f for f in os.listdir(input_folder) if f.endswith('.png')]
        if not files:
            return False, "Nu s-au găsit imagini .png în folderul de conversie!"
            
        os.makedirs(output_folder, exist_ok=True)
        
        if k_size % 2 == 0:
            k_size += 1
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (k_size, k_size))
        
        for file_name in files:
            img_path = os.path.join(input_folder, file_name)
            img = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)
            
            if operator == "Eroziune":
                proc = cv2.erode(img, kernel, iterations=1)
            elif operator == "Dilatare":
                proc = cv2.dilate(img, kernel, iterations=1)
            elif operator == "Deschidere":
                proc = cv2.morphologyEx(img, cv2.MORPH_OPEN, kernel)
            elif operator == "Închidere":
                proc = cv2.morphologyEx(img, cv2.MORPH_CLOSE, kernel)
            elif operator == "Top-Hat":
                proc = cv2.morphologyEx(img, cv2.MORPH_TOPHAT, kernel)
            elif operator == "Black-Hat":
                proc = cv2.morphologyEx(img, cv2.MORPH_BLACKHAT, kernel)
            else:
                proc = img
                
            cv2.imwrite(os.path.join(output_folder, file_name), proc)
            
        return True, len(files)
    def apply_operator(self, operator, k_size):
        """Aplică algoritmul morfologic selectat."""
        if self.image_original is None:
            return False

        # Ne asigurăm că dimensiunea kernelului e impară
        if k_size % 2 == 0:
            k_size += 1

        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (k_size, k_size))

        if operator == "Eroziune":
            self.image_processed = cv2.erode(self.image_original, kernel, iterations=1)
        elif operator == "Dilatare":
            self.image_processed = cv2.dilate(self.image_original, kernel, iterations=1)
        elif operator == "Deschidere":
            self.image_processed = cv2.morphologyEx(self.image_original, cv2.MORPH_OPEN, kernel)
        elif operator == "Închidere":
            self.image_processed = cv2.morphologyEx(self.image_original, cv2.MORPH_CLOSE, kernel)
        elif operator == "Top-Hat":
            self.image_processed = cv2.morphologyEx(self.image_original, cv2.MORPH_TOPHAT, kernel)
        elif operator == "Black-Hat":
            self.image_processed = cv2.morphologyEx(self.image_original, cv2.MORPH_BLACKHAT, kernel)
        
        return True