from security.metadata_signing import (
    METADATA_SIGNATURE_REASON_INVALID_KEY_ID,
    METADATA_SIGNATURE_REASON_INVALID_SIGNATURE,
    METADATA_SIGNATURE_REASON_MISSING_SIGNATURE,
    METADATA_SIGNATURE_REASON_VALID,
    build_signed_record_metadata,
    verify_record_metadata_signature,
)


def _base_metadata():
    return {
        "record_id": "record-1",
        "record_version": "v1",
        "digest": "a" * 64,
    }


def _signed():
    return build_signed_record_metadata(
        record_metadata=_base_metadata(),
        signing_key="secret-key",
        key_id="key-1",
    )


def test_metadata_signing_round_trip_verifies():
    signed = _signed()

    result = verify_record_metadata_signature(
        record_metadata=signed["record_metadata"],
        signature_metadata=signed["signature_metadata"],
        verification_key="secret-key",
        key_id="key-1",
    )

    assert result["ok"] is True
    assert result["reason_code"] == METADATA_SIGNATURE_REASON_VALID


def test_metadata_signing_rejects_tampered_data():
    signed = _signed()
    tampered = dict(signed["record_metadata"])
    tampered["digest"] = "b" * 64

    result = verify_record_metadata_signature(
        record_metadata=tampered,
        signature_metadata=signed["signature_metadata"],
        verification_key="secret-key",
        key_id="key-1",
    )

    assert result["ok"] is False
    assert result["reason_code"] == METADATA_SIGNATURE_REASON_INVALID_SIGNATURE


def test_metadata_signing_rejects_wrong_key():
    signed = _signed()

    result = verify_record_metadata_signature(
        record_metadata=signed["record_metadata"],
        signature_metadata=signed["signature_metadata"],
        verification_key="wrong-key",
        key_id="key-1",
    )

    assert result["ok"] is False
    assert result["reason_code"] == METADATA_SIGNATURE_REASON_INVALID_SIGNATURE


def test_metadata_signing_rejects_wrong_key_id():
    signed = _signed()

    result = verify_record_metadata_signature(
        record_metadata=signed["record_metadata"],
        signature_metadata=signed["signature_metadata"],
        verification_key="secret-key",
        key_id="other-key",
    )

    assert result["ok"] is False
    assert result["reason_code"] == METADATA_SIGNATURE_REASON_INVALID_KEY_ID


def test_metadata_signing_rejects_missing_signature_metadata():
    result = verify_record_metadata_signature(
        record_metadata=_base_metadata(),
        signature_metadata=None,
        verification_key="secret-key",
        key_id="key-1",
    )

    assert result["ok"] is False
    assert result["reason_code"] == METADATA_SIGNATURE_REASON_MISSING_SIGNATURE
