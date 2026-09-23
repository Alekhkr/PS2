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


class AnalysisWorkspaceWidget(QWidget):
    """Primary scientific instrument workspace displaying synchronized plots and telemetry."""

    segment_selected = Signal(SignalSegment)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._full_buffer: SignalBuffer | None = None
        self._current_segment: SignalSegment | None = None
        self._init_ui()

    def _init_ui(self) -> None:
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(8)

        # Main Horizontal Splitter (Left Sidebar vs Center/Right Instrument Surface)
        self.main_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.main_splitter.setChildrenCollapsible(False)

        # Left Sidebar: Segments & Measured Parameters
        self.sidebar = self._create_sidebar()
        self.main_splitter.addWidget(self.sidebar)

        # Center/Right Container: Plots + Inspector Splitter
        self.center_right_splitter = QSplitter(Qt.Orientation.Vertical)
        self.center_right_splitter.setChildrenCollapsible(False)

        # Top Center: Waterfall Surface
        self.waterfall_plot = WaterfallPlotWidget(self)
        self.waterfall_plot.region_selected.connect(self._on_waterfall_region_changed)
        self.center_right_splitter.addWidget(self.waterfall_plot)

        # Middle Center Splitter: Time Waveform & Power Spectral Density
        self.mid_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.mid_splitter.setChildrenCollapsible(False)

        self.waveform_plot = WaveformPlotWidget(self)
        self.mid_splitter.addWidget(self.waveform_plot)

        self.spectrum_plot = SpectrumPlotWidget(self)
        self.mid_splitter.addWidget(self.spectrum_plot)

        self.center_right_splitter.addWidget(self.mid_splitter)

        # Bottom Splitter: Constellation vs Signal Inspector
        self.bottom_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.bottom_splitter.setChildrenCollapsible(False)

        self.constellation_plot = ConstellationPlotWidget(self)
        self.bottom_splitter.addWidget(self.constellation_plot)

        self.inspector_panel = self._create_inspector_panel()
        self.bottom_splitter.addWidget(self.inspector_panel)

        self.center_right_splitter.addWidget(self.bottom_splitter)
        self.main_splitter.addWidget(self.center_right_splitter)

        # Splitter proportion ratios
        self.main_splitter.setSizes([260, 1020])
        self.center_right_splitter.setSizes([320, 240, 260])
        self.mid_splitter.setSizes([500, 500])
        self.bottom_splitter.setSizes([450, 450])

        main_layout.addWidget(self.main_splitter)

    def _create_sidebar(self) -> QWidget:
        container = QFrame()
        container.setFrameShape(QFrame.Shape.StyledPanel)
        container.setStyleSheet(
            f"background-color: {ScientificPalette.BG_SURFACE}; border-radius: 4px;"
        )
        layout = QVBoxLayout(container)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)

        # Segments Section
        seg_header = QLabel("DETECTED SIGNALS")
        seg_header.setFont(get_ui_font(9, get_ui_font().weight().Bold))
        seg_header.setStyleSheet(f"color: {ScientificPalette.TEXT_MUTED}; letter-spacing: 1px;")
        layout.addWidget(seg_header)

        self.segments_list = QListWidget()
        self.segments_list.setStyleSheet(
            f"""
            QListWidget {{
                background-color: {ScientificPalette.BG_BASE};
                border: 1px solid {ScientificPalette.BORDER_SUBTLE};
                border-radius: 4px;
            }}
            QListWidget::item {{
                padding: 6px 8px;
                border-bottom: 1px solid {ScientificPalette.BORDER_SUBTLE};
            }}
            """
        )
        self.segments_list.itemClicked.connect(self._on_segment_item_clicked)
        layout.addWidget(self.segments_list, 1)

        # Measured Parameters Table
        param_header = QLabel("ESTIMATED PARAMETERS")
        param_header.setFont(get_ui_font(9, get_ui_font().weight().Bold))
        param_header.setStyleSheet(f"color: {ScientificPalette.TEXT_MUTED}; letter-spacing: 1px;")
        layout.addWidget(param_header)

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
        layout.addWidget(self.param_table, 2)

        return container

    def _create_inspector_panel(self) -> QWidget:
        container = QFrame()
        container.setFrameShape(QFrame.Shape.StyledPanel)
        container.setStyleSheet(
            f"background-color: {ScientificPalette.BG_SURFACE}; border-radius: 4px;"
        )
        layout = QVBoxLayout(container)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(6)

        # Tabs for Evidence vs Bitstream
        self.inspector_tabs = QTabWidget()
        self.inspector_tabs.setStyleSheet(
            f"""
            QTabWidget::pane {{
                border: 1px solid {ScientificPalette.BORDER_SUBTLE};
                background: {ScientificPalette.BG_BASE};
            }}
            QTabBar::tab {{
                background: {ScientificPalette.BG_SURFACE};
                color: {ScientificPalette.TEXT_SECONDARY};
                padding: 6px 12px;
                font-family: 'Inter', sans-serif;
                font-weight: bold;
                font-size: 11px;
            }}
            QTabBar::tab:selected {{
                background: {ScientificPalette.BG_CARD};
                color: {ScientificPalette.ACCENT_CYAN};
                border-bottom: 2px solid {ScientificPalette.ACCENT_CYAN};
            }}
            """
        )

        # Tab 1: Modulation & Evidence
        tab_evidence = QWidget()
        ev_layout = QVBoxLayout(tab_evidence)
        ev_layout.setContentsMargins(8, 8, 8, 8)
        ev_layout.setSpacing(8)

        self.candidate_box = QFrame()
        self.candidate_box.setStyleSheet(
            f"background-color: {ScientificPalette.BG_CARD}; border: 1px solid {ScientificPalette.BORDER_SUBTLE}; border-radius: 4px; padding: 6px;"
        )
        cand_layout = QVBoxLayout(self.candidate_box)
        cand_layout.setContentsMargins(8, 8, 8, 8)
        cand_layout.setSpacing(4)

        self.mod_name_lbl = QLabel("MODULATION: PENDING")
        self.mod_name_lbl.setFont(get_monospace_font(12, get_monospace_font().weight().Bold))
        self.mod_name_lbl.setStyleSheet(f"color: {ScientificPalette.TEXT_PRIMARY};")
        cand_layout.addWidget(self.mod_name_lbl)

        self.mod_confidence_lbl = QLabel("Confidence: --%")
        self.mod_confidence_lbl.setFont(get_monospace_font(10))
        self.mod_confidence_lbl.setStyleSheet(f"color: {ScientificPalette.TEXT_SECONDARY};")
        cand_layout.addWidget(self.mod_confidence_lbl)

        self.evidence_list = QLabel("No active signal segment selected.")
        self.evidence_list.setFont(get_monospace_font(9))
        self.evidence_list.setStyleSheet(f"color: {ScientificPalette.TEXT_MUTED};")
        self.evidence_list.setWordWrap(True)
        cand_layout.addWidget(self.evidence_list)

        ev_layout.addWidget(self.candidate_box)
        ev_layout.addStretch()

        self.inspector_tabs.addTab(tab_evidence, "Modulation & Evidence")

        # Tab 2: Bitstream & Frames
        self.bitstream_viewer = BitstreamViewer(self)
        self.bitstream_viewer.time_navigated.connect(self._on_bitstream_time_navigated)
        self.inspector_tabs.addTab(self.bitstream_viewer, "Bitstream & Frames")

        layout.addWidget(self.inspector_tabs)
        return container

    def _on_bitstream_time_navigated(self, timestamp_s: float) -> None:
        """Center the waterfall time selection on the clicked bit's physical timestamp."""
        if not self._full_buffer or not self._full_buffer.sample_rate_hz:
            return
        span_s = 0.005  # 5 ms window
        start_s = max(0.0, timestamp_s - span_s / 2)
        end_s = start_s + span_s
        self.waterfall_plot.set_region(start_s, end_s)

    def set_demodulated_bits(
        self,
        bits: np.ndarray,
        sps: int = 4,
        bits_per_symbol: int = 2,
    ) -> None:
        """Forward demodulated bits to the bitstream inspector."""
        fs = self._full_buffer.sample_rate_hz if self._full_buffer and self._full_buffer.sample_rate_hz else 1.0
        self.bitstream_viewer.set_bitstream(
            bits, sample_rate_hz=fs, sps=sps, bits_per_symbol=bits_per_symbol
        )

    def set_signal_buffer(self, buffer: SignalBuffer) -> None:
        """Load a full signal capture into all synchronized instruments."""
        self._full_buffer = buffer
        self.waterfall_plot.set_signal(buffer)
        self.waveform_plot.set_signal(buffer)
        self.spectrum_plot.set_signal(buffer)
        self.constellation_plot.set_signal(buffer)

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
            item = QListWidgetItem(f"Seg #{idx + 1}: {dur_ms:.1f}ms @ {fc_mhz:.3f}MHz")
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
        """Update measured parameters table."""
        self.param_table.setRowCount(len(evidence_list))
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

    def set_modulation_candidate(self, candidate: ModulationCandidate | None) -> None:
        """Update inspector candidate and evidence breakdown."""
        if not candidate:
            self.mod_name_lbl.setText("MODULATION: UNKNOWN")
            self.mod_confidence_lbl.setText("Confidence: --")
            self.evidence_list.setText("No evidence recorded.")
            return

        self.mod_name_lbl.setText(f"MODULATION: {candidate.name}")
        self.mod_confidence_lbl.setText(
            f"Confidence: {int(candidate.score * 100)}% ({candidate.validation})"
        )
        if candidate.evidence:
            ev_str = "Supporting Evidence:\n" + "\n".join(
                f"• {item}" for item in candidate.evidence
            )
        else:
            ev_str = f"Algorithm: {candidate.algorithm}"
        self.evidence_list.setText(ev_str)
