import sys
from PySide6.QtWidgets import QApplication
from spectrogram_config_widget import SpectrogramConfigWidget

app = QApplication(sys.argv)

widget = SpectrogramConfigWidget()
print("Widget created OK")

settings = widget.get_settings()
print("get_settings OK:", settings)

widget.set_settings(settings)
print("set_settings OK")

widget._reset_to_default()
print("_reset_to_default OK")

print("All tests passed!")
