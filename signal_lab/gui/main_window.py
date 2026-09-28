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
from signal_lab.domain.models.signal import SignalSegment
from signal_lab.gui.theme import DARK_SCIENTIFIC_QSS
from signal_lab.gui.widgets.analysis_workspace import AnalysisWorkspaceWidget
from signal_lab.gui.widgets.dossier_dialog import ScientificDossierDialog
from signal_lab.gui.widgets.drop_zone import DropZoneWidget
from signal_lab.gui.widgets.header_bar import HeaderBar
from signal_lab.gui.widgets.pipeline_status import PipelineStatusWidget
from signal_lab.services.orchestrator import AnalysisOrchestrator
from signal_lab.services.report_service import ReportService
from signal_lab.services.session_service import SessionService


class MainWindow(QMainWindow):
    """Primary application window implementing the Awwwards dark scientific instrument UI."""

    def __init__(self, session_service: SessionService, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.session_service = session_service
        self.orchestrator = AnalysisOrchestrator(repository=session_service.repository)
        self.report_service = ReportService(repository=session_service.repository)

        self.setWindowTitle("Signal Lab — Automated IQ/WAV Signal Analysis Platform")
        self.resize(1360, 860)
        self.setMinimumSize(1024, 680)
        self.setStyleSheet(DARK_SCIENTIFIC_QSS)

        self._active_session: Session | None = None
        self._init_ui()
        self._wire_orchestrator()
        self._refresh_recent_sessions()

    def _init_ui(self) -> None:
        central = QWidget(self)
        self.setCentralWidget(central)
        root_layout = QVBoxLayout(central)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # Top Header Bar
        self.header_bar = HeaderBar(self)
        self.header_bar.new_session_requested.connect(self._on_new_session)
        root_layout.addWidget(self.header_bar)

        # Central View Stack (0: DropZone/Home, 1: Analysis Workspace)
        self.view_stack = QStackedWidget(self)

        self.drop_zone = DropZoneWidget(self)
        self.drop_zone.file_selected.connect(self._on_file_selected)
        self.drop_zone.session_opened.connect(self._on_session_opened)
        self.view_stack.addWidget(self.drop_zone)

        self.analysis_workspace = AnalysisWorkspaceWidget(self)
        self.view_stack.addWidget(self.analysis_workspace)

        root_layout.addWidget(self.view_stack, 1)

        # Bottom Pipeline Breadcrumb Bar
        self.pipeline_status = PipelineStatusWidget(self)
        root_layout.addWidget(self.pipeline_status)

    def _wire_orchestrator(self) -> None:
        """Connect asynchronous orchestrator signals to UI status and widgets."""
        self.orchestrator.progress_updated.connect(self._on_progress_updated)
        self.orchestrator.stage_completed.connect(self.pipeline_status.set_stage_status)
        self.orchestrator.demodulation_completed.connect(self._on_demodulation_completed)
        self.orchestrator.analysis_completed.connect(self._on_analysis_completed)
        self.orchestrator.analysis_failed.connect(self._on_analysis_failed)

    def _refresh_recent_sessions(self) -> None:
        """Fetch and populate recent sessions list in drop zone."""
        recent = self.session_service.list_recent_sessions(limit=10)
        self.drop_zone.populate_recent_sessions(recent)

    @Slot()
    def _on_new_session(self) -> None:
        """Switch back to drop zone for new capture."""
        self.orchestrator.cancel_current()
        self._active_session = None
        self.header_bar.set_capture_info("NO CAPTURE LOADED", None, None)
        self.header_bar.set_job_status("IDLE", 0.0)
        self.pipeline_status.reset_all()
        self._refresh_recent_sessions()
        self.view_stack.setCurrentIndex(0)

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

    def _open_session(self, session: Session, buffer: Any | None = None) -> None:
        """Transition into Analysis Workspace with loaded session and kick off processing."""
        self._active_session = session
        file_name = Path(session.input_file_path).name if session.input_file_path else "Unspecified"
        self.header_bar.set_capture_info(
            file_name,
            session.sample_rate_hz,
            session.center_frequency_hz,
        )
        self.header_bar.set_job_status("READY", 0.0)

        if buffer is not None:
            self.analysis_workspace.set_signal_buffer(buffer)
            self.pipeline_status.reset_all()
            self.orchestrator.start_analysis(session, buffer)

        self.view_stack.setCurrentIndex(1)

    @Slot(str, float, str)
    def _on_progress_updated(self, stage: str, pct: float, msg: str) -> None:
        self.header_bar.set_job_status(msg, pct)

    @Slot(object)
    def _on_demodulation_completed(self, demod_res: Any) -> None:
        if demod_res and hasattr(demod_res, "hard_bits"):
            self.analysis_workspace.set_demodulated_bits(demod_res.hard_bits)

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
        self.header_bar.set_job_status("COMPLETE", 1.0)

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
        else:
            super().keyPressEvent(event)

