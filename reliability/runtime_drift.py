from __future__ import annotations

from dataclasses import dataclass
from typing import Any

_DRIFT_SEVERITIES: tuple[str, ...] = (
    "low",
    "medium",
    "high",
    "critical",
)


@dataclass(frozen=True)
class RuntimeDriftReport:
    run_id: str
    task_index: int
    drift_detected: bool
    expected_contract: str
    observed_behavior: str
    severity: str
    recommendation: str


def _require_str(value: Any, field_name: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a string")
    return value


def _require_int(value: Any, field_name: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise ValueError(f"{field_name} must be an int")
    return value


def _require_bool(value: Any, field_name: str) -> bool:
    if not isinstance(value, bool):
        raise ValueError(f"{field_name} must be a bool")
    return value


def _validate_severity(value: str) -> str:
    if value not in _DRIFT_SEVERITIES:
        raise ValueError(f"invalid severity: {value}")
    return value


def new_drift_report(
    *,
    run_id: str,
    task_index: int,
    drift_detected: bool,
    expected_contract: str,
    observed_behavior: str,
    severity: str,
    recommendation: str,
) -> RuntimeDriftReport:
    return RuntimeDriftReport(
        run_id=_require_str(run_id, "run_id"),
        task_index=_require_int(task_index, "task_index"),
        drift_detected=_require_bool(drift_detected, "drift_detected"),
        expected_contract=_require_str(expected_contract, "expected_contract"),
        observed_behavior=_require_str(observed_behavior, "observed_behavior"),
        severity=_validate_severity(_require_str(severity, "severity")),
        recommendation=_require_str(recommendation, "recommendation"),
    )


def drift_report_to_dict(report: RuntimeDriftReport) -> dict[str, Any]:
    if not isinstance(report, RuntimeDriftReport):
        raise ValueError("report must be RuntimeDriftReport")
    return {
        "run_id": report.run_id,
        "task_index": report.task_index,
        "drift_detected": report.drift_detected,
        "expected_contract": report.expected_contract,
        "observed_behavior": report.observed_behavior,
        "severity": report.severity,
        "recommendation": report.recommendation,
    }


def drift_report_from_dict(payload: dict[str, Any]) -> RuntimeDriftReport:
    if not isinstance(payload, dict):
        raise ValueError("payload must be a dict")

    required_fields = (
        "run_id",
        "task_index",
        "drift_detected",
        "expected_contract",
        "observed_behavior",
        "severity",
        "recommendation",
    )
    payload_keys = set(payload.keys())
    required_keys = set(required_fields)
    if not required_keys.issubset(payload_keys):
        raise ValueError("payload is missing required runtime drift report keys")

    return new_drift_report(
        run_id=payload["run_id"],
        task_index=payload["task_index"],
        drift_detected=payload["drift_detected"],
        expected_contract=payload["expected_contract"],
        observed_behavior=payload["observed_behavior"],
        severity=payload["severity"],
        recommendation=payload["recommendation"],
    )


def build_runtime_drift_report(data: dict[str, object]) -> RuntimeDriftReport:
    """Build a RuntimeDriftReport from untrusted dictionary data."""
    return RuntimeDriftReport(
        run_id=_require_str(data.get("run_id"), "run_id"),
        task_index=_require_int(data.get("task_index"), "task_index"),
        drift_detected=_require_bool(data.get("drift_detected"), "drift_detected"),
        expected_contract=_require_str(data.get("expected_contract"), "expected_contract"),
        observed_behavior=_require_str(data.get("observed_behavior"), "observed_behavior"),
        severity=_validate_severity(_require_str(data.get("severity"), "severity")),
        recommendation=_require_str(data.get("recommendation"), "recommendation"),
    )
