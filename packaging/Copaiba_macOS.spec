# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path

block_cipher = None

# Localiza a raiz do projeto mesmo se o spec estiver dentro de packaging/
ROOT_DIR = Path(SPECPATH).resolve().parent if Path(SPECPATH).name == 'packaging' else Path(SPECPATH).resolve()

a = Analysis(
    [str(ROOT_DIR / 'main.py')],
    pathex=[str(ROOT_DIR)],
    binaries=[],
    datas=[
        (str(ROOT_DIR / 'plugins'), 'plugins'),
        (str(ROOT_DIR / 'translations'), 'translations'),
        (str(ROOT_DIR / 'favicon.ico'), '.'),
    ],
    hiddenimports=[
        'PySide6', 
        'scipy', 
        'scipy.signal', 
        'numpy', 
        'sounddevice', 
        'pyqtgraph',
        'pypresence',
        'OpenGL',
        'OpenGL.platform',
        'OpenGL.GL',
        'librosa',
        'librosa.display',
        'matplotlib',
        'matplotlib.pyplot',
        'matplotlib.backends.backend_qtagg',
        'matplotlib.backends.backend_qt5agg'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'torch',
        'torchaudio', 
        'torchvision',
        'sympy',
        'onnx',
        'onnxruntime',
        'networkx',
        'pandas',
        'PIL.ImageQt',
        'IPython',
        'jupyter',
        'notebook'
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Copaiba',
    debug=False,
    bootloader_ignore_signals=False,
    strip=True,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=[str(ROOT_DIR / 'favicon.ico')],
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=True,
    upx=True,
    upx_exclude=[],
    name='Copaiba',
)

app = BUNDLE(
    coll,
    name='Copaiba.app',
    icon=str(ROOT_DIR / 'favicon.ico'),
    bundle_identifier='com.copaiba.lexicon',
    info_plist={
        'NSHighResolutionCapable': 'True',
        'CFBundleDisplayName': 'Copaiba Lexikon',
        'CFBundleName': 'Copaiba',
        'CFBundleShortVersionString': '2026.4-v130.8c',
        'NSRequiresAquaSystemAppearance': 'False'
    }
)
