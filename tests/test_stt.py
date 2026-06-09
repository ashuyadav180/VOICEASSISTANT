"""STT pipeline tests."""

import numpy as np
import pytest

from siri.config import Config
from siri.audio.stt import STTPipeline


def test_clean_disfluencies():
    text = STTPipeline._clean_disfluencies("um hello uh world")
    assert "um" not in text.lower().split()
    assert "hello" in text


def test_stt_pipeline_init():
    config = Config()
    pipeline = STTPipeline(config)
    assert pipeline.config is not None
