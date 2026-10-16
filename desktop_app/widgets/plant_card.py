"""
Plant DNA Identification System — Collapsible Plant Result Card Widget
========================================================================
Interactive card component displaying plant thumbnail, taxonomy badges,
botanical details grid, and embedded BLAST alignment viewer panels.
"""

import os
import shutil
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
    QFrame, QPushButton, QSizePolicy, QFileDialog, QMessageBox, QDialog
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPixmap, QPainter, QPainterPath

from database import get_field_value
from widgets.alignment_viewer import AlignmentViewerWidget
from report_generator import generate_plant_lab_report


class ClickableThumbnail(QLabel):
    clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setToolTip("Click to view full photograph")

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)


class ImagePreviewDialog(QDialog):
    def __init__(self, image_path: str, sci_name: str, common_name: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"{sci_name} — High-Resolution Specimen Photograph")
        self.image_path = image_path
        self.sci_name = sci_name
        self.resize(760, 640)
        self.setStyleSheet("""
            QDialog {
                background-color: #090d12;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)

        # Header bar
        header = QHBoxLayout()
        title_box = QVBoxLayout()
        title_box.setSpacing(2)

        t_lbl = QLabel(f"<em>{sci_name}</em>")
        t_lbl.setStyleSheet("color: #ffffff; font-size: 19px; font-weight: 700;")
        title_box.addWidget(t_lbl)

        if common_name and common_name != 'N/A':
            s_lbl = QLabel(f"🌿 {common_name}")
            s_lbl.setStyleSheet("color: #8b949e; font-size: 13px; font-weight: 500;")
            title_box.addWidget(s_lbl)

        header.addLayout(title_box)
        header.addStretch()

        close_icon_btn = QPushButton("✕")
        close_icon_btn.setFixedSize(32, 32)
        close_icon_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_icon_btn.setStyleSheet("""
            QPushButton {
                background-color: #161b22;
                color: #8b949e;
                border: 1px solid #30363d;
                border-radius: 16px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #21262d;
                color: #ffffff;
                border-color: #58a6ff;
            }
        """)
        close_icon_btn.clicked.connect(self.accept)
        header.addWidget(close_icon_btn)
        layout.addLayout(header)

        # Main image container
        img_frame = QFrame()
        img_frame.setStyleSheet("""
            background-color: #0d1117;
            border: 1px solid #30363d;
            border-radius: 18px;
        """)
        img_layout = QVBoxLayout(img_frame)
        img_layout.setContentsMargins(16, 16, 16, 16)
        img_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        img_label = QLabel()
        img_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        pixmap = QPixmap(image_path)
        if not pixmap.isNull():
            scaled = pixmap.scaled(700, 500, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            img_label.setPixmap(scaled)
        else:
            img_label.setText("Unable to load full resolution photograph.")
            img_label.setStyleSheet("color: #8b949e; font-size: 14px;")

        img_layout.addWidget(img_label)
        layout.addWidget(img_frame, stretch=1)

        # Bottom Action Bar
        bottom_bar = QHBoxLayout()
        bottom_bar.setSpacing(12)

        file_info = QLabel(f"📁 {os.path.basename(image_path)}")
        file_info.setStyleSheet("color: #6e7681; font-size: 12px; font-family: monospace;")
        bottom_bar.addWidget(file_info)

        bottom_bar.addStretch()

        save_btn = QPushButton("💾 Save Image As...")
        save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        save_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #0a84ff, stop:1 #0071e3);
                border: 1px solid rgba(255, 255, 255, 0.15);
                color: #ffffff;
                font-weight: 600;
                border-radius: 12px;
                padding: 8px 18px;
                font-size: 12px;
            }
            QPushButton:hover {
                background: #2997ff;
            }
        """)
        save_btn.clicked.connect(self._save_image)
        bottom_bar.addWidget(save_btn)

        close_btn = QPushButton("Close")
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #21262d;
                border: 1px solid #30363d;
                color: #c9d1d9;
                font-weight: 500;
                border-radius: 12px;
                padding: 8px 20px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #30363d;
                color: #ffffff;
            }
        """)
        close_btn.clicked.connect(self.accept)
        bottom_bar.addWidget(close_btn)

        layout.addLayout(bottom_bar)

    def _save_image(self):
        ext = os.path.splitext(self.image_path)[1] or ".jpg"
        clean_name = "".join(c for c in self.sci_name if c.isalnum() or c in (' ', '_')).strip().replace(' ', '_')
        save_path, _ = QFileDialog.getSaveFileName(
            self, "Save Photograph", f"{clean_name}{ext}", f"Images (*{ext});;All Files (*)"
        )
        if save_path:
            try:
                shutil.copyfile(self.image_path, save_path)
                QMessageBox.information(self, "Image Saved", f"Photograph saved successfully to:\n{save_path}")
            except Exception as e:
                QMessageBox.critical(self, "Save Failed", f"Could not save photograph:\n{e}")


class PlantCardWidget(QFrame):
    def __init__(self, row: dict, index: int, images_dir: str = "", parent=None):
        super().__init__(parent)
        self.setObjectName("plantCardItem")
        self.row = row
        self.images_dir = images_dir
        self.is_expanded = False
        self.matched_image_path = None

        self._build_ui()

    def _build_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ── Header Row ──
        self.header_frame = QFrame()
        self.header_frame.setObjectName("plantCardHeader")
        header_layout = QHBoxLayout(self.header_frame)
        header_layout.setContentsMargins(16, 14, 16, 14)
        header_layout.setSpacing(16)

        # Thumbnail Image
        thumb_lbl = self._create_thumbnail()
        header_layout.addWidget(thumb_lbl)

        # Info Box (Title + Subtitle + Badges)
        info_layout = QVBoxLayout()
        info_layout.setSpacing(4)

        sci_name = get_field_value(self.row, ['Scientific Name', 'name', 'ශාකයේ නම']) or 'Unknown Plant'
        common_name = get_field_value(self.row, ['Common Name', 'common name', 'local name', 'පොදු නම']) or 'N/A'
        family = get_field_value(self.row, ['Family', 'family', 'කුලය']) or 'N/A'
        plant_type = get_field_value(self.row, ['Plant Type / Growth Form', 'Plant Type', 'type']) or 'N/A'
        identity_val = get_field_value(self.row, ['Identity Percentage', 'identity']) or ''

        title_lbl = QLabel(f"<em>{sci_name}</em>")
        title_lbl.setObjectName("plantTitle")
        info_layout.addWidget(title_lbl)

        if common_name != 'N/A':
            sub_lbl = QLabel(f"🌿 {common_name}")
            sub_lbl.setObjectName("plantSubtitle")
            info_layout.addWidget(sub_lbl)

        # Badges Row
        badge_layout = QHBoxLayout()
        badge_layout.setSpacing(8)

        # Plant Type Badge
        if plant_type != 'N/A':
            type_b = QLabel(f"🌱 {plant_type}")
            type_b.setStyleSheet("background-color:#1c2438; color:#79c0ff; border:1px solid rgba(121, 192, 255, 0.25); border-radius:10px; padding:3px 10px; font-size:11px; font-weight:600;")
            badge_layout.addWidget(type_b)

        # Family Badge
        if family != 'N/A':
            fam_b = QLabel(f"🗂️ {family}")
            fam_b.setStyleSheet("background-color:#261b3d; color:#d2a8ff; border:1px solid rgba(210, 168, 255, 0.25); border-radius:10px; padding:3px 10px; font-size:11px; font-weight:600;")
            badge_layout.addWidget(fam_b)

        # Identity or Taxonomic Match Badge
        has_dna_alignment = self.row.get('_has_dna_alignment', False)
        if has_dna_alignment:
            identity_num = self.row.get('_identity_num', 0.0)
            bg = "#0c2d48" if identity_num >= 90 else "#341a00" if identity_num >= 70 else "#3c1618"
            fg = "#79c0ff" if identity_num >= 90 else "#f0883e" if identity_num >= 70 else "#ff7b72"
            bd = "#0a84ff" if identity_num >= 90 else "#d29922" if identity_num >= 70 else "#f85149"

            id_b = QLabel(f"🎯 Identity: {identity_num:.1f}%")
            id_b.setStyleSheet(f"background-color:{bg}; color:{fg}; border:1px solid {bd}; border-radius:10px; padding:3px 11px; font-size:11px; font-weight:700;")
            badge_layout.addWidget(id_b)
        else:
            tax_b = QLabel("🔍 Taxonomic Match")
            tax_b.setStyleSheet("background-color:#161f30; color:#58a6ff; border:1px solid rgba(88, 166, 255, 0.25); border-radius:10px; padding:3px 10px; font-size:11px; font-weight:600;")
            badge_layout.addWidget(tax_b)

        badge_layout.addStretch()
        info_layout.addLayout(badge_layout)
        header_layout.addLayout(info_layout, stretch=1)

        # Buttons layout
        btn_box = QHBoxLayout()
        btn_box.setSpacing(8)

        # PDF Report Button (Apple Electric Blue)
        self.btn_pdf = QPushButton("📄 PDF Report")
        self.btn_pdf.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_pdf.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #0a84ff, stop:1 #0071e3);
                border: 1px solid rgba(255, 255, 255, 0.15);
                color: #ffffff;
                font-weight: 600;
                font-size: 12px;
                border-radius: 12px;
                padding: 7px 15px;
            }
            QPushButton:hover {
                background: #2997ff;
            }
            QPushButton:pressed {
                background: #0056b3;
            }
        """)
        self.btn_pdf.clicked.connect(self.export_pdf)
        btn_box.addWidget(self.btn_pdf)

        # Expand/Collapse Toggle Button (Apple Frosted Glass)
        self.toggle_btn = QPushButton("Details ▾")
        self.toggle_btn.setFixedWidth(100)
        self.toggle_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.toggle_btn.setStyleSheet("""
            QPushButton {
                background-color: #21262d;
                border: 1px solid #30363d;
                color: #c9d1d9;
                font-weight: 500;
                font-size: 12px;
                border-radius: 12px;
                padding: 7px 14px;
            }
            QPushButton:hover {
                background-color: #30363d;
                color: #ffffff;
            }
        """)
        self.toggle_btn.clicked.connect(self.toggle_expand)
        btn_box.addWidget(self.toggle_btn)

        header_layout.addLayout(btn_box)

        main_layout.addWidget(self.header_frame)

        # ── Collapsible Body ──
        self.body_frame = QFrame()
        self.body_frame.setStyleSheet("background-color:#0d1117; border: 1px solid #30363d; border-top: none; border-bottom-left-radius:18px; border-bottom-right-radius:18px; padding:18px;")
        body_layout = QVBoxLayout(self.body_frame)
        body_layout.setContentsMargins(16, 16, 16, 16)
        body_layout.setSpacing(16)

        # Details Grid
        grid_layout = QGridLayout()
        grid_layout.setSpacing(12)

        fields = [
            ("Scientific Name", sci_name, False),
            ("Common Name", common_name, False),
            ("Family", family, False),
            ("Species", get_field_value(self.row, ['Species', 'species', 'විශේෂය']) or 'N/A', False),
            ("Plant Type", plant_type, False),
            ("Distribution", get_field_value(self.row, ['Distribution', 'distribution', 'ව්‍යාප්තිය']) or 'N/A', False),
            ("Habitat", get_field_value(self.row, ['Habitat', 'habitat', 'වාසස්ථාන']) or 'N/A', False),
            ("Uses", get_field_value(self.row, ['Uses', 'uses', 'වාණිජ']) or 'N/A', False),
            ("Plant Description", get_field_value(self.row, ['Plant Description', 'description', 'විස්තර']) or 'N/A', True),
            ("Morphological Features", get_field_value(self.row, ['Morphological Features', 'morphology']) or 'N/A', True),
            ("Climate & Soil", get_field_value(self.row, ['Climate & Soil Requirements', 'climate & soil']) or 'N/A', True),
            ("Traditional Uses (SL)", get_field_value(self.row, ['Traditional Uses (Sri Lanka)', 'traditional uses']) or 'N/A', False),
            ("Key Phytochemicals", get_field_value(self.row, ['Key Phytochemicals', 'phytochemicals']) or 'N/A', True),
        ]

        row_idx = 0
        col_idx = 0
        for title, value, is_full_width in fields:
            box = self._create_detail_box(title, value)
            if is_full_width:
                if col_idx == 1:
                    row_idx += 1
                    col_idx = 0
                grid_layout.addWidget(box, row_idx, 0, 1, 2)
                row_idx += 1
                col_idx = 0
            else:
                grid_layout.addWidget(box, row_idx, col_idx, 1, 1)
                col_idx += 1
                if col_idx >= 2:
                    col_idx = 0
                    row_idx += 1

        body_layout.addLayout(grid_layout)

        # Embed Alignment Viewers if available
        alignments = self.row.get('_alignments', [])
        if alignments:
            align_section_title = QLabel("🔬 Sequence Alignments (BLAST Viewer)")
            align_section_title.setStyleSheet("color:#58a6ff; font-size:14px; font-weight:700; margin-top:10px;")
            body_layout.addWidget(align_section_title)

            for a_data in alignments:
                viewer = AlignmentViewerWidget(a_data)
                body_layout.addWidget(viewer)

        main_layout.addWidget(self.body_frame)

        # Hidden by default
        self.body_frame.setVisible(False)

    def _create_thumbnail(self) -> QLabel:
        thumb_lbl = ClickableThumbnail()
        thumb_lbl.setFixedSize(64, 64)
        thumb_lbl.setStyleSheet("""
            QLabel {
                background-color: #161b22;
                border: 1px solid #30363d;
                border-radius: 14px;
            }
            QLabel:hover {
                border: 1.5px solid #0a84ff;
                background-color: #21262d;
            }
        """)
        thumb_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        thumb_lbl.clicked.connect(self._open_image_viewer)

        # Attempt to load local image
        raw_img = get_field_value(self.row, ['Plant Images', 'image', 'photo']) or ''
        sci_name = get_field_value(self.row, ['Scientific Name', 'name']) or ''

        img_path = None
        candidates = []
        if raw_img and os.path.isabs(raw_img) and os.path.isfile(raw_img):
            img_path = raw_img
        elif raw_img and self.images_dir and os.path.isfile(os.path.join(self.images_dir, os.path.basename(raw_img))):
            img_path = os.path.join(self.images_dir, os.path.basename(raw_img))
        elif sci_name and self.images_dir:
            # Check sanitized names like messua_ferrea.jpg or Mesua ferrea.jpg
            candidates = [
                os.path.join(self.images_dir, f"{sci_name}.jpg"),
                os.path.join(self.images_dir, f"{sci_name.lower().replace(' ', '_')}.jpg"),
                os.path.join(self.images_dir, f"{sci_name.lower().replace(' ', '')}.jpg"),
                os.path.join(self.images_dir, "messua_ferrea.jpg") if "mesua" in sci_name.lower() else None
            ]
            for c in candidates:
                if c and os.path.isfile(c):
                    img_path = c
                    break

        self.matched_image_path = img_path

        if img_path and os.path.isfile(img_path):
            pixmap = QPixmap(img_path)
            if not pixmap.isNull():
                scaled = pixmap.scaled(64, 64, Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation)
                # Crop to rounded square
                cropped = scaled.copy((scaled.width() - 64) // 2, (scaled.height() - 64) // 2, 64, 64)
                thumb_lbl.setPixmap(cropped)
                return thumb_lbl

        # Fallback leaf icon
        thumb_lbl.setText("🌿")
        thumb_lbl.setToolTip("No photographic image available")
        return thumb_lbl

    def _create_detail_box(self, title: str, value: str) -> QFrame:
        box = QFrame()
        box.setObjectName("detailBox")
        box_layout = QVBoxLayout(box)
        box_layout.setContentsMargins(12, 10, 12, 10)
        box_layout.setSpacing(4)

        t_lbl = QLabel(title)
        t_lbl.setObjectName("detailBoxTitle")
        box_layout.addWidget(t_lbl)

        v_lbl = QLabel(value)
        v_lbl.setObjectName("detailBoxValue")
        v_lbl.setWordWrap(True)
        box_layout.addWidget(v_lbl)

        return box

    def toggle_expand(self):
        self.is_expanded = not self.is_expanded
        self.body_frame.setVisible(self.is_expanded)
        self.toggle_btn.setText("Details ▴" if self.is_expanded else "Details ▾")
        if self.is_expanded:
            self.toggle_btn.setStyleSheet("background-color:#0a84ff; color:#ffffff; font-weight:600; border:none; border-radius:12px; padding:7px 14px;")
        else:
            self.toggle_btn.setStyleSheet("""
                QPushButton {
                    background-color: #21262d;
                    border: 1px solid #30363d;
                    color: #c9d1d9;
                    font-weight: 500;
                    font-size: 12px;
                    border-radius: 12px;
                    padding: 7px 14px;
                }
                QPushButton:hover {
                    background-color: #30363d;
                    color: #ffffff;
                }
            """)

    def export_pdf(self):
        sci_name = get_field_value(self.row, ['Scientific Name', 'name']) or 'Plant'
        safe_name = "".join(c for c in sci_name if c.isalnum() or c in (' ', '_')).strip().replace(' ', '_')
        default_filename = f"Lab_Report_{safe_name}.pdf"

        file_path, _ = QFileDialog.getSaveFileName(
            self, f"Save PDF Lab Report for {sci_name}", default_filename, "PDF Files (*.pdf)"
        )
        if not file_path:
            return

        try:
            generate_plant_lab_report(self.row, file_path, self.images_dir)
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Icon.Information)
            msg.setWindowTitle("Lab Report Generated")
            msg.setText(f"Professional Lab Report PDF successfully generated!\n\nFile: {os.path.basename(file_path)}")
            open_btn = msg.addButton("Open PDF", QMessageBox.ButtonRole.ActionRole)
            msg.addButton(QMessageBox.StandardButton.Ok)
            msg.exec()

            if msg.clickedButton() == open_btn:
                os.startfile(file_path)
        except Exception as e:
            QMessageBox.critical(self, "Export Failed", f"Could not generate PDF report:\n{e}")

    def _open_image_viewer(self):
        sci_name = get_field_value(self.row, ['Scientific Name', 'name', 'ශාකයේ නම']) or 'Plant Specimen'
        common_name = get_field_value(self.row, ['Common Name', 'local name', 'පොදු නම']) or ''
        if self.matched_image_path and os.path.isfile(self.matched_image_path):
            dlg = ImagePreviewDialog(self.matched_image_path, sci_name, common_name, self)
            dlg.exec()
        else:
            QMessageBox.information(
                self, "No Photo Available",
                f"No high-resolution photographic image is available for {sci_name} in the database."
            )

