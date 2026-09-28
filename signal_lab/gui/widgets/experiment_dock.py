"""Austensor-style Floating Experiment Navigation Dock for Signal Lab."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QWidget,
)

from signal_lab.gui.theme import ScientificPalette, get_monospace_font


class ExperimentDock(QFrame):
    """Floating glassmorphic dock inspired by the Austensor experiment navigation.

    Allows 1-click exploration of golden terrestrial RF datasets:
    - 01: WWV HF (15 MHz Timecode)
    - 02: LMR VHF (38 MHz Terrestrial Mobile)
    - 03: WLAN UHF (2.4 GHz 320 MB Zero-Copy)
    - 04: RadioMod-R16 (Neural AMC Benchmark)
    """

    experiment_selected = Signal(str)  # Emits absolute file path or experiment key
    dossier_requested = Signal()        # Opens Austensor-style Scientific Dossier

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setFixedHeight(46)
        self.setStyleSheet(
            f"""
            ExperimentDock {{
                background-color: rgba(9, 13, 21, 0.85);
                border: 1px solid {ScientificPalette.BORDER_HAIRLINE};
                border-radius: 23px;
            }}
            """
        )
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 4, 12, 4)
        layout.setSpacing(8)

        # Micro Tag (Austensor EXP header)
        tag_lbl = QLabel("EXPERIMENTS:")
        tag_lbl.setFont(get_monospace_font(9))
        tag_lbl.setStyleSheet(f"color: {ScientificPalette.TEXT_MUTED}; letter-spacing: 1.5px;")
        layout.addWidget(tag_lbl)

        # Experiments mapping
        self._experiments = [
            ("01", "WWV HF", "15 MHz Ionospheric Timecode", "data/wav/N6GN_20211115T190749_iq_15.wav"),
            ("02", "LMR VHF", "38 MHz Land Mobile Radio", "data/wav/audio_37996921Hz_13-51-23_11-11-2023.wav"),
            ("03", "WLAN UHF", "802.11 320MB Zero-Copy", "data/WLAN_laptop_refMeas_M3_rep1.bin"),
            ("04", "R16 AMC", "16-Class ResNet-1D Dataset", "data/RadioMod-R16 dataset.h5"),
        ]

        for num, title, desc, file_path in self._experiments:
            btn = QPushButton(f"{num} {title}")
            btn.setProperty("dockItem", "true")
            btn.setToolTip(f"<b>Experiment {num}: {title}</b><br>{desc}<br><i>Click to load capture</i>")
            btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            btn.clicked.connect(lambda checked=False, p=file_path: self._on_experiment_clicked(p))
            layout.addWidget(btn)

        layout.addSpacing(6)

        # Separator
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.VLine)
        sep.setStyleSheet(f"color: {ScientificPalette.BORDER_SUBTLE};")
        layout.addWidget(sep)

        # Austensor Golden Ratio & Scientific Dossier Pill
        self.btn_dossier = QPushButton("φ DOSSIER")
        self.btn_dossier.setProperty("gold", "true")
        self.btn_dossier.setToolTip("Open Scientific & Mathematical Evidence Dossier (Shortcut: D)")
        self.btn_dossier.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.btn_dossier.clicked.connect(self.dossier_requested.emit)
        layout.addWidget(self.btn_dossier)

    def _on_experiment_clicked(self, rel_path: str) -> None:
        full_path = Path(rel_path).resolve()
        if full_path.exists():
            self.experiment_selected.emit(str(full_path))
        else:
            # Fallback to current working directory
            cwd_path = Path.cwd() / rel_path
            if cwd_path.exists():
                self.experiment_selected.emit(str(cwd_path))
