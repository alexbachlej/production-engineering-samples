"""Cursor helpers for stable pagination with nullable timestamps."""
from __future__ import annotations

from datetime import datetime, timezone
import math


class InvalidCursorError(ValueError):
    """Raised when a pagination cursor is malformed."""


def epoch_to_iso(value: float) -> str:
    """Convert a Unix epoch timestamp to an ISO 8601 UTC string with microsecond precision."""
    truncated = math.floor(value * 1_000_000) / 1_000_000
    return datetime.fromtimestamp(truncated, tz=timezone.utc).isoformat()


def parse_cursor(cursor: str | None) -> tuple[str | None, str] | None:
    """
    Parse "<started_at_iso>|<record_id>".

    The started_at part may be the literal string "null" for records whose timestamp
    is missing. Timestamp validation accepts normal ISO 8601 values and a trailing Z.
    """
    if cursor is None:
        return None

    parts = cursor.split("|", 1)
    if len(parts) != 2:
        raise InvalidCursorError("expected '<started_at_iso>|<record_id>'")

    started_at_str, record_id = parts
    if not record_id:
        raise InvalidCursorError("missing record id")

    if started_at_str == "null":
        return (None, record_id)

    try:
        iso_normalized = (
            started_at_str.replace("Z", "+00:00")
            if started_at_str.endswith("Z")
            else started_at_str
        )
        datetime.fromisoformat(iso_normalized)
    except ValueError as exc:
        raise InvalidCursorError("invalid timestamp") from exc

    return (started_at_str, record_id)


def build_cursor(started_at_value: datetime | float | None, record_id: str) -> str:
    """Build "<started_at_iso>|<record_id>" or "null|<record_id>"."""
    if started_at_value is None:
        return f"null|{record_id}"

    if isinstance(started_at_value, datetime):
        return f"{started_at_value.isoformat()}|{record_id}"

    return f"{epoch_to_iso(started_at_value)}|{record_id}"
