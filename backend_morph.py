import cv2
import numpy as np
import os

class MorphoBackend:
    
    def __init__(self):
        self.image_original = None
        self.image_processed = None
        self.operation_stack = []  # Stivă pentru a ține istoricul operațiilor aplicate


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
            
            # Initialize base_data to store original slices
            self.base_data = {}
            
            for i in range(num_slices):
                slice_2d = data[:, :, i]
                if np.max(slice_2d) > 0:
                    slice_2d = (slice_2d - np.min(slice_2d)) / (np.max(slice_2d) - np.min(slice_2d))
                    slice_2d = slice_2d * 255.0
                slice_2d = slice_2d.astype(np.uint8)
                
                nume_fisier = f"slice_{i:03d}.png"
                cv2.imwrite(os.path.join(output_folder, nume_fisier), slice_2d)
                
                # Store in base_data
                self.base_data[nume_fisier] = slice_2d.copy()
                
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
    def batch_process_to_memory(self, input_folder, operator, k_size):
        """Procesează tot folderul și ține rezultatele în memoria RAM pentru preview."""
        # If base_data not initialized, read from disk
        if not hasattr(self, 'base_data') or not self.base_data:
            self.base_data = {}
            files = [f for f in os.listdir(input_folder) if f.endswith('.png')]
            for file_name in files:
                img_path = os.path.join(input_folder, file_name)
                img = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)
                if img is not None:
                    self.base_data[file_name] = img
        
        self.batch_cache = {} # Aici vom ține imaginile
        
        if not self.base_data:
            return False, "Nu s-au găsit imagini!"
            
        if k_size % 2 == 0:
            k_size += 1
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (k_size, k_size))
        
        for file_name, img in self.base_data.items():
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
                
            # Salvăm imaginea generată în dicționar (RAM), NU pe disc
            self.batch_cache[file_name] = proc
            
        return True, len(self.batch_cache)

    def save_batch_from_memory(self, output_folder):
        """Ia pozele din RAM și le scrie pe hard disk doar la cerere."""
        if not hasattr(self, 'batch_cache') or not self.batch_cache:
            return False, "Nu există date procesate în memorie!"
            
        os.makedirs(output_folder, exist_ok=True)
        for file_name, img in self.batch_cache.items():
            cv2.imwrite(os.path.join(output_folder, file_name), img)
            
        return True, len(self.batch_cache)
    
    def remove_operation(self, index):
        """Șterge o operație din stivă."""
        if 0 <= index < len(self.operation_stack):
            self.operation_stack.pop(index)
            self.recalculate_pipeline() # Reaplică filtrele rămase din stivă

    def move_operation(self, old_index, new_index):
        """Mută o operație (pentru Drag & Drop)."""
        # Ne asigurăm că noii indecși sunt valizi
        if 0 <= old_index < len(self.operation_stack):
            # Limităm new_index să nu iasă din listă
            new_index = max(0, min(new_index, len(self.operation_stack) - 1))
            
            # Extragem operația și o inserăm la noua poziție
            op = self.operation_stack.pop(old_index)
            self.operation_stack.insert(new_index, op)     
            self.recalculate_pipeline() # Reconstruim instantaneu imaginea RMN
    def recalculate_pipeline(self):
        """Reaplică în lanț toate operațiile din stivă pe datele brute din RAM (Batch + Single Image)."""
        
        # --- FUNCȚIE AJUTĂTOARE: Procesează logica OpenCV o singură dată ---
        def aplica_filtru(img, nume_filtru, k_size):
            if k_size % 2 == 0:
                k_size += 1
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (k_size, k_size))
            
            if nume_filtru == "Eroziune":
                return cv2.erode(img, kernel)
            elif nume_filtru == "Dilatare":
                return cv2.dilate(img, kernel)
            elif nume_filtru == "Deschidere":
                return cv2.morphologyEx(img, cv2.MORPH_OPEN, kernel)
            elif nume_filtru == "Închidere":
                return cv2.morphologyEx(img, cv2.MORPH_CLOSE, kernel)
            elif nume_filtru == "Top-Hat":
                return cv2.morphologyEx(img, cv2.MORPH_TOPHAT, kernel)
            elif nume_filtru == "Black-Hat":
                return cv2.morphologyEx(img, cv2.MORPH_BLACKHAT, kernel)
            elif nume_filtru == "Gradient":
                return cv2.morphologyEx(img, cv2.MORPH_GRADIENT, kernel)
            return img

        # --- 1. RECALCULARE PENTRU BATCH / PIPELINE ---
        if hasattr(self, 'base_data') and self.base_data:
            temp_data = self.base_data.copy()
            for op in self.operation_stack:
                for file_name, img in temp_data.items():
                    temp_data[file_name] = aplica_filtru(img, op["nume"], op["kernel"])
            self.batch_cache = temp_data

        # --- 2. RECALCULARE PENTRU SINGLE IMAGE ---
        if hasattr(self, 'image_original') and self.image_original is not None:
            temp_img = self.image_original.copy()
            
            # Reaplicăm toate filtrele rămase în stivă peste imaginea originală
            for op in self.operation_stack:
                temp_img = aplica_filtru(temp_img, op["nume"], op["kernel"])
                
            self.image_processed = temp_img