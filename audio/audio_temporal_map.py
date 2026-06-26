"""
temporal_map.py - Audio temporal mapping and analysis.

This module will provide functionality for analyzing audio tracks
and generating temporal maps that identify beat positions, energy
levels, and other timing cues used to synchronize video cuts
with audio.
"""

from dataclasses import dataclass
import librosa
import numpy as np





MIN_SILENCE_DURATION = 0.25
SILENCE_ENERGY_THRESHOLD = 0.1
ENERGY_RISE_DELTA_THRESHOLD = 0.4
BEATS_PER_BAR = 4


@dataclass(frozen=True)
class Beat:
    """Detected beat position in seconds."""

    time: float
    index: int


@dataclass(frozen=True)
class EnergyPoint:
    """Normalized audio energy value at a timestamp."""

    time: float
    energy: float


@dataclass(frozen=True)
class TemporalMap:
    """Audio timing map with tempo, beats, bars, energy_rises, energy curve, and silence regions."""

    duration: float
    bpm: float
    beats: list[Beat]
    bars: list[float]
    energy_rises: list[float]
    energy_curve: list[EnergyPoint]
    silence_regions: list[tuple[float, float]]

def build_temporal_map(audio_path: str) -> TemporalMap:
    # 1. Load audio
    y, sr = librosa.load(audio_path, sr=None)

    # 2. Detect tempo and beats
    tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr)
    beat_times = librosa.frames_to_time(beat_frames, sr=sr)

    beats: list[Beat] = []
    for i, t in enumerate(beat_times):
        beats.append(Beat(time=float(t), index=i))

    # 3. Build energy curve
    rms = librosa.feature.rms(y=y)[0]
    rms_times = librosa.frames_to_time(range(len(rms)), sr=sr)

    rms_min = rms.min()
    rms_max = rms.max()
    if rms_max - rms_min > 0:
        rms_normalized = (rms - rms_min) / (rms_max - rms_min)
    else:
        rms_normalized = np.zeros_like(rms)

    energy_points: list[EnergyPoint] = []
    for i, t in enumerate(rms_times):
        energy_points.append(EnergyPoint(time=float(t), energy=float(rms_normalized[i])))

    # 4. Detect silence regions
    silence_regions: list[tuple[float, float]] = []
    in_silence = False
    silence_start = 0.0

    for i, energy in enumerate(rms_normalized):
        t = float(rms_times[i])
        if energy < SILENCE_ENERGY_THRESHOLD:
            if not in_silence:
                in_silence = True
                silence_start = t
        else:
            if in_silence:
                silence_end = t
                if silence_end - silence_start >= MIN_SILENCE_DURATION:
                    silence_regions.append((silence_start, silence_end))
                in_silence = False

    if in_silence:
        silence_end = float(rms_times[-1])
        if silence_end - silence_start >= MIN_SILENCE_DURATION:
            silence_regions.append((silence_start, silence_end))

    # 5. Detect energy_rises
    energy_rises: list[float] = []
    for i in range(1, len(rms_normalized)):
        if rms_normalized[i] - rms_normalized[i - 1] > ENERGY_RISE_DELTA_THRESHOLD:
            energy_rises.append(float(rms_times[i]))

    # 6. Bars (every 4th beat)
    bars: list[float] = []
    for i in range(0, len(beat_times), BEATS_PER_BAR):
        bars.append(float(beat_times[i]))

    # 7. Construct and return TemporalMap
    duration_seconds = float(len(y) / sr)
    return TemporalMap(
        bpm=float(np.atleast_1d(tempo)[0]),
        beats=beats,
        bars=bars,
        energy_rises=energy_rises,
        energy_curve=energy_points,
        silence_regions=silence_regions,
        duration=duration_seconds,
    )
