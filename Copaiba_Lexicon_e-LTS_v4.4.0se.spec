# -*- mode: python ; coding: utf-8 -*-

# Hook para sounddevice e pyqtgraph - coleta todos os módulos necessários
from PyInstaller.utils.hooks import collect_data_files, collect_dynamic_libs, collect_all

# Coleta arquivos de _sounddevice_data (inclui libportaudio*.dll no Windows)
sounddevice_datas = collect_data_files('_sounddevice_data')
sounddevice_binaries = collect_dynamic_libs('_sounddevice_data')

# Coleta TODOS os módulos do pyqtgraph
pyqtgraph_datas, pyqtgraph_binaries, pyqtgraph_hiddenimports = collect_all('pyqtgraph')

# Adiciona favicon.ico para o ícone da janela em runtime
extra_datas = [('favicon.ico', '.')]

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=sounddevice_binaries + pyqtgraph_binaries,
    datas=sounddevice_datas + extra_datas + pyqtgraph_datas,
    hiddenimports=['sounddevice', '_sounddevice_data', 'pyopencl', 'pyopencl.reduction', 'pyopencl.scan'] + pyqtgraph_hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['matplotlib', 'tkinter', 'test', 'unittest'],
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
    name='Copaiba_Lexikon_LTS_v5.2.0',
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
    icon=['favicon.ico'],
)
