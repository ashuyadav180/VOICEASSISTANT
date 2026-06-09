"""SIRI entry point."""

from __future__ import annotations

import argparse
import asyncio
import logging
import signal
import sys

from siri.agent.loop import AgentLoop
from siri.config import config


def setup_logging(level: str = "INFO") -> None:
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )


def run_setup_wizard() -> None:
    """First-run setup: mic test + API key check."""
    print("\n=== SIRI Setup Wizard ===\n")

    from siri.audio.io import AudioIO

    audio = AudioIO(config.sample_rate, config.channels)
    devices = audio.list_devices()
    print("Available microphones:")
    for d in devices:
        print(f"  [{d['index']}] {d['name']}")

    print("\nAPI Key Status:")
    print(f"  LLM:        {'OK' if config.has_llm() else 'MISSING — set ANTHROPIC_API_KEY or OPENAI_API_KEY'}")
    print(f"  Deepgram:   {'OK' if config.deepgram_api_key else 'MISSING — will use local Whisper'}")
    print(f"  ElevenLabs: {'OK' if config.elevenlabs_api_key else 'MISSING — will use offline TTS'}")
    print(f"  Tavily:     {'OK' if config.tavily_api_key else 'MISSING — will use DuckDuckGo fallback'}")

    if config.offline_mode:
        print("\n  Offline mode: ENABLED")

    print("\nDownloading wake word models (one-time)...")
    try:
        import openwakeword

        openwakeword.utils.download_models()
        print("  Wake word models: OK")
    except Exception as e:
        print(f"  Wake word models: FAILED — {e} (Ctrl+Space still works)")

    print("\nTesting 3-second recording...")
    try:
        audio.record_seconds(3.0)
        print("  Microphone: OK")
    except Exception as e:
        print(f"  Microphone: FAILED — {e}")

    print("\nInstalling Playwright browser (one-time)...")
    try:
        import subprocess

        subprocess.run(
            [sys.executable, "-m", "playwright", "install", "chromium"],
            check=True,
            timeout=300,
        )
        print("  Playwright Chromium: OK")
    except Exception as e:
        print(f"  Playwright: FAILED — {e}")

    print("\nSetup complete. Run: python -m siri.main\n")


async def main_async(args: argparse.Namespace) -> None:
    loop = AgentLoop(config)

    def _shutdown(*_):
        print("\nShutting down SIRI...")
        loop.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, _shutdown)
    if sys.platform != "win32":
        signal.signal(signal.SIGTERM, _shutdown)

    if args.text:
        await loop.process_text(args.text)
        return

    if args.ui:
        import uvicorn
        from siri.api.server import app
        app.state.agent_loop = loop
        
        # Suppress uvicorn logs unless log-level is debug
        log_level = "info" if args.log_level.lower() == "debug" else "warning"
        server = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=8888, log_level=log_level))
        
        print("UI Server running at http://127.0.0.1:8888")
        
        # We start both the uvicorn server and the agent loop
        await asyncio.gather(
            server.serve(),
            loop.start()
        )
    else:
        await loop.start()


def main() -> None:
    parser = argparse.ArgumentParser(description="SIRI — Voice-first desktop agent")
    parser.add_argument("--setup", action="store_true", help="Run first-run setup wizard")
    parser.add_argument("--ui", action="store_true", help="Start the Web UI server at localhost:8888")
    parser.add_argument("--text", type=str, help="Process a text command (no mic)")
    parser.add_argument("--log-level", type=str, default=config.log_level)
    args = parser.parse_args()

    setup_logging(args.log_level)

    if args.setup:
        run_setup_wizard()
        return

    print("Starting SIRI...")
    print(f"  STT: {config.effective_stt_provider}")
    print(f"  TTS: {config.effective_tts_provider}")
    print(f"  LLM: {config.llm_provider} ({'configured' if config.has_llm() else 'NOT configured'})")
    print(f"  Wake: '{config.wake_word}' + Ctrl+Space")
    print()

    asyncio.run(main_async(args))


if __name__ == "__main__":
    main()
