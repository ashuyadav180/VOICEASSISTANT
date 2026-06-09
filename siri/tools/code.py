"""Code execution tools."""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any


def _ok(result: Any) -> dict:
    return {"success": True, "result": result, "error": None}


def _err(msg: str) -> dict:
    return {"success": False, "result": None, "error": msg}


def run_python(code_string: str) -> dict:
    try:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False, encoding="utf-8") as f:
            f.write(code_string)
            path = f.name
        result = subprocess.run(
            [sys.executable, path],
            capture_output=True,
            text=True,
            timeout=60,
        )
        Path(path).unlink(missing_ok=True)
        return _ok({
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode,
        })
    except Exception as e:
        return _err(str(e))


def run_terminal_command(command: str) -> dict:
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=120,
        )
        return _ok({
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode,
        })
    except Exception as e:
        return _err(str(e))


def run_js(code_string: str) -> dict:
    try:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".js", delete=False, encoding="utf-8") as f:
            f.write(code_string)
            path = f.name
        result = subprocess.run(
            ["node", path],
            capture_output=True,
            text=True,
            timeout=60,
        )
        Path(path).unlink(missing_ok=True)
        return _ok({
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode,
        })
    except Exception as e:
        return _err(str(e))


def open_terminal() -> dict:
    try:
        subprocess.Popen(["wt.exe"], shell=True)
        return _ok("Terminal opened")
    except Exception:
        try:
            subprocess.Popen(["cmd.exe"], shell=True)
            return _ok("CMD opened")
        except Exception as e:
            return _err(str(e))


def create_and_run_script(filename: str, code: str) -> dict:
    try:
        path = Path(filename).expanduser().resolve()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(code, encoding="utf-8")
        if path.suffix == ".py":
            return run_python(code)
        if path.suffix == ".js":
            return run_js(code)
        return run_terminal_command(str(path))
    except Exception as e:
        return _err(str(e))
