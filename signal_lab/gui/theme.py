"""Theme definitions and dark scientific instrument styling for Signal Lab."""

from __future__ import annotations

from PySide6.QtGui import QFont


class ScientificPalette:
    """Awwwards-level restrained dark scientific instrument color palette with Austensor obsidian aesthetics."""

    # Obsidian & Carbon Surfaces (Austensor benchmark)
    BG_BASE = "#030508"  # True obsidian canvas
    BG_SURFACE = "#090D15"  # Deep panel surface
    BG_CARD = "#0F1420"  # Frosted card container
    BG_CARD_TRANSLUCENT = "rgba(15, 20, 32, 0.75)"
    BG_HOVER = "#182030"  # Interactive hover state
    BG_ACTIVE = "#222D42"  # Pressed / active state

    # Hairline Borders & Dividers
    BORDER_SUBTLE = "#161E2E"
    BORDER_STRONG = "#253248"
    BORDER_HAIRLINE = "#1A2332"
    BORDER_GOLD = "#6B581B"
    BORDER_FOCUS = "#00F0FF"

    # Text
    TEXT_PRIMARY = "#F4F7FB"  # Crisp readable white
    TEXT_SECONDARY = "#8E9EAF"  # Muted technical slate
    TEXT_MUTED = "#60718A"  # Monospace micro tags and plot axes (Austensor style)

    # Austensor & Scientific Accents
    ACCENT_GOLD = "#D4AF37"  # Golden ratio (phi = 1.618) & curatorial accent
    ACCENT_AMBER = "#FFB300"  # Warning / active beacon
    ACCENT_CYAN = "#00F0FF"  # High-energy electric signal cyan
    ACCENT_BLUE = "#0A84FF"  # Secondary data blue
    ACCENT_RED = "#FF453A"  # Error / out-of-band red
    ACCENT_GREEN = "#30D158"  # Verified / converged green


AustensorPalette = ScientificPalette



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
    background-color: #003B45;
    color: {ScientificPalette.ACCENT_CYAN};
    border: 1px solid {ScientificPalette.ACCENT_CYAN};
    border-radius: 6px;
    padding: 7px 16px;
}}
QPushButton[primary="true"]:hover {{
    background-color: #005666;
    border-color: #33F5FF;
}}

/* Austensor Imperial Gold Accent Button */
QPushButton[gold="true"] {{
    background-color: rgba(212, 175, 55, 0.12);
    color: {ScientificPalette.ACCENT_GOLD};
    border: 1px solid {ScientificPalette.ACCENT_GOLD};
    border-radius: 20px;
    padding: 5px 14px;
    font-weight: 600;
}}
QPushButton[gold="true"]:hover {{
    background-color: rgba(212, 175, 55, 0.25);
    color: #FFE58F;
}}

/* Austensor Floating Experiment Dock Pill */
QPushButton[dockItem="true"] {{
    background-color: rgba(255, 255, 255, 0.04);
    color: {ScientificPalette.TEXT_PRIMARY};
    border: 1px solid {ScientificPalette.BORDER_HAIRLINE};
    border-radius: 18px;
    padding: 4px 12px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 11px;
}}
QPushButton[dockItem="true"]:hover {{
    background-color: rgba(255, 255, 255, 0.10);
    border-color: {ScientificPalette.ACCENT_GOLD};
    color: {ScientificPalette.ACCENT_GOLD};
}}

/* Frosted Glass Cards */
QFrame[glassCard="true"] {{
    background-color: {ScientificPalette.BG_CARD};
    border: 1px solid {ScientificPalette.BORDER_HAIRLINE};
    border-radius: 12px;
}}
QFrame[glassCard="true"]:hover {{
    border-color: {ScientificPalette.BORDER_STRONG};
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
