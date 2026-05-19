import os
import nibabel as nib
import numpy as np
import cv2

def extrage_felii_din_nii(nii_path, output_folder):
    """
    Citeste un volum 3D medical (.nii) si il taie in felii 2D (.png).
    """
    print(f"Procesam volumul: {nii_path} ...")

    # 1. Incarcam fisierul NIfTI folosind nibabel
    img_3d = nib.load(nii_path)
    
    # 2. Extragem matricea de date matematice (de ex: 256 x 256 x 150)
    data = img_3d.get_fdata()
    
    # Numarul de felii se afla de obicei pe axa Z (a 3-a dimensiune a matricii)
    num_slices = data.shape[2]
    print(f"S-au detectat {num_slices} felii. Incepem conversia...")

    # Cream folderul de iesire daca nu exista deja
    os.makedirs(output_folder, exist_ok=True)

    # 3. Iteram prin fiecare felie a volumului 3D
    for i in range(num_slices):
        # Taiem o "felie" din matrice
        slice_2d = data[:, :, i]

        # 4. NORMALIZAREA (Foarte important!)
        # Senzorii RMN genereaza valori ciudate (ex: -100 la 3000). 
        # Noi trebuie sa le aducem in spectrul unei poze normale (0 - 255)
        if np.max(slice_2d) > 0: # Evitam impartirea la zero pentru felii goale
            slice_2d = (slice_2d - np.min(slice_2d)) / (np.max(slice_2d) - np.min(slice_2d))
            slice_2d = slice_2d * 255.0

        # Convertim numerele cu virgula in numere intregi pe 8 biti (format standard poza)
        slice_2d = slice_2d.astype(np.uint8)

        # Optional: Uneori feliile NIfTI sunt rotite la 90 de grade. Daca da, decomenteaza linia de mai jos:
        # slice_2d = cv2.rotate(slice_2d, cv2.ROTATE_90_CLOCKWISE)

        # 5. Salvarea imaginii ca fisier .png
        nume_fisier = f"slice_{i:03d}.png" # Ex: slice_001.png, slice_002.png
        output_path = os.path.join(output_folder, nume_fisier)
        
        cv2.imwrite(output_path, slice_2d)

    print(f"Gata! Feliile au fost salvate cu succes in: {output_folder}")

if __name__ == "__main__":
    cale_intrare = "../Licenta_Morfologie/datasets/raw_3d/BraTS20_Training_001_flair.nii" # SCHIMBA AICI NUMELE FISIERULUI
    cale_iesire = "../Licenta_Morfologie/datasets/processed_2d/"

    # Rulam functia
    if os.path.exists(cale_intrare):
        extrage_felii_din_nii(cale_intrare, cale_iesire)
    else:
        print(f"Eroare: Nu am gasit fisierul la adresa {cale_intrare}. Verifica numele!")