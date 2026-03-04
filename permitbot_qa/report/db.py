from __future__ import annotations

import os
from sqlalchemy import create_engine, text


def save_run_summary(run_id: str, project_type: str, findings_count: int) -> None:
    db = os.getenv("DATABASE_URL", "").strip()
    if not db:
        return

    engine = create_engine(db)
    with engine.begin() as conn:
        conn.execute(text("""
            create table if not exists permitbot_runs (
              run_id text primary key,
              project_type text,
              findings_count integer,
              created_at timestamptz default now()
            )
        """))
        conn.execute(
            text("insert into permitbot_runs (run_id, project_type, findings_count) values (:r,:p,:f) on conflict (run_id) do nothing"),
            {"r": run_id, "p": project_type, "f": findings_count},
        )
