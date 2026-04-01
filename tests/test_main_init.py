import sys
from PySide6.QtWidgets import QApplication
from main import MainWindow

app = QApplication(sys.argv)
try:
    window = MainWindow()
    print("MainWindow initialized successfully!")
except Exception as e:
    import traceback
    traceback.print_exc()
