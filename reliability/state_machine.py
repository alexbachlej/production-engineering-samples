"""Deterministic task lifecycle state and transition validation."""
from __future__ import annotations

TASK_STATES: tuple[str, ...] = (
    "planned",
    "active",
    "blocked",
    "waiting_limit",
    "review_required",
    "completed",
    "failed",
    "cancelled",
)

_VALID_TASK_STATES: frozenset[str] = frozenset(TASK_STATES)

_ALLOWED_TASK_TRANSITIONS: dict[str, frozenset[str]] = {
    "planned": frozenset({"active", "blocked", "cancelled"}),
    "active": frozenset({"review_required", "blocked", "waiting_limit", "completed", "failed", "cancelled"}),
    "waiting_limit": frozenset({"active", "blocked", "cancelled"}),
    "review_required": frozenset({"active", "completed", "blocked", "failed", "cancelled"}),
    "blocked": frozenset({"active", "cancelled", "failed"}),
    "failed": frozenset({"active", "cancelled"}),
    "completed": frozenset(),
    "cancelled": frozenset(),
}


def _normalize_task_state(state: str) -> str:
    return state.strip().lower()


def is_valid_task_state(state: str) -> bool:
    normalized = _normalize_task_state(state)
    return normalized in _VALID_TASK_STATES


def validate_task_state(state: str) -> str:
    normalized = _normalize_task_state(state)
    if normalized not in _VALID_TASK_STATES:
        raise ValueError(f"invalid task state: {state!r}")
    return normalized


def can_transition_task_state(from_state: str, to_state: str) -> bool:
    from_normalized = _normalize_task_state(from_state)
    to_normalized = _normalize_task_state(to_state)
    if from_normalized not in _VALID_TASK_STATES or to_normalized not in _VALID_TASK_STATES:
        return False
    return to_normalized in _ALLOWED_TASK_TRANSITIONS[from_normalized]


def validate_task_transition(from_state: str, to_state: str) -> tuple[str, str]:
    from_normalized = validate_task_state(from_state)
    to_normalized = validate_task_state(to_state)
    if to_normalized not in _ALLOWED_TASK_TRANSITIONS[from_normalized]:
        raise ValueError(
            f"disallowed task state transition: {from_normalized!r} -> {to_normalized!r}"
        )
    return from_normalized, to_normalized




def is_valid_task_transition(from_state: str, to_state: str) -> bool:
    """Return True when moving from from_state to to_state is allowed."""
    try:
        validate_task_transition(from_state, to_state)
    except ValueError:
        return False
    return True

__all__ = [
    "TASK_STATES",
    "is_valid_task_state",
    "validate_task_state",
    "can_transition_task_state",
    "validate_task_transition",
    "is_valid_task_transition",
]
