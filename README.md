# Morphological Image Processing Application 🔬

**Status: Work in Progress (Bachelor's Thesis)** An advanced image processing desktop application focused on mathematical morphology, specifically designed for medical imaging (NIfTI) and document restoration.

## 🚀 Key Features
- **Morphological Operations:** Implementation of Erosion, Dilation, Opening, Closing, and Top-Hat transforms using OpenCV.
- **Medical Data Handling:** Specialized pipeline for processing 3D NIfTI volumetric data and converting it to 2D slices.
- **Modern UI:** Built with `CustomTkinter` featuring a real-time split-view for "Before & After" comparisons.
- **MVC Architecture:** Clean separation between image processing logic and the graphical interface.

## 🛠️ Tech Stack
- **Language:** Python 3.x
- **Libraries:** OpenCV, NumPy, CustomTkinter, NiBabel (for NIfTI files)

## 📂 Project Structure
- `/core`: Mathematical morphology algorithms.
- `/gui`: CustomTkinter interface components.
- `/utils`: Data conversion and file handling utilities.

## 📝 Future Updates
- [ ] Adaptive thresholding for low-contrast medical scans.
- [ ] Batch processing for large datasets.
