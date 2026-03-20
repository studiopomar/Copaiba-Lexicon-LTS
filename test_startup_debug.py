import sys
import traceback
from pathlib import Path

print("--- FASE 1: Imports basicos ---", flush=True)
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QSurfaceFormat, QPalette, QColor, QIcon
from PySide6.QtCore import QTimer
print("OK", flush=True)

print("--- FASE 2: QApplication ---", flush=True)
fmt = QSurfaceFormat()
fmt.setSwapInterval(1)
fmt.setSwapBehavior(QSurfaceFormat.DoubleBuffer)
QSurfaceFormat.setDefaultFormat(fmt)
app = QApplication(sys.argv)
app.setApplicationName("Copaiba Lexikon")
app.setStyle("Fusion")
print("OK", flush=True)

print("--- FASE 3: MainWindow() ---", flush=True)
try:
    from main import MainWindow
    window = MainWindow()
    print("MainWindow criado OK", flush=True)
except Exception as e:
    print(f"ERRO na MainWindow: {e}", flush=True)
    traceback.print_exc()
    sys.exit(1)

print("--- FASE 4: window.show() ---", flush=True)
window.show()
print("show() chamado OK", flush=True)

print(f"  isVisible: {window.isVisible()}", flush=True)
print(f"  geometry: {window.geometry()}", flush=True)
print(f"  size: {window.size()}", flush=True)

print("--- FASE 5: app.exec() ---", flush=True)
# Fecha automaticamente após 3s para não travar o teste
QTimer.singleShot(3000, app.quit)
result = app.exec()
print(f"app.exec() retornou: {result}", flush=True)
