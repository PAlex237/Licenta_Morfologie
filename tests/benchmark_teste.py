import cv2
import numpy as np
import time
import tracemalloc
from skimage.metrics import peak_signal_noise_ratio as psnr
from skimage.metrics import structural_similarity as ssim

def add_salt_and_pepper_noise(image, amount=0.05):
    """Adaugă zgomot artificial pentru a avea ce filtra."""
    row, col = image.shape
    noisy = np.copy(image)
    
    # Adăugare Sare (pixeli albi)
    num_salt = np.ceil(amount * image.size * 0.5)
    coords = [np.random.randint(0, i - 1, int(num_salt)) for i in image.shape]
    noisy[tuple(coords)] = 255

    # Adăugare Piper (pixeli negri)
    num_pepper = np.ceil(amount * image.size * 0.5)
    coords = [np.random.randint(0, i - 1, int(num_pepper)) for i in image.shape]
    noisy[tuple(coords)] = 0
    return noisy

def run_benchmark():
    # 1. ÎNREGISTREAZĂ CALEA CĂTRE O IMAGINE CURATĂ DIN PROIECTUL TĂU
    cale_imagine = ".\\datasets\\converted_2d\\sub-18_ses-01_T1w1019\\slice_167.png" # <--- MODIFICĂ AICI
    
    img_originala = cv2.imread(cale_imagine, cv2.IMREAD_GRAYSCALE)
    if img_originala is None:
        print("Eroare: Nu am putut găsi imaginea!")
        return

    # Creăm o versiune cu zgomot pentru test
    img_zgomot = add_salt_and_pepper_noise(img_originala, amount=0.05)
    
    # Definim kernel-urile pentru test (Fin, Mediu, Puternic)
    kernels = {
        "Fina (3x3)": np.ones((3, 3), np.uint8),
        "Medie (5x5)": np.ones((5, 5), np.uint8),
        "Puternica (7x7)": np.ones((7, 7), np.uint8)
    }

    print(f"{'Intensitate':<15} | {'Timp (ms)':<10} | {'RAM (MB)':<10} | {'PSNR (dB)':<10} | {'SSIM':<10}")
    print("-" * 65)

    for nume, kernel in kernels.items():
        # --- MĂSURĂM RAM ȘI TIMP ---
        tracemalloc.start()
        start_time = time.perf_counter()
        
        # Aplicăm "Filtrare Zgomot de Fond" (Deschidere)
        img_procesata = cv2.morphologyEx(img_zgomot, cv2.MORPH_OPEN, kernel)
        
        timp_executie_ms = (time.perf_counter() - start_time) * 1000
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        peak_ram_mb = peak / 10**6

        # --- MĂSURĂM CALITATEA (Raportat la originalul perfect curat) ---
        scor_psnr = psnr(img_originala, img_procesata)
        scor_ssim = ssim(img_originala, img_procesata, data_range=255)

        # Afișăm rezultatele
        print(f"{nume:<15} | {timp_executie_ms:<10.2f} | {peak_ram_mb:<10.2f} | {scor_psnr:<10.2f} | {scor_ssim:<10.3f}")

if __name__ == "__main__":
    run_benchmark()