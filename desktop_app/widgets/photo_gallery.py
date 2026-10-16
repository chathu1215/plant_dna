"""
Plant DNA Identification System — Apple macOS Photo Gallery Module
====================================================================
Comprehensive Plant Photo Gallery View featuring:
- Responsive macOS-style image grid with dynamic thumbnail resizing
- Live instant search-as-you-type and taxonomic Family filter
- Interactive Slideshow / Lightbox Modal with Next (➔) and Prev (⬅) controls
- Single-click Photo Upload / Replace for any botanical specimen
- Direct high-resolution image export
"""

import os
import shutil
from typing import List, Dict, Any, Optional

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
    QFrame, QPushButton, QLineEdit, QComboBox, QSlider,
    QScrollArea, QDialog, QFileDialog, QMessageBox, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPixmap, QPainter, QPainterPath, QKeyEvent

from database import get_field_value


def resolve_plant_image(row: dict, images_dir: str) -> Optional[str]:
    """Resolves whether a plant has an existing image in the filesystem."""
    raw_img = get_field_value(row, ['Plant Images', 'image', 'photo']) or ''
    sci_name = get_field_value(row, ['Scientific Name', 'name']) or ''

    if raw_img and os.path.isabs(raw_img) and os.path.isfile(raw_img):
        return raw_img
    elif raw_img and images_dir and os.path.isfile(os.path.join(images_dir, os.path.basename(raw_img))):
        return os.path.join(images_dir, os.path.basename(raw_img))
    elif sci_name and images_dir:
        candidates = [
            os.path.join(images_dir, f"{sci_name}.jpg"),
            os.path.join(images_dir, f"{sci_name.lower().replace(' ', '_')}.jpg"),
            os.path.join(images_dir, f"{sci_name.lower().replace(' ', '')}.jpg"),
            os.path.join(images_dir, "messua_ferrea.jpg") if "mesua" in sci_name.lower() else None
        ]
        for c in candidates:
            if c and os.path.isfile(c):
                return c
    return None


