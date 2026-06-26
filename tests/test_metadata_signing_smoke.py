from pathlib import Path
import importlib


def test_metadata_signing_imports():
    module = importlib.import_module("security.metadata_signing")
    assert hasattr(module, "_canonical_json")


def test_metadata_signing_is_product_neutral():
    text = Path("security/metadata_signing.py").read_text(encoding="utf-8").lower()
    assert ("prompt" + "_id") not in text
    assert ("prompt" + "_version") not in text
    assert "prompt body" not in text
