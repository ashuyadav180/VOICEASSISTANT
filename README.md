# SIRI — Voice-First Desktop Agent

Autonomous voice-controlled AI agent for Windows. Wake word or Ctrl+Space → speak → SIRI acts on your machine and talks back.

## Features

- **Wake word** detection (OpenWakeWord) + Ctrl+Space fallback
- **Speech-to-text** — Deepgram Nova (cloud) or faster-whisper (offline)
- **Text-to-speech** — ElevenLabs (cloud) or pyttsx3 (offline)
- **LLM brain** — Claude or GPT-4o with 70+ tools
- **Computer control** — mouse, keyboard, screenshots, windows
- **File system** — read, write, search, zip
- **Browser automation** — Playwright (Chrome)
- **System control** — battery, volume, processes, clipboard
- **Memory** — short-term context + ChromaDB long-term
- **Vision** — screen understanding via vision LLM

## Quick Start

```bash
# 1. Install dependencies
python -m pip install -r requirements.txt
python -m playwright install chromium

# 2. Configure API keys
copy .env.example .env
# Edit .env with your keys

# 3. Run setup wizard
python -m siri.main --setup

# 4. Start SIRI
python -m siri.main
```

## Usage

| Action | How |
|--------|-----|
| Activate | Say wake word or press **Ctrl+Space** |
| Talk | Speak for up to 5 seconds after activation |
| Text mode | `python -m siri.main --text "open notepad"` |
| Sleep | Say "Siri, go to sleep" |

## API Keys

| Key | Required | Fallback |
|-----|----------|----------|
| `ANTHROPIC_API_KEY` or `OPENAI_API_KEY` | Recommended | Basic rule-based commands |
| `DEEPGRAM_API_KEY` | Optional | faster-whisper (local) |
| `ELEVENLABS_API_KEY` | Optional | pyttsx3 (local) |
| `TAVILY_API_KEY` | Optional | DuckDuckGo |

Set `OFFLINE_MODE=true` to force local STT + TTS.

## Project Structure

```
siri/
├── main.py              # Entry point
├── config.py            # Configuration
├── audio/               # Wake word, STT, TTS
├── agent/               # Brain, loop, LangGraph
├── tools/               # 70+ tool implementations
├── memory/              # Short + long term memory
├── vision/              # Screen analysis
└── logging/             # SQLite interaction log
```

## Build Executable

```bash
pyinstaller siri.spec
# Output: dist/SIRI.exe
```

## Tests

```bash
python -m pytest tests/ -v
```
