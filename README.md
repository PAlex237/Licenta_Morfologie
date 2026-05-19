# Morfomed – Sistem de Procesare și Analiză Morfologică pentru Imagistică Medicală 3D

Morfomed este o aplicație desktop avansată dezvoltată în Python, concepută pentru vizualizarea, decodificarea și procesarea volumelor de date medicale 3D (în format NIfTI) utilizând tehnici fundamentale de **Morfologie Matematică**. Proiectul este optimizat pentru preprocesarea imaginilor obținute prin Rezonanță Magnetică (RMN / MRI), oferind suport critic în izolarea structurilor anatomice complexe și facilitarea segmentării formațiunilor tumorale.

Aplicația este structurată pe o arhitectură decuplată de tip **Backend-Frontend**, asigurând o viteză ridicată de procesare prin utilizarea unui cache direct în memoria RAM a sistemului (In-Memory Processing Pipeline) pentru loturile mari de cadre axiale.

---

## 🚀 Caracteristici Principale

### 1. Pipeline Volumetric 3D (Mod Segmentare/Lot)
* **Decodificare NIfTI (.nii, .nii.gz):** Extracția automată a cadrelor axiale 2D din volume medicale tridimensionale (ex: seturi de date oncologice/neurologice tip BraTS).
* **Procesare Secvențială în RAM:** Execuția operatorilor morfologici direct pe întregul lot de imagini din memorie, eliminând latențele de scriere/citire pe disc în timpul fazei de ajustare.
* **Sistem Premium de Navigare:** Slider interactiv pentru parcurgerea cadrelor anatomice în timp real cu sincronizare instantanee a rezultatelor procesate (Preview RAM).
* **Management de Persistență:** Exportul loturilor procesate în structuri organizate de directoare (`datasets/processed_2d/`).

### 2. Procesare Cadru 2D (Mod Individual)
* Încărcarea independentă a imaginilor grayscale/binare.
* Aplicarea individuală a algoritmilor și salvarea rapidă a rezultatului editat.

### 3. Operatori Morfologici Implementați
* **Eroziune & Dilatare:** Operatori fundamentali pentru reducerea zgomotului de fond sau extinderea regiunilor de interes.
* **Deschidere (Opening) & Închidere (Closing):** Eliminarea artefactelor izolate și umplerea golurilor structurale interne.
* **Top-Hat & Black-Hat:** Extracția elementelor luminoase sau întunecate pe fundaluri neuniforme (corecție de iluminare/contrast medical).
* **Kernel Ajustabil:** Suport pentru elemente structurante (S.E.) cu dimensiuni dinamice impare (de la 3x3 până la 15x15).

---

## 🛠️ Tehnologii Utilizate

* **Limbaj de programare:** Python 3.9+
* **Interfață Grafică (GUI):** `customtkinter` (Arhitectură modernă Dark Mode cu suport nativ pentru afișaje HighDPI).
* **Procesare de Imagine & Vision:** `OpenCV` (suport matematic de înaltă performanță) și `Pillow` (PIL).
* **Manipulare Date Medicale:** `NiBabel` (pentru parsarea și citirea corectă a metadatelor și voxelilor din fișierele `.nii`/`.nii.gz`).

---

## 📂 Structura Proiectului

Licenta-Morfologie/
│
├── main.py                  # Punctul de intrare (Entry-point) în aplicație
├── frontend_gui.py          # Implementarea interfeței grafice și gestionarea stărilor (CustomTkinter)
├── backend_morph.py         # Nucleul algoritmic (Algoritmi morfologici, parsare NIfTI, RAM caching)
│
├── datasets/                # Structura standardizată pentru stocarea datelor
│   ├── converted_2d/        # Cadrele 2D extrase în urma decodificării volumelor .nii
│   └── processed_2d/        # Seturile de date salvate definitiv după aplicarea filtrelor
│
└── requirements.txt         # Dependențele și bibliotecile externe necesare

---

## ⚙️ Instalare și Configurare

### 1. Clonarea repository-ului
git clone <url-repository>
cd Licenta-Morfologie

### 2. Instalarea dependențelor
Asigurați-vă că aveți un mediu virtual activat, apoi rulați:
pip install -r requirements.txt

*Notă: Fișierul requirements.txt trebuie să conțină cel puțin:*
customtkinter
opencv-python
pillow
nibabel

### 3. Lansarea aplicației
python main.py

---

## 📖 Ghid de Utilizare Academică

### Modul Pipeline Volumetric 3D (Recomandat pentru Volume RMN)
1. Selectați tab-ul **Pipeline Volumetric 3D** din meniul lateral stâng.
2. Apăsați **Conversie Nouă (.nii)** și selectați un volum medical de pe disc.
3. Introduceți un identificator unic pentru setul de date. Aplicația va decodifica volumul și va inițializa slider-ul de navigare axială.
4. Ajustați **Setările de Procesare** (Tipul operatorului și dimensiunea kernelului).
5. Apăsați **PREVIZUALIZEAZĂ LOT** pentru a executa procesarea în cache-ul RAM.
6. Navigați prin felii folosind slider-ul inferior pentru a valida vizual rezultatul preprocesării.
7. Dacă rezultatul este optim, apăsați **SALVEAZĂ LOTUL** pentru a scrie rezultatele pe disc.

---

## 🧑‍💻 Autor
* **Alex-Mario Pop** – Student, Facultatea de Matematică și Informatică, Universitatea de Vest din Timișoara (UVT).
* Proiect dezvoltat ca aplicație practică în cadrul lucrării de licență axată pe preprocesarea și morfologia matematică aplicată pe imagini medicale.