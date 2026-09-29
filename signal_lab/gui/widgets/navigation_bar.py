"""Top primary navigation bar for Signal Lab desktop platform."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QButtonGroup,
    QFrame,
    QHBoxLayout,
    QPushButton,
    QWidget,
)

from signal_lab.gui.theme import ScientificPalette, get_ui_font


class NavigationBar(QFrame):
    """Primary 7-tab scientific navigation bar."""

    tab_changed = Signal(str, int)  # tab_name, tab_index

    TABS = (
        ("OVERVIEW", 0),
        ("ANALYSIS", 1),
        ("SIGNAL", 2),
        ("DEMOD", 3),
        ("BITS", 4),
        ("EVIDENCE", 5),
        ("REPORT", 6),
    )

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setFixedHeight(38)
        self.setStyleSheet(
            f"""
            NavigationBar {{
                background-color: {ScientificPalette.BG_BASE};
                border-bottom: 1px solid {ScientificPalette.BORDER_SUBTLE};
            }}
            QPushButton {{
                background-color: transparent;
                color: {ScientificPalette.TEXT_MUTED};
                border: none;
                border-bottom: 2px solid transparent;
                padding: 8px 18px;
                font-family: 'Inter', sans-serif;
                font-size: 11px;
                font-weight: 600;
                letter-spacing: 1.5px;
            }}
            QPushButton:hover {{
                color: {ScientificPalette.TEXT_PRIMARY};
                background-color: {ScientificPalette.BG_SURFACE};
            }}
            QPushButton:checked {{
                color: {ScientificPalette.ACCENT_CYAN};
                border-bottom: 2px solid {ScientificPalette.ACCENT_CYAN};
                background-color: {ScientificPalette.BG_SURFACE};
                font-weight: bold;
            }}
            """
        )
        self._buttons: dict[str, QPushButton] = {}
        self._button_group = QButtonGroup(self)
        self._button_group.setExclusive(True)
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 0, 12, 0)
        layout.setSpacing(4)

        for name, idx in self.TABS:
            btn = QPushButton(name)
            btn.setCheckable(True)
            btn.setFont(get_ui_font(9, get_ui_font().weight().DemiBold))
            btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            if idx == 0:
                btn.setChecked(True)
            self._button_group.addButton(btn, idx)
            self._buttons[name] = btn
            btn.clicked.connect(lambda checked=False, n=name, i=idx: self.tab_changed.emit(n, i))
            layout.addWidget(btn)

        layout.addStretch()

    def set_active_tab(self, index: int) -> None:
        """Programmatically switch active tab by index."""
        btn = self._button_group.button(index)
        if btn:
            btn.setChecked(True)

    def set_active_tab_name(self, name: str) -> None:
        """Programmatically switch active tab by name."""
        if name.upper() in self._buttons:
            self._buttons[name.upper()].setChecked(True)
