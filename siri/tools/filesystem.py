"""Filesystem tools."""

from __future__ import annotations

import os
import shutil
import zipfile
from pathlib import Path
from typing import Any


def _ok(result: Any) -> dict:
    return {"success": True, "result": result, "error": None}


def _err(msg: str) -> dict:
    return {"success": False, "result": None, "error": msg}


def _resolve(path: str) -> Path:
    p = Path(path).expanduser()
    return p.resolve()


def read_file(path: str) -> dict:
    try:
        p = _resolve(path)
        return _ok(p.read_text(encoding="utf-8", errors="replace"))
    except Exception as e:
        return _err(str(e))


def write_file(path: str, content: str) -> dict:
    try:
        p = _resolve(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
        return _ok(str(p))
    except Exception as e:
        return _err(str(e))


def append_file(path: str, content: str) -> dict:
    try:
        p = _resolve(path)
        with p.open("a", encoding="utf-8") as f:
            f.write(content)
        return _ok(str(p))
    except Exception as e:
        return _err(str(e))


def delete_file(path: str) -> dict:
    try:
        p = _resolve(path)
        if p.is_dir():
            shutil.rmtree(p)
        else:
            p.unlink()
        return _ok(f"Deleted {p}")
    except Exception as e:
        return _err(str(e))


def move_file(src: str, dst: str) -> dict:
    try:
        s, d = _resolve(src), _resolve(dst)
        d.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(s), str(d))
        return _ok(str(d))
    except Exception as e:
        return _err(str(e))


def copy_file(src: str, dst: str) -> dict:
    try:
        s, d = _resolve(src), _resolve(dst)
        d.parent.mkdir(parents=True, exist_ok=True)
        if s.is_dir():
            shutil.copytree(s, d, dirs_exist_ok=True)
        else:
            shutil.copy2(s, d)
        return _ok(str(d))
    except Exception as e:
        return _err(str(e))


def list_directory(path: str) -> dict:
    try:
        p = _resolve(path)
        items = [
            {"name": c.name, "is_dir": c.is_dir(), "size": c.stat().st_size if c.is_file() else 0}
            for c in sorted(p.iterdir())
        ]
        return _ok(items)
    except Exception as e:
        return _err(str(e))


def create_folder(path: str) -> dict:
    try:
        p = _resolve(path)
        p.mkdir(parents=True, exist_ok=True)
        return _ok(str(p))
    except Exception as e:
        return _err(str(e))


def search_files(query: str, root_path: str | None = None) -> dict:
    try:
        root = _resolve(root_path or str(Path.home()))
        matches = sorted(root.rglob(query), key=lambda p: p.stat().st_mtime, reverse=True)
        results = [str(m) for m in matches[:50]]
        return _ok(results)
    except Exception as e:
        return _err(str(e))


def open_file(path: str) -> dict:
    try:
        p = _resolve(path)
        os.startfile(str(p))
        return _ok(str(p))
    except Exception as e:
        return _err(str(e))


def zip_folder(path: str, output: str) -> dict:
    try:
        src = _resolve(path)
        out = _resolve(output)
        with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zf:
            for f in src.rglob("*"):
                if f.is_file():
                    zf.write(f, f.relative_to(src))
        return _ok(str(out))
    except Exception as e:
        return _err(str(e))


def unzip_file(path: str, destination: str) -> dict:
    try:
        src = _resolve(path)
        dest = _resolve(destination)
        dest.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(src, "r") as zf:
            zf.extractall(dest)
        return _ok(str(dest))
    except Exception as e:
        return _err(str(e))
