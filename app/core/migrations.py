import os
import re
from pathlib import Path
from sqlalchemy import text
from app.core.db import engine

MIGRATIONS_DIR = Path(__file__).resolve().parents[2] / "migrations"


def ensure_migrations_table(conn):
    conn.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS schema_migrations (
              version TEXT PRIMARY KEY,
              applied_at TIMESTAMPTZ NOT NULL DEFAULT now()
            )
            """
        )
    )


def applied_versions(conn) -> set[str]:
    rows = conn.execute(text("SELECT version FROM schema_migrations")).fetchall()
    return {row[0] for row in rows}


def run_migrations():
    if not MIGRATIONS_DIR.exists():
        return
    files = sorted(MIGRATIONS_DIR.glob("V*__*.sql"), key=lambda p: p.name)
    with engine.begin() as conn:
        ensure_migrations_table(conn)
        applied = applied_versions(conn)
        for file in files:
            version = file.name.split("__", 1)[0]
            if version in applied:
                continue
            sql = file.read_text(encoding="utf-8")
            if not sql.strip():
                conn.execute(text("INSERT INTO schema_migrations (version) VALUES (:v)"), {"v": version})
                continue
            for statement in [s for s in re.split(r";\s*$", sql, flags=re.MULTILINE) if s.strip()]:
                conn.execute(text(statement))
            conn.execute(text("INSERT INTO schema_migrations (version) VALUES (:v)"), {"v": version})
