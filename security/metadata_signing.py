"""Deterministic metadata record signature helpers."""
from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from hashlib import sha256
import hmac
import json
import re


METADATA_SIGNATURE_SCHEMA_VERSION = 1
METADATA_SIGNATURE_ALGORITHM = "hmac-sha256-v1"
_LEGACY_METADATA_SIGNATURE_ALGORITHM = "legacy-hmac-sha256-v1"
METADATA_SIGNATURE_SOURCE_OF_TRUTH = "metadata_signature_verification"

METADATA_SIGNATURE_REASON_VALID = "valid_metadata_signature"
METADATA_SIGNATURE_REASON_INVALID_METADATA = "invalid_metadata_signature_metadata"
METADATA_SIGNATURE_REASON_MISSING_SIGNATURE = "missing_metadata_signature"
METADATA_SIGNATURE_REASON_WRONG_VERSION = "wrong_metadata_signature_version"
METADATA_SIGNATURE_REASON_INVALID_ALGORITHM = "invalid_metadata_signature_algorithm"
METADATA_SIGNATURE_REASON_INVALID_KEY_ID = "invalid_metadata_signature_key_id"
METADATA_SIGNATURE_REASON_INVALID_SIGNATURE = "invalid_metadata_signature"
METADATA_SIGNATURE_REASON_INVALID_VERIFICATION_KEY = "invalid_metadata_signature_verification_key"

_SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")
_SIGNATURE_PREFIX_BY_ALGORITHM = {
    METADATA_SIGNATURE_ALGORITHM: "hmac-sha256",
    _LEGACY_METADATA_SIGNATURE_ALGORITHM: "fixture-hmac-sha256",
}
_SIGNATURE_PATTERN_BY_ALGORITHM = {
    algorithm: re.compile(rf"^{re.escape(prefix)}:[0-9a-f]{{64}}$")
    for algorithm, prefix in _SIGNATURE_PREFIX_BY_ALGORITHM.items()
}


