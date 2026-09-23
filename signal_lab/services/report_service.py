"""Session reporting and auditable export service."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from signal_lab.storage.repository import SessionRepository


class ReportService:
    """Exports comprehensive analysis reports in JSON, CSV, and Markdown formats."""

    def __init__(self, repository: SessionRepository) -> None:
        self.repository = repository

    def generate_report_dict(self, session_id: str) -> dict[str, Any]:
        """Compiles complete session data into a structured dictionary."""
        session = self.repository.get_session(session_id)
        if not session:
            raise ValueError(f"Session not found: {session_id}")

        segments = self.repository.get_segments(session_id)
        evidence = self.repository.get_evidence_for_session(session_id)
        candidates = self.repository.get_modulation_candidates(session_id)
        pipeline = self.repository.get_pipeline_nodes(session_id)

        return {
            "session": {
                "id": session.id,
                "name": session.name,
                "created_at": session.created_at,
                "updated_at": session.updated_at,
                "input_file_path": session.input_file_path,
                "input_file_hash": session.input_file_hash,
                "sample_rate_hz": session.sample_rate_hz,
                "center_frequency_hz": session.center_frequency_hz,
                "state": session.state.value
                if hasattr(session.state, "value")
                else str(session.state),
            },
            "segments": [
                {
                    "id": s.id,
                    "start_sample": s.start_sample,
                    "end_sample": s.end_sample,
                    "start_time_s": s.start_time_s,
                    "duration_s": s.duration_s,
                    "center_frequency_hz": s.center_frequency_hz,
                    "bandwidth_hz": s.bandwidth_hz,
                    "snr_db": s.snr_db,
                }
                for s in segments
            ],
            "parameter_evidence": [ev.to_dict() for ev in evidence],
            "modulation_candidates": [
                {
                    "name": c.name,
                    "score": c.score,
                    "evidence": c.evidence,
                    "algorithm": c.algorithm,
                    "validation": str(
                        c.validation.value if hasattr(c.validation, "value") else c.validation
                    ),
                }
                for c in candidates
            ],
            "pipeline_nodes": [
                {
                    "operation": n.operation,
                    "algorithm": n.algorithm,
                    "created_at": n.created_at,
                }
                for n in pipeline
            ],
        }

    def export_json(self, session_id: str, output_path: str | Path) -> Path:
        """Export session report as JSON."""
        data = self.generate_report_dict(session_id)
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        with open(out, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        return out

    def export_csv(self, session_id: str, output_path: str | Path) -> Path:
        """Export estimated parameters as a flat CSV file."""
        evidence = self.repository.get_evidence_for_session(session_id)
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        with open(out, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(
                ["Parameter", "Value", "Unit", "Source", "Algorithm", "Confidence", "Validation"]
            )
            for ev in evidence:
                writer.writerow(
                    [
                        ev.name,
                        ev.value,
                        ev.unit or "",
                        ev.source.value if hasattr(ev.source, "value") else str(ev.source),
                        ev.algorithm or "",
                        f"{ev.confidence:.3f}",
                        ev.validation.value
                        if hasattr(ev.validation, "value")
                        else str(ev.validation),
                    ]
                )
        return out

    def export_markdown(self, session_id: str, output_path: str | Path) -> Path:
        """Export human-readable Markdown summary report."""
        data = self.generate_report_dict(session_id)
        sess = data["session"]
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)

        lines = [
            f"# Signal Lab Analysis Report: {sess['name']}",
            f"**Session ID:** `{sess['id']}`  ",
            f"**Capture File:** `{sess['input_file_path']}`  ",
            f"**Sample Rate:** {sess['sample_rate_hz'] or 'Unknown'} Hz  ",
            f"**Center Frequency:** {sess['center_frequency_hz'] or 'Unknown'} Hz  ",
            "",
            "## Modulation Hypotheses",
            "| Modulation | Confidence | Validation | Key Evidence |",
            "|---|---|---|---|",
        ]

        for cand in data["modulation_candidates"]:
            ev_str = "; ".join(cand["evidence"][:2])
            lines.append(
                f"| **{cand['name']}** | {int(cand['score'] * 100)}% | {cand['validation']} | {ev_str} |"
            )

        lines.extend(
            [
                "",
                "## Measured Parameters & Provenance",
                "| Parameter | Value | Unit | Source | Algorithm | Confidence | Status |",
                "|---|---|---|---|---|---|---|",
            ]
        )

        for p in data["parameter_evidence"]:
            lines.append(
                f"| {p['name']} | `{p['value']}` | {p['unit'] or '-'} | {p['source']} | {p['algorithm']} | {int(p['confidence'] * 100)}% | {p['validation']} |"
            )

        with open(out, "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")

        return out
