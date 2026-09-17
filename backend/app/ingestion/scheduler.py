"""Cron/Airflow entrypoints that trigger each poller on its own cadence
and persist per-source cursors (last successful poll timestamp)."""
from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from app.db.models import PollCursor
from app.db.postgres import SessionLocal

# Sources may never have been polled; fall back to a bounded look-back window.
DEFAULT_LOOKBACK = timedelta(days=7)


def get_last_poll_timestamp(source: str) -> datetime:
    with SessionLocal() as db:
        cursor = db.get(PollCursor, source)
        if cursor is not None:
            return cursor.last_polled_at
    return datetime.now(timezone.utc) - DEFAULT_LOOKBACK


def set_last_poll_timestamp(source: str, value: datetime) -> None:
    with SessionLocal() as db:
        cursor = db.get(PollCursor, source)
        if cursor is None:
            db.add(PollCursor(source=source, last_polled_at=value))
        else:
            cursor.last_polled_at = value
        db.commit()
