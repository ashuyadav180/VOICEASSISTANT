"""Wake word detection with OpenWakeWord + keyboard fallback."""

from __future__ import annotations

import logging
import threading
from typing import Callable

import numpy as np

logger = logging.getLogger(__name__)

from siri.audio.clap_detector import ClapDetector

try:
    from openwakeword.model import Model as OWWModel

    OWW_AVAILABLE = True
except ImportError:
    OWW_AVAILABLE = False
    logger.warning("openwakeword not installed — wake word uses keyboard fallback only")

try:
    import keyboard

    KEYBOARD_AVAILABLE = True
except ImportError:
    KEYBOARD_AVAILABLE = False


class WakeWordDetector:
    def __init__(
        self,
        wake_word: str = "siri",
        threshold: float = 0.5,
        sample_rate: int = 16000,
        on_wake: Callable[[], None] | None = None,
    ) -> None:
        self.wake_word = wake_word.lower()
        self.threshold = threshold
        self.sample_rate = sample_rate
        self.on_wake = on_wake
        self._model: OWWModel | None = None
        self._active = False
        self._keyboard_hooked = False
        self._clap_detector = ClapDetector(on_clap=self._trigger)

        if OWW_AVAILABLE:
            try:
                import openwakeword

                openwakeword.utils.download_models()
                # No "siri" model — map to closest pre-trained wake words
                model_map = {
                    "siri": "hey_jarvis",
                    "hey siri": "hey_jarvis",
                    "jarvis": "hey_jarvis",
                    "alexa": "alexa",
                    "mycroft": "hey_mycroft",
                }
                target = model_map.get(self.wake_word, "hey_jarvis")
                self._model = OWWModel(
                    wakeword_models=[target],
                    inference_framework="onnx",
                )
                logger.info(
                    "OpenWakeWord loaded (wake='%s' → model='%s')",
                    self.wake_word,
                    target,
                )
            except Exception as e:
                logger.warning("Failed to load OpenWakeWord: %s", e)

    def _trigger(self) -> None:
        logger.info("Wake word triggered!")
        if self.on_wake:
            self.on_wake()

    def process_audio(self, audio_chunk: np.ndarray) -> None:
        if not self._active or not self._model:
            return
        # openwakeword expects int16
        if audio_chunk.dtype == np.float32:
            audio_int16 = (audio_chunk * 32767).astype(np.int16)
        else:
            audio_int16 = audio_chunk.astype(np.int16)

        prediction = self._model.predict(audio_int16)
        for model_name, score in prediction.items():
            if score >= self.threshold:
                # Match custom wake word or any high-confidence detection
                if self.wake_word in model_name.lower() or score >= self.threshold + 0.2:
                    self._trigger()
                    break

    def start(self) -> None:
        self._active = True
        self._setup_keyboard_fallback()
        self._clap_detector.start()
        logger.info("Wake word detector active (threshold=%.2f)", self.threshold)

    def stop(self) -> None:
        self._active = False
        self._clap_detector.stop()
        if KEYBOARD_AVAILABLE and self._keyboard_hooked:
            try:
                keyboard.remove_hotkey("ctrl+space")
            except Exception:
                pass
            self._keyboard_hooked = False

    def _setup_keyboard_fallback(self) -> None:
        if not KEYBOARD_AVAILABLE:
            logger.warning("keyboard module unavailable — install 'keyboard' for Ctrl+Space fallback")
            return

        def _hotkey():
            if self._active:
                self._trigger()

        try:
            keyboard.add_hotkey("ctrl+space", _hotkey, suppress=False)
            self._keyboard_hooked = True
            logger.info("Keyboard fallback active: Ctrl+Space")
        except Exception as e:
            logger.warning("Could not register Ctrl+Space hotkey: %s", e)

    def trigger_manual(self) -> None:
        """Manual trigger for testing."""
        threading.Thread(target=self._trigger, daemon=True).start()
