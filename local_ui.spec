# -*- mode: python ; coding: utf-8 -*-
import logging

# Configure logging
logging.basicConfig(filename="local_ui_error.log", level=logging.ERROR)

a = Analysis(
    ['local_ui.py'],
    pathex=['.venv/Lib/site-packages', 'gui', 'src'],
    binaries=[],
    datas=[('gui', 'gui'), ('gui/MainWindow.ui', 'gui'), ('src', 'src')],
    hiddenimports=['gui.interface', 'gui.server_thread', 'gui.sig_plot', 'pyqtgraph'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

# Removed the second 'EXE' section
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='local_ui',
    debug=True,
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
)
