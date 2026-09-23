"""Repository for typed persistence operations over SQLite."""

from __future__ import annotations

import json
import sqlite3

from signal_lab.domain.enums import EvidenceSource, JobState, ValidationStatus
from signal_lab.domain.models.evidence import ModulationCandidate, ParameterEvidence
from signal_lab.domain.models.session import PipelineNode, Session
from signal_lab.domain.models.signal import SignalSegment
from signal_lab.storage.database import DatabaseManager


class SessionRepository:
    """Provides typed database access for sessions, segments, evidence, and pipeline steps."""

    def __init__(self, db_manager: DatabaseManager) -> None:
        self.db_manager = db_manager

    def save_session(self, session: Session) -> None:
        """Upsert a session record."""
        query = """
        INSERT INTO sessions (
            id, name, created_at, updated_at, input_file_path, input_file_hash,
            sample_rate_hz, center_frequency_hz, state, metadata_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
            name=excluded.name,
            updated_at=excluded.updated_at,
            input_file_path=excluded.input_file_path,
            input_file_hash=excluded.input_file_hash,
            sample_rate_hz=excluded.sample_rate_hz,
            center_frequency_hz=excluded.center_frequency_hz,
            state=excluded.state,
            metadata_json=excluded.metadata_json;
        """
        with self.db_manager.get_connection() as conn:
            conn.execute(
                query,
                (
                    session.id,
                    session.name,
                    session.created_at,
                    session.updated_at,
                    session.input_file_path,
                    session.input_file_hash,
                    session.sample_rate_hz,
                    session.center_frequency_hz,
                    session.state.value if hasattr(session.state, "value") else str(session.state),
                    json.dumps(session.metadata),
                ),
            )
            conn.commit()

    def get_session(self, session_id: str) -> Session | None:
        """Retrieve a session by its unique ID."""
        query = "SELECT * FROM sessions WHERE id = ?;"
        with self.db_manager.get_connection() as conn:
            row = conn.execute(query, (session_id,)).fetchone()
            if not row:
                return None
            return self._row_to_session(row)

    def list_recent_sessions(self, limit: int = 15) -> list[Session]:
        """List recently updated sessions."""
        query = "SELECT * FROM sessions ORDER BY updated_at DESC LIMIT ?;"
        with self.db_manager.get_connection() as conn:
            rows = conn.execute(query, (limit,)).fetchall()
            return [self._row_to_session(r) for r in rows]

    def delete_session(self, session_id: str) -> bool:
        """Delete a session and all its cascading records."""
        query = "DELETE FROM sessions WHERE id = ?;"
        with self.db_manager.get_connection() as conn:
            cursor = conn.execute(query, (session_id,))
            conn.commit()
            return cursor.rowcount > 0

    def save_segment(self, session_id: str, segment: SignalSegment) -> None:
        """Upsert a signal segment."""
        query = """
        INSERT INTO segments (
            id, session_id, start_sample, end_sample, start_time_s, duration_s,
            center_frequency_hz, bandwidth_hz, snr_db, metadata_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
            start_sample=excluded.start_sample,
            end_sample=excluded.end_sample,
            start_time_s=excluded.start_time_s,
            duration_s=excluded.duration_s,
            center_frequency_hz=excluded.center_frequency_hz,
            bandwidth_hz=excluded.bandwidth_hz,
            snr_db=excluded.snr_db,
            metadata_json=excluded.metadata_json;
        """
        with self.db_manager.get_connection() as conn:
            conn.execute(
                query,
                (
                    segment.id,
                    session_id,
                    segment.start_sample,
                    segment.end_sample,
                    segment.start_time_s,
                    segment.duration_s,
                    segment.center_frequency_hz,
                    segment.bandwidth_hz,
                    segment.snr_db,
                    json.dumps(segment.metadata),
                ),
            )
            conn.commit()

    def get_segments(self, session_id: str) -> list[SignalSegment]:
        """Get all segments belonging to a session."""
        query = "SELECT * FROM segments WHERE session_id = ? ORDER BY start_sample ASC;"
        with self.db_manager.get_connection() as conn:
            rows = conn.execute(query, (session_id,)).fetchall()
            return [
                SignalSegment(
                    id=r["id"],
                    start_sample=r["start_sample"],
                    end_sample=r["end_sample"],
                    start_time_s=r["start_time_s"],
                    duration_s=r["duration_s"],
                    center_frequency_hz=r["center_frequency_hz"],
                    bandwidth_hz=r["bandwidth_hz"],
                    snr_db=r["snr_db"],
                    metadata=json.loads(r["metadata_json"] or "{}"),
                )
                for r in rows
            ]

    def save_evidence(
        self, session_id: str, evidence: ParameterEvidence, segment_id: str | None = None
    ) -> None:
        """Save a piece of parameter evidence."""
        query = """
        INSERT INTO parameter_evidence (
            id, session_id, segment_id, name, value_json, unit, source,
            algorithm, confidence, assumptions_json, validation
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
            value_json=excluded.value_json,
            confidence=excluded.confidence,
            validation=excluded.validation;
        """
        with self.db_manager.get_connection() as conn:
            conn.execute(
                query,
                (
                    evidence.id,
                    session_id,
                    segment_id,
                    evidence.name,
                    json.dumps(evidence.value),
                    evidence.unit,
                    evidence.source.value
                    if hasattr(evidence.source, "value")
                    else str(evidence.source),
                    evidence.algorithm,
                    evidence.confidence,
                    json.dumps(evidence.assumptions),
                    evidence.validation.value
                    if hasattr(evidence.validation, "value")
                    else str(evidence.validation),
                ),
            )
            conn.commit()

    def get_evidence_for_session(self, session_id: str) -> list[ParameterEvidence]:
        """Fetch all parameter evidence records for a session."""
        query = "SELECT * FROM parameter_evidence WHERE session_id = ?;"
        with self.db_manager.get_connection() as conn:
            rows = conn.execute(query, (session_id,)).fetchall()
            return [
                ParameterEvidence(
                    id=r["id"],
                    name=r["name"],
                    value=json.loads(r["value_json"]),
                    unit=r["unit"],
                    source=EvidenceSource(r["source"])
                    if r["source"] in EvidenceSource._value2member_map_
                    else r["source"],
                    algorithm=r["algorithm"],
                    confidence=r["confidence"],
                    assumptions=json.loads(r["assumptions_json"] or "[]"),
                    validation=ValidationStatus(r["validation"])
                    if r["validation"] in ValidationStatus._value2member_map_
                    else r["validation"],
                )
                for r in rows
            ]

    def save_modulation_candidates(
        self, session_id: str, candidates: list[ModulationCandidate], segment_id: str | None = None
    ) -> None:
        """Save ranked modulation candidates."""
        query = """
        INSERT INTO modulation_candidates (
            id, session_id, segment_id, name, score, evidence_json, algorithm, validation
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
            score=excluded.score,
            evidence_json=excluded.evidence_json,
            validation=excluded.validation;
        """
        with self.db_manager.get_connection() as conn:
            for c in candidates:
                conn.execute(
                    query,
                    (
                        c.id,
                        session_id,
                        segment_id,
                        c.name,
                        c.score,
                        json.dumps(c.evidence),
                        c.algorithm,
                        c.validation.value if hasattr(c.validation, "value") else str(c.validation),
                    ),
                )
            conn.commit()

    def get_modulation_candidates(self, session_id: str) -> list[ModulationCandidate]:
        """Retrieve modulation candidates ordered by score descending."""
        query = "SELECT * FROM modulation_candidates WHERE session_id = ? ORDER BY score DESC;"
        with self.db_manager.get_connection() as conn:
            rows = conn.execute(query, (session_id,)).fetchall()
            return [
                ModulationCandidate(
                    id=r["id"],
                    name=r["name"],
                    score=r["score"],
                    evidence=json.loads(r["evidence_json"] or "[]"),
                    algorithm=r["algorithm"],
                    validation=ValidationStatus(r["validation"])
                    if r["validation"] in ValidationStatus._value2member_map_
                    else r["validation"],
                )
                for r in rows
            ]

    def save_pipeline_node(self, session_id: str, node: PipelineNode) -> None:
        """Record a pipeline transformation node."""
        query = """
        INSERT INTO pipeline_nodes (
            id, session_id, operation, input_id, output_id, parameters_json, algorithm, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?);
        """
        with self.db_manager.get_connection() as conn:
            conn.execute(
                query,
                (
                    node.id,
                    session_id,
                    node.operation,
                    node.input_id,
                    node.output_id,
                    json.dumps(node.parameters),
                    node.algorithm,
                    node.created_at,
                ),
            )
            conn.commit()

    def get_pipeline_nodes(self, session_id: str) -> list[PipelineNode]:
        """Get ordered pipeline transformations."""
        query = "SELECT * FROM pipeline_nodes WHERE session_id = ? ORDER BY created_at ASC;"
        with self.db_manager.get_connection() as conn:
            rows = conn.execute(query, (session_id,)).fetchall()
            return [
                PipelineNode(
                    id=r["id"],
                    operation=r["operation"],
                    input_id=r["input_id"],
                    output_id=r["output_id"],
                    parameters=json.loads(r["parameters_json"] or "{}"),
                    algorithm=r["algorithm"],
                    created_at=r["created_at"],
                )
                for r in rows
            ]

    def _row_to_session(self, row: sqlite3.Row) -> Session:
        state_val = row["state"]
        state = JobState(state_val) if state_val in JobState._value2member_map_ else JobState.QUEUED
        return Session(
            id=row["id"],
            name=row["name"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            input_file_path=row["input_file_path"],
            input_file_hash=row["input_file_hash"],
            sample_rate_hz=row["sample_rate_hz"],
            center_frequency_hz=row["center_frequency_hz"],
            state=state,
            metadata=json.loads(row["metadata_json"] or "{}"),
        )
