"""LLM agent brain with tool-use loop."""

from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Any

from siri.config import Config
from siri.memory.long_term import LongTermMemory
from siri.memory.short_term import ShortTermMemory
from siri.tools.executor import ToolExecutor
from siri.tools.registry import get_anthropic_tools, get_openai_tools
from siri.vision.analyzer import VisionAnalyzer

logger = logging.getLogger(__name__)

MAX_TOOL_CALLS = 8


class AgentBrain:
    def __init__(
        self,
        config: Config,
        executor: ToolExecutor,
        short_memory: ShortTermMemory,
        long_memory: LongTermMemory,
        vision: VisionAnalyzer,
    ) -> None:
        self.config = config
        self.executor = executor
        self.short_memory = short_memory
        self.long_memory = long_memory
        self.vision = vision
        self.system_prompt = self._load_system_prompt()
        self._tool_call_count = 0

    def _load_system_prompt(self) -> str:
        path = self.config.system_prompt_path
        if path.exists():
            return path.read_text(encoding="utf-8")
        return "You are SIRI, an autonomous desktop agent. Execute tasks using tools. Keep spoken responses to 1-2 sentences."

    def _build_system_state(self) -> dict:
        from siri.tools import computer, system

        state: dict[str, Any] = {"time": datetime.now().isoformat()}
        try:
            win = computer.get_active_window()
            if win["success"]:
                state["active_window"] = win["result"]
        except Exception:
            pass
        try:
            bat = system.get_battery_status()
            if bat["success"] and bat["result"].get("percent") is not None:
                state["battery"] = f"{bat['result']['percent']}%"
        except Exception:
            pass
        return state

    async def process(self, transcript: str, confirmed: bool = False) -> str:
        self._tool_call_count = 0

        if confirmed and self.executor.has_pending_confirmation():
            result = self.executor.confirm_pending()
            if result:
                return self._format_tool_result(result)

        # Handle sleep command locally
        lower = transcript.lower().strip()
        if any(p in lower for p in ("go to sleep", "stop listening", "goodbye siri")):
            return "__SLEEP__"

        if lower in ("yes", "yeah", "yep", "confirm", "proceed") and self.executor.has_pending_confirmation():
            result = self.executor.confirm_pending()
            return self._format_tool_result(result) if result else "Nothing pending to confirm."

        memory_context = self.long_memory.retrieve(transcript) if self.config.memory_enabled else []
        system_state = self._build_system_state()

        self.short_memory.add("user", transcript)

        if not self.config.has_llm():
            return await self._fallback_handler(transcript)

        response = await self._llm_loop(transcript, memory_context, system_state)

        self.short_memory.add("assistant", response)

        if self.config.memory_enabled and len(transcript) > 10:
            facts = self._extract_facts(transcript, response)
            for fact in facts:
                self.long_memory.store(fact)

        return response

    async def _llm_loop(
        self,
        transcript: str,
        memory_context: list[str],
        system_state: dict,
    ) -> str:
        messages = self._build_messages(transcript, memory_context, system_state)

        for _ in range(MAX_TOOL_CALLS):
            llm_response = await self._call_llm(messages)
            tool_calls = llm_response.get("tool_calls", [])

            if not tool_calls:
                text = llm_response.get("text", "Done.")
                return text

            tool_results = []
            for tc in tool_calls:
                self._tool_call_count += 1
                name = tc["name"]
                args = tc.get("arguments", {})

                # Route vision tools
                if name == "explain_screen":
                    result = await self.vision.explain_screen()
                elif name == "answer_from_screen":
                    result = await self.vision.answer_from_screen(args.get("question", ""))
                elif name == "summarize_document":
                    result = await self._summarize_document(args.get("path", ""))
                elif name == "code_review":
                    result = await self._code_review(args.get("path", ""))
                elif name == "draft_email":
                    result = await self._draft_email(args.get("context", ""))
                elif name == "generate_image":
                    result = {"success": False, "result": None, "error": "Image generation requires DALL-E API key setup"}
                else:
                    result = self.executor.execute(name, args)

                if result.get("needs_confirmation"):
                    return f"I need your confirmation to {name.replace('_', ' ')}. Say yes to proceed."

                tool_results.append({"tool": name, "result": result})
                messages.append({
                    "role": "assistant",
                    "content": json.dumps({"tool_call": name, "arguments": args}),
                })
                messages.append({
                    "role": "user",
                    "content": f"Tool result for {name}: {json.dumps(result, default=str)[:4000]}",
                })

        return "I've done what I can for that request."

    def _build_messages(
        self,
        transcript: str,
        memory_context: list[str],
        system_state: dict,
    ) -> list[dict]:
        memory_block = ""
        if memory_context:
            memory_block = "\nRelevant memory:\n" + "\n".join(f"- {m}" for m in memory_context)

        system = (
            f"{self.system_prompt}\n\n"
            f"System state: {json.dumps(system_state)}\n"
            f"{memory_block}\n\n"
            "Respond with tool calls to execute tasks, then a short spoken response when done. "
            "Keep final spoken text to 1-2 sentences."
        )

        messages = [{"role": "system", "content": system}]
        messages.extend(self.short_memory.to_context())
        messages.append({"role": "user", "content": transcript})
        return messages

    async def _call_llm(self, messages: list[dict]) -> dict:
        primary = self.config.llm_provider
        providers = [primary]
        for p in ["gemini", "openai", "anthropic"]:
            if p not in providers:
                providers.append(p)

        last_error = "No LLM provider responded."
        for provider in providers:
            # Check if API key is present
            if provider == "anthropic" and not self.config.anthropic_api_key:
                continue
            if provider == "openai" and not self.config.openai_api_key:
                continue
            if provider == "gemini" and not self.config.gemini_api_key:
                continue

            try:
                logger.info(f"Attempting to call LLM via provider: {provider}")
                if provider == "anthropic":
                    res = await self._call_anthropic(messages)
                elif provider == "gemini":
                    res = await self._call_gemini(messages)
                else: # openai
                    res = await self._call_openai(messages)
                
                # Succeeded - make it sticky
                if provider != self.config.llm_provider:
                    logger.info(f"Switching primary LLM provider to: {provider}")
                    self.config.llm_provider = provider
                return res
            except Exception as e:
                logger.warning(f"Provider {provider} failed: {e}")
                last_error = f"{provider} failed: {e}"

        logger.error(f"All LLM providers failed: {last_error}")
        return {"text": f"I had trouble thinking that through. Errors: {last_error}", "tool_calls": []}

    async def _call_gemini(self, messages: list[dict]) -> dict:
        import aiohttp

        primary_model = self.config.llm_model if self.config.llm_model and "gemini" in self.config.llm_model else "gemini-2.5-flash-lite"
        models = [primary_model]
        for m in ["gemini-2.5-flash-lite", "gemini-2.5-flash"]:
            if m not in models:
                models.append(m)

        last_error = ""
        for model in models:
            payload = {
                "model": model,
                "messages": messages,
                "tools": get_openai_tools(),
                "max_tokens": 1024,
            }
            headers = {
                "Authorization": f"Bearer {self.config.gemini_api_key}",
                "Content-Type": "application/json",
            }

            try:
                logger.info(f"Attempting Gemini model: {model}")
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions",
                        headers=headers,
                        json=payload,
                    ) as resp:
                        data = await resp.json()
                        if resp.status == 200:
                            msg = data["choices"][0]["message"]
                            tool_calls = []
                            for tc in msg.get("tool_calls", []):
                                tool_calls.append({
                                    "name": tc["function"]["name"],
                                    "arguments": json.loads(tc["function"]["arguments"]),
                                })
                            if model != self.config.llm_model and "gemini" in self.config.llm_model:
                                logger.info(f"Switching primary Gemini model to: {model}")
                                self.config.llm_model = model
                            return {"text": msg.get("content") or "", "tool_calls": tool_calls}
                        else:
                            logger.warning(f"Gemini model {model} failed with status {resp.status}: {data}")
                            last_error = f"status {resp.status}, response: {data}"
            except Exception as e:
                logger.warning(f"Gemini model {model} raised exception: {e}")
                last_error = str(e)

        raise RuntimeError(f"All Gemini models failed: {last_error}")

    async def _call_anthropic(self, messages: list[dict]) -> dict:
        import aiohttp

        system_msg = next((m["content"] for m in messages if m["role"] == "system"), "")
        chat_msgs = [m for m in messages if m["role"] != "system"]

        model = self.config.llm_model if "claude" in self.config.llm_model else "claude-3-5-sonnet-20241022"
        payload = {
            "model": model,
            "max_tokens": 1024,
            "system": system_msg,
            "messages": chat_msgs,
            "tools": get_anthropic_tools(),
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
                    raise RuntimeError(f"status {resp.status}, response: {data}")

                tool_calls = []
                text_parts = []
                for block in data.get("content", []):
                    if block["type"] == "text":
                        text_parts.append(block["text"])
                    elif block["type"] == "tool_use":
                        tool_calls.append({
                            "name": block["name"],
                            "arguments": block.get("input", {}),
                        })

                return {
                    "text": " ".join(text_parts),
                    "tool_calls": tool_calls,
                }

    async def _call_openai(self, messages: list[dict]) -> dict:
        import aiohttp

        payload = {
            "model": self.config.llm_model if "gpt" in self.config.llm_model else "gpt-4o",
            "messages": messages,
            "tools": get_openai_tools(),
            "max_tokens": 1024,
        }
        headers = {
            "Authorization": f"Bearer {self.config.openai_api_key}",
            "Content-Type": "application/json",
        }

        base_url = self.config.llm_base_url or "https://api.openai.com/v1"
        url = f"{base_url.rstrip('/')}/chat/completions"
        async with aiohttp.ClientSession() as session:
            async with session.post(
                url,
                headers=headers,
                json=payload,
            ) as resp:
                data = await resp.json()
                if resp.status != 200:
                    raise RuntimeError(f"status {resp.status}, response: {data}")

                msg = data["choices"][0]["message"]
                tool_calls = []
                for tc in msg.get("tool_calls", []):
                    tool_calls.append({
                        "name": tc["function"]["name"],
                        "arguments": json.loads(tc["function"]["arguments"]),
                    })
                return {"text": msg.get("content") or "", "tool_calls": tool_calls}

    async def _fallback_handler(self, transcript: str) -> str:
        """Rule-based fallback when no LLM API key."""
        lower = transcript.lower()

        if "time" in lower:
            return f"It's {datetime.now().strftime('%I:%M %p')}."

        if "battery" in lower:
            from siri.tools import system
            r = system.get_battery_status()
            if r["success"] and r["result"].get("percent"):
                return f"Battery is at {r['result']['percent']}%."
            return "No battery info available."

        if "open" in lower:
            for app in ("notepad", "chrome", "calculator", "spotify", "vscode", "vs code"):
                if app in lower:
                    from siri.tools import apps
                    apps.open_app(app)
                    return f"Opening {app}."

        if "screenshot" in lower or "screen" in lower:
            r = await self.vision.explain_screen()
            return r.get("result", "I took a screenshot but can't analyze it without an API key.")

        if "search" in lower:
            query = lower.replace("search", "").replace("for", "").strip()
            from siri.tools import search as search_tools
            r = search_tools.search_web(query, self.config.tavily_api_key)
            if r["success"]:
                answer = r["result"].get("answer") or r["result"].get("results", [{}])[0].get("snippet", "")
                return answer[:200] or "I found some results."
            return "Search failed."

        return "I need an API key to handle that. Set ANTHROPIC_API_KEY or OPENAI_API_KEY in .env."

    async def _summarize_document(self, path: str) -> dict:
        from siri.tools import filesystem
        r = filesystem.read_file(path)
        if not r["success"]:
            return r
        content = r["result"][:8000]
        if not self.config.has_llm():
            return {"success": True, "result": content[:500], "error": None}
        messages = [{"role": "user", "content": f"Summarize this document in 3 sentences:\n\n{content}"}]
        resp = await self._call_llm([{"role": "system", "content": "Summarize concisely."}, *messages])
        return {"success": True, "result": resp.get("text", ""), "error": None}

    async def _code_review(self, path: str) -> dict:
        from siri.tools import filesystem
        r = filesystem.read_file(path)
        if not r["success"]:
            return r
        if not self.config.has_llm():
            return {"success": True, "result": "Code review requires LLM API key.", "error": None}
        messages = [{"role": "user", "content": f"Review this code:\n\n{r['result'][:6000]}"}]
        resp = await self._call_llm([{"role": "system", "content": "You are a code reviewer."}, *messages])
        return {"success": True, "result": resp.get("text", ""), "error": None}

    async def _draft_email(self, context: str) -> dict:
        if not self.config.has_llm():
            return {"success": False, "result": None, "error": "LLM required"}
        messages = [{"role": "user", "content": f"Draft a professional email for: {context}"}]
        resp = await self._call_llm([{"role": "system", "content": "Draft concise emails."}, *messages])
        return {"success": True, "result": resp.get("text", ""), "error": None}

    @staticmethod
    def _extract_facts(transcript: str, response: str) -> list[str]:
        facts = []
        lower = transcript.lower()
        if "my name is" in lower:
            name = transcript.lower().split("my name is", 1)[-1].strip().split(".")[0]
            facts.append(f"User's name is {name}")
        if "i prefer" in lower or "i like" in lower:
            facts.append(transcript.strip())
        if "my github" in lower or "my email" in lower:
            facts.append(transcript.strip())
        return facts

    @staticmethod
    def _format_tool_result(result: dict) -> str:
        if result.get("success"):
            r = result.get("result")
            if isinstance(r, str):
                return r
            return "Done."
        return result.get("error", "That didn't work.")
