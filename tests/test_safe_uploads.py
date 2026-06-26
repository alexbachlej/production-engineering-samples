import asyncio

import pytest

from backend.safe_uploads import (
    MAX_FILENAME_LENGTH,
    UploadTooLargeError,
    safe_filename,
    stream_upload_to_disk,
    unique_filename,
)


class FakeUpload:
    def __init__(self, chunks):
        self._chunks = list(chunks)

    async def read(self, size=-1):
        if not self._chunks:
            return b""
        return self._chunks.pop(0)


def test_safe_filename_removes_path_and_bad_chars():
    assert safe_filename("../../bad name!.txt", "fallback.txt") == "bad_name_.txt"


def test_safe_filename_blocks_hidden_files():
    assert safe_filename(".htaccess", "fallback.txt") == "htaccess"


def test_safe_filename_enforces_max_length():
    result = safe_filename("a" * 10_000 + ".txt", "fallback.txt")
    assert len(result) <= MAX_FILENAME_LENGTH


def test_unique_filename_adds_suffix():
    used = {"file.txt"}
    assert unique_filename("file.txt", used) == "file__2.txt"


def test_stream_upload_removes_partial_on_limit(tmp_path):
    target = tmp_path / "upload.bin"
    upload = FakeUpload([b"123", b"456"])

    with pytest.raises(UploadTooLargeError):
        asyncio.run(stream_upload_to_disk(upload, str(target), 5, chunk_size=3))

    assert not target.exists()
    assert not list(tmp_path.glob("*.part"))


def test_stream_upload_removes_partial_on_write_failure(monkeypatch, tmp_path):
    target = tmp_path / "upload.bin"
    temp = tmp_path / ".upload.bin.test.part"
    upload = FakeUpload([b"123"])

    class FailingNamedTemporaryFile:
        name = str(temp)

        def __enter__(self):
            temp.write_bytes(b"partial")
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def write(self, chunk):
            raise OSError("simulated disk write failure")

        def flush(self):
            raise AssertionError("flush should not be reached after write failure")

        def fileno(self):
            raise AssertionError("fileno should not be reached after write failure")

    def fake_named_temporary_file(*args, **kwargs):
        return FailingNamedTemporaryFile()

    monkeypatch.setattr("backend.safe_uploads.tempfile.NamedTemporaryFile", fake_named_temporary_file)

    with pytest.raises(OSError):
        asyncio.run(stream_upload_to_disk(upload, str(target), 10, chunk_size=3))

    assert not target.exists()
    assert not temp.exists()


def test_stream_upload_replaces_destination_only_after_success(tmp_path):
    target = tmp_path / "upload.bin"
    upload = FakeUpload([b"abc", b"def"])

    written = asyncio.run(stream_upload_to_disk(upload, str(target), 10, chunk_size=3))

    assert written == 6
    assert target.read_bytes() == b"abcdef"
    assert not list(tmp_path.glob("*.part"))
