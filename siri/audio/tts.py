"""Text-to-speech: ElevenLabs + Piper fallback with background queue."""

from __future__ import annotations

import asyncio
import logging
import queue
import re
import threading
from pathlib import Path

import numpy as np

from siri.audio.io import AudioIO
from siri.config import Config

logger = logging.getLogger(__name__)


def _strip_for_speech(text: str) -> str:
    """Remove markdown, URLs, and technical formatting from spoken text."""
    text = re.sub(r"https?://\S+", "the page", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    text = re.sub(r"[#*_`]", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


class TTSPipeline:
    def __init__(self, config: Config) -> None:
        self.config = config
        self._queue: queue.Queue[str | None] = queue.Queue()
        self._worker = threading.Thread(target=self._worker_loop, daemon=True)
        self._running = False
        self._speaking = threading.Event()

    def start(self) -> None:
        if not self._running:
            self._running = True
            self._worker.start()
            logger.info("TTS queue started")

    def stop(self) -> None:
        self._queue.put(None)
        self._running = False

    def speak(self, text: str, block: bool = False) -> None:
        clean = _strip_for_speech(text)
        if not clean:
            return
        self._queue.put(clean)
        if block:
            self._queue.join()

    def is_speaking(self) -> bool:
        return self._speaking.is_set()

    def _worker_loop(self) -> None:
        while self._running:
            try:
                text = self._queue.get(timeout=0.5)
            except queue.Empty:
                continue
            if text is None:
                break
            try:
                self._speaking.set()
                asyncio.run(self._synthesize_and_play(text))
            except Exception as e:
                logger.error("TTS error: %s", e)
            finally:
                self._speaking.clear()
                self._queue.task_done()

    async def _synthesize_and_play(self, text: str) -> None:
        provider = self.config.effective_tts_provider
        if provider == "elevenlabs" and self.config.elevenlabs_api_key:
            audio = await self._elevenlabs(text)
        else:
            audio = await self._piper(text)

        if audio is not None:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, lambda: AudioIO.play_audio(audio, 22050))

    async def _elevenlabs(self, text: str) -> np.ndarray | None:
        try:
            import aiohttp

            url = f"https://api.elevenlabs.io/v1/text-to-speech/{self.config.elevenlabs_voice_id}"
            headers = {
                "xi-api-key": self.config.elevenlabs_api_key,
                "Content-Type": "application/json",
                "Accept": "audio/mpeg",
            }
            payload = {
                "text": text,
                "model_id": "eleven_turbo_v2_5",
                "voice_settings": {"stability": 0.5, "similarity_boost": 0.75},
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=payload) as resp:
                    if resp.status != 200:
                        logger.error("ElevenLabs error: %s", await resp.text())
                        return await self._piper(text)
                    mp3_bytes = await resp.read()

            return await self._decode_mp3(mp3_bytes)
        except Exception as e:
            logger.warning("ElevenLabs failed: %s", e)
            return await self._piper(text)

    async def _piper(self, text: str) -> np.ndarray | None:
        """Offline TTS via pyttsx3 (cross-platform fallback for Piper)."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._pyttsx3_speak_capture, text)

    @staticmethod
    def _pyttsx3_speak_capture(text: str) -> np.ndarray | None:
        try:
            import pyttsx3

            engine = pyttsx3.init()
            engine.setProperty("rate", 175)
            engine.say(text)
            engine.runAndWait()
            return None  # pyttsx3 plays directly
        except Exception as e:
            logger.error("Offline TTS failed: %s", e)
            print(f"SIRI: {text}")
            return None

    @staticmethod
    async def _decode_mp3(mp3_bytes: bytes) -> np.ndarray:
        import io

        from pydub import AudioSegment

        segment = AudioSegment.from_mp3(io.BytesIO(mp3_bytes))
        segment = segment.set_frame_rate(22050).set_channels(1)
        samples = np.array(segment.get_array_of_samples(), dtype=np.float32)
        samples /= np.iinfo(np.int16).max
        return samples
