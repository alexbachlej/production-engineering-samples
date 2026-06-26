import ast
from pathlib import Path

import numpy as np

import audio.audio_temporal_map as temporal_map


def test_audio_temporal_map_is_standalone_source():
    path = Path("audio/audio_temporal_map.py")
    text = path.read_text(encoding="utf-8")

    assert ("audio" + "_engine.") not in text
    assert "class Beat" in text
    assert "class EnergyPoint" in text
    assert "class TemporalMap" in text

    ast.parse(text)


def test_build_temporal_map_returns_declared_contract(monkeypatch, tmp_path):
    audio_path = tmp_path / "sample.wav"
    audio_path.write_bytes(b"fake")

    fake_audio = np.array([0.0, 0.5, 1.0, 0.5, 0.0], dtype=float)

    monkeypatch.setattr(
        temporal_map.librosa,
        "load",
        lambda path, sr=None: (fake_audio, 10),
    )
    monkeypatch.setattr(
        temporal_map.librosa.beat,
        "beat_track",
        lambda y, sr: (120.0, np.array([0, 2, 4])),
    )
    monkeypatch.setattr(
        temporal_map.librosa,
        "frames_to_time",
        lambda frames, sr: np.array(list(frames), dtype=float) / float(sr),
    )
    monkeypatch.setattr(
        temporal_map.librosa.feature,
        "rms",
        lambda y: np.array([[0.0, 0.5, 1.0, 0.5, 0.0]], dtype=float),
    )

    result = temporal_map.build_temporal_map(str(audio_path))

    assert isinstance(result, temporal_map.TemporalMap)
    assert result.duration == 0.5
    assert result.bpm == 120.0
    assert len(result.beats) == 3
    assert isinstance(result.bars, list)
    assert isinstance(result.energy_rises, list)
    assert result.energy_curve
    assert isinstance(result.silence_regions, list)
