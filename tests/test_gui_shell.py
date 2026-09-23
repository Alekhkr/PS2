"""Integration and GUI shell tests using pytest-qt and offscreen platform."""

import os

import pytest

from signal_lab.domain.enums import ValidationStatus
from signal_lab.domain.models.evidence import ModulationCandidate, ParameterEvidence
from signal_lab.gui.main_window import MainWindow
from signal_lab.services.session_service import SessionService


@pytest.fixture(autouse=True)
def configure_qt_offscreen() -> None:
    """Ensure tests run in offscreen mode."""
    os.environ["QT_QPA_PLATFORM"] = "offscreen"


def test_main_window_initial_state(qtbot, session_service: SessionService) -> None:
    """Verify MainWindow initializes to DropZone view with clean telemetry."""
    window = MainWindow(session_service)
    qtbot.addWidget(window)

    # Initial view should be DropZone (index 0)
    assert window.view_stack.currentIndex() == 0
    assert window.header_bar.file_label.text() == "NO CAPTURE LOADED"
    assert window.header_bar.status_label.text() == "IDLE"


def test_file_selection_transitions_to_analysis(
    qtbot, session_service: SessionService, tmp_path
) -> None:
    """Verify that selecting a file creates a session and transitions to Analysis Workspace."""
    window = MainWindow(session_service)
    qtbot.addWidget(window)

    fake_capture = tmp_path / "test_signal.iq"
    fake_capture.write_bytes(b"\x00" * 1024)

    # Trigger file selection
    window.drop_zone.file_selected.emit(str(fake_capture))

    # Should switch to Analysis Workspace (index 1)
    assert window.view_stack.currentIndex() == 1
    assert window.header_bar.file_label.text() == "test_signal.iq"
    assert window.header_bar.status_label.text() == "READY"

    # Test "New Session" button switches back to DropZone
    window.header_bar.new_session_requested.emit()
    assert window.view_stack.currentIndex() == 0


def test_telemetry_and_pipeline_updates(qtbot, session_service: SessionService) -> None:
    """Verify header telemetry badges and pipeline status progression."""
    window = MainWindow(session_service)
    qtbot.addWidget(window)

    # Update telemetry
    window.header_bar.set_capture_info(
        "capture_2400.wav", sample_rate_hz=2_400_000, center_frequency_hz=145_000_000
    )
    assert "2.400 MS/s" in window.header_bar.rate_badge.val_label.text()
    assert "145.000 MHz" in window.header_bar.freq_badge.val_label.text()

    # Progress bar and status
    window.header_bar.set_job_status("Analyzing", 0.63)
    assert window.header_bar.status_label.text() == "ANALYZING"
    assert window.header_bar.progress_bar.value() == 63

    # Pipeline stages
    window.pipeline_status.set_stage_status("Detect", "done")
    window.pipeline_status.set_stage_status("Sync", "running")
    window.pipeline_status.set_stage_status("Demod", "pending")

    assert "✓" in window.pipeline_status._stage_labels["detect"].text()
    assert "●" in window.pipeline_status._stage_labels["sync"].text()
    assert "○" in window.pipeline_status._stage_labels["demod"].text()


def test_analysis_workspace_parameter_inspector(qtbot, session_service: SessionService) -> None:
    """Verify that parameters and modulation candidates populate inspector tables."""
    window = MainWindow(session_service)
    qtbot.addWidget(window)
    workspace = window.analysis_workspace

    # Set parameters
    ev1 = ParameterEvidence(name="Carrier Freq", value="145.000 MHz", confidence=0.98)
    ev2 = ParameterEvidence(name="Symbol Rate", value="9.58 kSym/s", confidence=0.82)
    workspace.set_parameters([ev1, ev2])

    assert workspace.param_table.rowCount() == 2
    assert workspace.param_table.item(0, 0).text() == "Carrier Freq"
    assert workspace.param_table.item(1, 0).text() == "Symbol Rate"

    # Set Modulation Candidate
    cand = ModulationCandidate(
        name="QPSK",
        score=0.87,
        evidence=["4 phase clusters", "constant envelope fit"],
        validation=ValidationStatus.PARTIAL,
    )
    workspace.set_modulation_candidate(cand)

    assert "QPSK" in workspace.mod_name_lbl.text()
    assert "87%" in workspace.mod_confidence_lbl.text()
    assert "4 phase clusters" in workspace.evidence_list.text()
