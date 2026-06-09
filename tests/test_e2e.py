"""End-to-end agent tests (text mode, no mic)."""

import asyncio
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