def _canonical_json(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _normalize_non_empty_string(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    normalized = value.strip()
    if not normalized:
        return None
    return normalized


def _normalize_metadata_signature_metadata(record_metadata: Mapping[str, object]) -> dict[str, str] | None:
    record_id = _normalize_non_empty_string(record_metadata.get("record_id"))
    record_version = _normalize_non_empty_string(record_metadata.get("record_version"))
    digest = _normalize_non_empty_string(record_metadata.get("digest"))
    if record_id is None or record_version is None or digest is None:
        return None
    digest = digest.lower()
    if _SHA256_PATTERN.fullmatch(digest) is None:
        return None
    return {
        "record_id": record_id,
        "record_version": record_version,
        "digest": digest,
    }


def _signature_for(
    *,
    record_metadata: dict[str, str],
    signing_key: str,
    key_id: str,
    algorithm: str = METADATA_SIGNATURE_ALGORITHM,
) -> str:
    payload = "|".join(
        [
            algorithm,
            key_id,
            _canonical_json(record_metadata),
        ]
    )
    digest = hmac.new(
        signing_key.encode("utf-8"),
        payload.encode("utf-8"),
        sha256,
    ).hexdigest()
    return f"{_SIGNATURE_PREFIX_BY_ALGORITHM[algorithm]}:{digest}"


def build_signed_record_metadata(
    *,
    record_metadata: Mapping[str, object],
    signing_key: str,
    key_id: str,
) -> dict[str, object]:
    """Wrap metadata record with deterministic local signature metadata."""
    normalized_metadata = _normalize_metadata_signature_metadata(record_metadata)
    normalized_signing_key = _normalize_non_empty_string(signing_key)
    normalized_key_id = _normalize_non_empty_string(key_id)
    if normalized_metadata is None:
        raise ValueError("record_metadata must include record_id, record_version, and digest")
    if normalized_signing_key is None:
        raise ValueError("signing_key must be a non-empty string")
    if normalized_key_id is None:
        raise ValueError("key_id must be a non-empty string")

    return {
        "schema_version": METADATA_SIGNATURE_SCHEMA_VERSION,
        "source": "signed_record_metadata",
        "local_only": True,
        "external_signing_service": False,
        "external_network_calls": False,
        "record_metadata": deepcopy(normalized_metadata),
        "signature_metadata": {
            "schema_version": METADATA_SIGNATURE_SCHEMA_VERSION,
            "algorithm": METADATA_SIGNATURE_ALGORITHM,
            "key_id": normalized_key_id,
            "signature": _signature_for(
                record_metadata=normalized_metadata,
                signing_key=normalized_signing_key,
                key_id=normalized_key_id,
            ),
            "external_signing_service": False,
            "external_network_calls": False,
        },
    }


def verify_record_metadata_signature(
    *,
    record_metadata: Mapping[str, object],
    signature_metadata: object,
    verification_key: str,
    key_id: str,
) -> dict[str, object]:
    """Verify metadata record signature without returning record body or keys."""
    normalized_metadata = _normalize_metadata_signature_metadata(record_metadata)
    normalized_verification_key = _normalize_non_empty_string(verification_key)
    normalized_key_id = _normalize_non_empty_string(key_id)
    if normalized_metadata is None:
        return _verification_result(False, METADATA_SIGNATURE_REASON_INVALID_METADATA)
    if normalized_verification_key is None or normalized_key_id is None:
        return _verification_result(False, METADATA_SIGNATURE_REASON_INVALID_VERIFICATION_KEY)
    if not isinstance(signature_metadata, Mapping):
        return _verification_result(False, METADATA_SIGNATURE_REASON_MISSING_SIGNATURE)
    if signature_metadata.get("schema_version") != METADATA_SIGNATURE_SCHEMA_VERSION:
        return _verification_result(False, METADATA_SIGNATURE_REASON_WRONG_VERSION)
    algorithm = signature_metadata.get("algorithm")
    if algorithm not in _SIGNATURE_PREFIX_BY_ALGORITHM:
        return _verification_result(False, METADATA_SIGNATURE_REASON_INVALID_ALGORITHM)
    if signature_metadata.get("key_id") != normalized_key_id:
        return _verification_result(False, METADATA_SIGNATURE_REASON_INVALID_KEY_ID)
    if signature_metadata.get("external_signing_service") is not False:
        return _verification_result(False, METADATA_SIGNATURE_REASON_INVALID_SIGNATURE)
    if signature_metadata.get("external_network_calls") is not False:
        return _verification_result(False, METADATA_SIGNATURE_REASON_INVALID_SIGNATURE)

    signature = signature_metadata.get("signature")
    signature_pattern = _SIGNATURE_PATTERN_BY_ALGORITHM[algorithm]
    if not isinstance(signature, str) or signature_pattern.fullmatch(signature) is None:
        return _verification_result(False, METADATA_SIGNATURE_REASON_INVALID_SIGNATURE)

    expected_signature = _signature_for(
        record_metadata=normalized_metadata,
        signing_key=normalized_verification_key,
        key_id=normalized_key_id,
        algorithm=algorithm,
    )
    if not hmac.compare_digest(signature, expected_signature):
        return _verification_result(False, METADATA_SIGNATURE_REASON_INVALID_SIGNATURE)

    return _verification_result(True, METADATA_SIGNATURE_REASON_VALID)


def _verification_result(ok: bool, reason_code: str) -> dict[str, object]:
    return {
        "schema_version": METADATA_SIGNATURE_SCHEMA_VERSION,
        "source_of_truth": METADATA_SIGNATURE_SOURCE_OF_TRUTH,
        "ok": ok,
        "status": "verified" if ok else "blocked",
        "reason_code": reason_code,
    }


__all__ = [
    "METADATA_SIGNATURE_ALGORITHM",
    "METADATA_SIGNATURE_REASON_INVALID_ALGORITHM",
    "METADATA_SIGNATURE_REASON_INVALID_KEY_ID",
    "METADATA_SIGNATURE_REASON_INVALID_METADATA",
    "METADATA_SIGNATURE_REASON_INVALID_SIGNATURE",
    "METADATA_SIGNATURE_REASON_INVALID_VERIFICATION_KEY",
    "METADATA_SIGNATURE_REASON_MISSING_SIGNATURE",
    "METADATA_SIGNATURE_REASON_VALID",
    "METADATA_SIGNATURE_REASON_WRONG_VERSION",
    "METADATA_SIGNATURE_SCHEMA_VERSION",
    "METADATA_SIGNATURE_SOURCE_OF_TRUTH",
    "build_signed_record_metadata",
    "verify_record_metadata_signature",
]
