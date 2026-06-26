import pytest

from backend.cursor_pagination import build_cursor, parse_cursor, InvalidCursorError


def test_parse_null_cursor():
    assert parse_cursor("null|abc") == (None, "abc")


def test_build_null_cursor():
    assert build_cursor(None, "abc") == "null|abc"


def test_parse_invalid_cursor():
    with pytest.raises(InvalidCursorError):
        parse_cursor("broken")


def test_epoch_cursor_truncates_to_microseconds():
    cursor = build_cursor(1.123456789, "abc")
    assert cursor.startswith("1970-01-01T00:00:01.123456+00:00|")
