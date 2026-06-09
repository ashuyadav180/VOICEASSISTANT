"""TTS pipeline tests."""

from siri.audio.tts import _strip_for_speech


def test_strip_urls():
    text = _strip_for_speech("Opened https://example.com/page for you")
    assert "https" not in text
    assert "the page" in text


def test_strip_markdown():
    text = _strip_for_speech("**Bold** and _italic_ text")
    assert "**" not in text
    assert "Bold" in text
