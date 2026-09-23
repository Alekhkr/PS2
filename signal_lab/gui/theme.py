"""Theme definitions and dark scientific instrument styling for Signal Lab."""

from __future__ import annotations

from PySide6.QtGui import QFont


class ScientificPalette:
    """Awwwards-level restrained dark scientific instrument color palette."""

    # Surfaces
    BG_BASE = "#090B0E"  # Deep near-black graphite
    BG_SURFACE = "#12151B"  # Panel surface
    BG_CARD = "#181D25"  # Active card / container
    BG_HOVER = "#202632"  # Interactive hover state
    BG_ACTIVE = "#28303F"  # Pressed / active state

    # Borders & Dividers
    BORDER_SUBTLE = "#1C222C"
    BORDER_STRONG = "#2B3444"
    BORDER_FOCUS = "#00E5FF"

    # Text
    TEXT_PRIMARY = "#F2F5F8"  # Crisp readable white
    TEXT_SECONDARY = "#8B98A9"  # Muted technical gray
    TEXT_MUTED = "#556375"  # Subtle hints / units

    # Accents & Semantics
    ACCENT_CYAN = "#00E5FF"  # Primary electric cyan
    ACCENT_BLUE = "#0A84FF"  # Secondary data blue
    ACCENT_AMBER = "#FF9F0A"  # Restrained warning amber
    ACCENT_RED = "#FF453A"  # Crisp error red
    ACCENT_GREEN = "#30D158"  # Verified / converged green


def get_monospace_font(point_size: int = 10, weight: QFont.Weight = QFont.Weight.Normal) -> QFont:
    """Returns the primary monospace font for numeric and signal data."""
    font = QFont("JetBrains Mono", point_size)
    font.setStyleHint(QFont.StyleHint.Monospace)
    font.setWeight(weight)
    return font


def get_ui_font(point_size: int = 10, weight: QFont.Weight = QFont.Weight.Normal) -> QFont:
    """Returns the primary UI font."""
    font = QFont("Inter", point_size)
    font.setStyleHint(QFont.StyleHint.SansSerif)
    font.setWeight(weight)
    return font


DARK_SCIENTIFIC_QSS = f"""
QMainWindow, QDialog {{
    background-color: {ScientificPalette.BG_BASE};
    color: {ScientificPalette.TEXT_PRIMARY};
}}

QWidget {{
    background-color: transparent;
    color: {ScientificPalette.TEXT_PRIMARY};
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    font-size: 12px;
}}

/* Panels and Containers */
QFrame[frameShape="1"], QFrame[frameShape="2"], QFrame[frameShape="6"] {{
    border: 1px solid {ScientificPalette.BORDER_SUBTLE};
    border-radius: 4px;
}}

/* Splitter */
QSplitter::handle {{
    background-color: {ScientificPalette.BORDER_SUBTLE};
}}
QSplitter::handle:hover {{
    background-color: {ScientificPalette.ACCENT_CYAN};
}}

/* Buttons */
QPushButton {{
    background-color: {ScientificPalette.BG_CARD};
    color: {ScientificPalette.TEXT_PRIMARY};
    border: 1px solid {ScientificPalette.BORDER_SUBTLE};
    border-radius: 4px;
    padding: 6px 14px;
    font-weight: 500;
}}
QPushButton:hover {{
    background-color: {ScientificPalette.BG_HOVER};
    border-color: {ScientificPalette.BORDER_STRONG};
}}
QPushButton:pressed {{
    background-color: {ScientificPalette.BG_ACTIVE};
    border-color: {ScientificPalette.ACCENT_CYAN};
}}
QPushButton:disabled {{
    background-color: {ScientificPalette.BG_SURFACE};
    color: {ScientificPalette.TEXT_MUTED};
    border-color: {ScientificPalette.BORDER_SUBTLE};
}}

/* Primary Action Accent Button */
QPushButton[primary="true"] {{
    background-color: #004D5A;
    color: {ScientificPalette.ACCENT_CYAN};
    border: 1px solid {ScientificPalette.ACCENT_CYAN};
}}
QPushButton[primary="true"]:hover {{
    background-color: #006070;
}}

/* Progress Bar */
QProgressBar {{
    background-color: {ScientificPalette.BG_SURFACE};
    border: 1px solid {ScientificPalette.BORDER_SUBTLE};
    border-radius: 2px;
    height: 4px;
    text-align: center;
}}
QProgressBar::chunk {{
    background-color: {ScientificPalette.ACCENT_CYAN};
    border-radius: 2px;
}}

/* Scrollbars */
QScrollBar:vertical {{
    background: {ScientificPalette.BG_BASE};
    width: 6px;
    margin: 0;
}}
QScrollBar::handle:vertical {{
    background: {ScientificPalette.BORDER_STRONG};
    border-radius: 3px;
    min-height: 20px;
}}
QScrollBar::handle:vertical:hover {{
    background: {ScientificPalette.ACCENT_CYAN};
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}

QScrollBar:horizontal {{
    background: {ScientificPalette.BG_BASE};
    height: 6px;
    margin: 0;
}}
QScrollBar::handle:horizontal {{
    background: {ScientificPalette.BORDER_STRONG};
    border-radius: 3px;
    min-width: 20px;
}}
QScrollBar::handle:horizontal:hover {{
    background: {ScientificPalette.ACCENT_CYAN};
}}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    width: 0px;
}}

/* Labels & Status */
QLabel {{
    color: {ScientificPalette.TEXT_PRIMARY};
}}

/* Input Fields */
QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {{
    background-color: {ScientificPalette.BG_SURFACE};
    color: {ScientificPalette.TEXT_PRIMARY};
    border: 1px solid {ScientificPalette.BORDER_SUBTLE};
    border-radius: 4px;
    padding: 5px 8px;
    font-family: 'JetBrains Mono', monospace;
}}
QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus {{
    border: 1px solid {ScientificPalette.ACCENT_CYAN};
}}

/* Tables & Lists */
QTableWidget, QListView, QTreeView {{
    background-color: {ScientificPalette.BG_SURFACE};
    alternate-background-color: {ScientificPalette.BG_BASE};
    border: 1px solid {ScientificPalette.BORDER_SUBTLE};
    gridline-color: {ScientificPalette.BORDER_SUBTLE};
    selection-background-color: {ScientificPalette.BG_ACTIVE};
    selection-color: {ScientificPalette.ACCENT_CYAN};
}}
QHeaderView::section {{
    background-color: {ScientificPalette.BG_CARD};
    color: {ScientificPalette.TEXT_SECONDARY};
    padding: 4px 8px;
    border: none;
    border-right: 1px solid {ScientificPalette.BORDER_SUBTLE};
    border-bottom: 1px solid {ScientificPalette.BORDER_SUBTLE};
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
}}
"""
