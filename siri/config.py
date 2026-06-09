"""SIRI configuration loader."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"
NOTES_DIR = DATA_DIR / "notes"
CHROMA_DIR = DATA_DIR / "chroma"
LOGS_DB = DATA_DIR / "logs.db"

for d in (DATA_DIR, NOTES_DIR, CHROMA_DIR):
    d.mkdir(parents=True, exist_ok=True)

load_dotenv(ROOT_DIR / ".env")


def _bool(key: str, default: bool = False) -> bool:
    return os.getenv(key, str(default)).lower() in ("1", "true", "yes", "on")


def _int(key: str, default: int) -> int:
    try:
        return int(os.getenv(key, str(default)))
    except ValueError:
        return default


@dataclass
class Config:
    # API keys
    deepgram_api_key: str = field(default_factory=lambda: os.getenv("DEEPGRAM_API_KEY", ""))
    elevenlabs_api_key: str = field(default_factory=lambda: os.getenv("ELEVENLABS_API_KEY", ""))
    elevenlabs_voice_id: str = field(
        default_factory=lambda: os.getenv("ELEVENLABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM")
    )
    anthropic_api_key: str = field(default_factory=lambda: os.getenv("ANTHROPIC_API_KEY", ""))
    openai_api_key: str = field(default_factory=lambda: os.getenv("OPENAI_API_KEY", ""))
    tavily_api_key: str = field(default_factory=lambda: os.getenv("TAVILY_API_KEY", ""))

    # LLM
    llm_provider: str = field(default_factory=lambda: os.getenv("LLM_PROVIDER", "anthropic"))
    llm_model: str = field(
        default_factory=lambda: os.getenv("LLM_MODEL", "claude-sonnet-4-20250514")
    )

    # Audio / wake
    wake_word: str = field(default_factory=lambda: os.getenv("WAKE_WORD", "siri"))
    wake_word_threshold: float = field(
        default_factory=lambda: float(os.getenv("WAKE_WORD_THRESHOLD", "0.5"))
    )
    sample_rate: int = field(default_factory=lambda: _int("SAMPLE_RATE", 16000))
    channels: int = field(default_factory=lambda: _int("CHANNELS", 1))

    # Providers
    stt_provider: str = field(default_factory=lambda: os.getenv("STT_PROVIDER", "deepgram"))
    tts_provider: str = field(default_factory=lambda: os.getenv("TTS_PROVIDER", "elevenlabs"))
    offline_mode: bool = field(default_factory=lambda: _bool("OFFLINE_MODE", False))

    # Features
    screen_vision_enabled: bool = field(default_factory=lambda: _bool("SCREEN_VISION_ENABLED", True))
    memory_enabled: bool = field(default_factory=lambda: _bool("MEMORY_ENABLED", True))
    log_level: str = field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))

    # Paths
    root_dir: Path = field(default_factory=lambda: ROOT_DIR)
    data_dir: Path = field(default_factory=lambda: DATA_DIR)
    notes_dir: Path = field(default_factory=lambda: NOTES_DIR)
    chroma_dir: Path = field(default_factory=lambda: CHROMA_DIR)
    logs_db: Path = field(default_factory=lambda: LOGS_DB)
    system_prompt_path: Path = field(
        default_factory=lambda: ROOT_DIR / "siri" / "system_prompt.txt"
    )

    @property
    def effective_stt_provider(self) -> str:
        if self.offline_mode or not self.deepgram_api_key:
            return "whisper_local"
        return self.stt_provider

    @property
    def effective_tts_provider(self) -> str:
        if self.offline_mode or not self.elevenlabs_api_key:
            return "piper"
        return self.tts_provider

    @property
    def llm_api_key(self) -> str:
        if self.llm_provider == "openai":
            return self.openai_api_key
        return self.anthropic_api_key

    def has_llm(self) -> bool:
        return bool(self.llm_api_key)


config = Config()
