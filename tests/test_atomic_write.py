from reliability.atomic_write import write_text_atomic, write_json_atomic


def test_write_text_atomic(tmp_path):
    target = tmp_path / "sample.txt"
    write_text_atomic(target, "hello")
    assert target.read_text() == "hello"


def test_write_json_atomic(tmp_path):
    target = tmp_path / "sample.json"
    write_json_atomic(target, {"ok": True})
    assert '"ok": true' in target.read_text()
