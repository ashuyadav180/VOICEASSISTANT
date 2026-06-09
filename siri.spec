# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec for SIRI Windows executable

import sys
from pathlib import Path

block_cipher = None
root = Path(SPECPATH)

a = Analysis(
    [str(root / 'siri' / 'main.py')],
    pathex=[str(root)],
    binaries=[],
    datas=[
        (str(root / 'siri' / 'system_prompt.txt'), 'siri'),
        (str(root / '.env.example'), '.'),
    ],
    hiddenimports=[
        'siri', 'siri.config', 'siri.agent.loop', 'siri.agent.brain',
        'siri.audio.stt', 'siri.audio.tts', 'siri.audio.wake_word',
        'siri.tools.executor', 'siri.tools.registry',
        'siri.memory.long_term', 'siri.memory.short_term',
        'sounddevice', 'mss', 'pyautogui', 'chromadb',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='SIRI',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)
