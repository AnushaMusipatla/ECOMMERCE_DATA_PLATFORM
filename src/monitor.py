"""Read pipeline execution history and operational metrics from SQLite."""

import sqlite3
from contextlib import closing
from pathlib import Path


def run_history(db_path: Path) -> list[dict]:
    with closing(sqlite3.connect(db_path)) as conn:
        conn.row_factory = sqlite3.Row
        return [dict(row) for row in conn.execute("SELECT * FROM pipeline_runs ORDER BY start_time DESC")]
