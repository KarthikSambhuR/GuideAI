"""Whisper transcription utilities.

Provides helpers for transcribing audio both from a live NumPy buffer
(used during push-to-talk recording) and from a local WAV file (useful
for offline testing and debugging without a microphone).
"""

from __future__ import annotations

import wave
from pathlib import Path

import numpy as np
from pywhispercpp.model import Model

from config import SAMPLE_RATE, WHISPER_LANGUAGE


def transcribe_buffer(audio: np.ndarray, model: Model, language: str = WHISPER_LANGUAGE) -> str:
    """Transcribe a normalised float32 NumPy audio array.

    Parameters
    ----------
    audio:
        1-D float32 array sampled at ``SAMPLE_RATE`` Hz, values in [-1, 1].
    model:
        A loaded ``pywhispercpp`` Whisper model instance.
    language:
        Language code (default: read from config WHISPER_LANGUAGE).

    Returns
    -------
    str
        The transcribed text, stripped of leading/trailing whitespace.
        Returns an empty string if no speech was detected.
    """
    audio = np.nan_to_num(audio, nan=0.0, posinf=1.0, neginf=-1.0)
    peak = np.max(np.abs(audio))
    if peak:
        audio = audio / peak
    kwargs = {}
    if language and language != "auto":
        kwargs["language"] = language
    segments = model.transcribe(audio, **kwargs)
    return " ".join(seg.text for seg in segments).strip()


def transcribe_wav(path: str | Path, model: Model) -> str:
    """Transcribe a local WAV file using the provided Whisper model.

    The WAV file is read, converted to a normalised float32 mono array,
    resampled to ``SAMPLE_RATE`` if necessary, and then passed to Whisper.

    Parameters
    ----------
    path:
        Absolute or relative path to a ``.wav`` file.
    model:
        A loaded ``pywhispercpp`` Whisper model instance.

    Returns
    -------
    str
        The transcribed text, stripped of leading/trailing whitespace.

    Raises
    ------
    FileNotFoundError
        If *path* does not point to an existing file.
    ValueError
        If the WAV file cannot be read or has an unsupported format.
    """
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"WAV file not found: {path}")

    with wave.open(str(path), "rb") as wf:
        n_channels = wf.getnchannels()
        sample_width = wf.getsampwidth()  # bytes per sample
        framerate = wf.getframerate()
        n_frames = wf.getnframes()
        raw_bytes = wf.readframes(n_frames)

    # Convert raw bytes → int array.
    if sample_width == 1:
        dtype = np.int8
    elif sample_width == 2:
        dtype = np.int16
    elif sample_width == 4:
        dtype = np.int32
    else:
        raise ValueError(f"Unsupported sample width: {sample_width} bytes")

    samples = np.frombuffer(raw_bytes, dtype=dtype).astype(np.float32)

    # Normalise to [-1, 1].
    samples /= float(np.iinfo(dtype).max)

    # Convert stereo (or multi-channel) to mono by averaging channels.
    if n_channels > 1:
        samples = samples.reshape(-1, n_channels).mean(axis=1)

    # Resample to SAMPLE_RATE using linear interpolation when needed.
    if framerate != SAMPLE_RATE:
        duration = len(samples) / framerate
        target_len = int(duration * SAMPLE_RATE)
        old_indices = np.linspace(0, len(samples) - 1, len(samples))
        new_indices = np.linspace(0, len(samples) - 1, target_len)
        samples = np.interp(new_indices, old_indices, samples)

    print(f"GuideAI whisper_utils: transcribing {path.name} "
          f"({len(samples) / SAMPLE_RATE:.1f}s @ {SAMPLE_RATE} Hz)")
    return transcribe_buffer(samples.astype(np.float32), model)


def save_audio_to_wav(audio: np.ndarray, output_path: str | Path, sample_rate: int = SAMPLE_RATE) -> Path:
    """Save a 1D float32 audio NumPy buffer to a 16kHz mono 16-bit PCM WAV file.

    Parameters
    ----------
    audio:
        1-D float32 array with sample values in [-1, 1].
    output_path:
        Destination file path for the .wav output.
    sample_rate:
        Target sample rate in Hz (default: 16,000 Hz).

    Returns
    -------
    Path
        Path to the saved WAV file.
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    # Normalize and scale to int16 PCM
    audio_clean = np.nan_to_num(audio, nan=0.0, posinf=1.0, neginf=-1.0)
    audio_pcm16 = (audio_clean * 32767.0).astype(np.int16)

    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)  # 16-bit PCM
        wf.setframerate(sample_rate)
        wf.writeframes(audio_pcm16.tobytes())

    print(f"GuideAI whisper_utils: saved audio buffer to {path} ({len(audio) / sample_rate:.2f}s)")
    return path

