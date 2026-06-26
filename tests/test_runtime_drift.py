import pytest

from reliability.runtime_drift import build_runtime_drift_report


def _valid_payload():
    return {
        "run_id": "run-1",
        "task_index": 1,
        "drift_detected": False,
        "expected_contract": "expected",
        "observed_behavior": "observed",
        "severity": "low",
        "recommendation": "none",
    }


def test_runtime_drift_builder_accepts_valid_payload():
    report = build_runtime_drift_report(_valid_payload())
    assert report.run_id == "run-1"
    assert report.severity == "low"


def test_runtime_drift_rejects_bool_as_int():
    payload = _valid_payload()
    payload["task_index"] = True

    with pytest.raises(ValueError):
        build_runtime_drift_report(payload)


def test_runtime_drift_rejects_invalid_severity():
    payload = _valid_payload()
    payload["severity"] = "catastrophic"

    with pytest.raises(ValueError):
        build_runtime_drift_report(payload)
