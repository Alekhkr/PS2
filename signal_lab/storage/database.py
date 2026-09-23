"""SQLite database schema and connection management for Signal Lab."""

from __future__ import annotations

import os
import sqlite3
from pathlib import Path

DEFAULT_DB_FILENAME = "signal_lab.db"


def get_default_storage_dir() -> Path:
    """Returns the base storage directory for sessions and database."""
    base_dir = os.environ.get("SIGNAL_LAB_HOME")
    if base_dir:
        storage_path = Path(base_dir)
    else:
        storage_path = Path.cwd() / "workspace"
    storage_path.mkdir(parents=True, exist_ok=True)
    return storage_path


def get_database_path(custom_path: str | Path | None = None) -> Path:
    """Get the SQLite database path."""
    if custom_path:
        path = Path(custom_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        return path
    return get_default_storage_dir() / DEFAULT_DB_FILENAME


class DatabaseManager:
    """Manages SQLite database connections and table schemas."""

    def __init__(self, db_path: str | Path | None = None) -> None:
        self.db_path = get_database_path(db_path)
        self.init_db()

    def get_connection(self) -> sqlite3.Connection:
        """Create a new SQLite connection with row factories enabled."""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.execute("PRAGMA journal_mode = WAL;")
        return conn

    def init_db(self) -> None:
        """Initialize all schema tables if not present."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Sessions table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS sessions (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    input_file_path TEXT,
                    input_file_hash TEXT,
                    sample_rate_hz REAL,
                    center_frequency_hz REAL,
                    state TEXT NOT NULL,
                    metadata_json TEXT
                );
                """
            )

            # Signal Segments table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS segments (
                    id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    start_sample INTEGER NOT NULL,
                    end_sample INTEGER NOT NULL,
                    start_time_s REAL NOT NULL,
                    duration_s REAL NOT NULL,
                    center_frequency_hz REAL,
                    bandwidth_hz REAL,
                    snr_db REAL,
                    metadata_json TEXT,
                    FOREIGN KEY(session_id) REFERENCES sessions(id) ON DELETE CASCADE
                );
                """
            )

            # Parameter Evidence table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS parameter_evidence (
                    id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    segment_id TEXT,
                    name TEXT NOT NULL,
                    value_json TEXT,
                    unit TEXT,
                    source TEXT NOT NULL,
                    algorithm TEXT,
                    confidence REAL NOT NULL,
                    assumptions_json TEXT,
                    validation TEXT NOT NULL,
                    FOREIGN KEY(session_id) REFERENCES sessions(id) ON DELETE CASCADE
                );
                """
            )

            # Modulation Candidates table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS modulation_candidates (
                    id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    segment_id TEXT,
                    name TEXT NOT NULL,
                    score REAL NOT NULL,
                    evidence_json TEXT,
                    algorithm TEXT NOT NULL,
                    validation TEXT NOT NULL,
                    FOREIGN KEY(session_id) REFERENCES sessions(id) ON DELETE CASCADE
                );
                """
            )

            # Pipeline Nodes table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS pipeline_nodes (
                    id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    operation TEXT NOT NULL,
                    input_id TEXT,
                    output_id TEXT,
                    parameters_json TEXT,
                    algorithm TEXT,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(session_id) REFERENCES sessions(id) ON DELETE CASCADE
                );
                """
            )

            # Derived Artifacts table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS artifacts (
                    id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    artifact_type TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    content_hash TEXT,
                    created_at TEXT NOT NULL,
                    metadata_json TEXT,
                    FOREIGN KEY(session_id) REFERENCES sessions(id) ON DELETE CASCADE
                );
                """
            )

            # Indexes for high-performance lookup
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_segments_session ON segments(session_id);"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_evidence_session ON parameter_evidence(session_id);"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_mod_candidates_session ON modulation_candidates(session_id);"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_pipeline_session ON pipeline_nodes(session_id);"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_artifacts_session ON artifacts(session_id);"
            )
            conn.commit()
