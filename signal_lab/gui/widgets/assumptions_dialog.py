"""Assumptions Required Dialog for uncalibrated or missing signal metadata."""

from __future__ import annotations

from typing import ClassVar

import numpy as np
import pyqtgraph as pg
from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
)
from scipy import signal

from signal_lab.domain.enums import EvidenceSource, ValidationStatus
from signal_lab.domain.models.evidence import ParameterEvidence
from signal_lab.domain.models.signal import SignalBuffer
from signal_lab.gui.theme import ScientificPalette


class AssumptionsDialog(QDialog):
    """Interactive dialog allowing the user to select or override signal assumptions

    (e.g., missing sample rate, center frequency) with a live miniature FFT preview.
    """

    assumptions_applied = Signal(float, float)  # sample_rate_hz, center_frequency_hz

    STANDARD_RATES: ClassVar[list[tuple[str, float]]] = [
        ("48 kHz (Audio / VLF)", 48_000.0),
        ("192 kHz (VHF Soundcard / SDR)", 192_000.0),
        ("1.0 MHz (Narrowband SDR)", 1_000_000.0),
        ("2.048 MHz (RTL-SDR / DAB)", 2_048_000.0),
        ("2.4 MHz (RTL-SDR Standard)", 2_400_000.0),
        ("5.0 MHz (LimeSDR / Pluto)", 5_000_000.0),
        ("10.0 MHz (USRP / BladeRF)", 10_000_000.0),
        ("20.0 MHz (802.11 WLAN 20MHz)", 20_000_000.0),
        ("40.0 MHz (802.11 WLAN 40MHz)", 40_000_000.0),
    ]

    def __init__(
        self,
        buffer: SignalBuffer,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Assumptions Required — Signal Parameters")
        self.resize(650, 520)
        self.setModal(True)

        self._buffer = buffer
        self._samples_preview = (
            buffer.samples[:16384] if buffer.num_samples > 16384 else buffer.samples
        )

        self._current_sample_rate = buffer.sample_rate_hz or 2_048_000.0
        self._current_center_freq = buffer.center_frequency_hz or 0.0

        self._init_ui()
        self._update_preview()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # Header alert
        header = QLabel(
            "<b>Signal Metadata Incomplete:</b> "
            "Please confirm or calibrate the physical sampling rate and center frequency. "
            "All subsequent DSP bandwidths and baud rates depend on these assumptions."
        )
        header.setWordWrap(True)
        header.setStyleSheet(
            f"color: {ScientificPalette.ACCENT_CYAN}; background: #111822; padding: 8px; border-radius: 4px;"
        )
        layout.addWidget(header)

        # Controls Group
        controls_group = QGroupBox("Signal Parameter Calibration")
        controls_layout = QFormLayout(controls_group)

        # Standard preset combo
        self.combo_presets = QComboBox()
        for label, rate in self.STANDARD_RATES:
            self.combo_presets.addItem(label, rate)
        self.combo_presets.currentIndexChanged.connect(self._on_preset_changed)
        controls_layout.addRow("Standard Rates:", self.combo_presets)

        # Sample Rate Spinbox
        self.spin_rate = QDoubleSpinBox()
        self.spin_rate.setRange(1.0, 10_000_000_000.0)
        self.spin_rate.setValue(self._current_sample_rate)
        self.spin_rate.setSuffix(" Hz")
        self.spin_rate.setDecimals(1)
        self.spin_rate.valueChanged.connect(self._on_rate_manual_changed)
        controls_layout.addRow("Sample Rate ($f_s$):", self.spin_rate)

        # Center Frequency Spinbox
        self.spin_fc = QDoubleSpinBox()
        self.spin_fc.setRange(0.0, 100_000_000_000.0)
        self.spin_fc.setValue(self._current_center_freq)
        self.spin_fc.setSuffix(" Hz")
        self.spin_fc.setDecimals(1)
        self.spin_fc.valueChanged.connect(self._on_fc_manual_changed)
        controls_layout.addRow("Center Frequency ($f_c$):", self.spin_fc)

        # Computed telemetry readouts
        self.lbl_telemetry = QLabel()
        self.lbl_telemetry.setStyleSheet(
            f"font-family: 'JetBrains Mono', monospace; color: {ScientificPalette.TEXT_SECONDARY};"
        )
        controls_layout.addRow("Derived Bounds:", self.lbl_telemetry)

        layout.addWidget(controls_group)

        # Live Spectrum Preview
        preview_group = QGroupBox("Live Spectrum Preview (Welch PSD)")
        preview_layout = QVBoxLayout(preview_group)
        self.plot_preview = pg.PlotWidget()
        self.plot_preview.setBackground("#090B0E")
        self.plot_preview.showGrid(x=True, y=True, alpha=0.3)
        self.plot_preview.setLabel("bottom", "Frequency", units="Hz")
        self.plot_preview.setLabel("left", "Power Density", units="dBFS/Hz")
        self.curve_preview = self.plot_preview.plot(
            pen=pg.mkPen(color=ScientificPalette.ACCENT_CYAN, width=1.5)
        )
        preview_layout.addWidget(self.plot_preview)
        layout.addWidget(preview_group)

        # Action Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.clicked.connect(self.reject)
        button_layout.addWidget(self.btn_cancel)

        self.btn_apply = QPushButton("Apply Assumptions")
        self.btn_apply.setStyleSheet(
            f"background-color: {ScientificPalette.ACCENT_CYAN}; color: #000; font-weight: bold; padding: 6px 16px;"
        )
        self.btn_apply.clicked.connect(self._on_apply)
        button_layout.addWidget(self.btn_apply)

        layout.addLayout(button_layout)

    def _on_preset_changed(self, idx: int) -> None:
        rate = float(self.combo_presets.itemData(idx))
        self.spin_rate.blockSignals(True)
        self.spin_rate.setValue(rate)
        self.spin_rate.blockSignals(False)
        self._current_sample_rate = rate
        self._update_preview()

    def _on_rate_manual_changed(self, val: float) -> None:
        self._current_sample_rate = val
        self._update_preview()

    def _on_fc_manual_changed(self, val: float) -> None:
        self._current_center_freq = val
        self._update_preview()

    def _update_preview(self) -> None:
        fs = self._current_sample_rate
        fc = self._current_center_freq
        dur = self._buffer.num_samples / fs
        bin_spacing = fs / 2048

        self.lbl_telemetry.setText(
            f"Span: {dur:.3f} s  |  Span: ±{fs / 2 / 1e6:.3f} MHz  |  Res: {bin_spacing:.1f} Hz"
        )

        # Compute preview PSD
        if len(self._samples_preview) >= 64:
            nperseg = min(1024, len(self._samples_preview))
            freqs, psd = signal.welch(
                self._samples_preview,
                fs=fs,
                window="hann",
                nperseg=nperseg,
                return_onesided=False,
                scaling="density",
            )
            freqs = np.fft.fftshift(freqs) + fc
            psd_db = 10.0 * np.log10(np.fft.fftshift(psd) + 1e-15)
            self.curve_preview.setData(freqs, psd_db)

    def _on_apply(self) -> None:
        self._buffer.sample_rate_hz = self._current_sample_rate
        self._buffer.center_frequency_hz = self._current_center_freq
        self.assumptions_applied.emit(self._current_sample_rate, self._current_center_freq)
        self.accept()

    def get_parameter_evidences(self) -> list[ParameterEvidence]:
        """Returns evidence objects recording this user calibration."""
        ev_fs = ParameterEvidence(
            name="sample_rate",
            value=self._current_sample_rate,
            unit="Hz",
            source=EvidenceSource.USER,
            algorithm="interactive_assumptions_dialog",
            confidence=0.95,
            validation=ValidationStatus.VALIDATED,
            assumptions=["User calibrated physical sampling rate"],
        )
        ev_fc = ParameterEvidence(
            name="center_frequency",
            value=self._current_center_freq,
            unit="Hz",
            source=EvidenceSource.USER,
            algorithm="interactive_assumptions_dialog",
            confidence=0.95,
            validation=ValidationStatus.VALIDATED,
            assumptions=["User calibrated RF center frequency"],
        )
        return [ev_fs, ev_fc]
