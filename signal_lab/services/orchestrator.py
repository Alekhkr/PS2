"""Analysis Orchestrator executing the non-blocking signal processing graph."""

from __future__ import annotations

from PySide6.QtCore import QObject, QThread, Signal

from signal_lab.classification import classify_modulation
from signal_lab.correlation import (
    STANDARD_SYNC_WORDS,
    correlate_sync_word,
    detect_frame_periodicity,
)
from signal_lab.demodulation import demodulate_signal
from signal_lab.domain.enums import JobState
from signal_lab.domain.models.evidence import (
    ModulationCandidate,
    ParameterEvidence,
)
from signal_lab.domain.models.session import Session
from signal_lab.domain.models.signal import SignalBuffer, SignalSegment
from signal_lab.estimation import analyze_signal_parameters
from signal_lab.fec import evaluate_fec_hypotheses
from signal_lab.interleaving import evaluate_interleaver_hypotheses
from signal_lab.services.event_bus import (
    AnalysisCompleted,
    AnalysisFailed,
    EventBus,
    ModulationCandidateCreated,
    ParameterEstimated,
    SignalDetected,
)
from signal_lab.services.evidence_engine import EvidenceEngine
from signal_lab.storage.repository import SessionRepository


class AnalysisWorker(QObject):
    """Worker object running DSP, hypothesis testing, and evidence fusion off the GUI thread."""

    progress_updated = Signal(str, float, str)  # stage_name, progress_0_to_1, status_message
    stage_completed = Signal(str, str)  # stage_name, status ("done" / "failed")
    analysis_finished = Signal(object, object, object)  # segments, evidence, modulation_candidate
    error_occurred = Signal(str)

    def __init__(
        self,
        session: Session,
        buffer: SignalBuffer,
        repository: SessionRepository,
        event_bus: EventBus,
    ) -> None:
        super().__init__()
        self.session = session
        self.buffer = buffer
        self.repository = repository
        self.event_bus = event_bus
        self._is_cancelled = False

    def cancel(self) -> None:
        self._is_cancelled = True

    def run(self) -> None:
        try:
            self._execute_pipeline()
        except (ValueError, RuntimeError, OSError, TypeError) as e:
            self.error_occurred.emit(str(e))
            self.event_bus.publish(AnalysisFailed(session_id=self.session.id, error_message=str(e)))

    def _execute_pipeline(self) -> None:
        if self._is_cancelled:
            return

        # Stage 1: Detect
        self.progress_updated.emit("detect", 0.10, "Detecting signal regions...")
        segments, evidence_list = analyze_signal_parameters(self.buffer)
        for seg in segments:
            self.repository.save_segment(self.session.id, seg)
        for ev in evidence_list:
            self.repository.save_evidence(self.session.id, ev)

        self.event_bus.publish(
            SignalDetected(session_id=self.session.id, segment_count=len(segments))
        )
        self.stage_completed.emit("detect", "done")

        if self._is_cancelled:
            return

        # Stage 2: Estimate
        self.progress_updated.emit(
            "estimate", 0.30, "Estimating carrier, bandwidth, and baud rate..."
        )
        for ev in evidence_list:
            self.event_bus.publish(
                ParameterEstimated(
                    session_id=self.session.id,
                    parameter_name=ev.name,
                    value=ev.value,
                    confidence=ev.confidence,
                )
            )
        self.stage_completed.emit("estimate", "done")

        if self._is_cancelled:
            return

        # Stage 3: Modulation Classification
        self.progress_updated.emit("sync", 0.45, "Classifying modulation...")
        candidates = classify_modulation(self.buffer)
        top_mod = candidates[0].name if candidates else "QPSK"
        self.stage_completed.emit("sync", "done")

        if self._is_cancelled:
            return

        # Stage 4: Demodulation
        self.progress_updated.emit("demod", 0.60, f"Demodulating as {top_mod}...")
        demod_res = demodulate_signal(self.buffer, modulation=top_mod, sps=4)
        self.stage_completed.emit("demod", "done")

        if self._is_cancelled:
            return

        # Stage 5: Interleaver & FEC Hypotheses
        self.progress_updated.emit("interleave", 0.75, "Testing interleaver hypotheses...")
        _ = evaluate_interleaver_hypotheses(demod_res.hard_bits)
        self.stage_completed.emit("interleave", "done")

        self.progress_updated.emit("fec", 0.85, "Testing forward error correction hypotheses...")
        fec_cands = evaluate_fec_hypotheses(demod_res.hard_bits)
        self.stage_completed.emit("fec", "done")

        if self._is_cancelled:
            return

        # Stage 6: Correlation
        self.progress_updated.emit(
            "correlate", 0.92, "Correlating frame preambles and sync words..."
        )
        _ = correlate_sync_word(demod_res.hard_bits, STANDARD_SYNC_WORDS["Barker_13"])
        _ = detect_frame_periodicity(demod_res.hard_bits)
        self.stage_completed.emit("correlate", "done")

        # Stage 7: Evidence Aggregation
        self.progress_updated.emit("evidence", 0.98, "Aggregating multi-source evidence...")
        final_cand, final_conf, _ = EvidenceEngine.aggregate_evidence(
            parameters=evidence_list,
            modulation_candidates=candidates,
            demod_result=demod_res,
            fec_candidates=fec_cands,
        )
        self.repository.save_modulation_candidates(self.session.id, [final_cand])

        # Complete
        self.session.state = JobState.SUCCEEDED
        self.repository.save_session(self.session)
        self.event_bus.publish(
            ModulationCandidateCreated(
                session_id=self.session.id,
                modulation=final_cand.name,
                score=final_conf,
            )
        )
        self.event_bus.publish(AnalysisCompleted(session_id=self.session.id))
        self.progress_updated.emit("complete", 1.0, "Analysis complete.")
        self.analysis_finished.emit(segments, evidence_list, final_cand)


