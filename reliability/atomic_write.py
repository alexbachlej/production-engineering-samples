"""Atomic filesystem write helpers."""
from __future__ import annotations

import json
import os
from pathlib import Path
import tempfile
from typing import Any


def write_text_atomic(path: str | Path, text: str, *, encoding: str = "utf-8") -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)

    temp_file = tempfile.NamedTemporaryFile(
        mode="w",
        encoding=encoding,
        dir=str(target.parent),
        prefix=f".{target.name}.",
        suffix=".tmp",
        delete=False,
    )
    temp_path = Path(temp_file.name)

    try:
        temp_file.write(text)
        temp_file.flush()
        os.fsync(temp_file.fileno())
        temp_file.close()
        os.replace(temp_path, target)
    except Exception:
        try:
            temp_file.close()
        finally:
            if temp_path.exists():
                temp_path.unlink()
        raise


def write_json_atomic(
    path: str | Path,
    payload: Any,
    *,
    sort_keys: bool = True,
    indent: int | None = 2,
    trailing_newline: bool = True,
) -> None:
    body = json.dumps(payload, sort_keys=sort_keys, indent=indent)
    if trailing_newline:
        body += "\n"
    write_text_atomic(path, body, encoding="utf-8")
