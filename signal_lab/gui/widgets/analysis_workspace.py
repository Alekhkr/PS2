"""Analysis Workspace widget hosting synchronized PyQtGraph instruments and parameter inspector."""

from __future__ import annotations

import numpy as np
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from signal_lab.domain.models.evidence import ModulationCandidate, ParameterEvidence
from signal_lab.domain.models.signal import SignalBuffer, SignalSegment
from signal_lab.gui.plots.constellation_plot import ConstellationPlotWidget
from signal_lab.gui.plots.spectrum_plot import SpectrumPlotWidget
from signal_lab.gui.plots.waterfall_plot import WaterfallPlotWidget
from signal_lab.gui.plots.waveform_plot import WaveformPlotWidget
from signal_lab.gui.theme import ScientificPalette, get_monospace_font, get_ui_font
from signal_lab.gui.widgets.bitstream_viewer import BitstreamViewer
from signal_lab.gui.widgets.signal_profile import SignalProfileWidget


class AnalysisWorkspaceWidget(QWidget):
    """Primary scientific instrument workspace displaying synchronized plots and telemetry."""

    segment_selected = Signal(SignalSegment)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._full_buffer: SignalBuffer | None = None
        self._current_segment: SignalSegment | None = None
        self._latest_candidate: ModulationCandidate | None = None
        self._init_ui()

    def _init_ui(self) -> None:
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(6, 6, 6, 6)
        main_layout.setSpacing(6)

        # Main Horizontal Splitter (Left Sidebar vs Center/Right Instrument Surface)
        self.main_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.main_splitter.setChildrenCollapsible(False)

        # Left Sidebar: Segments & Measured Parameters
        self.sidebar = self._create_sidebar()
        self.main_splitter.addWidget(self.sidebar)

        # Center/Right Container: Waterfall (top) -> Spectrum (middle) -> Synchronized Row (bottom)
        self.center_right_splitter = QSplitter(Qt.Orientation.Vertical)
        self.center_right_splitter.setChildrenCollapsible(False)

        # 1. Main Canvas: WATERFALL Surface
        self.waterfall_plot = WaterfallPlotWidget(self)
        self.waterfall_plot.region_selected.connect(self._on_waterfall_region_changed)
        self.center_right_splitter.addWidget(self.waterfall_plot)

        # 2. Below Canvas: SPECTRUM (Power Spectral Density / FFT)
        self.spectrum_plot = SpectrumPlotWidget(self)
        self.center_right_splitter.addWidget(self.spectrum_plot)

        # 3. Synchronized Analysis Row: TIME | CONSTELLATION | SIGNAL PROFILE
        self.sync_analysis_row = QSplitter(Qt.Orientation.Horizontal)
        self.sync_analysis_row.setChildrenCollapsible(False)

        # TIME (Waveform)
        self.waveform_plot = WaveformPlotWidget(self)
        self.sync_analysis_row.addWidget(self.waveform_plot)

        # CONSTELLATION
        self.constellation_plot = ConstellationPlotWidget(self)
        self.sync_analysis_row.addWidget(self.constellation_plot)

        # SIGNAL PROFILE
        self.signal_profile = SignalProfileWidget(self)
        self.mod_name_lbl = self.signal_profile.mod_val
        self.mod_confidence_lbl = self.signal_profile.confidence_badge
        self.evidence_list = self.signal_profile.evidence_label
        self.sync_analysis_row.addWidget(self.signal_profile)

        self.center_right_splitter.addWidget(self.sync_analysis_row)
        self.main_splitter.addWidget(self.center_right_splitter)

        # Splitter proportion ratios
        self.main_splitter.setSizes([260, 1060])
        self.center_right_splitter.setSizes([280, 240, 260])
        self.sync_analysis_row.setSizes([380, 340, 340])

        main_layout.addWidget(self.main_splitter)

    def _create_sidebar(self) -> QWidget:
        container = QFrame()
        container.setFrameShape(QFrame.Shape.StyledPanel)
        container.setStyleSheet(
            f"background-color: {ScientificPalette.BG_SURFACE}; border: 1px solid {ScientificPalette.BORDER_SUBTLE}; border-radius: 4px;"
        )
        layout = QVBoxLayout(container)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # Tabs in sidebar: DETECTED SIGNALS vs PARAMETERS vs BITS
        self.sidebar_tabs = QTabWidget()
        self.sidebar_tabs.setStyleSheet(
            f"""
            QTabWidget::pane {{
                border: 1px solid {ScientificPalette.BORDER_SUBTLE};
                background: {ScientificPalette.BG_BASE};
            }}
            QTabBar::tab {{
                background: {ScientificPalette.BG_SURFACE};
                color: {ScientificPalette.TEXT_MUTED};
                padding: 5px 10px;
                font-family: 'Inter', sans-serif;
                font-weight: 600;
                font-size: 10px;
            }}
            QTabBar::tab:selected {{
                background: {ScientificPalette.BG_CARD};
                color: {ScientificPalette.ACCENT_CYAN};
                border-bottom: 2px solid {ScientificPalette.ACCENT_CYAN};
            }}
            """
        )

        # Tab 1: Signals & Parameters
        signals_widget = QWidget()
        sig_layout = QVBoxLayout(signals_widget)
        sig_layout.setContentsMargins(6, 6, 6, 6)
        sig_layout.setSpacing(8)

        seg_header = QLabel("DETECTED BURSTS")
        seg_header.setFont(get_ui_font(9, get_ui_font().weight().Bold))
        seg_header.setStyleSheet(f"color: {ScientificPalette.TEXT_MUTED}; letter-spacing: 1px;")
        sig_layout.addWidget(seg_header)

        self.segments_list = QListWidget()
        self.segments_list.setStyleSheet(
            f"""
            QListWidget {{
                background-color: {ScientificPalette.BG_BASE};
                border: 1px solid {ScientificPalette.BORDER_SUBTLE};
                border-radius: 3px;
                color: {ScientificPalette.TEXT_PRIMARY};
            }}
            QListWidget::item {{
                padding: 5px 8px;
                border-bottom: 1px solid {ScientificPalette.BORDER_SUBTLE};
            }}
            QListWidget::item:selected {{
                background-color: {ScientificPalette.BG_CARD};
                color: {ScientificPalette.ACCENT_CYAN};
            }}
            """
        )
        self.segments_list.itemClicked.connect(self._on_segment_item_clicked)
        sig_layout.addWidget(self.segments_list, 1)

        param_header = QLabel("MEASURED PARAMETERS")
        param_header.setFont(get_ui_font(9, get_ui_font().weight().Bold))
        param_header.setStyleSheet(f"color: {ScientificPalette.TEXT_MUTED}; letter-spacing: 1px;")
        sig_layout.addWidget(param_header)

        self.param_table = QTableWidget(0, 3)
        self.param_table.setHorizontalHeaderLabels(["PARAM", "VALUE", "CONF"])
        self.param_table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.ResizeToContents
        )
        self.param_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.param_table.horizontalHeader().setSectionResizeMode(
            2, QHeaderView.ResizeMode.ResizeToContents
        )
        self.param_table.verticalHeader().setVisible(False)
        self.param_table.setFont(get_monospace_font(9))
        self.param_table.setStyleSheet(
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
        sig_layout.addWidget(self.param_table, 2)
        self.sidebar_tabs.addTab(signals_widget, "Telemetry")

        # Tab 2: Bitstream & Frames
        self.bitstream_viewer = BitstreamViewer(self)
        self.bitstream_viewer.time_navigated.connect(self._on_bitstream_time_navigated)
        self.sidebar_tabs.addTab(self.bitstream_viewer, "Bitstream")

        layout.addWidget(self.sidebar_tabs)
        return container

    def _on_bitstream_time_navigated(self, timestamp_s: float) -> None:
        """Center the waterfall time selection on the clicked bit's physical timestamp."""
        if not self._full_buffer or not self._full_buffer.sample_rate_hz:
            return
        span_s = 0.005
        start_s = max(0.0, timestamp_s - span_s / 2)
        end_s = start_s + span_s
        self.waterfall_plot.set_region(start_s, end_s)

    def set_demodulated_bits(
        self,
        bits: np.ndarray,
        sps: int = 4,
        bits_per_symbol: int = 2,
    ) -> None:
        """Forward demodulated bits to the bitstream inspector and update sync status."""
        fs = (
            self._full_buffer.sample_rate_hz
            if self._full_buffer and self._full_buffer.sample_rate_hz
            else 1.0
        )
        self.bitstream_viewer.set_bitstream(
            bits, sample_rate_hz=fs, sps=sps, bits_per_symbol=bits_per_symbol
        )
        self.signal_profile.update_profile(sync_locked=True)

    def set_signal_buffer(self, buffer: SignalBuffer) -> None:
        """Load a full signal capture into all synchronized instruments."""
        self._full_buffer = buffer
        self.waterfall_plot.set_signal(buffer)
        self.waveform_plot.set_signal(buffer)
        self.spectrum_plot.set_signal(buffer)
        self.constellation_plot.set_signal(buffer)
        self.signal_profile.reset_profile()

    def _on_waterfall_region_changed(self, start_time_s: float, end_time_s: float) -> None:
        """Synchronize waveform, spectrum, constellation, and inspector upon region selection."""
        if not self._full_buffer or not self._full_buffer.sample_rate_hz:
            return

        fs = self._full_buffer.sample_rate_hz
        start_idx = max(0, int(start_time_s * fs))
        end_idx = min(self._full_buffer.num_samples, int(end_time_s * fs))

        if end_idx - start_idx < 16:
            return

        sub_buffer = self._full_buffer.slice(start_idx, end_idx)

        # Synchronize plots
        self.waveform_plot.set_signal(sub_buffer)
        self.spectrum_plot.set_signal(sub_buffer)
        self.constellation_plot.set_signal(sub_buffer)

        # Create active SignalSegment
        segment = SignalSegment(
            start_sample=start_idx,
            end_sample=end_idx,
            start_time_s=start_time_s,
            duration_s=end_time_s - start_time_s,
            center_frequency_hz=self._full_buffer.center_frequency_hz,
        )
        self._current_segment = segment
        self.segment_selected.emit(segment)

    def set_segments(self, segments: list[SignalSegment]) -> None:
        """Populate the sidebar with detected signal regions."""
        self.segments_list.clear()
        for idx, seg in enumerate(segments):
            dur_ms = seg.duration_s * 1000.0
            fc_mhz = (seg.center_frequency_hz / 1e6) if seg.center_frequency_hz else 0.0
            item = QListWidgetItem(f"Burst #{idx + 1}: {dur_ms:.1f}ms @ {fc_mhz:.3f}MHz")
            item.setData(Qt.ItemDataRole.UserRole, seg)
            item.setFont(get_monospace_font(9))
            self.segments_list.addItem(item)

    def _on_segment_item_clicked(self, item: QListWidgetItem) -> None:
        """Center the waterfall region on the selected segment."""
        seg: SignalSegment = item.data(Qt.ItemDataRole.UserRole)
        if seg:
            self.waterfall_plot.region.setRegion(
                [seg.start_time_s, seg.start_time_s + seg.duration_s]
            )

    def set_parameters(self, evidence_list: list[ParameterEvidence]) -> None:
        """Update measured parameters table and signal profile panel."""
        self.param_table.setRowCount(len(evidence_list))
        carrier_hz: float | None = None
        baud_hz: float | None = None
        obw_hz: float | None = None
        snr_db: float | None = None
        conf: float | None = None

        for row, ev in enumerate(evidence_list):
            unit_str = f" {ev.unit}" if ev.unit else ""
            val_str = f"{ev.value}{unit_str}"
            conf_str = f"{int(ev.confidence * 100)}%"

            item_name = QTableWidgetItem(ev.name)
            item_val = QTableWidgetItem(val_str)
            item_conf = QTableWidgetItem(conf_str)

            item_name.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            item_val.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            item_conf.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

            self.param_table.setItem(row, 0, item_name)
            self.param_table.setItem(row, 1, item_val)
            self.param_table.setItem(row, 2, item_conf)

            # Extract metrics for SignalProfile
            n = ev.name.lower()
            try:
                v = (
                    float(ev.value)
                    if isinstance(ev.value, (int, float))
                    else float(str(ev.value).split()[0])
                )
                if "carrier" in n or "cfo" in n:
                    carrier_hz = v
                elif "symbol" in n or "baud" in n:
                    baud_hz = v
                elif "bandwidth" in n or "obw" in n:
                    obw_hz = v
                elif "snr" in n:
                    snr_db = v
                if ev.confidence:
                    conf = max(conf or 0.0, ev.confidence)
            except (ValueError, IndexError):
                pass

        self.signal_profile.update_profile(
            carrier_offset_hz=carrier_hz,
            symbol_rate_hz=baud_hz,
            bandwidth_hz=obw_hz,
            snr_db=snr_db,
            confidence=conf,
        )

    def set_modulation_candidate(self, candidate: ModulationCandidate | None) -> None:
        """Update inspector candidate and evidence breakdown in SignalProfile."""
        self._latest_candidate = candidate
        if not candidate:
            return

        self.signal_profile.update_profile(
            modulation=candidate.name,
            confidence=candidate.score,
            evidence_notes=candidate.evidence,
        )
