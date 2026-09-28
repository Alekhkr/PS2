"""Austensor & Awwwards-inspired Main Landing Workspace for Signal Lab."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QDragEnterEvent, QDragLeaveEvent, QDropEvent
from PySide6.QtWidgets import (
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from signal_lab.domain.models.session import Session
from signal_lab.gui.theme import ScientificPalette, get_monospace_font, get_ui_font
from signal_lab.gui.widgets.dossier_dialog import ScientificDossierDialog
from signal_lab.gui.widgets.experiment_dock import ExperimentDock
from signal_lab.gui.widgets.wavefield_canvas import WavefieldCanvas


class DropZoneWidget(QWidget):
    """Initial landing workspace elevated with Austensor obsidian aesthetics and procedural wavefields."""

    file_selected = Signal(str)
    session_opened = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setAcceptDrops(True)
        self._init_ui()

    def _init_ui(self) -> None:
        # Root layout for entire landing page
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # Ambient procedural wavefield canvas in background
        self.wave_canvas = WavefieldCanvas(self)

        # Overlay widget that holds the foreground UI
        overlay = QWidget(self)
        overlay_layout = QVBoxLayout(overlay)
        overlay_layout.setContentsMargins(48, 24, 48, 36)
        overlay_layout.setSpacing(20)

        # 1. Top Austensor Floating Experiment Dock
        dock_container = QHBoxLayout()
        dock_container.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.experiment_dock = ExperimentDock(self)
        self.experiment_dock.experiment_selected.connect(self.file_selected.emit)
        self.experiment_dock.dossier_requested.connect(self._open_dossier)
        dock_container.addWidget(self.experiment_dock)
        overlay_layout.addLayout(dock_container)

        # 2. Main Cybernetic Aperture Drop Zone
        self.drop_frame = QFrame()
        self.drop_frame.setProperty("glassCard", "true")
        self.drop_frame.setStyleSheet(
            f"""
            QFrame {{
                background-color: rgba(15, 20, 32, 0.70);
                border: 1px solid {ScientificPalette.BORDER_HAIRLINE};
                border-radius: 16px;
            }}
            QFrame:hover {{
                border-color: {ScientificPalette.BORDER_GOLD};
                background-color: rgba(20, 27, 44, 0.85);
            }}
            """
        )

        drop_layout = QVBoxLayout(self.drop_frame)
        drop_layout.setContentsMargins(40, 44, 40, 40)
        drop_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        drop_layout.setSpacing(14)

        # Micro Metadata Tag (Austensor style)
        tag_lbl = QLabel("EXP 00 // TERRESTRIAL RF INGESTION PORTAL")
        tag_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        tag_lbl.setFont(get_monospace_font(9))
        tag_lbl.setStyleSheet(f"color: {ScientificPalette.ACCENT_GOLD}; letter-spacing: 2.5px; font-weight: 600;")
        drop_layout.addWidget(tag_lbl)

        # Primary Title
        title_lbl = QLabel("INGEST RF WAVEFORM CAPTURE")
        title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_lbl.setFont(get_ui_font(18, get_ui_font().weight().Bold))
        title_lbl.setStyleSheet(f"color: {ScientificPalette.TEXT_PRIMARY}; letter-spacing: 1.5px;")
        drop_layout.addWidget(title_lbl)

        # Curatorial Philosophical Proposition
        curatorial_lbl = QLabel("“Where computation transcends notation: Waveform as geometry, bitstream as space.”")
        curatorial_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        curatorial_lbl.setFont(get_ui_font(10))
        curatorial_lbl.setStyleSheet(f"color: {ScientificPalette.TEXT_SECONDARY}; font-style: italic;")
        drop_layout.addWidget(curatorial_lbl)

        # Format capability pill
        sub_lbl = QLabel("RAW IQ (.iq / .bin / .raw)  ·  AUDIO WAV (PCM/Float)  ·  STANDARDIZED SIGMF (.sigmf-meta)")
        sub_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sub_lbl.setFont(get_monospace_font(9))
        sub_lbl.setStyleSheet(f"color: {ScientificPalette.TEXT_MUTED}; letter-spacing: 1px;")
        drop_layout.addWidget(sub_lbl)

        drop_layout.addSpacing(6)

        # Action Buttons Row
        btn_row = QHBoxLayout()
        btn_row.setAlignment(Qt.AlignmentFlag.AlignCenter)
        btn_row.setSpacing(14)

        self.btn_browse = QPushButton("Open Capture File")
        self.btn_browse.setProperty("primary", "true")
        self.btn_browse.setFixedWidth(180)
        self.btn_browse.clicked.connect(self._on_browse_clicked)
        btn_row.addWidget(self.btn_browse)

        self.btn_dossier = QPushButton("Explore Theory (D)")
        self.btn_dossier.setProperty("gold", "true")
        self.btn_dossier.clicked.connect(self._open_dossier)
        btn_row.addWidget(self.btn_dossier)

        drop_layout.addLayout(btn_row)

        overlay_layout.addWidget(self.drop_frame, 1)

        # 3. Hardware & Architecture Telemetry Strip
        telemetry_bar = QHBoxLayout()
        telemetry_bar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        telemetry_bar.setSpacing(24)

        for badge_text in [
            "⚡ C++20 SIMD: ACTIVE",
            "◈ STREAMING: ZERO-COPY MEMMAP",
            "⬡ NEURAL AMC: RESNET-1D (16 MODS)",
            "✓ STANDARDS: SIGMF v1.0.0",
        ]:
            b_lbl = QLabel(badge_text)
            b_lbl.setFont(get_monospace_font(9))
            b_lbl.setStyleSheet(f"color: {ScientificPalette.TEXT_MUTED}; letter-spacing: 1.2px;")
            telemetry_bar.addWidget(b_lbl)

        overlay_layout.addLayout(telemetry_bar)

        # 4. Recent Sessions Area
        self.recent_box = QWidget()
        recent_layout = QVBoxLayout(self.recent_box)
        recent_layout.setContentsMargins(0, 0, 0, 0)
        recent_layout.setSpacing(8)

        recent_header = QHBoxLayout()
        recent_title = QLabel("RECORDED SESSIONS & PROVENANCE ARCHIVE")
        recent_title.setFont(get_monospace_font(9))
        recent_title.setStyleSheet(f"color: {ScientificPalette.TEXT_MUTED}; letter-spacing: 1.5px;")
        recent_header.addWidget(recent_title)
        recent_header.addStretch()
        recent_layout.addLayout(recent_header)

        self.recent_list = QListWidget()
        self.recent_list.setFixedHeight(120)
        self.recent_list.setStyleSheet(
            f"""
            QListWidget {{
                background-color: rgba(10, 14, 23, 0.70);
                border: 1px solid {ScientificPalette.BORDER_HAIRLINE};
                border-radius: 8px;
            }}
            QListWidget::item {{
                padding: 7px 12px;
                border-bottom: 1px solid {ScientificPalette.BORDER_SUBTLE};
                color: {ScientificPalette.TEXT_PRIMARY};
            }}
            QListWidget::item:hover {{
                background-color: {ScientificPalette.BG_HOVER};
                color: {ScientificPalette.ACCENT_CYAN};
            }}
            """
        )
        self.recent_list.itemClicked.connect(self._on_recent_item_clicked)
        recent_layout.addWidget(self.recent_list)

        overlay_layout.addWidget(self.recent_box)

        root_layout.addWidget(overlay)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self.wave_canvas.setGeometry(self.rect())

    def _open_dossier(self) -> None:
        dialog = ScientificDossierDialog(self)
        dialog.exec()

    def populate_recent_sessions(self, sessions: list[Session]) -> None:
        """Fill recent sessions list."""
        self.recent_list.clear()
        if not sessions:
            item = QListWidgetItem("No recent sessions archive")
            item.setFlags(Qt.ItemFlag.NoItemFlags)
            self.recent_list.addItem(item)
            return

        for sess in sessions:
            fname = Path(sess.input_file_path).name if sess.input_file_path else "No file"
            date_str = sess.updated_at[:19].replace("T", " ")
            item = QListWidgetItem(f"◈ {sess.name:<24}  —  {fname:<36}  ({date_str} UTC)")
            item.setData(Qt.ItemDataRole.UserRole, sess.id)
            item.setFont(get_monospace_font(9))
            self.recent_list.addItem(item)

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.drop_frame.setStyleSheet(
                f"""
                QFrame {{
                    background-color: rgba(20, 30, 50, 0.90);
                    border: 2px solid {ScientificPalette.ACCENT_CYAN};
                    border-radius: 16px;
                }}
                """
            )

    def dragLeaveEvent(self, event: QDragLeaveEvent) -> None:
        self.drop_frame.setStyleSheet(
            f"""
            QFrame {{
                background-color: rgba(15, 20, 32, 0.70);
                border: 1px solid {ScientificPalette.BORDER_HAIRLINE};
                border-radius: 16px;
            }}
            """
        )

    def dropEvent(self, event: QDropEvent) -> None:
        urls = event.mimeData().urls()
        if urls:
            path = urls[0].toLocalFile()
            if path:
                self.file_selected.emit(path)
        event.acceptProposedAction()

    def _on_browse_clicked(self) -> None:
        filepath, _ = QFileDialog.getOpenFileName(
            self,
            "Open Signal Capture",
            "",
            "Signal Files (*.wav *.wave *.iq *.bin *.raw *.dat *.sigmf-meta *.sigmf-data *.sigmf);;All Files (*.*)",
        )
        if filepath:
            self.file_selected.emit(filepath)

    def _on_recent_item_clicked(self, item: QListWidgetItem) -> None:
        session_id = item.data(Qt.ItemDataRole.UserRole)
        if session_id:
            self.session_opened.emit(session_id)
