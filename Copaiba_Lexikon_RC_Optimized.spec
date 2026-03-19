# -*- mode: python ; coding: utf-8 -*-
# Spec file otimizado para reduzir tamanho do executável

import sys
from pathlib import Path

block_cipher = None

# Módulos a serem excluídos para reduzir tamanho
EXCLUDES = [
    # Qt modules que NÃO usamos
    'PySide6.QtWebEngine',
    'PySide6.QtWebEngineCore',
    'PySide6.QtWebEngineWidgets',
    'PySide6.QtWebChannel',
    'PySide6.QtQuick',
    'PySide6.QtQuickWidgets',
    'PySide6.QtQuickControls2',
    'PySide6.QtQml',
    'PySide6.QtQmlModels',
    'PySide6.QtDesigner',
    'PySide6.QtHelp',
    'PySide6.QtBluetooth',
    'PySide6.QtNfc',
    'PySide6.QtPositioning',
    'PySide6.QtLocation',
    'PySide6.QtSensors',
    'PySide6.QtSerialPort',
    'PySide6.QtRemoteObjects',
    'PySide6.QtTest',
    'PySide6.QtSql',
    'PySide6.QtDataVisualization',
    'PySide6.QtCharts',
    'PySide6.Qt3DCore',
    'PySide6.Qt3DExtras',
    'PySide6.Qt3DInput',
    'PySide6.Qt3DLogic',
    'PySide6.Qt3DRender',
    'PySide6.Qt3DAnimation',
    'PySide6.QtPdf',
    'PySide6.QtPdfWidgets',
    'PySide6.QtAxContainer',
    'PySide6.QtNetworkAuth',
    'PySide6.QtTextToSpeech',
    'PySide6.QtScxml',
    'PySide6.QtStateMachine',
    'PySide6.QtSpatialAudio',
    'PySide6.QtVirtualKeyboard',
    
    # numpy extras
    'numpy.distutils',
    'numpy.f2py',
    'numpy.testing',
    'numpy.tests',
    'numpy.doc',
    
    # Outros módulos pesados desnecessários
    'matplotlib',

    'pandas',
    'PIL',
    'cv2',
    'tkinter',
    'unittest',
    'email',
    'html',
    'http',
    'xmlrpc',
    'pydoc',
    'doctest',

    'pdb',
    'profile',
    'cProfile',
    'timeit',
    'trace',
    'curses',
    'multiprocessing.popen_spawn_win32',
    'multiprocessing.popen_fork',
    'multiprocessing.popen_forkserver',
]

# Dados a incluir
datas = [
    ('translations', 'translations'),
    ('favicon.ico', '.'),
]

# Hidden imports necessários
hiddenimports = [
    'PySide6.QtCore',
    'PySide6.QtGui',
    'PySide6.QtWidgets',
    'PySide6.QtMultimedia',
    'PySide6.QtOpenGL',
    'PySide6.QtOpenGLWidgets',
    'pyqtgraph',
    'pyqtgraph.graphicsItems',
    'pyqtgraph.functions',
    'numpy',
    'sounddevice',
    'OpenGL',
    'OpenGL.GL',
    'OpenGL.platform.win32',
]

# Tenta adicionar pyopencl se disponível
try:
    import pyopencl
    hiddenimports.extend([
        'pyopencl',
        'pyopencl.array',
    ])
except ImportError:
    pass

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=EXCLUDES,
    noarchive=False,
    optimize=1,  # Otimização de bytecode (remove asserts, mantém docstrings para compatibilidade numpy)
)

# Remove binários desnecessários do Qt
excluded_binaries = [
    'Qt6WebEngine',
    'Qt6Quick',
    'Qt6Qml',
    'Qt6Designer',
    'Qt6Help',
    'Qt6Pdf',
    'Qt6Charts',
    'Qt6DataVisualization',
    'Qt63D',
    'd3dcompiler',
    'opengl32sw',  # Software OpenGL - usamos hardware
]

def should_exclude(name):
    name_lower = name.lower()
    for excluded in excluded_binaries:
        if excluded.lower() in name_lower:
            return True
    return False

a.binaries = [(name, path, type) for name, path, type in a.binaries if not should_exclude(name)]

pyz = PYZ(a.pure, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='Copaiba_Lexikon_RC',
    debug=False,
    bootloader_ignore_signals=False,
    strip=True,  # Remove símbolos de debug
    upx=True,  # Habilita compressão UPX
    upx_exclude=[
        'vcruntime140.dll',
        'python*.dll',
        'MSVCP140.dll',
        'api-ms-*.dll',
    ],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['favicon.ico'],
)
