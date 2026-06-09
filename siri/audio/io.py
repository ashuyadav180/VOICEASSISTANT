"""Audio input/output utilities."""

from __future__ import annotations

import logging
import queue
import threading
from typing import Callable

import numpy as np
import sounddevice as sd

logger = logging.getLogger(__name__)


class AudioIO:
    def __init__(self, sample_rate: int = 16000, channels: int = 1, chunk_ms: int = 80) -> None:
        self.sample_rate = sample_rate
        self.channels = channels
        self.chunk_size = int(sample_rate * chunk_ms / 1000)
        self._stream: sd.InputStream | None = None
        self._running = False

    def list_devices(self) -> list[dict]:
        devices = sd.query_devices()
        return [
            {"index": i, "name": d["name"], "inputs": d["max_input_channels"]}
            for i, d in enumerate(devices)
            if d["max_input_channels"] > 0
        ]

    def start_mic_stream(self, callback: Callable[[np.ndarray], None]) -> None:
        if self._running:
            return

        def _cb(indata, _frames, _time, status):
            if status:
                logger.warning("Audio status: %s", status)
            callback(indata.copy())

        self._stream = sd.InputStream(
            samplerate=self.sample_rate,
            channels=self.channels,
            dtype="float32",
            blocksize=self.chunk_size,
            callback=_cb,
        )
        self._stream.start()
        self._running = True
        logger.info("Microphone stream started (%d Hz)", self.sample_rate)

    def stop_mic_stream(self) -> None:
        if self._stream:
            self._stream.stop()
            self._stream.close()
            self._stream = None
        self._running = False

    def record_seconds(self, duration: float = 5.0) -> np.ndarray:
        frames = int(self.sample_rate * duration)
        logger.info("Recording %.1fs of audio...", duration)
        audio = sd.rec(
            frames,
            samplerate=self.sample_rate,
            channels=self.channels,
            dtype="float32",
        )
        sd.wait()
        return audio.flatten()

    def play_audio(self, audio: np.ndarray, sample_rate: int | None = None) -> None:
        sr = sample_rate or self.sample_rate
        sd.play(audio, sr)
        sd.wait()

    @staticmethod
    def play_bytes_async(audio_bytes: bytes, sample_rate: int = 22050) -> threading.Thread:
        """Play raw PCM/wav bytes in background thread."""
        q: queue.Queue[bytes | None] = queue.Queue()

        def _worker():
            try:
                import io
                import wave

                with wave.open(io.BytesIO(audio_bytes), "rb") as wf:
                    sr = wf.getframerate()
                    data = np.frombuffer(wf.readframes(wf.getnframes()), dtype=np.int16)
                    data = data.astype(np.float32) / 32768.0
                    sd.play(data, sr)
                    sd.wait()
            except Exception:
                # Fallback: treat as int16 PCM
                data = np.frombuffer(audio_bytes, dtype=np.int16).astype(np.float32) / 32768.0
                sd.play(data, sample_rate)
                sd.wait()

        t = threading.Thread(target=_worker, daemon=True)
        t.start()
        return t
