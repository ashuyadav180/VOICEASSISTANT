"""End-to-end agent tests (text mode, no mic)."""

import asyncio
import time
import pytest

from siri.config import Config
from siri.agent.loop import AgentLoop


@pytest.mark.asyncio
async def test_text_time_query():
    config = Config()
    loop = AgentLoop(config)
    response = await loop.brain.process("what time is it")
    assert response
    assert len(response) > 3


@pytest.mark.asyncio
async def test_short_term_memory():
    config = Config()
    loop = AgentLoop(config)
    loop.short_memory.add("user", "hello")
    loop.short_memory.add("assistant", "hi there")
    msgs = loop.short_memory.get_messages()
    assert len(msgs) == 2


@pytest.mark.asyncio
async def test_process_text_does_not_block_event_loop(monkeypatch):
    config = Config()
    loop = AgentLoop(config)

    async def fake_process(text):
        return "Done."

    monkeypatch.setattr(loop.brain, "process", fake_process)
    monkeypatch.setattr(loop.tts, "speak", lambda text: None)

    task = asyncio.create_task(loop.process_text("hello"))
    started = time.perf_counter()
    await asyncio.sleep(0.05)

    assert time.perf_counter() - started < 0.2
    assert not task.done()
    assert await task == "Done."
