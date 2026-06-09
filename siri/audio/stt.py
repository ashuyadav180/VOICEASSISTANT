"""Speech-to-text: Deepgram streaming + faster-whisper fallback."""

from __future__ import annotations

import asyncio
import json
import logging
from typing import AsyncIterator

import numpy as np

from siri.config import Config

logger = logging.getLogger(__name__)

try:
    from faster_whisper import WhisperModel

    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False


class STTPipeline:
    def __init__(self, config: Config) -> None:
        self.config = config
        self._whisper: WhisperModel | None = None

    def _get_whisper(self) -> WhisperModel:
        if not WHISPER_AVAILABLE:
            raise RuntimeError("faster-whisper not installed. Run: pip install faster-whisper")
        if self._whisper is None:
            logger.info("Loading faster-whisper model (base)...")
            self._whisper = WhisperModel("base", device="cpu", compute_type="int8")
        return self._whisper

    async def transcribe_audio(self, audio: np.ndarray) -> str:
        provider = self.config.effective_stt_provider
        if provider == "deepgram" and self.config.deepgram_api_key:
            return await self._transcribe_deepgram(audio)
        return await self._transcribe_whisper(audio)

    async def _transcribe_whisper(self, audio: np.ndarray) -> str:
        loop = asyncio.get_event_loop()

        def _run():
            model = self._get_whisper()
            if audio.dtype == np.float32:
                audio_f = audio
            else:
                audio_f = audio.astype(np.float32) / 32768.0
            segments, info = model.transcribe(audio_f, language=None, vad_filter=True)
            text = " ".join(s.text.strip() for s in segments)
            logger.info("Detected language: %s (prob: %.2f)", info.language, info.language_probability)
            return self._clean_disfluencies(text)

        return await loop.run_in_executor(None, _run)

    async def _transcribe_deepgram(self, audio: np.ndarray) -> str:
        try:
            import io
            import wave

            import aiohttp

            if audio.dtype != np.int16:
                audio_i16 = (audio * 32767).astype(np.int16)
            else:
                audio_i16 = audio

            buf = io.BytesIO()
            with wave.open(buf, "wb") as wf:
                wf.setnchannels(self.config.channels)
                wf.setsampwidth(2)
                wf.setframerate(self.config.sample_rate)
                wf.writeframes(audio_i16.tobytes())
            buf.seek(0)

            url = "https://api.deepgram.com/v1/listen?model=nova-3&smart_format=true&punctuate=true&detect_language=true"
            headers = {
                "Authorization": f"Token {self.config.deepgram_api_key}",
                "Content-Type": "audio/wav",
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, data=buf.read()) as resp:
                    if resp.status != 200:
                        err = await resp.text()
                        logger.error("Deepgram error %s: %s", resp.status, err)
                        return await self._transcribe_whisper(audio)
                    data = await resp.json()
                    transcript = (
                        data.get("results", {})
                        .get("channels", [{}])[0]
                        .get("alternatives", [{}])[0]
                        .get("transcript", "")
                    )
                    return self._clean_disfluencies(transcript)
        except Exception as e:
            logger.warning("Deepgram failed, falling back to whisper: %s", e)
            return await self._transcribe_whisper(audio)

    @staticmethod
    def _clean_disfluencies(text: str) -> str:
        fillers = {"uh", "um", "uhh", "umm", "er", "ah"}
        words = text.split()
        cleaned = [w for w in words if w.lower().strip(".,!?") not in fillers]
        return " ".join(cleaned).strip()

    async def transcribe_file(self, path: str) -> str:
        import soundfile as sf

        audio, sr = sf.read(path, dtype="float32")
        if sr != self.config.sample_rate:
            import librosa

            audio = librosa.resample(audio, orig_sr=sr, target_sr=self.config.sample_rate)
        return await self.transcribe_audio(audio)
