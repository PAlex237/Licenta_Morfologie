import os
import shutil
import time
import cv2
import numpy as np

NR_FELII = 155
DIM_FELIE = (240, 240)

print(f"Generăm volumul RMN sintetic ({NR_FELII} felii de {DIM_FELIE[0]}x{DIM_FELIE[1]} px)...")
np.random.seed(42) # Seed fix pentru ca zgomotul generat să fie identic la fiecare rulare
volum_brats = [np.random.randint(0, 255, DIM_FELIE, dtype=np.uint8) for _ in range(NR_FELII)]

kernele_test = {
    "5x5 (Medie)": np.ones((5, 5), dtype=np.uint8),
    "15x15 (Extremă)": np.ones((15, 15), dtype=np.uint8)
}

FOLDER_TEMP_DISK = "./temp_benchmark_io"

print("\n=== START BENCHMARK: IN-MEMORY CACHE vs. DISK I/O ===")

for nume_k, kernel in kernele_test.items():
    print(f"\n--- Rulăm testul pentru Kernel: {nume_k} ---")
    
    # ----------------------------------------------------
    # SCENARIUL A: In-Memory Cache (Abordarea Morfomed)
    # ----------------------------------------------------
    cache_ram = {}
    
    # Folosim perf_counter() pentru precizie de nanosecundă la nivel de CPU
    start_ram = time.perf_counter() 
    
    for i, felie in enumerate(volum_brats):
        # Aplicăm un filtru compus (Deschidere)
        rezultat = cv2.morphologyEx(felie, cv2.MORPH_OPEN, kernel)
        cache_ram[f"cadru_{i}"] = rezultat # Salvăm pur în memoria RAM
        
    timp_ram = time.perf_counter() - start_ram
    print(f" [RAM Cache]  Timp procesare și stocare: {timp_ram:.4f} secunde")

    # ----------------------------------------------------
    # SCENARIUL B: Disk I/O (Abordarea clasică neoptimizată)
    # ----------------------------------------------------
    if os.path.exists(FOLDER_TEMP_DISK):
        shutil.rmtree(FOLDER_TEMP_DISK)
    os.makedirs(FOLDER_TEMP_DISK, exist_ok=True)
    
    start_disk = time.perf_counter()
    
    for i, felie in enumerate(volum_brats):
        rezultat = cv2.morphologyEx(felie, cv2.MORPH_OPEN, kernel)
        # Simulează un soft care scrie pe SSD fiecare cadru pentru a-l afișa
        cv2.imwrite(f"{FOLDER_TEMP_DISK}/cadru_{i}.png", rezultat)
        
    timp_disk = time.perf_counter() - start_disk
    print(f" [Disk I/O]   Timp procesare și scriere: {timp_disk:.4f} secunde")
    
    # Ștergem pozele de pe SSD ca să nu lăsăm gunoi după test
    shutil.rmtree(FOLDER_TEMP_DISK)
    
    # Calculăm de câte ori e mai rapid
    accelerare = timp_disk / timp_ram
    print(f" -> Arhitectura In-Memory a fost de {accelerare:.2f}x mai rapidă!")

print("\n===================================================")