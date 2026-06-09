"""Tool unit tests."""

import tempfile
from pathlib import Path

import pytest

from siri.tools import filesystem, system, code


def test_write_and_read_file():
    with tempfile.TemporaryDirectory() as tmp:
        path = str(Path(tmp) / "test.txt")
        w = filesystem.write_file(path, "hello world")
        assert w["success"]
        r = filesystem.read_file(path)
        assert r["success"]
        assert r["result"] == "hello world"


def test_list_directory():
    with tempfile.TemporaryDirectory() as tmp:
        filesystem.write_file(str(Path(tmp) / "a.txt"), "a")
        r = filesystem.list_directory(tmp)
        assert r["success"]
        assert len(r["result"]) >= 1


def test_get_cpu_usage():
    r = system.get_cpu_usage()
    assert r["success"]
    assert "percent" in r["result"]


def test_run_python():
    r = code.run_python("print('hello')")
    assert r["success"]
    assert "hello" in r["result"]["stdout"]


def test_run_terminal_command():
    r = code.run_terminal_command("echo test123")
    assert r["success"]
    assert "test123" in r["result"]["stdout"]
