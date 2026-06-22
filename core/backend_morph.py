"""
Backend
Responsabil exclusiv pentru logica de procesare a imaginilor.
"""

import os
import cv2
import numpy as np
from typing import Dict, List, Optional, Tuple, Union

# Importăm modelul de date creat la Pasul 1
from core.models import Operatie


class MorphoBackend:

    def __init__(self):
        self.image_original: Optional[np.ndarray] = None
        self.image_processed: Optional[np.ndarray] = None
        self.operation_stack: List[Operatie] = []

        # Datele brute ale volumului/setului (nu se modifică niciodată)
        self.base_data: Dict[str, np.ndarray] = {}
        # Cache-ul rezultatelor procesate (recalculat la fiecare schimbare de stivă)
        self.batch_cache: Dict[str, np.ndarray] = {}

    # ------------------------------------------------------------------
    # Operații pe stivă
    # ------------------------------------------------------------------

    def adauga_operatie(self, operatie: Operatie) -> None:
        self.operation_stack.append(operatie)
        self.recalculate_pipeline()

    def sterge_operatie(self, index: int) -> bool:
        if 0 <= index < len(self.operation_stack):
            self.operation_stack.pop(index)
            self.recalculate_pipeline()
            return True
        return False

    def muta_operatie(self, old_index: int, new_index: int) -> bool:
        """Mută o operație (Drag & Drop). Returnează True dacă s-a modificat ceva."""
        if not (0 <= old_index < len(self.operation_stack)):
            return False
        new_index = max(0, min(new_index, len(self.operation_stack) - 1))
        if old_index == new_index:
            return False
        op = self.operation_stack.pop(old_index)
        self.operation_stack.insert(new_index, op)
        self.recalculate_pipeline()
        return True

    def undo(self) -> bool:
        """Elimină ultima operație din stivă."""
        if self.operation_stack:
            self.operation_stack.pop()
            self.recalculate_pipeline()
            return True
        return False

    def reset(self) -> None:
        """Golește stiva și recalculează (revine la original)."""
        self.operation_stack.clear()
        self.recalculate_pipeline()

    # ------------------------------------------------------------------
    # Recalculare pipeline (nucleul logicii)
    # ------------------------------------------------------------------

    def recalculate_pipeline(self) -> None:
        """
        Reaplicăm toți operatorii din stivă, în ordine, atât pe
        imaginea unică cât și pe întregul set batch.
        """
        # 1. Single Image
        if self.image_original is not None:
            rezultat = self.image_original.copy()
            for op in self.operation_stack:
                rezultat = self._aplica_filtru(rezultat, op.nume, op.kernel)
            self.image_processed = rezultat

        # 2. Batch
        if self.base_data:
            temp: Dict[str, np.ndarray] = {}
            for file_name, img in self.base_data.items():
                rezultat = img.copy()
                for op in self.operation_stack:
                    rezultat = self._aplica_filtru(rezultat, op.nume, op.kernel)
                temp[file_name] = rezultat
            self.batch_cache = temp

    # ------------------------------------------------------------------
    # Gestionare imagine unică
    # ------------------------------------------------------------------

    def load_image(self, file_path: str) -> bool:
        img = cv2.imread(file_path, cv2.IMREAD_GRAYSCALE)
        if img is None:
            return False
        self.image_original = img
        self.image_processed = None
        # Nu resetăm stiva – utilizatorul poate vrea să aplice același pipeline pe o nouă imagine
        self.recalculate_pipeline()
        return True

    def save_image(self, file_path: str) -> bool:
        if self.image_processed is not None:
            return cv2.imwrite(file_path, self.image_processed)
        return False

    def get_original_image(self) -> Optional[np.ndarray]:
        return self.image_original

    def get_processed_image(self) -> Optional[np.ndarray]:
        return self.image_processed

    # ------------------------------------------------------------------
    # Conversie volum NIfTI → felii 2D
    # ------------------------------------------------------------------

    def convert_nii_volume(self, nii_path: str, output_folder: str) -> Tuple[bool, Union[int, str]]:
        """
        Citește un volum 3D (.nii / .nii.gz) și salvează feliile pe disc,
        păstrând și o copie în RAM (base_data).
        """
        try:
            import nibabel as nib
        except ImportError:
            return False, "nibabel nu este instalat. Rulați: pip install nibabel"

        try:
            img_3d = nib.load(nii_path)
            data = img_3d.get_fdata()
            num_slices = data.shape[2]

            os.makedirs(output_folder, exist_ok=True)

            self.base_data = {}
            self.batch_cache = {}

            for i in range(num_slices):
                slice_2d = data[:, :, i].copy()

                max_val = np.max(slice_2d)
                min_val = np.min(slice_2d)
                if max_val > min_val:
                    slice_2d = (slice_2d - min_val) / (max_val - min_val) * 255.0
                else:
                    # Felie complet goală (toate valorile identice)
                    slice_2d = np.zeros_like(slice_2d)

                slice_2d = slice_2d.astype(np.uint8)

                file_name = f"slice_{i:03d}.png"
                cv2.imwrite(os.path.join(output_folder, file_name), slice_2d)
                self.base_data[file_name] = slice_2d

            return True, num_slices

        except Exception as e:
            return False, str(e)

    # ------------------------------------------------------------------
    # Gestionare batch
    # ------------------------------------------------------------------

    def load_batch_from_folder(self, folder: str) -> Tuple[bool, Union[int, str]]:
        """Citește toate imaginile .png dintr-un folder în RAM (base_data)."""
        if not os.path.isdir(folder):
            return False, "Directorul nu există."

        files = sorted(f for f in os.listdir(folder) if f.endswith(".png"))
        if not files:
            return False, "Nu s-au găsit imagini .png în director."

        self.base_data = {}
        self.batch_cache = {}

        for file_name in files:
            img = cv2.imread(os.path.join(folder, file_name), cv2.IMREAD_GRAYSCALE)
            if img is not None:
                self.base_data[file_name] = img

        if not self.base_data:
            return False, "Nicio imagine nu a putut fi citită."

        self.recalculate_pipeline()
        return True, len(self.base_data)

    def save_batch_from_memory(self, output_folder: str) -> Tuple[bool, Union[int, str]]:
        """Scrie cache-ul RAM pe disc."""
        if not self.batch_cache:
            return False, "Nu există date procesate în memorie."

        os.makedirs(output_folder, exist_ok=True)

        for file_name, img in self.batch_cache.items():
            cv2.imwrite(os.path.join(output_folder, file_name), img)

        return True, len(self.batch_cache)

    def get_batch_slice(self, file_name: str) -> Optional[np.ndarray]:
        """Returnează felie originală sau procesată (dacă există)."""
        if self.batch_cache:
            return self.batch_cache.get(file_name)
        return self.base_data.get(file_name)

    # ------------------------------------------------------------------
    # Funcție internă de procesare OpenCV
    # ------------------------------------------------------------------

    @staticmethod
    def _aplica_filtru(img: np.ndarray, operator: str, k_size: int) -> np.ndarray:
        """Aplică un singur operator morfologic pe o imagine."""
        if k_size % 2 == 0:
            k_size += 1
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (k_size, k_size))

        operatori = {
            "Eroziune":   lambda i, k: cv2.erode(i, k),
            "Dilatare":   lambda i, k: cv2.dilate(i, k),
            "Deschidere": lambda i, k: cv2.morphologyEx(i, cv2.MORPH_OPEN, k),
            "Închidere":  lambda i, k: cv2.morphologyEx(i, cv2.MORPH_CLOSE, k),
            "Top-Hat":    lambda i, k: cv2.morphologyEx(i, cv2.MORPH_TOPHAT, k),
            "Black-Hat":  lambda i, k: cv2.morphologyEx(i, cv2.MORPH_BLACKHAT, k),
            "Gradient":   lambda i, k: cv2.morphologyEx(i, cv2.MORPH_GRADIENT, k),
        }

        func = operatori.get(operator)
        if func is None:
            return img
        return func(img, kernel)