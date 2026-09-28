"""Audio Player Widget for Acoustic Monitoring of Demodulated Signals."""

from __future__ import annotations

import numpy as np
from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSlider,
    QWidget,
)

from signal_lab.gui.theme import ScientificPalette, get_monospace_font


class AudioPlayerWidget(QFrame):
    """Audio player widget for acoustic monitoring of AM/FM/CW demodulated audio streams."""

    playback_started = Signal()
    playback_stopped = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setFixedHeight(54)
        self.setProperty("glassCard", "true")
        self.setStyleSheet(
            f"""
            AudioPlayerWidget {{
                background-color: rgba(9, 13, 21, 0.85);
                border: 1px solid {ScientificPalette.BORDER_HAIRLINE};
                border-radius: 8px;
            }}
            """
        )

        self._audio_data: np.ndarray | None = None
        self._sample_rate: float = 48000.0
        self._is_playing: bool = False
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 4, 14, 4)
        layout.setSpacing(12)

        # Tag
        tag = QLabel("ACOUSTIC MONITOR:")
        tag.setFont(get_monospace_font(9))
        tag.setStyleSheet(f"color: {ScientificPalette.TEXT_MUTED}; letter-spacing: 1.5px;")
        layout.addWidget(tag)

        # Play / Pause Toggle Button
        self.btn_play = QPushButton("▶ PLAY")
        self.btn_play.setProperty("gold", "true")
        self.btn_play.setFixedWidth(80)
        self.btn_play.clicked.connect(self._toggle_playback)
        layout.addWidget(self.btn_play)

        # Audio Stream Metadata Badge
        self.info_lbl = QLabel("NO DEMODULATED AUDIO")
        self.info_lbl.setFont(get_monospace_font(9))
        self.info_lbl.setStyleSheet(f"color: {ScientificPalette.TEXT_PRIMARY};")
        layout.addWidget(self.info_lbl)

        layout.addStretch()

        # Volume Slider
        vol_tag = QLabel("VOL:")
        vol_tag.setFont(get_monospace_font(9))
        vol_tag.setStyleSheet(f"color: {ScientificPalette.TEXT_MUTED};")
        layout.addWidget(vol_tag)

        self.slider_vol = QSlider(Qt.Orientation.Horizontal)
        self.slider_vol.setRange(0, 100)
        self.slider_vol.setValue(80)
        self.slider_vol.setFixedWidth(90)
        layout.addWidget(self.slider_vol)

    def set_audio_data(self, audio_data: np.ndarray, sample_rate_hz: float = 48000.0) -> None:
        """Loads demodulated audio data into the player."""
        self._audio_data = np.asarray(audio_data, dtype=np.float32)
        self._sample_rate = sample_rate_hz
        duration_s = len(self._audio_data) / max(1.0, sample_rate_hz)
        self.info_lbl.setText(f"PCM {sample_rate_hz / 1000.0:.1f} kHz · {duration_s:.1f}s · {len(self._audio_data)} samples")

    @Slot()
    def _toggle_playback(self) -> None:
        if not self._is_playing:
            self._is_playing = True
            self.btn_play.setText("■ STOP")
            self.playback_started.emit()
        else:
            self._is_playing = False
            self.btn_play.setText("▶ PLAY")
            self.playback_stopped.emit()
