# Plant DNA Identification System — Desktop Application (PyQt6)
**Ruhuna BST • Advanced Bioinformatics**

A pure Python standalone desktop application featuring biological sequence alignment, multi-marker plant barcode matching, statistical E-value estimation, and a modern dark-emerald glassmorphic user interface.

---

## 🌿 Features

1. **Pure Python & Zero WebViews**:
   - Built natively with **PyQt6**.
   - Custom QSS glassmorphic dark theme (`#0b1411` background with `#10b981` mint accents).
2. **Bioinformatics Alignment Engine (`algorithms.py`)**:
   - **Needleman-Wunsch** Global Alignment.
   - **Smith-Waterman** Local Alignment (automatic fallback for partial Sanger reads and fragments).
   - **Dual-strand comparison** (Forward and Reverse Complement with IUPAC degenerate code support).
   - **Karlin-Altschul E-value calculation** for statistical hit significance.
   - Multi-marker weighted scoring:
     - `rbcL` (Weight: 40%)
     - `matK` (Weight: 40%)
     - `ITS` (Weight: 20%)
3. **Interactive Results Visualizer**:
   - **Detailed Card View**: Expandable/collapsible cards with plant thumbnail, scientific classification, 13 botanical fields, and embedded **BLAST-style Alignment Viewer** (color-coded matches, mismatches, gaps, coordinates, and identity progress bars).
   - **Table View**: Comprehensive data grid displaying all 37 database columns.
   - **Export to CSV**: Export matched hits directly to a new spreadsheet.
4. **Non-blocking Multi-threaded Engine**:
   - Computations run on a background `QThread` to ensure smooth UI responsiveness.

---

## 🚀 How to Run

### Option 1: 1-Click Batch Launcher
Double-click `run_desktop_app.bat` in the project root, or `run_app.bat` inside `desktop_app/`.

### Option 2: Command Line
```bash
cd desktop_app
python main.py
```

---

## 📦 Building Standalone `.exe`

To package this application into a standalone Windows `.exe` that runs without requiring Python:
1. Double-click `desktop_app/build_exe.bat`, OR
2. Run:
```bash
pip install pyinstaller
pyinstaller --noconfirm --onedir --windowed --add-data "Cleaned_Plant_DNA_Barcoding_Data.csv;." --add-data "images;images" --name "Plant_DNA_Identification_System" main.py
```
The compiled executable will be generated inside `desktop_app/dist/Plant_DNA_Identification_System/`.
