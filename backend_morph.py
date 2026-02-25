import cv2
import numpy as np

class MorphoBackend:
    def __init__(self):
        self.image_original = None
        self.image_processed = None

    def load_image(self, file_path):
        """Citește imaginea în format Grayscale."""
        self.image_original = cv2.imread(file_path, cv2.IMREAD_GRAYSCALE)
        self.image_processed = None  # <--- Acest rând resetează memoria!
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