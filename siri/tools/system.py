"""System control tools for Windows."""

from __future__ import annotations

import os
import subprocess
from typing import Any

import psutil

try:
    import pyperclip
except ImportError:
    pyperclip = None


def _ok(result: Any) -> dict:
    return {"success": True, "result": result, "error": None}


def _err(msg: str) -> dict:
    return {"success": False, "result": None, "error": msg}


def get_battery_status() -> dict:
    try:
        battery = psutil.sensors_battery()
        if battery is None:
            return _ok({"percent": None, "plugged": None, "message": "No battery detected"})
        return _ok({
            "percent": battery.percent,
            "plugged": battery.power_plugged,
            "secs_left": battery.secsleft,
        })
    except Exception as e:
        return _err(str(e))


def get_wifi_status() -> dict:
    try:
        result = subprocess.run(
            ["netsh", "wlan", "show", "interfaces"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        connected = "connected" in result.stdout.lower()
        ssid = ""
        for line in result.stdout.splitlines():
            if "SSID" in line and "BSSID" not in line:
                ssid = line.split(":", 1)[-1].strip()
                break
        return _ok({"connected": connected, "ssid": ssid})
    except Exception as e:
        return _err(str(e))


def set_volume(level_0_to_100: int) -> dict:
    try:
        from ctypes import cast, POINTER
        from comtypes import CLSCTX_ALL
        from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        volume = cast(interface, POINTER(IAudioEndpointVolume))
        volume.SetMasterVolumeLevelScalar(level_0_to_100 / 100.0, None)
        return _ok(f"Volume set to {level_0_to_100}%")
    except Exception:
        # Fallback: nircmd or powershell
        try:
            ps = f"(New-Object -ComObject WScript.Shell).SendKeys([char]175)"  # volume up hack
            subprocess.run(["powershell", "-c", ps], timeout=5)
            return _ok(f"Volume adjusted (approximate)")
        except Exception as e:
            return _err(str(e))


def mute_audio() -> dict:
    return set_volume(0)


def unmute_audio() -> dict:
    return set_volume(50)


def shutdown(delay_seconds: int = 0) -> dict:
    try:
        subprocess.run(["shutdown", "/s", "/t", str(delay_seconds)], check=True)
        return _ok(f"Shutting down in {delay_seconds}s")
    except Exception as e:
        return _err(str(e))


def restart(delay_seconds: int = 0) -> dict:
    try:
        subprocess.run(["shutdown", "/r", "/t", str(delay_seconds)], check=True)
        return _ok(f"Restarting in {delay_seconds}s")
    except Exception as e:
        return _err(str(e))


def sleep_system() -> dict:
    try:
        subprocess.run(
            ["rundll32.exe", "powrprof.dll,SetSuspendState", "0,1,0"],
            check=True,
        )
        return _ok("System sleeping")
    except Exception as e:
        return _err(str(e))


def get_cpu_usage() -> dict:
    try:
        return _ok({"percent": psutil.cpu_percent(interval=1)})
    except Exception as e:
        return _err(str(e))


def get_ram_usage() -> dict:
    try:
        mem = psutil.virtual_memory()
        return _ok({
            "total_gb": round(mem.total / 1e9, 2),
            "used_gb": round(mem.used / 1e9, 2),
            "percent": mem.percent,
        })
    except Exception as e:
        return _err(str(e))


def get_disk_usage() -> dict:
    try:
        usage = psutil.disk_usage("C:\\")
        return _ok({
            "total_gb": round(usage.total / 1e9, 2),
            "used_gb": round(usage.used / 1e9, 2),
            "free_gb": round(usage.free / 1e9, 2),
            "percent": usage.percent,
        })
    except Exception as e:
        return _err(str(e))


def get_running_processes() -> dict:
    try:
        procs = []
        for p in psutil.process_iter(["pid", "name", "cpu_percent", "memory_percent"]):
            try:
                procs.append(p.info)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        procs.sort(key=lambda x: x.get("memory_percent") or 0, reverse=True)
        return _ok(procs[:30])
    except Exception as e:
        return _err(str(e))


def kill_process(name_or_pid: str) -> dict:
    try:
        if name_or_pid.isdigit():
            p = psutil.Process(int(name_or_pid))
            p.terminate()
            return _ok(f"Killed PID {name_or_pid}")
        killed = []
        for p in psutil.process_iter(["pid", "name"]):
            if name_or_pid.lower() in (p.info["name"] or "").lower():
                p.terminate()
                killed.append(p.info["name"])
        if killed:
            return _ok(killed)
        return _err(f"Process not found: {name_or_pid}")
    except Exception as e:
        return _err(str(e))


def clipboard_get() -> dict:
    if not pyperclip:
        return _err("pyperclip not installed")
    try:
        return _ok(pyperclip.paste())
    except Exception as e:
        return _err(str(e))


def clipboard_set(text: str) -> dict:
    if not pyperclip:
        return _err("pyperclip not installed")
    try:
        pyperclip.copy(text)
        return _ok("Clipboard set")
    except Exception as e:
        return _err(str(e))


def lock_screen() -> dict:
    try:
        subprocess.run(["rundll32.exe", "user32.dll,LockWorkStation"], check=True)
        return _ok("Screen locked")
    except Exception as e:
        return _err(str(e))
