"""Dedicated Report Export and Audit Dossier viewer."""

from __future__ import annotations

import json
from pathlib import Path

from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from signal_lab.gui.theme import ScientificPalette, get_monospace_font, get_ui_font


class ReportViewWidget(QWidget):
    """Full-page technical audit report preview and export workspace."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._current_md: str = ""
        self._current_json: str = ""
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(10)

        # Header Bar
        header_bar = QFrame()
        header_bar.setFixedHeight(44)
        header_bar.setStyleSheet(
            f"background-color: {ScientificPalette.BG_SURFACE}; border: 1px solid {ScientificPalette.BORDER_SUBTLE}; border-radius: 4px;"
        )
        h_layout = QHBoxLayout(header_bar)
        h_layout.setContentsMargins(16, 0, 16, 0)
        h_layout.setSpacing(12)

        title = QLabel("ANALYSIS AUDIT REPORT & PROVENANCE DOSSIER")
        title.setFont(get_ui_font(10, get_ui_font().weight().Bold))
        title.setStyleSheet(f"color: {ScientificPalette.ACCENT_CYAN}; letter-spacing: 1.5px;")
        h_layout.addWidget(title)

        h_layout.addStretch()

        self.btn_copy = QPushButton("Copy to Clipboard")
        self.btn_copy.setStyleSheet(
            f"background-color: {ScientificPalette.BG_CARD}; color: {ScientificPalette.TEXT_PRIMARY}; border: 1px solid {ScientificPalette.BORDER_SUBTLE}; border-radius: 3px; padding: 4px 12px; font-size: 11px;"
        )
        self.btn_copy.clicked.connect(self._on_copy_clipboard)
        h_layout.addWidget(self.btn_copy)

        self.btn_export_md = QPushButton("Export .MD")
        self.btn_export_md.setStyleSheet(
            f"background-color: {ScientificPalette.ACCENT_CYAN}; color: {ScientificPalette.BG_BASE}; border: none; border-radius: 3px; padding: 4px 14px; font-size: 11px; font-weight: bold;"
        )
        self.btn_export_md.clicked.connect(self._on_export_md)
        h_layout.addWidget(self.btn_export_md)

        self.btn_export_json = QPushButton("Export .JSON")
        self.btn_export_json.setStyleSheet(
            f"background-color: {ScientificPalette.BG_CARD}; color: {ScientificPalette.TEXT_PRIMARY}; border: 1px solid {ScientificPalette.BORDER_SUBTLE}; border-radius: 3px; padding: 4px 12px; font-size: 11px;"
        )
        self.btn_export_json.clicked.connect(self._on_export_json)
        h_layout.addWidget(self.btn_export_json)

        layout.addWidget(header_bar)

        # Tabbed Viewer: Markdown Preview vs Raw JSON
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(
            f"""
            QTabWidget::pane {{
                border: 1px solid {ScientificPalette.BORDER_SUBTLE};
                background: {ScientificPalette.BG_BASE};
            }}
            QTabBar::tab {{
                background: {ScientificPalette.BG_SURFACE};
                color: {ScientificPalette.TEXT_MUTED};
                padding: 6px 14px;
                font-family: 'Inter', sans-serif;
                font-weight: 600;
                font-size: 11px;
            }}
            QTabBar::tab:selected {{
                background: {ScientificPalette.BG_CARD};
                color: {ScientificPalette.ACCENT_CYAN};
                border-bottom: 2px solid {ScientificPalette.ACCENT_CYAN};
            }}
            """
        )

        # Tab 1: Markdown
        self.md_viewer = QTextEdit()
        self.md_viewer.setReadOnly(True)
        self.md_viewer.setFont(get_monospace_font(10))
        self.md_viewer.setStyleSheet(
            f"background-color: {ScientificPalette.BG_BASE}; color: {ScientificPalette.TEXT_PRIMARY}; border: none; padding: 12px;"
        )
        self.tabs.addTab(self.md_viewer, "Markdown Report")

        # Tab 2: JSON
        self.json_viewer = QTextEdit()
        self.json_viewer.setReadOnly(True)
        self.json_viewer.setFont(get_monospace_font(10))
        self.json_viewer.setStyleSheet(
            f"background-color: {ScientificPalette.BG_BASE}; color: #38bdf8; border: none; padding: 12px;"
        )
        self.tabs.addTab(self.json_viewer, "JSON Schema")

        layout.addWidget(self.tabs, 1)

    def set_report_content(self, md_content: str, json_dict: dict | None = None) -> None:
        """Update report text in both tabs."""
        self._current_md = md_content
        self.md_viewer.setPlainText(md_content)

        if json_dict:
            self._current_json = json.dumps(json_dict, indent=2)
            self.json_viewer.setPlainText(self._current_json)
        else:
            self._current_json = ""
            self.json_viewer.setPlainText("{}")

    def _on_copy_clipboard(self) -> None:
        cb = QApplication.clipboard()
        if cb and self._current_md:
            cb.setText(self._current_md)

    def _on_export_md(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self, "Save Markdown Audit Report", "signal_lab_report.md", "Markdown (*.md)"
        )
        if path and self._current_md:
            Path(path).write_text(self._current_md, encoding="utf-8")

    def _on_export_json(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self, "Save JSON Session Telemetry", "signal_lab_session.json", "JSON (*.json)"
        )
        if path and self._current_json:
            Path(path).write_text(self._current_json, encoding="utf-8")
