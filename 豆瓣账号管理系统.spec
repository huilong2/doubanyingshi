# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[('data', 'data'), ('1.ico', '.'), ('styles.py', '.'), ('config.py', '.'), ('data_manager.py', '.'), ('douban_utils.py', '.'), ('douban_xieyi.py', '.'), ('liulanqi_gongcaozuo.py', '.'), ('renwuliucheng.py', '.'), ('suijipingpingxingliucheng.py', '.'), ('zhixingliucheng.py', '.'), ('utils.py', '.'), ('start_api.py', '.'), ('handlers', 'handlers'), ('ui', 'ui'), ('liulanqimokuai', 'liulanqimokuai'), ('qitagongju', 'qitagongju'), ('tests', 'tests')],
    hiddenimports=['PySide6.QtCore', 'PySide6.QtGui', 'PySide6.QtWidgets', 'sqlite3', 'json', 'logging', 'asyncio', 'threading', 'subprocess', 'platform', 'pathlib', 'random', 'time', 'requests', 'urllib3', 'playwright', 'websockets', 'uvicorn', 'fastapi', 'pydantic', 'tkinter', 'tkinter.ttk', 'tkinter.messagebox'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='豆瓣账号管理系统',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['1.ico'],
)
