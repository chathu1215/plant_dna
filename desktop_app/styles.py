"""
Plant DNA Identification System — Apple macOS Dark & Electric Blue Stylesheet
================================================================================
Premium Cupertino-inspired dark aesthetic featuring frosted translucent surfaces,
macOS segmented controls, electric blue action buttons, and refined micro-details.
"""

MODERN_QSS = """
/* === Global Typography & Surface === */
QWidget {
    font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', 'SF Pro Text', 'Segoe UI', 'Inter', sans-serif;
    color: #f0f6fc;
    background-color: transparent;
    selection-background-color: #0a84ff;
    selection-color: #ffffff;
}

QMainWindow {
    background-color: #090d12;
}

/* === Ultra-sleek macOS Scrollbars === */
QScrollArea {
    border: none;
    background-color: transparent;
}

QScrollBar:vertical {
    border: none;
    background: transparent;
    width: 8px;
    margin: 4px 2px 4px 2px;
    border-radius: 4px;
}

QScrollBar::handle:vertical {
    background: rgba(255, 255, 255, 0.16);
    min-height: 30px;
    border-radius: 4px;
}

QScrollBar::handle:vertical:hover {
    background: rgba(255, 255, 255, 0.32);
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

QScrollBar:horizontal {
    border: none;
    background: transparent;
    height: 8px;
    margin: 2px 4px 2px 4px;
    border-radius: 4px;
}

QScrollBar::handle:horizontal {
    background: rgba(255, 255, 255, 0.16);
    min-width: 30px;
    border-radius: 4px;
}

QScrollBar::handle:horizontal:hover {
    background: rgba(255, 255, 255, 0.32);
}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0px;
}

/* === macOS Top Bar / Header === */
QFrame#headerFrame {
    background-color: #11161d;
    border-bottom: 1px solid rgba(255, 255, 255, 0.08);
    padding: 12px 24px;
}

QLabel#brandTitle {
    color: #ffffff;
    font-size: 19px;
    font-weight: 700;
    letter-spacing: -0.4px;
}

QLabel#brandSubtitle {
    color: #58a6ff;
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 1.2px;
}

/* === Status Badge (Compact Apple Pill) === */
QFrame#dbStatusBadge {
    background-color: #161b22;
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 12px;
    padding: 4px 12px;
}

QLabel#dbStatusText {
    font-size: 12px;
    color: #8b949e;
    font-weight: 500;
}

/* === Cards (Apple Floating Surfaces) === */
QFrame#cardFrame {
    background-color: #13181f;
    border: 1px solid rgba(255, 255, 255, 0.07);
    border-radius: 20px;
    padding: 24px;
}

QLabel#cardTitle {
    color: #ffffff;
    font-size: 20px;
    font-weight: 700;
    letter-spacing: -0.3px;
}

QLabel#cardSubtitle {
    color: #8b949e;
    font-size: 13px;
    font-weight: 400;
}

/* === macOS Inputs (Subtle Glass & Glow) === */
QLineEdit, QTextEdit {
    background-color: #0d1117;
    border: 1px solid #30363d;
    border-radius: 12px;
    padding: 10px 14px;
    color: #f0f6fc;
    font-size: 13px;
}

QLineEdit:focus, QTextEdit:focus {
    border: 1.5px solid #0a84ff;
    background-color: #10151c;
}

QLineEdit::placeholder, QTextEdit::placeholder {
    color: #6e7681;
}

/* === macOS Select Menu (Dropdown) === */
QComboBox {
    background-color: #0d1117;
    border: 1px solid #30363d;
    border-radius: 12px;
    padding: 10px 14px;
    color: #f0f6fc;
    font-size: 13px;
    font-weight: 500;
}

QComboBox:hover {
    border: 1px solid #58a6ff;
}

QComboBox:focus {
    border: 1.5px solid #0a84ff;
}

QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 32px;
    border-left: none;
}

QComboBox QAbstractItemView {
    background-color: #161b22;
    border: 1px solid #30363d;
    border-radius: 10px;
    selection-background-color: #0a84ff;
    selection-color: #ffffff;
    color: #f0f6fc;
    padding: 6px;
}

/* === Apple Action Buttons === */
/* Primary Electric Blue Button */
QPushButton#btnPrimary {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #0a84ff, stop:1 #0071e3);
    color: #ffffff;
    border: 1px solid rgba(255, 255, 255, 0.15);
    border-radius: 14px;
    padding: 11px 26px;
    font-size: 13px;
    font-weight: 600;
    letter-spacing: -0.1px;
}

QPushButton#btnPrimary:hover {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #2997ff, stop:1 #0a84ff);
}

QPushButton#btnPrimary:pressed {
    background: #0056b3;
}

QPushButton#btnPrimary:disabled {
    background: #21262d;
    color: #6e7681;
    border: 1px solid #30363d;
}

/* Secondary Frosted Glass Button */
QPushButton#btnSecondary {
    background-color: #21262d;
    color: #c9d1d9;
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 14px;
    padding: 11px 22px;
    font-size: 13px;
    font-weight: 500;
}

QPushButton#btnSecondary:hover {
    background-color: #30363d;
    color: #ffffff;
    border: 1px solid rgba(255, 255, 255, 0.2);
}

QPushButton#btnSecondary:pressed {
    background-color: #161b22;
}

/* macOS Segmented Control Tabs (Toggle Buttons) */
QPushButton#toggleBtnActive {
    background-color: #0a84ff;
    color: #ffffff;
    border: none;
    border-radius: 10px;
    padding: 8px 18px;
    font-weight: 600;
    font-size: 12px;
}

QPushButton#toggleBtnInactive {
    background-color: #161b22;
    color: #8b949e;
    border: 1px solid #30363d;
    border-radius: 10px;
    padding: 8px 18px;
    font-weight: 500;
    font-size: 12px;
}

QPushButton#toggleBtnInactive:hover {
    background-color: #21262d;
    color: #f0f6fc;
}

/* === macOS Table View === */
QTableWidget {
    background-color: #0d1117;
    border: 1px solid #30363d;
    border-radius: 16px;
    gridline-color: #21262d;
    font-size: 13px;
    color: #f0f6fc;
}

QTableWidget::item {
    padding: 10px 14px;
    border-bottom: 1px solid #161b22;
}

QTableWidget::item:selected {
    background-color: #0c2d48;
    color: #58a6ff;
}

QHeaderView::section {
    background-color: #161b22;
    color: #8b949e;
    font-weight: 600;
    font-size: 12px;
    padding: 10px 14px;
    border: none;
    border-bottom: 1px solid #30363d;
    border-right: 1px solid #21262d;
}

/* === Plant Result Card === */
QFrame#plantCardItem {
    background-color: #161b22;
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 18px;
}

QFrame#plantCardItem:hover {
    border: 1px solid rgba(255, 255, 255, 0.16);
}

QFrame#plantCardHeader {
    background-color: #1c2128;
    border-top-left-radius: 18px;
    border-top-right-radius: 18px;
    padding: 14px 18px;
}

QLabel#plantTitle {
    color: #ffffff;
    font-size: 17px;
    font-weight: 700;
    letter-spacing: -0.2px;
}

QLabel#plantSubtitle {
    color: #8b949e;
    font-size: 13px;
    font-weight: 500;
}

/* Details Grid Box (Squircle Card) */
QFrame#detailBox {
    background-color: #0d1117;
    border: 1px solid #30363d;
    border-radius: 12px;
    padding: 11px 14px;
}

QLabel#detailBoxTitle {
    color: #58a6ff;
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.6px;
}

QLabel#detailBoxValue {
    color: #f0f6fc;
    font-size: 13px;
    font-weight: 400;
    line-height: 1.5;
}

/* === BLAST Alignment Viewer Panel === */
QFrame#alignmentPanel {
    background-color: #0d1117;
    border: 1px solid #30363d;
    border-radius: 16px;
}

QFrame#alignmentHeader {
    background: #161b22;
    border-top-left-radius: 16px;
    border-top-right-radius: 16px;
    border-bottom: 1px solid #30363d;
    padding: 12px 18px;
}

QLabel#alignmentHeaderText {
    color: #ffffff;
    font-size: 13px;
    font-weight: 600;
}

QLabel#alignmentStatBadge {
    background-color: rgba(255, 255, 255, 0.06);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 8px;
    padding: 4px 10px;
    font-size: 11px;
    font-weight: 500;
    color: #c9d1d9;
}

QTextEdit#alignmentText {
    background-color: #070a0e;
    border: none;
    font-family: 'SF Mono', 'Consolas', 'Courier New', monospace;
    font-size: 12px;
    line-height: 1.6;
    color: #e6edf3;
    padding: 16px 18px;
}

/* === Apple Blue Progress Bar === */
QProgressBar {
    background-color: #0d1117;
    border: 1px solid #30363d;
    border-radius: 6px;
    text-align: center;
    color: #ffffff;
    font-weight: 600;
    font-size: 11px;
}

QProgressBar::chunk {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0071e3, stop:1 #0a84ff);
    border-radius: 5px;
}
"""
