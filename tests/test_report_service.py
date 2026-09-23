"""Unit tests for ReportService export capabilities."""

import json
from pathlib import Path

from signal_lab.domain.models.evidence import ModulationCandidate, ParameterEvidence
from signal_lab.domain.models.session import Session
from signal_lab.domain.models.signal import SignalSegment
from signal_lab.services.report_service import ReportService
from signal_lab.storage.repository import SessionRepository


def test_report_export_json_csv_markdown(
    session_repository: SessionRepository, tmp_path: Path
) -> None:
    """Verify exporting session reports to JSON, CSV, and Markdown files."""
    session = Session(
        name="Report Test Session",
        input_file_path="/data/sample.iq",
        sample_rate_hz=2_000_000.0,
        center_frequency_hz=145_000_000.0,
    )
    session_repository.save_session(session)

    # Save segment
    seg = SignalSegment(
        start_sample=0,
        end_sample=1000,
        start_time_s=0.0,
        duration_s=0.0005,
        center_frequency_hz=145_000_000.0,
        snr_db=22.0,
    )
    session_repository.save_segment(session.id, seg)

    # Save evidence
    ev = ParameterEvidence(name="Carrier Freq", value=145_000_000.0, unit="Hz", confidence=0.98)
    session_repository.save_evidence(session.id, ev)

    # Save candidate
    cand = ModulationCandidate(name="QPSK", score=0.92, evidence=["Phase clusters: 4"])
    session_repository.save_modulation_candidates(session.id, [cand])

    report_service = ReportService(session_repository)

    # 1. JSON Export
    json_path = tmp_path / "report.json"
    report_service.export_json(session.id, json_path)
    assert json_path.exists()
    with open(json_path, encoding="utf-8") as f:
        data = json.load(f)
    assert data["session"]["name"] == "Report Test Session"
    assert len(data["segments"]) == 1
    assert data["modulation_candidates"][0]["name"] == "QPSK"

    # 2. CSV Export
    csv_path = tmp_path / "report.csv"
    report_service.export_csv(session.id, csv_path)
    assert csv_path.exists()
    csv_content = csv_path.read_text(encoding="utf-8")
    assert "Carrier Freq" in csv_content

    # 3. Markdown Export
    md_path = tmp_path / "report.md"
    report_service.export_markdown(session.id, md_path)
    assert md_path.exists()
    md_content = md_path.read_text(encoding="utf-8")
    assert "# Signal Lab Analysis Report" in md_content
    assert "QPSK" in md_content
