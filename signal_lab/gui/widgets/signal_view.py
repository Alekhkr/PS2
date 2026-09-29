"""Signal view widget providing interactive conditioning and spectral burst details."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from signal_lab.domain.models.signal import SignalBuffer, SignalSegment
from signal_lab.dsp.conditioning import (
    correct_iq_imbalance,
    normalize_amplitude,
    remove_dc_offset,
)
from signal_lab.gui.plots.spectrum_plot import SpectrumPlotWidget
from signal_lab.gui.plots.waveform_plot import WaveformPlotWidget
from signal_lab.gui.theme import ScientificPalette, get_monospace_font, get_ui_font


class SignalViewWidget(QWidget):
    """Dedicated Signal Conditioning and Spectral Activity workspace."""

    conditioning_applied = Signal(SignalBuffer)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._raw_buffer: SignalBuffer | None = None
        self._current_buffer: SignalBuffer | None = None
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        # Control Bar
        control_bar = QFrame()
        control_bar.setFixedHeight(44)
        control_bar.setStyleSheet(
            f"background-color: {ScientificPalette.BG_SURFACE}; border: 1px solid {ScientificPalette.BORDER_SUBTLE}; border-radius: 4px;"
        )
        c_layout = QHBoxLayout(control_bar)
        c_layout.setContentsMargins(16, 0, 16, 0)
        c_layout.setSpacing(20)

        title = QLabel("SIGNAL CONDITIONING")
        title.setFont(get_ui_font(10, get_ui_font().weight().Bold))
        title.setStyleSheet(f"color: {ScientificPalette.ACCENT_CYAN}; letter-spacing: 1.5px;")
        c_layout.addWidget(title)

        self.chk_dc = QCheckBox("DC Block")
        self.chk_dc.setChecked(True)
        self.chk_dc.stateChanged.connect(self._recalculate_conditioning)
        c_layout.addWidget(self.chk_dc)

        self.chk_iq = QCheckBox("IQ Imbalance (Gram-Schmidt)")
        self.chk_iq.setChecked(True)
        self.chk_iq.stateChanged.connect(self._recalculate_conditioning)
        c_layout.addWidget(self.chk_iq)

        self.chk_norm = QCheckBox("Normalize Power (RMS = 1.0)")
        self.chk_norm.setChecked(True)
        self.chk_norm.stateChanged.connect(self._recalculate_conditioning)
        c_layout.addWidget(self.chk_norm)

        c_layout.addStretch()

        self.btn_reset = QPushButton("Reset Conditioning")
        self.btn_reset.setStyleSheet(
            f"background-color: {ScientificPalette.BG_CARD}; color: {ScientificPalette.TEXT_PRIMARY}; border: 1px solid {ScientificPalette.BORDER_SUBTLE}; border-radius: 3px; padding: 4px 10px;"
        )
        self.btn_reset.clicked.connect(self._on_reset)
        c_layout.addWidget(self.btn_reset)

        layout.addWidget(control_bar)

        # Main Splitter: Upper Plots vs Lower Burst Table
        splitter = QSplitter(Qt.Orientation.Vertical)
        splitter.setChildrenCollapsible(False)

        # Plot Row: Time Waveform + Spectral Zoom
        plots_splitter = QSplitter(Qt.Orientation.Horizontal)
        plots_splitter.setChildrenCollapsible(False)

        self.waveform_plot = WaveformPlotWidget(self)
        plots_splitter.addWidget(self.waveform_plot)

        self.spectrum_plot = SpectrumPlotWidget(self)
        plots_splitter.addWidget(self.spectrum_plot)

        splitter.addWidget(plots_splitter)

        # Lower Container: Detected Signal Bursts Table
        burst_container = QFrame()
        burst_container.setStyleSheet(
            f"background-color: {ScientificPalette.BG_SURFACE}; border: 1px solid {ScientificPalette.BORDER_SUBTLE}; border-radius: 4px;"
        )
        b_layout = QVBoxLayout(burst_container)
        b_layout.setContentsMargins(10, 8, 10, 8)
        b_layout.setSpacing(6)

        b_header = QLabel("DETECTED SIGNAL BURSTS & ENERGY REGIONS")
        b_header.setFont(get_ui_font(9, get_ui_font().weight().Bold))
        b_header.setStyleSheet(f"color: {ScientificPalette.TEXT_MUTED}; letter-spacing: 1px;")
        b_layout.addWidget(b_header)

        self.burst_table = QTableWidget(0, 6)
        self.burst_table.setHorizontalHeaderLabels(
            ["BURST #", "START (s)", "DURATION (ms)", "CENTER FREQ", "OBW (99%)", "SNR (dB)"]
        )
        self.burst_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.burst_table.verticalHeader().setVisible(False)
        self.burst_table.setFont(get_monospace_font(9))
        self.burst_table.setStyleSheet(
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
                padding: 4px;
                font-size: 9px;
            }}
            """
        )
        b_layout.addWidget(self.burst_table)
        splitter.addWidget(burst_container)

        splitter.setSizes([450, 220])
        layout.addWidget(splitter)

    def set_signal_buffer(self, buffer: SignalBuffer) -> None:
        """Load signal buffer into the conditioning view."""
        self._raw_buffer = buffer
        self._recalculate_conditioning()

    def set_segments(self, segments: list[SignalSegment]) -> None:
        """Populate the detected signal bursts table."""
        self.burst_table.setRowCount(len(segments))
        for row, seg in enumerate(segments):
            dur_ms = seg.duration_s * 1000.0
            fc_str = (
                f"{seg.center_frequency_hz / 1e6:.3f} MHz"
                if seg.center_frequency_hz
                else "Baseband"
            )
            bw_str = f"{seg.bandwidth_hz / 1e3:.1f} kHz" if seg.bandwidth_hz else "--"
            snr_str = f"{seg.snr_db:.1f}" if seg.snr_db is not None else "--"

            items = [
                QTableWidgetItem(f"Burst #{row + 1}"),
                QTableWidgetItem(f"{seg.start_time_s:.4f}"),
                QTableWidgetItem(f"{dur_ms:.2f}"),
                QTableWidgetItem(fc_str),
                QTableWidgetItem(bw_str),
                QTableWidgetItem(snr_str),
            ]
            for col, item in enumerate(items):
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.burst_table.setItem(row, col, item)

    def _recalculate_conditioning(self) -> None:
        if self._raw_buffer is None:
            return

        buf = self._raw_buffer
        if self.chk_dc.isChecked():
            buf = remove_dc_offset(buf)
        if self.chk_iq.isChecked():
            buf = correct_iq_imbalance(buf)
        if self.chk_norm.isChecked():
            buf = normalize_amplitude(buf)

        self._current_buffer = buf
        self.waveform_plot.set_signal(buf)
        self.spectrum_plot.set_signal(buf)
        self.conditioning_applied.emit(buf)

    def _on_reset(self) -> None:
        self.chk_dc.setChecked(True)
        self.chk_iq.setChecked(True)
        self.chk_norm.setChecked(True)
        self._recalculate_conditioning()
