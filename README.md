# production-engineering-samples

Small, reviewable Python samples for backend, security, and reliability patterns.

This repository is a curated public sample pack extracted and sanitized from private work. It is not a product source dump and does not include product internals, deployment details, billing flows, customer data, or private automation logic.

## Modules

### security/metadata_signing.py

HMAC-based metadata signing and verification.

Covers:

- canonical JSON serialization with deterministic key ordering
- timing-safe signature comparison with hmac.compare_digest
- versioned signature metadata
- explicit verification reason codes
- mapping-based input instead of mutable concrete dict assumptions

### reliability/atomic_write.py

Atomic text and JSON file writes.

Covers:

- temporary file creation in the target directory
- flush and fsync
- atomic replacement with os.replace
- cleanup of temporary files on failure

### reliability/state_machine.py

Explicit task-state validation and transition checks.

Covers:

- closed set of allowed states
- transition validation
- boolean transition checks
- normalized state handling

### reliability/runtime_drift.py

Immutable runtime drift report records.

Covers:

- frozen dataclasses
- strict serialization and deserialization
- exact key validation
- type guards for bool/int ambiguity
- severity validation

### backend/safe_uploads.py

Chunked upload streaming with defensive cleanup.

Covers:

- filename sanitization
- unique filename generation
- maximum byte enforcement
- partial-file cleanup on size limit failures
- partial-file cleanup on unexpected write failures

### backend/cursor_pagination.py

Cursor parsing and generation for timestamp-based pagination.

Covers:

- explicit null timestamp handling
- UTC ISO timestamp conversion
- microsecond truncation for stable cursor precision
- custom cursor parsing errors

### audio/audio_temporal_map.py

Lightweight audio timing map generation.

Covers:

- tempo and beat extraction
- bar marker generation
- normalized energy curve generation
- silence region detection
- energy-rise marker detection

## Verification

The repository includes a GitHub Actions CI workflow that runs:

- editable package installation with development and audio extras
- the pytest suite
- a strict public-risk scan for secret-like tokens, private identifiers, and product-specific names

Run locally:

    python -m venv .venv
    . .venv/bin/activate
    python -m pip install -e ".[dev,audio]"
    python -m pytest -q

## Scope

This repository is intentionally narrow. It is meant for code review, not as a complete application.

It does not include:

- production services
- product-specific business logic
- billing or payment flows
- customer data
- private runtime formats
- deployment configuration
- internal automation pipelines

## Review focus

The most relevant files to review first are:

1. security/metadata_signing.py
2. reliability/atomic_write.py
3. backend/safe_uploads.py
4. backend/cursor_pagination.py
5. reliability/runtime_drift.py
