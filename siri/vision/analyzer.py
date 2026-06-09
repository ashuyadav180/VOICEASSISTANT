"""Screen vision analysis using vision-capable LLM."""

from __future__ import annotations

import base64
import json
import logging
import urllib.request
from typing import Any

from siri.config import Config
from siri.tools import computer

logger = logging.getLogger(__name__)


class VisionAnalyzer:
    def __init__(self, config: Config) -> None:
        self.config = config

    def capture_screen_b64(self) -> str | None:
        result = computer.take_screenshot()
        if result["success"]:
            return result["result"]["base64"]
        return None

    async def explain_screen(self) -> dict:
        b64 = self.capture_screen_b64()
        if not b64:
            return {"success": False, "result": None, "error": "Screenshot failed"}
        return await self._analyze_image(b64, "Describe what is on this computer screen in 2-3 sentences.")

    async def answer_from_screen(self, question: str) -> dict:
        b64 = self.capture_screen_b64()
        if not b64:
            return {"success": False, "result": None, "error": "Screenshot failed"}
        return await self._analyze_image(b64, question)

    async def _analyze_image(self, b64: str, prompt: str) -> dict:
        if not self.config.has_llm():
            return {
                "success": True,
                "result": "Screen captured but no LLM API key configured for vision analysis.",
                "error": None,
            }

        if self.config.llm_provider == "anthropic":
            return await self._anthropic_vision(b64, prompt)
        return await self._openai_vision(b64, prompt)

    async def _anthropic_vision(self, b64: str, prompt: str) -> dict:
        try:
            import aiohttp

            payload = {
                "model": self.config.llm_model,
                "max_tokens": 500,
                "messages": [{
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/png",
                                "data": b64,
                            },
                        },
                        {"type": "text", "text": prompt},
                    ],
                }],
            }
            headers = {
                "x-api-key": self.config.anthropic_api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            }
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "https://api.anthropic.com/v1/messages",
                    headers=headers,
                    json=payload,
                ) as resp:
                    data = await resp.json()
                    if resp.status != 200:
                        return {"success": False, "result": None, "error": str(data)}
                    text = data["content"][0]["text"]
                    return {"success": True, "result": text, "error": None}
        except Exception as e:
            return {"success": False, "result": None, "error": str(e)}

    async def _openai_vision(self, b64: str, prompt: str) -> dict:
        try:
            import aiohttp

            payload = {
                "model": "gpt-4o",
                "messages": [{
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/png;base64,{b64}"},
                        },
                    ],
                }],
                "max_tokens": 500,
            }
            headers = {
                "Authorization": f"Bearer {self.config.openai_api_key}",
                "Content-Type": "application/json",
            }
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers=headers,
                    json=payload,
                ) as resp:
                    data = await resp.json()
                    if resp.status != 200:
                        return {"success": False, "result": None, "error": str(data)}
                    text = data["choices"][0]["message"]["content"]
                    return {"success": True, "result": text, "error": None}
        except Exception as e:
            return {"success": False, "result": None, "error": str(e)}