class GalleryLightboxModal(QDialog):
    """Full-featured Slideshow & Lightbox Modal with Next/Prev keyboard & button controls."""
    def __init__(self, items: List[Dict[str, Any]], current_index: int, images_dir: str, parent=None):
        super().__init__(parent)
        self.items = items
        self.current_idx = current_index
        self.images_dir = images_dir
        self.resize(860, 700)
        self.setStyleSheet("background-color: #070a0e;")

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(24, 18, 24, 20)
        self.layout.setSpacing(14)

        # ── Top Bar ──
        header = QHBoxLayout()
        self.title_vbox = QVBoxLayout()
        self.title_vbox.setSpacing(2)

        self.sci_title_lbl = QLabel("")
        self.sci_title_lbl.setStyleSheet("color:#ffffff; font-size:19px; font-weight:700;")
        self.common_sub_lbl = QLabel("")
        self.common_sub_lbl.setStyleSheet("color:#8b949e; font-size:13px;")

        self.title_vbox.addWidget(self.sci_title_lbl)
        self.title_vbox.addWidget(self.common_sub_lbl)
        header.addLayout(self.title_vbox)

        header.addStretch()

        self.counter_lbl = QLabel("")
        self.counter_lbl.setStyleSheet("""
            background-color: #161b22;
            border: 1px solid #30363d;
            border-radius: 10px;
            color: #58a6ff;
            font-size: 12px;
            font-weight: 600;
            padding: 4px 12px;
        """)
        header.addWidget(self.counter_lbl)

        btn_close = QPushButton("✕")
        btn_close.setFixedSize(32, 32)
        btn_close.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_close.setStyleSheet("""
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
        btn_close.clicked.connect(self.accept)
        header.addWidget(btn_close)

        self.layout.addLayout(header)

        # ── Image Viewer Body with Left/Right Arrows ──
        body_layout = QHBoxLayout()
        body_layout.setSpacing(12)

        # Prev Button
        self.btn_prev = QPushButton("◀")
        self.btn_prev.setFixedSize(44, 44)
        self.btn_prev.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_prev.setStyleSheet(self._arrow_btn_style())
        self.btn_prev.clicked.connect(self._show_prev)
        body_layout.addWidget(self.btn_prev)

        # Display Frame
        self.img_frame = QFrame()
        self.img_frame.setStyleSheet("""
            background-color: #0d1117;
            border: 1.5px solid #30363d;
            border-radius: 20px;
        """)
        frame_layout = QVBoxLayout(self.img_frame)
        frame_layout.setContentsMargins(16, 16, 16, 16)
        frame_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.img_display_lbl = QLabel()
        self.img_display_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        frame_layout.addWidget(self.img_display_lbl)

        body_layout.addWidget(self.img_frame, stretch=1)

        # Next Button
        self.btn_next = QPushButton("▶")
        self.btn_next.setFixedSize(44, 44)
        self.btn_next.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_next.setStyleSheet(self._arrow_btn_style())
        self.btn_next.clicked.connect(self._show_next)
        body_layout.addWidget(self.btn_next)

        self.layout.addLayout(body_layout, stretch=1)

        # ── Bottom Action Bar ──
        bottom_bar = QHBoxLayout()
        self.meta_badge_lbl = QLabel("")
        self.meta_badge_lbl.setStyleSheet("color:#6e7681; font-size:12px; font-family:monospace;")
        bottom_bar.addWidget(self.meta_badge_lbl)

        bottom_bar.addStretch()

        self.btn_save = QPushButton("💾 Save Image As...")
        self.btn_save.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_save.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #0a84ff, stop:1 #0071e3);
                border: 1px solid rgba(255, 255, 255, 0.15);
                color: #ffffff;
                font-weight: 600;
                border-radius: 12px;
                padding: 8px 18px;
                font-size: 12px;
            }
            QPushButton:hover { background: #2997ff; }
        """)
        self.btn_save.clicked.connect(self._save_current_image)
        bottom_bar.addWidget(self.btn_save)

        self.layout.addLayout(bottom_bar)

        self._render_current()

    def _arrow_btn_style(self) -> str:
        return """
            QPushButton {
                background-color: #161b22;
                border: 1px solid #30363d;
                border-radius: 22px;
                color: #f0f6fc;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0a84ff;
                border-color: #0a84ff;
                color: #ffffff;
            }
        """

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key.Key_Left:
            self._show_prev()
        elif event.key() == Qt.Key.Key_Right:
            self._show_next()
        elif event.key() == Qt.Key.Key_Escape:
            self.accept()
        else:
            super().keyPressEvent(event)

    def _show_prev(self):
        if not self.items:
            return
        self.current_idx = (self.current_idx - 1) % len(self.items)
        self._render_current()

    def _show_next(self):
        if not self.items:
            return
        self.current_idx = (self.current_idx + 1) % len(self.items)
        self._render_current()

    def _render_current(self):
        if not self.items:
            return
        item = self.items[self.current_idx]
        sci = get_field_value(item, ['Scientific Name', 'name']) or 'Unknown Plant'
        common = get_field_value(item, ['Common Name', 'local name']) or 'N/A'
        family = get_field_value(item, ['Family', 'family']) or 'N/A'

        self.setWindowTitle(f"{sci} — Specimen Photo ({self.current_idx + 1} of {len(self.items)})")
        self.sci_title_lbl.setText(f"<em>{sci}</em>")
        self.common_sub_lbl.setText(f"🌿 {common} • Family: {family}")
        self.counter_lbl.setText(f"{self.current_idx + 1} / {len(self.items)}")

        img_path = resolve_plant_image(item, self.images_dir)
        if img_path and os.path.isfile(img_path):
            pix = QPixmap(img_path)
            if not pix.isNull():
                scaled = pix.scaled(720, 500, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                self.img_display_lbl.setPixmap(scaled)
                self.meta_badge_lbl.setText(f"📁 {os.path.basename(img_path)} ({pix.width()} x {pix.height()} px)")
                self.btn_save.setEnabled(True)
                return

        # Fallback
        self.img_display_lbl.setPixmap(QPixmap())
        self.img_display_lbl.setText("🌿\n\nNo High-Resolution Photograph Uploaded Yet\n(Use 'Upload Photo' to add one)")
        self.img_display_lbl.setStyleSheet("color:#8b949e; font-size:14px; font-weight:500; text-align:center;")
        self.meta_badge_lbl.setText("No photo attached")
        self.btn_save.setEnabled(False)

    def _save_current_image(self):
        if not self.items:
            return
        item = self.items[self.current_idx]
        img_path = resolve_plant_image(item, self.images_dir)
        if not img_path or not os.path.isfile(img_path):
            return

        sci = get_field_value(item, ['Scientific Name', 'name']) or 'Plant'
        clean_name = "".join(c for c in sci if c.isalnum() or c in (' ', '_')).strip().replace(' ', '_')
        ext = os.path.splitext(img_path)[1] or ".jpg"
        save_path, _ = QFileDialog.getSaveFileName(
            self, "Save Photograph", f"{clean_name}{ext}", f"Images (*{ext});;All Files (*)"
        )
        if save_path:
            try:
                shutil.copyfile(img_path, save_path)
                QMessageBox.information(self, "Saved", f"Photograph saved to:\n{save_path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save image:\n{e}")


class GalleryPhotoCard(QFrame):
    """Individual plant photo card in the gallery grid."""
    photo_clicked = pyqtSignal(int)
    photo_updated = pyqtSignal()

    def __init__(self, row: dict, index: int, images_dir: str, card_size: int = 200, parent=None):
        super().__init__(parent)
        self.row = row
        self.index = index
        self.images_dir = images_dir
        self.card_size = card_size

        self.setObjectName("galleryPhotoCard")
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        self.setStyleSheet("""
            QFrame#galleryPhotoCard {
                background-color: #13181f;
                border: 1px solid #30363d;
                border-radius: 18px;
            }
            QFrame#galleryPhotoCard:hover {
                border: 1.5px solid #0a84ff;
                background-color: #161d26;
            }
        """)

        # Image Container
        self.img_lbl = QLabel()
        self.img_lbl.setFixedSize(self.card_size, self.card_size)
        self.img_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.img_lbl.setStyleSheet("""
            background-color: #090d12;
            border: 1px solid #21262d;
            border-radius: 14px;
        """)

        self._load_image()
        layout.addWidget(self.img_lbl)

        # Plant Info
        sci_name = get_field_value(self.row, ['Scientific Name', 'name']) or 'Unknown Plant'
        common_name = get_field_value(self.row, ['Common Name', 'local name']) or ''
        family = get_field_value(self.row, ['Family', 'family']) or ''

        info_vbox = QVBoxLayout()
        info_vbox.setSpacing(3)

        title_lbl = QLabel(f"<em>{sci_name}</em>")
        title_lbl.setStyleSheet("color:#ffffff; font-size:14px; font-weight:700;")
        title_lbl.setWordWrap(True)
        info_vbox.addWidget(title_lbl)

        if common_name and common_name != 'N/A':
            sub_lbl = QLabel(common_name)
            sub_lbl.setStyleSheet("color:#8b949e; font-size:12px; font-weight:500;")
            sub_lbl.setWordWrap(True)
            info_vbox.addWidget(sub_lbl)

        badge_row = QHBoxLayout()
        badge_row.setSpacing(6)

        if family and family != 'N/A':
            fam_badge = QLabel(f"🗂️ {family}")
            fam_badge.setStyleSheet("""
                background-color: #261b3d;
                color: #d2a8ff;
                border: 1px solid rgba(210, 168, 255, 0.25);
                border-radius: 8px;
                padding: 2px 8px;
                font-size: 10.5px;
                font-weight: 600;
            """)
            badge_row.addWidget(fam_badge)

        badge_row.addStretch()

        # Upload / Replace Button
        btn_upload = QPushButton("📷 Upload")
        btn_upload.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_upload.setStyleSheet("""
            QPushButton {
                background-color: #21262d;
                border: 1px solid #30363d;
                color: #c9d1d9;
                border-radius: 8px;
                font-size: 11px;
                font-weight: 600;
                padding: 3px 8px;
            }
            QPushButton:hover {
                background-color: #0a84ff;
                border-color: #0a84ff;
                color: #ffffff;
            }
        """)
        btn_upload.clicked.connect(self._upload_photo)
        badge_row.addWidget(btn_upload)

        info_vbox.addLayout(badge_row)
        layout.addLayout(info_vbox)

    def _load_image(self):
        img_path = resolve_plant_image(self.row, self.images_dir)
        if img_path and os.path.isfile(img_path):
            pix = QPixmap(img_path)
            if not pix.isNull():
                scaled = pix.scaled(self.card_size, self.card_size, Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation)
                cropped = scaled.copy((scaled.width() - self.card_size) // 2, (scaled.height() - self.card_size) // 2, self.card_size, self.card_size)
                self.img_lbl.setPixmap(cropped)
                self.img_lbl.setToolTip("Click to enlarge photo")
                return

        # Fallback leaf icon
        self.img_lbl.setText("🌿")
        self.img_lbl.setStyleSheet(f"""
            background-color: #0d1117;
            border: 1px solid #30363d;
            border-radius: 14px;
            font-size: {int(self.card_size * 0.35)}px;
        """)
        self.img_lbl.setToolTip("Click to view photo options")

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.photo_clicked.emit(self.index)
        super().mousePressEvent(event)

    def _upload_photo(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Plant Photograph", "", "Images (*.jpg *.jpeg *.png *.webp);;All Files (*)"
        )
        if not file_path:
            return

        sci_name = get_field_value(self.row, ['Scientific Name', 'name']) or 'Plant'
        clean_name = sci_name.lower().replace(' ', '_')
        ext = os.path.splitext(file_path)[1].lower() or ".jpg"

        os.makedirs(self.images_dir, exist_ok=True)
        dest_path = os.path.join(self.images_dir, f"{clean_name}{ext}")

        try:
            shutil.copyfile(file_path, dest_path)
            # Update row record in memory
            self.row['Plant Images'] = dest_path
            self._load_image()
            self.photo_updated.emit()
            QMessageBox.information(self, "Success", f"Photograph uploaded and linked for {sci_name}!")
        except Exception as e:
            QMessageBox.critical(self, "Upload Failed", f"Could not copy photo to images folder:\n{e}")


class PlantPhotoGalleryWidget(QWidget):
    """Main Photo Gallery Tab widget."""
    def __init__(self, database: List[Dict[str, Any]], images_dir: str, parent=None):
        super().__init__(parent)
        self.database = database
        self.images_dir = images_dir
        self.filtered_items: List[Dict[str, Any]] = list(database)
        self.card_size = 200

        self._build_ui()

    def _build_ui(self):
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(36, 20, 36, 28)
        root_layout.setSpacing(18)

        # ── 1. Top Controls Bar ──
        ctrl_card = QFrame()
        ctrl_card.setObjectName("cardFrame")
        ctrl_card.setStyleSheet("""
            QFrame#cardFrame {
                background-color: #13181f;
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 18px;
                padding: 14px 20px;
            }
        """)
        ctrl_layout = QHBoxLayout(ctrl_card)
        ctrl_layout.setContentsMargins(16, 12, 16, 12)
        ctrl_layout.setSpacing(16)

        # Search Box
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Filter gallery by Scientific Name, Common Name...")
        self.search_input.setFixedWidth(300)
        self.search_input.textChanged.connect(self._apply_filters)
        ctrl_layout.addWidget(self.search_input)

        # Family Filter
        self.family_combo = QComboBox()
        self.family_combo.setFixedWidth(200)
        self._populate_families()
        self.family_combo.currentIndexChanged.connect(self._apply_filters)
        ctrl_layout.addWidget(self.family_combo)

        # Availability Filter (All / With Photos / Missing)
        self.avail_combo = QComboBox()
        self.avail_combo.setFixedWidth(160)
        self.avail_combo.addItem("🖼️ All Specimens", "all")
        self.avail_combo.addItem("📷 With Photos Only", "has_photo")
        self.avail_combo.addItem("🌿 Missing Photos", "no_photo")
        self.avail_combo.currentIndexChanged.connect(self._apply_filters)
        ctrl_layout.addWidget(self.avail_combo)

        ctrl_layout.addStretch()

        # Thumbnail Size Buttons
        size_lbl = QLabel("Size:")
        size_lbl.setStyleSheet("color:#8b949e; font-size:12px; font-weight:600;")
        ctrl_layout.addWidget(size_lbl)

        btn_small = QPushButton("S")
        btn_small.setFixedSize(30, 30)
        btn_small.setStyleSheet(self._size_btn_style())
        btn_small.clicked.connect(lambda: self._set_card_size(150))
        ctrl_layout.addWidget(btn_small)

        btn_med = QPushButton("M")
        btn_med.setFixedSize(30, 30)
        btn_med.setStyleSheet(self._size_btn_style())
        btn_med.clicked.connect(lambda: self._set_card_size(200))
        ctrl_layout.addWidget(btn_med)

        btn_large = QPushButton("L")
        btn_large.setFixedSize(30, 30)
        btn_large.setStyleSheet(self._size_btn_style())
        btn_large.clicked.connect(lambda: self._set_card_size(260))
        ctrl_layout.addWidget(btn_large)

        # Counter Badge
        self.counter_badge = QLabel("")
        self.counter_badge.setStyleSheet("""
            background-color: #0c2d48;
            border: 1px solid #0a84ff;
            color: #79c0ff;
            border-radius: 10px;
            padding: 5px 12px;
            font-size: 12px;
            font-weight: 700;
        """)
        ctrl_layout.addWidget(self.counter_badge)

        root_layout.addWidget(ctrl_card)

        # ── 2. Scrollable Photo Grid ──
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border:none; background:transparent;")

        self.grid_container = QWidget()
        self.grid_layout = QGridLayout(self.grid_container)
        self.grid_layout.setContentsMargins(10, 10, 10, 10)
        self.grid_layout.setSpacing(18)

        scroll.setWidget(self.grid_container)
        root_layout.addWidget(scroll, stretch=1)

        self._render_grid()

    def _size_btn_style(self) -> str:
        return """
            QPushButton {
                background-color: #161b22;
                border: 1px solid #30363d;
                border-radius: 8px;
                color: #c9d1d9;
                font-weight: 600;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #0a84ff;
                border-color: #0a84ff;
                color: #ffffff;
            }
        """

    def _set_card_size(self, size: int):
        self.card_size = size
        self._render_grid()

    def _populate_families(self):
        self.family_combo.clear()
        self.family_combo.addItem("🗂️ All Families", "")
        families = set()
        for row in self.database:
            fam = get_field_value(row, ['Family', 'family'])
            if fam and fam.strip() and fam != 'N/A':
                families.add(fam.strip())
        for f in sorted(list(families)):
            self.family_combo.addItem(f, f)

    def _apply_filters(self):
        query = self.search_input.text().strip().upper()
        selected_fam = self.family_combo.currentData() or ""
        avail_mode = self.avail_combo.currentData() or "all"

        self.filtered_items = []
        for row in self.database:
            sci = (get_field_value(row, ['Scientific Name', 'name']) or '').upper()
            common = (get_field_value(row, ['Common Name', 'local name']) or '').upper()
            fam = get_field_value(row, ['Family', 'family']) or ''

            # Name query filter
            if query and (query not in sci and query not in common):
                continue

            # Family filter
            if selected_fam and fam != selected_fam:
                continue

            # Photo availability
            has_photo = bool(resolve_plant_image(row, self.images_dir))
            if avail_mode == "has_photo" and not has_photo:
                continue
            if avail_mode == "no_photo" and has_photo:
                continue

            self.filtered_items.append(row)

        self._render_grid()

    def _render_grid(self):
        # Clear existing
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        # Update counter badge
        has_photo_count = sum(1 for r in self.filtered_items if resolve_plant_image(r, self.images_dir))
        self.counter_badge.setText(f"{len(self.filtered_items)} Specimens ({has_photo_count} with Photos)")

        if not self.filtered_items:
            no_lbl = QLabel("No specimens matching your gallery filters.")
            no_lbl.setStyleSheet("color:#8b949e; font-size:14px; padding:30px; text-align:center;")
            no_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.grid_layout.addWidget(no_lbl, 0, 0, 1, 4)
            return

        # Responsive columns based on card size
        # S (150) -> ~6 cols, M (200) -> ~4 cols, L (260) -> ~3 cols
        cols = max(1, 1000 // (self.card_size + 30))

        for idx, row in enumerate(self.filtered_items):
            card = GalleryPhotoCard(row, idx, self.images_dir, card_size=self.card_size)
            card.photo_clicked.connect(self._open_lightbox)
            card.photo_updated.connect(self._apply_filters)
            r = idx // cols
            c = idx % cols
            self.grid_layout.addWidget(card, r, c)

    def _open_lightbox(self, index: int):
        if not self.filtered_items or index >= len(self.filtered_items):
            return
        modal = GalleryLightboxModal(self.filtered_items, index, self.images_dir, self)
        modal.exec()

    def reload_database(self, database: List[Dict[str, Any]], images_dir: str):
        self.database = database
        self.images_dir = images_dir
        self._populate_families()
        self._apply_filters()