class AnalysisOrchestrator(QObject):
    """Manages background threads and analysis task queues for the desktop platform."""

    progress_updated = Signal(str, float, str)
    stage_completed = Signal(str, str)
    analysis_completed = Signal(object, object, object)
    analysis_failed = Signal(str)

    def __init__(
        self,
        repository: SessionRepository,
        event_bus: EventBus | None = None,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self.repository = repository
        self.event_bus = event_bus or EventBus.get_default()
        self._current_thread: QThread | None = None
        self._current_worker: AnalysisWorker | None = None

    def start_analysis(self, session: Session, buffer: SignalBuffer) -> None:
        """Kicks off asynchronous analysis pipeline on a background thread."""
        self.cancel_current()

        self._current_thread = QThread()
        self._current_worker = AnalysisWorker(
            session=session,
            buffer=buffer,
            repository=self.repository,
            event_bus=self.event_bus,
        )
        self._current_worker.moveToThread(self._current_thread)

        self._current_thread.started.connect(self._current_worker.run)
        self._current_worker.progress_updated.connect(self.progress_updated.emit)
        self._current_worker.stage_completed.connect(self.stage_completed.emit)
        self._current_worker.analysis_finished.connect(self._on_worker_finished)
        self._current_worker.error_occurred.connect(self.analysis_failed.emit)

        self._current_thread.start()

    def cancel_current(self) -> None:
        """Cancel ongoing analysis if running."""
        if self._current_worker:
            self._current_worker.cancel()
        if self._current_thread and self._current_thread.isRunning():
            self._current_thread.quit()
            self._current_thread.wait(500)
            self._current_thread = None
            self._current_worker = None

    def _on_worker_finished(
        self,
        segments: list[SignalSegment],
        evidence: list[ParameterEvidence],
        candidate: ModulationCandidate,
    ) -> None:
        self.analysis_completed.emit(segments, evidence, candidate)
        self.cancel_current()
