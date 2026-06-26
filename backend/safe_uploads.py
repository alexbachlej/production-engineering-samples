"""Safe upload helpers for chunked writes and filename normalization."""
from __future__ import annotations

import os
from pathlib import Path
import re
import tempfile
from typing import Protocol


CHUNK_SIZE = 1024 * 1024
MAX_FILENAME_LENGTH = 255


class ChunkedUpload(Protocol):
    async def read(self, size: int = -1) -> bytes:
        """Return the next upload chunk."""


class UploadTooLargeError(ValueError):
    """Raised when an upload exceeds the configured byte limit."""


def safe_filename(name: str, fallback: str) -> str:
    """Return a filesystem-safe filename with path components and hidden-file prefixes removed."""
    base = os.path.basename(name or "").strip()
    cleaned = re.sub(r"[^A-Za-z0-9._-]", "_", base)
    cleaned = cleaned.lstrip(".")

    if not cleaned:
        cleaned = fallback

    cleaned = cleaned[:MAX_FILENAME_LENGTH].rstrip(".")
    if not cleaned:
        cleaned = fallback[:MAX_FILENAME_LENGTH].rstrip(".") or "upload"

    return cleaned


def unique_filename(name: str, used: set[str]) -> str:
    """Return a filename that does not collide with names already present in used."""
    if name not in used:
        used.add(name)
        return name

    base, ext = os.path.splitext(name)
    n = 2

    while True:
        candidate = f"{base}__{n}{ext}"
        if candidate not in used:
            used.add(candidate)
            return candidate
        n += 1


async def stream_upload_to_disk(
    upload: ChunkedUpload,
    dest_path: str,
    max_bytes: int,
    *,
    chunk_size: int = CHUNK_SIZE,
) -> int:
    """Stream an upload to a unique temporary file and atomically replace the destination on success."""
    written = 0
    final_path = Path(dest_path)
    temp_file = tempfile.NamedTemporaryFile(
        mode="wb",
        dir=final_path.parent,
        prefix=f".{final_path.name}.",
        suffix=".part",
        delete=False,
    )
    temp_path = Path(temp_file.name)

    try:
        with temp_file as file_obj:
            while True:
                chunk = await upload.read(chunk_size)
                if not chunk:
                    break

                written += len(chunk)
                if written > max_bytes:
                    raise UploadTooLargeError(f"upload exceeds {max_bytes} bytes")

                file_obj.write(chunk)

            file_obj.flush()
            os.fsync(file_obj.fileno())

        os.replace(temp_path, final_path)
    except Exception:
        temp_path.unlink(missing_ok=True)
        raise

    return written
