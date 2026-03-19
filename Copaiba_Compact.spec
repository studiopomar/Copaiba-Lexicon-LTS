# -*- mode: python ; coding: utf-8 -*-
# Copaiba Lexikon - Build Otimizado para Windows (OneFile + UPX)
# Versão CPU-only, sem GPU/OpenGL

import os
import sys

# Caminho do UPX local
UPX_DIR = os.path.join(os.path.dirname(os.path.abspath(SPEC)), 'upx-4.2.4-win64')

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('plugins', 'plugins'),
        ('translations', 'translations'),
        ('site', 'site'),
        ('favicon.ico', '.'),
        ('coffee.jpg', '.'),
        ('site.webmanifest', '.')
    ],
    hiddenimports=[
        'PySide6.QtCore',
        'PySide6.QtGui', 
        'PySide6.QtWidgets',
        'PySide6.QtMultimedia',
        'PySide6.QtOpenGL',  # Necessário para PyQtGraph
        'PySide6.QtOpenGLWidgets',  # Necessário para PyQtGraph
        'scipy', 
        'scipy.signal', 
        'scipy.fft',
        'numpy', 
        'sounddevice', 
        'pyqtgraph',
        'pypresence',
        'chardet',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # GPU/OpenGL - REMOVIDOS
        'OpenGL',
        'OpenGL_accelerate',
        'PyOpenGL',
        'PyOpenGL_accelerate',
        'pyopencl',
        'cupy',
        
        # Machine Learning - não usados
        'torch',
        'torchaudio', 
        'torchvision',
        'tensorflow',
        'keras',
        'onnx',
        'onnxruntime',
        
        # Bibliotecas pesadas não usadas
        'matplotlib',
        'sympy',
        'networkx',
        'pandas',
        'PIL.ImageQt',
        'IPython',
        'jupyter',
        'notebook',
        'sphinx',
        
        # Testing
        'pytest',
        'unittest',
        
        # Qt modules não necessários
        'PySide6.QtWebEngine',
        'PySide6.QtWebEngineCore', 
        'PySide6.QtWebEngineWidgets',
        'PySide6.Qt3DCore',
        'PySide6.Qt3DRender',
        'PySide6.Qt3DInput',
        'PySide6.QtBluetooth',
        'PySide6.QtNfc',
        'PySide6.QtPositioning',
        'PySide6.QtLocation',
        'PySide6.QtSensors',
        'PySide6.QtRemoteObjects',
        'PySide6.QtSerialPort',
        'PySide6.QtSql',
        'PySide6.QtTest',
        'PySide6.QtDesigner',
        'PySide6.QtHelp',
        'PySide6.QtPdf',
        'PySide6.QtPdfWidgets',
        'PySide6.QtCharts',
        'PySide6.QtDataVisualization',
        'PySide6.QtQuick',
        'PySide6.QtQuickWidgets',
        'PySide6.QtQml',
        'PySide6.QtNetworkAuth',
        # QtOpenGL é necessário para PyQtGraph - NÃO EXCLUIR
        # 'PySide6.QtOpenGL',
        # 'PySide6.QtOpenGLWidgets',
        
        # Outros
        'tkinter',
        '_tkinter',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
    optimize=0,  # Não usar optimize=2 - causa erro com NumPy
)

# Remove arquivos desnecessários dos binários (NÃO remover OpenGL - PyQtGraph precisa)
a.binaries = [b for b in a.binaries if not any(x in b[0].lower() for x in [
    'qt6quick', 'qt6qml', 'qt6webengine', 
    'qt6pdf', 'qt6designer', 'qt63d', 'd3dcompiler',
    'vulkan',
])]

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='Copaiba',
    debug=False,
    bootloader_ignore_signals=False,
    strip=True,
    upx=True,
    upx_exclude=[
        'vcruntime140.dll',
        'python313.dll',
        'Qt6Core.dll',
        'Qt6Gui.dll',
        'Qt6Widgets.dll',
    ],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='favicon.ico',
    upx_dir=UPX_DIR,
)
