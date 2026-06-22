# Sistem de Procesare și Analiză Morfologică pentru Imagistică Medicală 3D

O aplicație desktop avansată, dezvoltată în Python, concepută pentru vizualizarea, decodificarea și procesarea volumelor de date medicale 3D (în format NIfTI) utilizând tehnici fundamentale și avansate de **Morfologie Matematică**. 

Proiectul este optimizat pentru preprocesarea imaginilor obținute prin Rezonanță Magnetică (RMN / MRI), oferind suport critic în izolarea structurilor anatomice complexe, reducerea zgomotului de fond și facilitarea segmentării formațiunilor tumorale. Aplicația utilizează o arhitectură modulară decuplată (Core-GUI), asigurând o viteză ridicată de procesare prin mecanisme de caching direct în memoria RAM (In-Memory Processing).

![Interfața Principală](assets/main_interface.png)
*(Adaugă aici o captură de ecran cu interfața principală a aplicației)*

---

## 🚀 Caracteristici Principale

### 1. Vizualizare și Procesare Volumetrică (Batch Processing)
* **Decodificare NIfTI (.nii, .nii.gz):** Extracția automată a cadrelor axiale 2D din volume medicale tridimensionale (ex: seturi de date oncologice/neurologice).
* **Procesare Secvențială în RAM:** Execuția operatorilor direct pe lotul de imagini din memorie, eliminând latențele de scriere/citire pe disc.
* **Sistem de Navigare Sincronizată:** Slider interactiv pentru parcurgerea cadrelor anatomice cu actualizarea instantanee a previzualizării procesate.

### 2. Mod Focus & Live Preview (Accelerare UI)
* **Navigare din Tastatură:** Posibilitatea de a schimba operatorii (Stânga/Dreapta) și intensitățile (Sus/Jos) direct din săgeți.
* **Procesare "Din Zbor":** Aplicația randează rezultatul vizual instantaneu, fără a încărca stiva de memorie, permițând o explorare rapidă a filtrelor.
* **Modul "Hold to Compare":** Funcționalitate avansată la apăsarea tastei `SPACE` pentru comutarea rapidă între imaginea originală și previzualizarea filtrului curent.

![Mod Focus](assets/focus_mode.png)
*(Adaugă aici o captură de ecran cu modul focus activat)*

### 3. Sistem Avansat de Adnotare Medicală (Labeling)
* **Bounding Boxes:** Desenare interactivă de chenare direct pe planșa procesată (cu transformări matematice precise la Zoom/Pan).
* **Meniu Contextual Dinamic:** Identificarea chenarelor la click-dreapta pentru ștergere individuală sau adăugare de noi etichete medicale.
* **Export cu Overlay:** Salvarea cadrelor de interes cu adnotările și textul suprapuse direct pe matricea de pixeli, utile pentru rapoarte clinice.

![Sistem Adnotare](assets/labeling.png)
*(Adaugă aici o captură de ecran cu meniul contextual și un chenar desenat)*

### 4. Istoric de Operații (Stacking Pipeline)
* Construirea de pipeline-uri complexe (ex: Deschidere → Eroziune → Top-Hat).
* Reordonarea filtrelor prin **Drag & Drop** cu recalcularea automată a rezultatului vizual.
* Suport integrat pentru `Undo` și resetare de sesiune.

---

## 🔬 Operatori Morfologici Implementați

* **Eroziune & Dilatare:** Operatori fundamentali pentru subțierea sau expandarea regiunilor de interes.
* **Deschidere & Închidere:** Eliminarea artefactelor izolate și umplerea golurilor structurale interne fără a afecta aria globală.
* **Top-Hat & Black-Hat:** Extracția elementelor luminoase/întunecate, excelentă pentru corecția de contrast pe fonduri neuniforme.
* **Gradient Morfologic:** Conturarea precisă a marginilor tumorale sau ale structurilor osoase.
* **Kernel Ajustabil:** Suport pentru elemente structurante pătratice dinamice (dimensiuni impare 3x3, 5x5, 7x7).

---

## 🛠️ Tehnologii și Arhitectură

Aplicația respectă principiile *Separation of Concerns*, având logica algoritmică strict separată de interfața grafică.

* **Limbaj:** Python 3.9+
* **Interfață Grafică (GUI):** `customtkinter` (Dark Mode, hardware acceleration, HighDPI support).
* **Procesare Matematică & Vision:** `OpenCV` (CV2) și `NumPy` pentru calcule de înaltă performanță pe matrice.
* **Manipulare și Randare Imagine:** `Pillow` (PIL) pentru adaptarea matricelor la UI cu resampling `NEAREST` pentru menținerea fidelității clinice la zoom.
* **Date Medicale:** `NiBabel` pentru parsarea voxelilor din fișiere `.nii`/`.nii.gz`.

### Structura Proiectului
```text
Licenta_Morfologie/
│
├── main.py                  # Punctul de intrare (Entry-point) în aplicație
├── core/                    # Logica de business și date (Backend)
│   ├── backend_morph.py     # Algoritmi morfologici, parsare NIfTI, RAM caching
│   └── models.py            # Structuri de date (ex: definiția operațiilor)
│
├── gui/                     # Interfața Grafică (Frontend)
│   ├── app.py               # Fereastra principală, randare canvas, evenimente
│   ├── config.py            # Hărți clinice, setări constante
│   └── dialogs.py           # Pop-up-uri și input-uri personalizate
│
├── data_pipeline/           # Scripturi utilitare
│   └── convert_nii.py       # Convertor standalone CLI pentru volume 3D
│
├── datasets/                # Stocare (ignorat în versionare)
│   ├── raw_3d/              # Volumele originale
│   ├── converted_2d/        # Cadrele 2D extrase (input)
│   └── processed_2d/        # Seturile de date salvate definitiv
│
└── requirements.txt         # Dependențele externe