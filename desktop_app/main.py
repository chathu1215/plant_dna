"""
Plant DNA Identification System — Desktop Application
========================================================
Main application entry point built with PyQt6.
Features multi-threaded DNA alignment, dual-mode results visualizer
(Detailed cards with BLAST viewer + Table grid), dynamic database loading,
and custom dark-emerald glassmorphic UI.
"""

import os
import sys
import csv
from typing import Dict, Any, List

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QGridLayout, QLabel, QLineEdit, QComboBox, QPushButton,
    QScrollArea, QFrame, QTableWidget, QTableWidgetItem, QHeaderView,
    QFileDialog, QMessageBox, QProgressBar, QStackedWidget
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QIcon, QFont, QColor

from algorithms import extract_dna_sequence
from database import load_database, search_database, get_field_value
from styles import MODERN_QSS
from widgets.plant_card import PlantCardWidget
from widgets.photo_gallery import PlantPhotoGalleryWidget
from report_generator import generate_plant_lab_report


CARDS_PER_PAGE = 5


class SearchWorker(QThread):
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, database, sci_name, rbcl, matk, its, threshold):
        super().__init__()
        self.database = database
        self.sci_name = sci_name
        self.rbcl = rbcl
        self.matk = matk
        self.its = its
        self.threshold = threshold

    def run(self):
        try:
            results = search_database(
                self.database,
                scientific_name=self.sci_name,
                rbcl_seq=self.rbcl,
                matk_seq=self.matk,
                its_seq=self.its,
                threshold=self.threshold
            )
            self.finished.emit(results)
        except Exception as e:
            self.error.emit(str(e))


class PlantDnaApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Plant DNA Identification System — Ruhuna BST")
        self.resize(1240, 880)
        self.setMinimumSize(1000, 720)

        # Paths
        base_dir = os.path.dirname(os.path.abspath(__file__))
        parent_dir = os.path.dirname(base_dir)

        # Look for CSV in parent directory first, then base_dir
        self.csv_path = os.path.join(parent_dir, "Cleaned_Plant_DNA_Barcoding_Data.csv")
        if not os.path.isfile(self.csv_path):
            self.csv_path = os.path.join(base_dir, "Cleaned_Plant_DNA_Barcoding_Data.csv")

        # Images directory
        self.images_dir = os.path.join(parent_dir, "images")
        if not os.path.isdir(self.images_dir):
            self.images_dir = os.path.join(base_dir, "images")

        self.database: List[Dict[str, str]] = []
        self.current_results: List[Dict[str, Any]] = []
        self.rendered_card_count = 0
        self.current_view = "detailed"
        self.worker = None

        self._init_ui()
        self._load_csv_database()

    def _init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        root_layout = QVBoxLayout(central_widget)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # ── 1. Top Navbar Header ──
        root_layout.addWidget(self._create_header())

        # ── 2. Stacked Content Pages ──
        self.stack = QStackedWidget()

        # Page 0: DNA Search & Analysis View
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setObjectName("mainScroll")

        content_widget = QWidget()
        self.content_layout = QVBoxLayout(content_widget)
        self.content_layout.setContentsMargins(36, 28, 36, 36)
        self.content_layout.setSpacing(24)

        # Search Panel Card
        self.content_layout.addWidget(self._create_search_card())

        # Results Container Card
        self.results_card = self._create_results_card()
        self.content_layout.addWidget(self.results_card)
        self.results_card.setVisible(False)

        # Bottom stretch to prevent vertical stretching
        self.content_layout.addStretch()

        scroll.setWidget(content_widget)
        self.stack.addWidget(scroll)

        # Page 1: Plant Photo Gallery View
        self.gallery_widget = PlantPhotoGalleryWidget(self.database, self.images_dir)
        self.stack.addWidget(self.gallery_widget)

        root_layout.addWidget(self.stack)

    def _create_header(self) -> QFrame:
        header = QFrame()
        header.setObjectName("headerFrame")
        layout = QHBoxLayout(header)
        layout.setContentsMargins(24, 12, 24, 12)
        layout.setSpacing(16)

        # Logo Icon (Apple Squircle)
        logo_lbl = QLabel("🌿")
        logo_lbl.setStyleSheet("""
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #0a84ff, stop:1 #0071e3);
            color: #ffffff;
            font-size: 22px;
            border: 1px solid rgba(255, 255, 255, 0.2);
            border-radius: 14px;
            padding: 8px 12px;
        """)
        layout.addWidget(logo_lbl)

        # Brand Text
        brand_vbox = QVBoxLayout()
        brand_vbox.setSpacing(2)
        title_lbl = QLabel("Plant DNA Identification System")
        title_lbl.setObjectName("brandTitle")
        sub_lbl = QLabel("RUHUNA BST • ADVANCED BIOINFORMATICS")
        sub_lbl.setObjectName("brandSubtitle")
        brand_vbox.addWidget(title_lbl)
        brand_vbox.addWidget(sub_lbl)
        layout.addLayout(brand_vbox)

        layout.addSpacing(16)

        # ── Navigation Tabs (Apple Segmented Style) ──
        nav_box = QFrame()
        nav_box.setObjectName("segmentedContainer")
        nav_layout = QHBoxLayout(nav_box)
        nav_layout.setContentsMargins(4, 4, 4, 4)
        nav_layout.setSpacing(4)

        self.btn_nav_dna = QPushButton("🧬 DNA Search & Analysis")
        self.btn_nav_dna.setObjectName("toggleBtnActive")
        self.btn_nav_dna.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_nav_dna.clicked.connect(lambda: self._switch_main_tab(0))
        nav_layout.addWidget(self.btn_nav_dna)

        self.btn_nav_gallery = QPushButton("🖼️ Photo Gallery")
        self.btn_nav_gallery.setObjectName("toggleBtnInactive")
        self.btn_nav_gallery.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_nav_gallery.clicked.connect(lambda: self._switch_main_tab(1))
        nav_layout.addWidget(self.btn_nav_gallery)

        layout.addWidget(nav_box)

        layout.addStretch()

        # Compact Database Status Badge (Integrated in Header)
        db_badge = QFrame()
        db_badge.setStyleSheet("""
            background-color: #161b22;
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 12px;
            padding: 4px 12px;
        """)
        db_layout = QHBoxLayout(db_badge)
        db_layout.setContentsMargins(8, 4, 8, 4)
        db_layout.setSpacing(8)

        self.db_status_dot = QLabel("●")
        self.db_status_dot.setStyleSheet("color:#0a84ff; font-size:12px;")
        db_layout.addWidget(self.db_status_dot)

        self.db_status_lbl = QLabel("Loading database...")
        self.db_status_lbl.setStyleSheet("color:#8b949e; font-size:12px; font-weight:500;")
        db_layout.addWidget(self.db_status_lbl)

        layout.addWidget(db_badge)

        # Header Actions
        btn_open_db = QPushButton("📁 Load CSV Database")
        btn_open_db.setObjectName("btnSecondary")
        btn_open_db.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_open_db.clicked.connect(self._browse_csv)
        layout.addWidget(btn_open_db)

        return header

    def _switch_main_tab(self, index: int):
        self.stack.setCurrentIndex(index)
        if index == 0:
            self.btn_nav_dna.setObjectName("toggleBtnActive")
            self.btn_nav_gallery.setObjectName("toggleBtnInactive")
        else:
            self.btn_nav_dna.setObjectName("toggleBtnInactive")
            self.btn_nav_gallery.setObjectName("toggleBtnActive")

        self.btn_nav_dna.setStyle(self.btn_nav_dna.style())
        self.btn_nav_gallery.setStyle(self.btn_nav_gallery.style())

    def _create_search_card(self) -> QFrame:
        card = QFrame()
        card.setObjectName("cardFrame")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(28, 24, 28, 26)
        layout.setSpacing(20)

        # Card Title
        header_vbox = QVBoxLayout()
        header_vbox.setSpacing(4)
        c_title = QLabel("🔬 Search Plant Database")
        c_title.setObjectName("cardTitle")
        c_sub = QLabel("Query by Scientific Name or DNA Sequences (rbcL / matK / ITS)")
        c_sub.setObjectName("cardSubtitle")
        header_vbox.addWidget(c_title)
        header_vbox.addWidget(c_sub)
        layout.addLayout(header_vbox)

        # Inputs Grid
        grid = QGridLayout()
        grid.setSpacing(16)

        # Scientific Name
        lbl_sci = QLabel("Scientific Name:")
        lbl_sci.setStyleSheet("font-weight:600; color:#58a6ff; font-size:12px;")
        self.input_sci = QLineEdit()
        self.input_sci.setPlaceholderText("e.g. Mesua ferrea, Cocos nucifera...")
        grid.addWidget(lbl_sci, 0, 0)
        grid.addWidget(self.input_sci, 1, 0)

        # rbcL Sequence
        lbl_rbcl = QLabel("rbcL Sequence:")
        lbl_rbcl.setStyleSheet("font-weight:600; color:#58a6ff; font-size:12px;")
        self.input_rbcl = QLineEdit()
        self.input_rbcl.setPlaceholderText("Paste rbcL FASTA or nucleotide sequence...")
        grid.addWidget(lbl_rbcl, 0, 1)
        grid.addWidget(self.input_rbcl, 1, 1)

        # matK Sequence
        lbl_matk = QLabel("matK Sequence:")
        lbl_matk.setStyleSheet("font-weight:600; color:#58a6ff; font-size:12px;")
        self.input_matk = QLineEdit()
        self.input_matk.setPlaceholderText("Paste matK FASTA or nucleotide sequence...")
        grid.addWidget(lbl_matk, 2, 0)
        grid.addWidget(self.input_matk, 3, 0)

        # ITS Sequence
        lbl_its = QLabel("ITS Sequence:")
        lbl_its.setStyleSheet("font-weight:600; color:#58a6ff; font-size:12px;")
        self.input_its = QLineEdit()
        self.input_its.setPlaceholderText("Paste ITS FASTA or nucleotide sequence...")
        grid.addWidget(lbl_its, 2, 1)
        grid.addWidget(self.input_its, 3, 1)

        layout.addLayout(grid)

        # Options Row: Identity Cutoff Dropdown + Analyze Button
        options_row = QHBoxLayout()
        options_row.setSpacing(16)

        v_cutoff = QVBoxLayout()
        v_cutoff.setSpacing(4)
        lbl_cutoff = QLabel("Minimum Identity Cutoff:")
        lbl_cutoff.setStyleSheet("font-weight:700; color:#94a3b8; font-size:12px;")
        self.combo_threshold = QComboBox()
        self.combo_threshold.addItem("70% (Default Filter)", 70.0)
        self.combo_threshold.addItem("90% (Strict Match)", 90.0)
        self.combo_threshold.addItem("50% (Lenient Match)", 50.0)
        self.combo_threshold.addItem("0% (Show All Results)", 0.0)
        v_cutoff.addWidget(lbl_cutoff)
        v_cutoff.addWidget(self.combo_threshold)
        options_row.addLayout(v_cutoff, stretch=1)

        # Action Buttons
        v_btns = QVBoxLayout()
        v_btns.setSpacing(4)
        v_btns.addWidget(QLabel(""))  # Spacer

        btn_box = QHBoxLayout()
        btn_box.setSpacing(12)

        self.btn_analyze = QPushButton("⚡ Analyze & Match DNA")
        self.btn_analyze.setObjectName("btnPrimary")
        self.btn_analyze.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_analyze.clicked.connect(self.perform_search)
        btn_box.addWidget(self.btn_analyze)

        self.btn_clear = QPushButton("🧹 Clear")
        self.btn_clear.setObjectName("btnSecondary")
        self.btn_clear.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_clear.clicked.connect(self.clear_inputs)
        btn_box.addWidget(self.btn_clear)

        v_btns.addLayout(btn_box)
        options_row.addLayout(v_btns, stretch=1)

        layout.addLayout(options_row)

        # Progress Indicator (Hidden by default)
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)  # Indeterminate pulse
        self.progress_bar.setFixedHeight(8)
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        self.search_status_lbl = QLabel("")
        self.search_status_lbl.setStyleSheet("color:#58a6ff; font-size:12px; font-weight:600; text-align:center;")
        self.search_status_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.search_status_lbl.setVisible(False)
        layout.addWidget(self.search_status_lbl)

        return card

    def _create_results_card(self) -> QFrame:
        card = QFrame()
        card.setObjectName("cardFrame")
        self.results_vbox = QVBoxLayout(card)
        self.results_vbox.setContentsMargins(28, 24, 28, 28)
        self.results_vbox.setSpacing(20)

        # Results Header + View Switcher
        top_bar = QHBoxLayout()
        top_bar.setSpacing(14)

        self.results_title = QLabel("Matching Results")
        self.results_title.setObjectName("cardTitle")
        top_bar.addWidget(self.results_title)

        top_bar.addStretch()

        # View Switcher Buttons
        self.btn_detailed_view = QPushButton("🪪 Detailed View")
        self.btn_detailed_view.setObjectName("toggleBtnActive")
        self.btn_detailed_view.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_detailed_view.clicked.connect(lambda: self.switch_view("detailed"))
        top_bar.addWidget(self.btn_detailed_view)

        self.btn_table_view = QPushButton("📊 Table View")
        self.btn_table_view.setObjectName("toggleBtnInactive")
        self.btn_table_view.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_table_view.clicked.connect(lambda: self.switch_view("table"))
        top_bar.addWidget(self.btn_table_view)

        # Export CSV Button
        btn_export = QPushButton("💾 Export CSV")
        btn_export.setObjectName("btnSecondary")
        btn_export.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_export.clicked.connect(self._export_results_csv)
        top_bar.addWidget(btn_export)

        # Export Top Hit PDF Lab Report Button
        self.btn_export_pdf = QPushButton("📄 PDF Lab Report")
        self.btn_export_pdf.setObjectName("btnPrimary")
        self.btn_export_pdf.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_export_pdf.clicked.connect(self._export_top_hit_pdf)
        top_bar.addWidget(self.btn_export_pdf)

        self.results_vbox.addLayout(top_bar)

        # Verdict Banner Frame
        self.verdict_frame = QFrame()
        self.verdict_layout = QHBoxLayout(self.verdict_frame)
        self.verdict_layout.setContentsMargins(16, 12, 16, 12)
        self.verdict_lbl = QLabel()
        self.verdict_lbl.setWordWrap(True)
        self.verdict_lbl.setStyleSheet("font-size:14px; font-weight:700;")
        self.verdict_layout.addWidget(self.verdict_lbl)
        self.results_vbox.addWidget(self.verdict_frame)
        self.verdict_frame.setVisible(False)

        # Detailed View Container
        self.detailed_container = QWidget()
        self.cards_layout = QVBoxLayout(self.detailed_container)
        self.cards_layout.setContentsMargins(0, 0, 0, 0)
        self.cards_layout.setSpacing(16)
        self.results_vbox.addWidget(self.detailed_container)

        # Load More Button
        self.load_more_frame = QFrame()
        lm_layout = QVBoxLayout(self.load_more_frame)
        lm_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.btn_load_more = QPushButton("⬇️ Load More Results")
        self.btn_load_more.setObjectName("btnSecondary")
        self.btn_load_more.setFixedWidth(240)
        self.btn_load_more.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_load_more.clicked.connect(self._load_more_cards)
        lm_layout.addWidget(self.btn_load_more)

        self.load_more_counter = QLabel("")
        self.load_more_counter.setStyleSheet("color:#64748b; font-size:12px; font-weight:600; margin-top:4px;")
        self.load_more_counter.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lm_layout.addWidget(self.load_more_counter)

        self.results_vbox.addWidget(self.load_more_frame)
        self.load_more_frame.setVisible(False)

        # Table View Container
        self.table_widget = QTableWidget()
        self.table_widget.setMinimumHeight(450)
        self.table_widget.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.table_widget.horizontalHeader().setStretchLastSection(True)
        self.table_widget.verticalHeader().setVisible(False)
        self.results_vbox.addWidget(self.table_widget)
        self.table_widget.setVisible(False)

        return card

    def _load_csv_database(self):
        if not os.path.isfile(self.csv_path):
            self.db_status_dot.setStyleSheet("color:#ef4444; font-size:16px;")
            self.db_status_lbl.setText("Database missing. Click 'Load CSV Database' to select file.")
            return

        try:
            self.database = load_database(self.csv_path)
            self.db_status_dot.setStyleSheet("color:#0a84ff; font-size:12px;")
            filename = os.path.basename(self.csv_path)
            self.db_status_lbl.setText(f"{filename} ({len(self.database)} records)")
            if hasattr(self, 'gallery_widget'):
                self.gallery_widget.reload_database(self.database, self.images_dir)
        except Exception as e:
            self.db_status_dot.setStyleSheet("color:#ef4444; font-size:12px;")
            self.db_status_lbl.setText(f"Failed to load CSV: {e}")

    def _browse_csv(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Plant DNA Database CSV", "", "CSV Files (*.csv);;All Files (*)"
        )
        if path:
            self.csv_path = path
            self._load_csv_database()

    def perform_search(self):
        if not self.database:
            QMessageBox.warning(
                self, "Database Not Loaded",
                "Please select and load a valid CSV database file first."
            )
            return

        sci_name = self.input_sci.text().strip()
        raw_rbcl = self.input_rbcl.text().strip()
        raw_matk = self.input_matk.text().strip()
        raw_its = self.input_its.text().strip()

        # Validate & parse FASTA nucleotide sequences
        parsed_rbcl = extract_dna_sequence(raw_rbcl)
        parsed_matk = extract_dna_sequence(raw_matk)
        parsed_its = extract_dna_sequence(raw_its)

        if not parsed_rbcl["is_valid"] or not parsed_matk["is_valid"] or not parsed_its["is_valid"]:
            QMessageBox.critical(
                self, "Invalid DNA Sequence",
                "Invalid characters detected in DNA sequence!\n"
                "Only standard nucleotides (A, T, C, G, U, N) and IUPAC degenerate codes are permitted."
            )
            return

        rbcl_seq = parsed_rbcl["sequence"]
        matk_seq = parsed_matk["sequence"]
        its_seq = parsed_its["sequence"]

        if not sci_name and not rbcl_seq and not matk_seq and not its_seq:
            QMessageBox.information(
                self, "Search Criteria Required",
                "Please enter at least one search query:\n"
                "• Scientific Name\n• rbcL sequence\n• matK sequence\n• ITS sequence"
            )
            return

        threshold = self.combo_threshold.currentData()

        # Start Async Worker to keep GUI responsive
        self.btn_analyze.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.search_status_lbl.setText("Aligning DNA sequences against database records...")
        self.search_status_lbl.setVisible(True)

        self.worker = SearchWorker(
            self.database, sci_name, rbcl_seq, matk_seq, its_seq, threshold
        )
        self.worker.finished.connect(self._on_search_finished)
        self.worker.error.connect(self._on_search_error)
        self.worker.start()

    def _on_search_finished(self, results_data: dict):
        self.btn_analyze.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.search_status_lbl.setVisible(False)

        results = results_data.get("results", [])
        self.current_results = results
        self.rendered_card_count = 0

        # Show Results Card
        self.results_card.setVisible(True)
        self.results_title.setText(f"Matching Results ({len(results)} found)")

        # Display Verdict Banner
        v_type = results_data.get("verdict_type", "none")
        v_msg = results_data.get("verdict_message", "")

        if v_type == "confirmed":
            self.verdict_frame.setStyleSheet("background-color:#0c2d48; border:1.5px solid #0a84ff; border-radius:14px; padding:12px 18px;")
            self.verdict_lbl.setStyleSheet("color:#79c0ff; font-weight:600; font-size:13px;")
            self.verdict_lbl.setText(f"✅ {v_msg}")
            self.verdict_frame.setVisible(True)
        elif v_type == "probable":
            self.verdict_frame.setStyleSheet("background-color:#341a00; border:1.5px solid #d29922; border-radius:14px; padding:12px 18px;")
            self.verdict_lbl.setStyleSheet("color:#f0883e; font-weight:600; font-size:13px;")
            self.verdict_lbl.setText(f"⚠️ {v_msg}")
            self.verdict_frame.setVisible(True)
        elif v_type == "weak":
            self.verdict_frame.setStyleSheet("background-color:#3c1618; border:1.5px solid #f85149; border-radius:14px; padding:12px 18px;")
            self.verdict_lbl.setStyleSheet("color:#ff7b72; font-weight:600; font-size:13px;")
            self.verdict_lbl.setText(f"❌ {v_msg}")
            self.verdict_frame.setVisible(True)
        elif v_type == "info":
            self.verdict_frame.setStyleSheet("background-color:#161f30; border:1.5px solid #1f6feb; border-radius:14px; padding:12px 18px;")
            self.verdict_lbl.setStyleSheet("color:#79c0ff; font-weight:600; font-size:13px;")
            self.verdict_lbl.setText(f"ℹ️ {v_msg}")
            self.verdict_frame.setVisible(True)
        else:
            self.verdict_frame.setVisible(False)

        # Clear existing card widgets
        while self.cards_layout.count():
            item = self.cards_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        if not results:
            no_lbl = QLabel("No matching plant records found matching your criteria.")
            no_lbl.setStyleSheet("color:#94a3b8; font-size:14px; padding:24px; text-align:center;")
            no_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.cards_layout.addWidget(no_lbl)
            self.load_more_frame.setVisible(False)
            self._populate_table([])
            return

        # Render first batch of cards
        self._load_more_cards()

        # Populate Table
        self._populate_table(results)

    def _on_search_error(self, err_msg: str):
        self.btn_analyze.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.search_status_lbl.setVisible(False)
        QMessageBox.critical(self, "Search Error", f"An error occurred during search:\n{err_msg}")

    def _load_more_cards(self):
        total = len(self.current_results)
        next_count = min(self.rendered_card_count + CARDS_PER_PAGE, total)

        for i in range(self.rendered_card_count, next_count):
            row_data = self.current_results[i]
            card = PlantCardWidget(row_data, i, images_dir=self.images_dir)
            self.cards_layout.addWidget(card)

        self.rendered_card_count = next_count

        if self.rendered_card_count >= total:
            self.load_more_frame.setVisible(False)
        else:
            self.load_more_frame.setVisible(True)
            self.load_more_counter.setText(f"Showing {self.rendered_card_count} of {total} records")

    def _populate_table(self, results: List[Dict[str, Any]]):
        if not results:
            self.table_widget.setRowCount(0)
            self.table_widget.setColumnCount(0)
            return

        # Extract non-internal columns
        sample_row = results[0]
        headers = [k for k in sample_row.keys() if not k.startswith('_')]

        self.table_widget.setColumnCount(len(headers))
        self.table_widget.setHorizontalHeaderLabels(headers)
        self.table_widget.setRowCount(len(results))

        for row_idx, row in enumerate(results):
            for col_idx, col_name in enumerate(headers):
                val = str(row.get(col_name, ''))
                item = QTableWidgetItem(val)
                item.setFlags(item.flags() ^ Qt.ItemFlag.ItemIsEditable)  # Read-only
                self.table_widget.setItem(row_idx, col_idx, item)

        self.table_widget.resizeColumnsToContents()

    def switch_view(self, view_type: str):
        self.current_view = view_type
        if view_type == "detailed":
            self.btn_detailed_view.setObjectName("toggleBtnActive")
            self.btn_table_view.setObjectName("toggleBtnInactive")
            self.detailed_container.setVisible(True)
            self.load_more_frame.setVisible(self.rendered_card_count < len(self.current_results))
            self.table_widget.setVisible(False)
        else:
            self.btn_detailed_view.setObjectName("toggleBtnInactive")
            self.btn_table_view.setObjectName("toggleBtnActive")
            self.detailed_container.setVisible(False)
            self.load_more_frame.setVisible(False)
            self.table_widget.setVisible(True)

        self.btn_detailed_view.setStyle(self.btn_detailed_view.style())
        self.btn_table_view.setStyle(self.btn_table_view.style())

    def clear_inputs(self):
        self.input_sci.clear()
        self.input_rbcl.clear()
        self.input_matk.clear()
        self.input_its.clear()
        self.combo_threshold.setCurrentIndex(0)
        self.results_card.setVisible(False)

    def _export_results_csv(self):
        if not self.current_results:
            QMessageBox.information(self, "No Data", "There are no matching results to export.")
            return

        save_path, _ = QFileDialog.getSaveFileName(
            self, "Export Matching Results to CSV", "Plant_DNA_Search_Results.csv", "CSV Files (*.csv)"
        )
        if not save_path:
            return

        try:
            headers = [k for k in self.current_results[0].keys() if not k.startswith('_')]
            with open(save_path, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.DictWriter(f, fieldnames=headers, extrasaction='ignore')
                writer.writeheader()
                for row in self.current_results:
                    writer.writerow(row)
            QMessageBox.information(self, "Export Success", f"Successfully exported {len(self.current_results)} records to:\n{save_path}")
        except Exception as e:
            QMessageBox.critical(self, "Export Failed", f"Could not write CSV file:\n{e}")

    def _export_top_hit_pdf(self):
        if not self.current_results:
            QMessageBox.information(self, "No Results", "No plant search results available to export.")
            return

        top_hit = self.current_results[0]
        sci_name = get_field_value(top_hit, ['Scientific Name', 'name']) or 'Plant'
        safe_name = "".join(c for c in sci_name if c.isalnum() or c in (' ', '_')).strip().replace(' ', '_')
        default_filename = f"Lab_Report_{safe_name}.pdf"

        file_path, _ = QFileDialog.getSaveFileName(
            self, f"Save PDF Lab Report for {sci_name}", default_filename, "PDF Files (*.pdf)"
        )
        if not file_path:
            return

        try:
            generate_plant_lab_report(top_hit, file_path, self.images_dir)
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Icon.Information)
            msg.setWindowTitle("Lab Report Generated")
            msg.setText(f"Professional Lab Report PDF successfully generated for:\n{sci_name}\n\nFile: {os.path.basename(file_path)}")
            open_btn = msg.addButton("Open PDF", QMessageBox.ButtonRole.ActionRole)
            msg.addButton(QMessageBox.StandardButton.Ok)
            msg.exec()

            if msg.clickedButton() == open_btn:
                os.startfile(file_path)
        except Exception as e:
            QMessageBox.critical(self, "Export Failed", f"Could not generate PDF report:\n{e}")



def main():
    app = QApplication(sys.argv)
    app.setStyleSheet(MODERN_QSS)

    window = PlantDnaApp()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
