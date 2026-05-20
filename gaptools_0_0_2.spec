# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['gaptools.py'],
    pathex=[],
    binaries=[],
    datas=[('assets/', 'assets/')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

splash = Splash(
    'assets/gaptools_splash.png', 
    binaries=a.binaries,
    datas=a.datas,
    text_pos=None,
    text_size=12,
    text_color='#FFFFFF',
    always_on_top=True,
)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    splash,
    splash.binaries,
    [],
    name='gaptools_0_0_2',
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
    icon=['assets/gaptools_icon.ico'],
)