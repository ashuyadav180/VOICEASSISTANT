"""Main SIRI agent orchestration loop."""

from __future__ import annotations

import asyncio
import logging
import threading
import time
from enum import Enum

import numpy as np

from siri.agent.brain import AgentBrain
from siri.audio.io import AudioIO
from siri.audio.stt import STTPipeline
from siri.audio.tts import TTSPipeline
from siri.audio.wake_word import WakeWordDetector
from siri.config import Config
from siri.logging.store import InteractionLogger
from siri.memory.long_term import LongTermMemory
from siri.memory.short_term import ShortTermMemory
from siri.tools.executor import ToolExecutor
from siri.vision.analyzer import VisionAnalyzer

logger = logging.getLogger(__name__)

LISTEN_DURATION = 5.0
RECORDING_BEEP = True


class AgentState(Enum):
    IDLE = "idle"
    LISTENING = "listening"
    PROCESSING = "processing"
    SPEAKING = "speaking"
    SLEEPING = "sleeping"


class AgentLoop:
    def __init__(self, config: Config) -> None:
        self.config = config
        self.state = AgentState.IDLE
        self.event_queue: asyncio.Queue | None = None
        self._running = False
        self._listen_requested = threading.Event()

        self.audio = AudioIO(config.sample_rate, config.channels, device_index=config.effective_input_device)
        self.stt = STTPipeline(config)
        self.tts = TTSPipeline(config)
        self.logger = InteractionLogger(config.logs_db)
        self.executor = ToolExecutor(config)
        self.short_memory = ShortTermMemory()
        self.long_memory = LongTermMemory(str(config.chroma_dir), config.memory_enabled)
        self.vision = VisionAnalyzer(config)
        self.brain = AgentBrain(
            config, self.executor, self.short_memory, self.long_memory, self.vision
        )

        self.wake_detector = WakeWordDetector(
            wake_word=config.wake_word,
            threshold=config.wake_word_threshold,
            sample_rate=config.sample_rate,
            on_wake=self._on_wake,
            device_index=config.effective_input_device,
        )

    def _emit(self, event_type: str, payload: dict) -> None:
        if self.event_queue:
            try:
                self.event_queue.put_nowait({"type": event_type, **payload})
            except Exception:
                pass

    def _set_state(self, new_state: AgentState) -> None:
        self.state = new_state
        self._emit("state", {"state": new_state.value})


    def _on_wake(self) -> None:
        if self.state in (AgentState.SLEEPING, AgentState.PROCESSING):
            if self.state == AgentState.SLEEPING:
                self._set_state(AgentState.IDLE)
                self.tts.speak("I'm back.")
            return
        if self.state == AgentState.SPEAKING:
            return
        self._listen_requested.set()

    async def start(self) -> None:
        self._running = True
        self.tts.start()
        self.wake_detector.start()
        self._set_state(AgentState.IDLE)

        self.tts.speak(
            "SIRI is online. Say the wake word or press Control Space to talk."
        )
        logger.info("SIRI agent loop started")

        while self._running:
            await self._idle_wait()
            if not self._running:
                break
            await self._listen_and_process()

    async def _idle_wait(self) -> None:
        while self._running and self.state != AgentState.SLEEPING:
            if self._listen_requested.is_set():
                self._listen_requested.clear()
                return
            await asyncio.sleep(0.05)

    async def _listen_and_process(self) -> None:
        self.wake_detector.stop()
        self._set_state(AgentState.LISTENING)
        logger.info("Listening...")

        loop = asyncio.get_event_loop()
        audio = await loop.run_in_executor(
            None, lambda: self.audio.record_seconds(LISTEN_DURATION)
        )

        if audio is None or len(audio) < self.config.sample_rate * 0.3:
            self._set_state(AgentState.IDLE)
            self.wake_detector.start()
            return

        self._set_state(AgentState.PROCESSING)
        transcript = await self.stt.transcribe_audio(audio)

        if not transcript or len(transcript.strip()) < 2:
            self._set_state(AgentState.IDLE)
            self.wake_detector.start()
            return

        logger.info("Transcript: %s", transcript)
        self.logger.log("user", transcript)
        self._emit("transcript", {"role": "user", "text": transcript})

        response = await self.brain.process(transcript)

        if response == "__SLEEP__":
            self._set_state(AgentState.SLEEPING)
            self.wake_detector.stop()
            self.tts.speak("Going to sleep. Press Control Space when you need me.")
            self.wake_detector.start()
            self._set_state(AgentState.SLEEPING)
            return

        self.logger.log("assistant", response)
        self._emit("transcript", {"role": "assistant", "text": response})
        self._set_state(AgentState.SPEAKING)
        self.tts.speak(response)
        time.sleep(0.3)
        self._set_state(AgentState.IDLE)
        self.wake_detector.start()

    def stop(self) -> None:
        self._running = False
        self.wake_detector.stop()
        self.tts.stop()
        self.audio.stop_mic_stream()
        logger.info("SIRI agent loop stopped")

    async def process_text(self, text: str) -> str:
        """Text input mode for testing without microphone."""
        self.logger.log("user", text)
        self._emit("transcript", {"role": "user", "text": text})
        self._set_state(AgentState.PROCESSING)
        response = await self.brain.process(text)
        if response != "__SLEEP__":
            self.logger.log("assistant", response)
            self._emit("transcript", {"role": "assistant", "text": response})
            self._set_state(AgentState.SPEAKING)
            self.tts.speak(response)
            time.sleep(0.3)
        self._set_state(AgentState.IDLE)
        return response
