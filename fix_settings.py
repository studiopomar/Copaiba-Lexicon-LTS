"""
Limpa o estado salvo do QSettings para corrigir crash de janela.
O Qt pode crashar ao tentar restaurar geometry/state corrompido.
"""
from PySide6.QtCore import QSettings

settings = QSettings("POMAR LTS", "Copaiba")

print("Chaves salvas:")
for key in settings.allKeys():
    print(f"  {key} = {settings.value(key)!r}")

print("\nLimpando geometry e windowState...")
settings.remove("geometry")
settings.remove("windowState")
settings.sync()

print("Feito! Tente abrir o aplicativo agora.")
