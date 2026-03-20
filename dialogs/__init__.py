# dialogs/__init__.py
"""
Módulo de diálogos do Copaiba Lexikon.
"""

from .exit_dialog import AdvancedExitDialog
from .plugin_manager import PluginManagerDialog
from .keybinding_config import KeybindingConfigDialog, DEFAULT_KEYBINDINGS, SETPARAM_KEYBINDINGS

__all__ = [
    'AdvancedExitDialog',
    'PluginManagerDialog',
    'KeybindingConfigDialog',
    'DEFAULT_KEYBINDINGS',
    'SETPARAM_KEYBINDINGS',
]

