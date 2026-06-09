import logging
import threading
import time
from typing import Callable, Optional

import numpy as np

logger = logging.getLogger(__name__)

try:
    import sounddevice as sd
    import scipy.signal
    SD_AVAILABLE = True
except ImportError:
    SD_AVAILABLE = False
    logger.warning("sounddevice or scipy not installed — clap detection disabled")


class ClapDetector:
    """Detects double-claps using sounddevice continuous background stream and transient energy filtering."""
    def __init__(self, on_clap: Callable[[], None]) -> None:
        self.on_clap = on_clap
        self._running = False
        self._stream: Optional[sd.InputStream] = None
        
        self.CHUNK = 1024
        self.CHANNELS = 1
        self.RATE = 16000
        
        # Double clap timing config
        self.CLAP_THRESHOLD = 0.15  # RMS threshold for float32 (-1.0 to 1.0)
        self.MAX_CLAP_INTERVAL = 1.5   # Max seconds between two claps
        self.MIN_CLAP_INTERVAL = 0.4   # Min seconds to avoid echo counting
        
        self._last_clap_time = 0.0

    def start(self) -> None:
        if not SD_AVAILABLE:
            return
        if self._running:
            return
            
        self._running = True
        try:
            self._stream = sd.InputStream(
                channels=self.CHANNELS,
                samplerate=self.RATE,
                blocksize=self.CHUNK,
                callback=self._audio_callback
            )
            self._stream.start()
            logger.info("Clap detector active (background stream)")
        except Exception as e:
            logger.error("Failed to start sounddevice stream for clap detector: %s", e)
            self._running = False

    def stop(self) -> None:
        self._running = False
        if self._stream:
            self._stream.stop()
            self._stream.close()

    def _audio_callback(self, indata: np.ndarray, frames: int, time_info: dict, status: sd.CallbackFlags) -> None:
        if not self._running:
            return
        try:
            if status:
                pass # Ignore status warnings like input overflow for clap detection
                
            audio_data = indata[:, 0]  # Mono channel (float32)
            
            # Simple High-pass filter to remove low freq hum
            b, a = scipy.signal.butter(1, 1000 / (self.RATE / 2), btype='highpass')
            filtered = scipy.signal.lfilter(b, a, audio_data)
            
            rms = np.sqrt(np.mean(filtered**2))
            if rms > self.CLAP_THRESHOLD:
                now = time.time()
                diff = now - self._last_clap_time
                if self.MIN_CLAP_INTERVAL < diff < self.MAX_CLAP_INTERVAL:
                    logger.info("Double clap detected!")
                    self._last_clap_time = 0.0  # Reset
                    # Call in a new thread to not block the audio callback
                    threading.Thread(target=self.on_clap, daemon=True).start()
                elif diff > self.MAX_CLAP_INTERVAL:
                    self._last_clap_time = now
        except Exception as e:
            logger.error("Clap detector callback error: %s", e)
