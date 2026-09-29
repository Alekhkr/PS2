"""Dedicated Evidence and Provenance inspection view."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from signal_lab.domain.models.evidence import ParameterEvidence
from signal_lab.gui.theme import ScientificPalette, get_monospace_font, get_ui_font


class EvidenceViewWidget(QWidget):
    """Full-page Parameter Evidence and Provenance table."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._all_evidence: list[ParameterEvidence] = []
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(10)

        # Header bar
        header_bar = QFrame()
        header_bar.setFixedHeight(44)
        header_bar.setStyleSheet(
            f"background-color: {ScientificPalette.BG_SURFACE}; border: 1px solid {ScientificPalette.BORDER_SUBTLE}; border-radius: 4px;"
        )
        h_layout = QHBoxLayout(header_bar)
        h_layout.setContentsMargins(16, 0, 16, 0)
        h_layout.setSpacing(16)

        title = QLabel("PARAMETER EVIDENCE & ALGORITHMIC PROVENANCE")
        title.setFont(get_ui_font(10, get_ui_font().weight().Bold))
        title.setStyleSheet(f"color: {ScientificPalette.ACCENT_CYAN}; letter-spacing: 1.5px;")
        h_layout.addWidget(title)

        h_layout.addStretch()

        search_caption = QLabel("FILTER:")
        search_caption.setFont(get_ui_font(8, get_ui_font().weight().Bold))
        search_caption.setStyleSheet(f"color: {ScientificPalette.TEXT_MUTED};")
        h_layout.addWidget(search_caption)

        self.filter_input = QLineEdit()
        self.filter_input.setPlaceholderText("Search parameter, algorithm, or source...")
        self.filter_input.setFixedWidth(260)
        self.filter_input.setStyleSheet(
            f"background-color: {ScientificPalette.BG_BASE}; color: {ScientificPalette.TEXT_PRIMARY}; border: 1px solid {ScientificPalette.BORDER_SUBTLE}; border-radius: 3px; padding: 4px 8px;"
        )
        self.filter_input.textChanged.connect(self._apply_filter)
        h_layout.addWidget(self.filter_input)

        layout.addWidget(header_bar)

        # Evidence Table
        self.table = QTableWidget(0, 8)
        self.table.setHorizontalHeaderLabels(
            [
                "PARAMETER",
                "VALUE",
                "UNIT",
                "SOURCE",
                "ALGORITHM",
                "CONFIDENCE",
                "ASSUMPTIONS",
                "VALIDATION",
            ]
        )
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(7, QHeaderView.ResizeMode.ResizeToContents)
        self.table.verticalHeader().setVisible(False)
        self.table.setFont(get_monospace_font(9))
        self.table.setStyleSheet(
            f"""
            QTableWidget {{
                background-color: {ScientificPalette.BG_BASE};
                border: 1px solid {ScientificPalette.BORDER_SUBTLE};
                color: {ScientificPalette.TEXT_PRIMARY};
            }}
            QHeaderView::section {{
                background-color: {ScientificPalette.BG_SURFACE};
                color: {ScientificPalette.TEXT_MUTED};
                border: none;
                border-bottom: 1px solid {ScientificPalette.BORDER_SUBTLE};
                padding: 6px;
                font-size: 9px;
            }}
            QTableWidget::item {{
                padding: 6px;
                border-bottom: 1px solid {ScientificPalette.BORDER_SUBTLE};
            }}
            """
        )
        layout.addWidget(self.table, 1)

    def set_evidence(self, evidence_list: list[ParameterEvidence]) -> None:
        """Update full evidence list."""
        self._all_evidence = list(evidence_list)
        self._apply_filter(self.filter_input.text())

    def _apply_filter(self, query: str) -> None:
        q = query.strip().lower()
        filtered = [
            ev
            for ev in self._all_evidence
            if not q
            or q in ev.name.lower()
            or q in str(ev.algorithm).lower()
            or q in str(ev.source).lower()
        ]

        self.table.setRowCount(len(filtered))
        for row, ev in enumerate(filtered):
            name_item = QTableWidgetItem(ev.name)
            name_item.setFont(get_monospace_font(9, get_monospace_font().weight().Bold))

            val_item = QTableWidgetItem(str(ev.value))
            unit_item = QTableWidgetItem(ev.unit or "--")
            source_item = QTableWidgetItem(str(ev.source).upper())
            algo_item = QTableWidgetItem(ev.algorithm or "--")

            conf_pct = int(ev.confidence * 100)
            conf_item = QTableWidgetItem(f"{conf_pct}%")
            if conf_pct >= 75:
                conf_item.setForeground(Qt.GlobalColor.green)
            elif conf_pct >= 40:
                conf_item.setForeground(Qt.GlobalColor.cyan)
            else:
                conf_item.setForeground(Qt.GlobalColor.yellow)

            assump_str = ", ".join(ev.assumptions) if ev.assumptions else "None"
            assump_item = QTableWidgetItem(assump_str)

            val_status_str = str(ev.validation).upper()
            val_item_stat = QTableWidgetItem(val_status_str)
            if "VALIDATED" in val_status_str:
                val_item_stat.setForeground(Qt.GlobalColor.green)
            elif "PARTIAL" in val_status_str:
                val_item_stat.setForeground(Qt.GlobalColor.cyan)
            else:
                val_item_stat.setForeground(Qt.GlobalColor.gray)

            items = [
                name_item,
                val_item,
                unit_item,
                source_item,
                algo_item,
                conf_item,
                assump_item,
                val_item_stat,
            ]
            for col, it in enumerate(items):
                self.table.setItem(row, col, it)
