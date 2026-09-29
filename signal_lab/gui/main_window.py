"""Main Window implementation for Signal Lab desktop platform."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from PySide6.QtCore import Qt, Slot
from PySide6.QtWidgets import (
    QFileDialog,
    QMainWindow,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from signal_lab.domain.models.evidence import ModulationCandidate, ParameterEvidence
from signal_lab.domain.models.session import Session
from signal_lab.domain.models.signal import SignalBuffer, SignalSegment
from signal_lab.gui.theme import DARK_SCIENTIFIC_QSS
from signal_lab.gui.widgets.analysis_workspace import AnalysisWorkspaceWidget
from signal_lab.gui.widgets.bitstream_viewer import BitstreamViewer
from signal_lab.gui.widgets.demod_view import DemodViewWidget
from signal_lab.gui.widgets.dossier_dialog import ScientificDossierDialog
from signal_lab.gui.widgets.drop_zone import DropZoneWidget
from signal_lab.gui.widgets.evidence_view import EvidenceViewWidget
from signal_lab.gui.widgets.header_bar import HeaderBar
from signal_lab.gui.widgets.navigation_bar import NavigationBar
from signal_lab.gui.widgets.pipeline_status import PipelineStatusWidget
from signal_lab.gui.widgets.report_view import ReportViewWidget
from signal_lab.gui.widgets.signal_view import SignalViewWidget
from signal_lab.services.orchestrator import AnalysisOrchestrator
from signal_lab.services.report_service import ReportService
from signal_lab.services.session_service import SessionService


class MainWindow(QMainWindow):
    """Primary scientific instrument application window."""

    def __init__(self, session_service: SessionService, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.session_service = session_service
        self.orchestrator = AnalysisOrchestrator(repository=session_service.repository)
        self.report_service = ReportService(repository=session_service.repository)

        self.setWindowTitle("Signal Lab — Automated IQ/WAV Signal Analysis Platform")
        self.resize(1380, 880)
        self.setMinimumSize(1024, 700)
        self.setStyleSheet(DARK_SCIENTIFIC_QSS)

        self._active_session: Session | None = None
        self._active_buffer: SignalBuffer | None = None
        self._init_ui()
        self._wire_signals()
        self._refresh_recent_sessions()

    def _init_ui(self) -> None:
        central = QWidget(self)
        self.setCentralWidget(central)
        root_layout = QVBoxLayout(central)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # 1. Top Telemetry Header Bar
        self.header_bar = HeaderBar(self)
        root_layout.addWidget(self.header_bar)

        # 2. Primary 7-Tab Navigation Bar (OVERVIEW, ANALYSIS, SIGNAL, DEMOD, BITS, EVIDENCE, REPORT)
        self.nav_bar = NavigationBar(self)
        root_layout.addWidget(self.nav_bar)

        # 3. Central Multi-View Stack (7 Pages)
        self.view_stack = QStackedWidget(self)

        # Page 0: OVERVIEW (DropZone / Presets / History)
        self.drop_zone = DropZoneWidget(self)
        self.view_stack.addWidget(self.drop_zone)

        # Page 1: ANALYSIS (Main Waterfall + Spectrum + Synced Time/Constellation/Profile)
        self.analysis_workspace = AnalysisWorkspaceWidget(self)
        self.view_stack.addWidget(self.analysis_workspace)

        # Page 2: SIGNAL (Signal Conditioning + Burst Energy Table)
        self.signal_view = SignalViewWidget(self)
        self.view_stack.addWidget(self.signal_view)

        # Page 3: DEMOD (Constellation Decision Boundaries + Sync Error Curves)
        self.demod_view = DemodViewWidget(self)
        self.view_stack.addWidget(self.demod_view)

        # Page 4: BITS (Full-page Bitstream & Frame Inspector)
        self.bits_view = BitstreamViewer(self)
        self.view_stack.addWidget(self.bits_view)

        # Page 5: EVIDENCE (Full-page Algorithmic Provenance & Evidence Table)
        self.evidence_view = EvidenceViewWidget(self)
        self.view_stack.addWidget(self.evidence_view)

        # Page 6: REPORT (Technical Audit Dossier & Export)
        self.report_view = ReportViewWidget(self)
        self.view_stack.addWidget(self.report_view)

        root_layout.addWidget(self.view_stack, 1)

        # 4. Bottom Pipeline Breadcrumb Bar
        self.pipeline_status = PipelineStatusWidget(self)
        root_layout.addWidget(self.pipeline_status)

    def _wire_signals(self) -> None:
        """Connect all widgets, navigation, orchestrator, and data flows."""
        # Navigation
        self.nav_bar.tab_changed.connect(self._on_nav_tab_changed)
        self.pipeline_status.stage_clicked.connect(self._on_pipeline_stage_clicked)

        # Header bar
        self.header_bar.new_session_requested.connect(self._on_new_session)
        self.header_bar.auto_analyze_requested.connect(self._on_auto_analyze_clicked)
        self.header_bar.export_report_requested.connect(self.export_report_dialog)

        # Drop zone
        self.drop_zone.file_selected.connect(self._on_file_selected)
        self.drop_zone.session_opened.connect(self._on_session_opened)

        # Orchestrator pipeline
        self.orchestrator.progress_updated.connect(self._on_progress_updated)
        self.orchestrator.stage_completed.connect(self.pipeline_status.set_stage_status)
        self.orchestrator.demodulation_completed.connect(self._on_demodulation_completed)
        self.orchestrator.analysis_completed.connect(self._on_analysis_completed)
        self.orchestrator.analysis_failed.connect(self._on_analysis_failed)

        # Click-to-time navigation from full-page bits view
        self.bits_view.time_navigated.connect(self.analysis_workspace._on_bitstream_time_navigated)

    def _refresh_recent_sessions(self) -> None:
        """Fetch and populate recent sessions list in drop zone."""
        recent = self.session_service.list_recent_sessions(limit=10)
        self.drop_zone.populate_recent_sessions(recent)

    @Slot(str, int)
    def _on_nav_tab_changed(self, tab_name: str, index: int) -> None:
        """Switch active page in view stack."""
        self.view_stack.setCurrentIndex(index)

    @Slot(str)
    def _on_pipeline_stage_clicked(self, stage_name: str) -> None:
        """Navigate to the appropriate view when a pipeline stage breadcrumb is clicked."""
        s = stage_name.lower()
        if s in ("detect", "estimate") or s == "classify":
            self.nav_bar.set_active_tab(1)  # ANALYSIS
            self.view_stack.setCurrentIndex(1)
        elif s in ("synchronize", "demodulate"):
            self.nav_bar.set_active_tab(3)  # DEMOD
            self.view_stack.setCurrentIndex(3)
        elif s in ("interleave", "fec", "correlate"):
            self.nav_bar.set_active_tab(4)  # BITS
            self.view_stack.setCurrentIndex(4)

    @Slot()
    def _on_new_session(self) -> None:
        """Switch back to drop zone / overview for new capture."""
        self.orchestrator.cancel_current()
        self._active_session = None
        self._active_buffer = None
        self.header_bar.set_session_id("SL-0000")
        self.header_bar.set_capture_info("NO CAPTURE LOADED", None, None, None, None)
        self.header_bar.set_job_status("IDLE", 0.0)
        self.pipeline_status.reset_all()
        self._refresh_recent_sessions()
        self.nav_bar.set_active_tab(0)
        self.view_stack.setCurrentIndex(0)

    @Slot()
    def _on_auto_analyze_clicked(self) -> None:
        """Trigger or restart automated analysis on current or new capture."""
        if self._active_session and self._active_buffer:
            self.pipeline_status.reset_all()
            self.header_bar.set_job_status("STARTING ANALYSIS...", 0.05)
            self.orchestrator.start_analysis(self._active_session, self._active_buffer)
            self.nav_bar.set_active_tab(1)
            self.view_stack.setCurrentIndex(1)
        else:
            path, _ = QFileDialog.getOpenFileName(
                self,
                "Select Signal Capture for Auto-Analysis",
                "",
                "All Supported (*.wav *.iq *.bin *.sigmf-meta);;WAV Captures (*.wav);;Raw IQ (*.iq *.bin);;SigMF (*.sigmf-meta)",
            )
            if path:
                self._on_file_selected(path)

    @Slot(str)
    def _on_file_selected(self, file_path_str: str) -> None:
        """Handle new file selection."""
        path = Path(file_path_str)
        try:
            from signal_lab.ingestion import load_signal_file

            buffer = load_signal_file(path)
            if buffer.sample_rate_hz is None:
                if os.environ.get("QT_QPA_PLATFORM") == "offscreen":
                    buffer.sample_rate_hz = 2_048_000.0
                else:
                    from signal_lab.gui.widgets.assumptions_dialog import AssumptionsDialog

                    dlg = AssumptionsDialog(buffer, parent=self)
                    dlg.exec()

            session = self.session_service.create_session(
                name=path.stem,
                input_file=path,
                sample_rate_hz=buffer.sample_rate_hz,
                center_frequency_hz=buffer.center_frequency_hz,
            )
            self._open_session(session, buffer=buffer)
        except (ValueError, OSError, RuntimeError) as e:
            self.header_bar.set_job_status(f"Error: {e}", 0.0)

    @Slot(str)
    def _on_session_opened(self, session_id: str) -> None:
        """Handle opening of existing session."""
        session = self.session_service.load_session(session_id)
        if session and session.input_file_path and Path(session.input_file_path).exists():
            from signal_lab.ingestion import load_signal_file

            buffer = load_signal_file(
                session.input_file_path,
                center_frequency_hz=session.center_frequency_hz,
            )
            self._open_session(session, buffer=buffer)
        elif session:
            self._open_session(session, buffer=None)

    def _open_session(self, session: Session, buffer: SignalBuffer | None = None) -> None:
        """Transition into Analysis Workspace with loaded session and kick off processing."""
        self._active_session = session
        self._active_buffer = buffer
        file_name = Path(session.input_file_path).name if session.input_file_path else "Unspecified"

        fmt_str = str(buffer.sample_format).replace("SampleFormat.", "") if buffer else "UNKNOWN"
        dur_s = buffer.duration_s if buffer else None

        self.header_bar.set_session_id(session.id)
        self.header_bar.set_capture_info(
            file_name,
            session.sample_rate_hz,
            session.center_frequency_hz,
            source_format=fmt_str,
            duration_s=dur_s,
        )
        self.header_bar.set_job_status("READY", 0.0)

        if buffer is not None:
            self.analysis_workspace.set_signal_buffer(buffer)
            self.signal_view.set_signal_buffer(buffer)
            self.demod_view.set_signal(buffer)
            self.pipeline_status.reset_all()
            self.orchestrator.start_analysis(session, buffer)

        # Switch to ANALYSIS tab
        self.nav_bar.set_active_tab(1)
        self.view_stack.setCurrentIndex(1)

    @Slot(str, float, str)
    def _on_progress_updated(self, stage: str, pct: float, msg: str) -> None:
        self.header_bar.set_job_status(msg, pct)

    @Slot(object)
    def _on_demodulation_completed(self, demod_res: Any) -> None:
        if demod_res and hasattr(demod_res, "hard_bits"):
            self.analysis_workspace.set_demodulated_bits(demod_res.hard_bits)
            self.demod_view.set_demodulation_result(demod_res)
            fs = self._active_buffer.sample_rate_hz if self._active_buffer else 1.0
            self.bits_view.set_bitstream(demod_res.hard_bits, sample_rate_hz=fs)

    @Slot(object, object, object)
    def _on_analysis_completed(
        self,
        segments: list[SignalSegment],
        evidence: list[ParameterEvidence],
        candidate: ModulationCandidate,
    ) -> None:
        self.analysis_workspace.set_segments(segments)
        self.analysis_workspace.set_parameters(evidence)
        self.analysis_workspace.set_modulation_candidate(candidate)

        self.signal_view.set_segments(segments)
        self.evidence_view.set_evidence(evidence)

        # Generate report text
        if self._active_session:
            md_text = self.report_service.generate_markdown(self._active_session.id)
            report_dict = self.report_service.generate_report_dict(self._active_session.id)
            self.report_view.set_report_content(md_text, report_dict)

        self.header_bar.set_job_status("ANALYSIS COMPLETE", 1.0)

    @Slot(str)
    def _on_analysis_failed(self, error_msg: str) -> None:
        self.header_bar.set_job_status(f"FAILED: {error_msg}", 0.0)

    def export_report_dialog(self) -> None:
        """Trigger file export dialog for session report."""
        if not self._active_session:
            return
        out_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Session Report",
            f"report_{self._active_session.name}.json",
            "JSON Report (*.json);;Markdown Report (*.md);;CSV Parameters (*.csv)",
        )
        if out_path:
            p = Path(out_path)
            if p.suffix.lower() == ".md":
                self.report_service.export_markdown(self._active_session.id, p)
            elif p.suffix.lower() == ".csv":
                self.report_service.export_csv(self._active_session.id, p)
            else:
                self.report_service.export_json(self._active_session.id, p)

    def keyPressEvent(self, event) -> None:
        if event.key() == Qt.Key.Key_D:
            dialog = ScientificDossierDialog(self)
            dialog.exec()
        elif event.key() == Qt.Key.Key_O and event.modifiers() & Qt.KeyboardModifier.ControlModifier or event.key() == Qt.Key.Key_R and event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            self._on_auto_analyze_clicked()
        else:
            super().keyPressEvent(event)
