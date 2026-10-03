"""SQLite storage for scenarios, analyses and decisions.

Everything the model received and answered is stored, so every result can be
traced back to its input.
"""

import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path

DEFAULT_DATABASE_PATH = Path(__file__).resolve().parents[1] / "cia.db"
DATABASE_PATH = Path(os.environ.get("DATABASE_PATH", DEFAULT_DATABASE_PATH))

# A scenario changes either a use case (change_type 'deactivate', 'modify' or 'add',
# the candidates are classes) or code (change_type 'code', the candidates are use cases).
SCHEMA = """
CREATE TABLE IF NOT EXISTS scenarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id TEXT NOT NULL,
    title TEXT NOT NULL,
    change_type TEXT NOT NULL,
    use_case_id TEXT NOT NULL,          -- '' for a code change
    original_text TEXT NOT NULL,        -- '' for a new use case
    new_text TEXT NOT NULL,             -- '' for a deactivated use case
    class_id TEXT NOT NULL,             -- only for a code change
    method_signature TEXT NOT NULL,     -- '' = the whole class changed
    original_code TEXT NOT NULL,
    new_code TEXT NOT NULL,
    created_at TEXT NOT NULL,
    applied_at TEXT
);

-- Derived from the trace links when the scenario is created, so later
-- changes of the links do not change an existing scenario.
CREATE TABLE IF NOT EXISTS candidates (
    scenario_id INTEGER NOT NULL REFERENCES scenarios(id) ON DELETE CASCADE,
    artifact_id TEXT NOT NULL,          -- class id or use case id
    PRIMARY KEY (scenario_id, artifact_id)
);

-- One model call for one candidate. Analysing again adds a new row;
-- the latest row of a candidate is the current one.
CREATE TABLE IF NOT EXISTS analyses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    scenario_id INTEGER NOT NULL REFERENCES scenarios(id) ON DELETE CASCADE,
    artifact_id TEXT NOT NULL,
    status TEXT NOT NULL,               -- 'pending', 'running', 'done' or 'failed'
    status_message TEXT NOT NULL DEFAULT '',
    prompt_version TEXT NOT NULL DEFAULT '',
    model TEXT NOT NULL DEFAULT '',
    prompt TEXT NOT NULL DEFAULT '',
    raw_answer TEXT NOT NULL DEFAULT '',
    reasoning TEXT NOT NULL DEFAULT '',
    class_note TEXT NOT NULL DEFAULT '',
    call_sites TEXT NOT NULL DEFAULT '[]',  -- JSON
    error TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL,
    started_at TEXT,
    finished_at TEXT
);

CREATE TABLE IF NOT EXISTS proposals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    analysis_id INTEGER NOT NULL REFERENCES analyses(id) ON DELETE CASCADE,
    target TEXT NOT NULL,               -- method signature, field name or use case id
    assessment TEXT NOT NULL,
    reason TEXT NOT NULL,
    requirement_reference TEXT NOT NULL,
    original_code TEXT NOT NULL,        -- current code, or current use case text
    proposed_code TEXT NOT NULL,        -- proposed code, or proposed use case text
    reference_problem TEXT NOT NULL,    -- '' if the reference exists
    decision TEXT NOT NULL DEFAULT 'open',
    decided_at TEXT
);
"""


def now() -> str:
    """Timestamps are stored as text, e.g. "2026-10-03T14:20:05"."""
    return datetime.now().isoformat(timespec="seconds")


@contextmanager
def connect():
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    try:
        yield connection
        connection.commit()
    finally:
        connection.close()


def init_database() -> None:
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with connect() as connection:
        connection.executescript(SCHEMA)
        # Analyses that were running when the server stopped will never finish.
        connection.execute(
            "UPDATE analyses SET status = 'failed', status_message = '', "
            "error = 'Abgebrochen, der Server wurde neu gestartet' WHERE status IN ('pending', 'running')"
        )
