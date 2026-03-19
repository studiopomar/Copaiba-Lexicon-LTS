# widgets/preset_config.py
"""
Widget de configuração de presets para Copaiba Lexikon.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QGridLayout, QGroupBox, 
    QLabel, QSpinBox, QPushButton, QCheckBox, QLineEdit, QHBoxLayout
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QKeySequence

# Importa presets
try:
    from presets import PRESETS, Preset
except ImportError:
    # Fallback se presets não existir
    from dataclasses import dataclass
    
    @dataclass
    class Preset:
        name: str
        overlap: int
        preutter: int
        consonant: int
        cutoff: int
    
    PRESETS = {
        "cv": Preset("CV", 50, 80, 120, -100),
        "vcv": Preset("VCV", 80, 120, 180, -150),
        "vv": Preset("VV", 40, 60, 100, -80),
        "vc": Preset("VC", 30, 50, 80, -60),
        "minus_v": Preset("-V", 20, 40, 60, -50),
    }

# Atalhos padrão para presets
DEFAULT_PRESET_SHORTCUTS = {
    "cv": "Ctrl+1",
    "vcv": "Ctrl+2",
    "vv": "Ctrl+3",
    "vc": "Ctrl+4",
    "minus_v": "Ctrl+5",
}

# Nomes padrão para presets
DEFAULT_PRESET_NAMES = {
    "cv": "CV",
    "vcv": "VCV",
    "vv": "VV",
    "vc": "VC",
    "minus_v": "-V",
}


class ShortcutLineEdit(QLineEdit):
    """LineEdit que captura atalhos de teclado."""
    
    shortcutChanged = Signal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setPlaceholderText("Clique e pressione teclas")
        self.setReadOnly(True)
        self._shortcut = ""
        
    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Control, Qt.Key_Alt, Qt.Key_Shift, Qt.Key_Meta):
            return
        
        modifiers = event.modifiers()
        key = event.key()
        
        # Constrói string do atalho
        parts = []
        if modifiers & Qt.ControlModifier:
            parts.append("Ctrl")
        if modifiers & Qt.AltModifier:
            parts.append("Alt")
        if modifiers & Qt.ShiftModifier:
            parts.append("Shift")
        
        # Converte key para nome
        key_seq = QKeySequence(key)
        key_text = key_seq.toString()
        if key_text:
            parts.append(key_text)
        
        self._shortcut = "+".join(parts) if parts else ""
        self.setText(self._shortcut)
        self.shortcutChanged.emit(self._shortcut)
        
    def get_shortcut(self) -> str:
        return self._shortcut
    
    def set_shortcut(self, shortcut: str):
        self._shortcut = shortcut
        self.setText(shortcut)


class PresetConfigWidget(QWidget):
    """
    Widget para configurar presets de parâmetros OTO.
    
    Permite personalizar valores de overlap, preutter, consonant e cutoff
    para diferentes tipos de fonemas (CV, VCV, VV, VC, -V).
    
    Também permite personalizar nomes e atalhos de teclado para cada preset.
    """
    
    # Sinal emitido quando configurações de presets mudam
    presetsChanged = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._custom_presets = {}
        self._presets_active = True
        self._init_ui()
        self._load_from_defaults()

    def _init_ui(self) -> None:
        """Inicializa a interface do usuário."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(10)

        # Checkbox para ativar/desativar presets
        self._active_checkbox = QCheckBox("Presets Ativos")
        self._active_checkbox.setChecked(True)
        self._active_checkbox.setToolTip(
            "Quando desativado, os botões de preset não terão efeito"
        )
        self._active_checkbox.toggled.connect(self._on_active_toggled)
        layout.addWidget(self._active_checkbox)

        # Widgets de preset
        self._preset_widgets = {}
        preset_configs = [
            ("cv", "CV"), 
            ("vcv", "VCV"), 
            ("vv", "VV"), 
            ("vc", "VC"), 
            ("minus_v", "-V")
        ]

        for key, default_label in preset_configs:
            group = QGroupBox(f"Preset {default_label}")
            group_layout = QGridLayout(group)
            group_layout.setSpacing(5)

            # --- NOVA: Linha com nome customizado e atalho ---
            name_edit = QLineEdit()
            name_edit.setText(default_label)
            name_edit.setMaximumWidth(100)
            name_edit.setToolTip("Nome customizado para este preset")
            name_edit.textChanged.connect(lambda text, k=key: self._on_name_changed(k, text))
            
            shortcut_edit = ShortcutLineEdit()
            shortcut_edit.set_shortcut(DEFAULT_PRESET_SHORTCUTS.get(key, ""))
            shortcut_edit.setMaximumWidth(120)
            shortcut_edit.setToolTip("Atalho de teclado para este preset")
            shortcut_edit.shortcutChanged.connect(lambda s: self.presetsChanged.emit())
            
            name_shortcut_layout = QHBoxLayout()
            name_shortcut_layout.addWidget(QLabel("Nome:"))
            name_shortcut_layout.addWidget(name_edit)
            name_shortcut_layout.addWidget(QLabel("Atalho:"))
            name_shortcut_layout.addWidget(shortcut_edit)
            name_shortcut_layout.addStretch()
            
            group_layout.addLayout(name_shortcut_layout, 0, 0, 1, 4)

            # Spinboxes para cada parâmetro
            spin_overlap = QSpinBox()
            spin_overlap.setRange(-1000, 1000)
            spin_overlap.setSuffix(" ms")

            spin_preutter = QSpinBox()
            spin_preutter.setRange(0, 2000)
            spin_preutter.setSuffix(" ms")

            spin_consonant = QSpinBox()
            spin_consonant.setRange(0, 2000)
            spin_consonant.setSuffix(" ms")

            spin_cutoff = QSpinBox()
            spin_cutoff.setRange(-2000, 0)
            spin_cutoff.setSuffix(" ms")

            # Layout dos spinboxes
            group_layout.addWidget(QLabel("Overlap:"), 1, 0)
            group_layout.addWidget(spin_overlap, 1, 1)
            group_layout.addWidget(QLabel("Preutter:"), 1, 2)
            group_layout.addWidget(spin_preutter, 1, 3)
            group_layout.addWidget(QLabel("Consonant:"), 2, 0)
            group_layout.addWidget(spin_consonant, 2, 1)
            group_layout.addWidget(QLabel("Cutoff:"), 2, 2)
            group_layout.addWidget(spin_cutoff, 2, 3)

            # Botão reset
            btn_reset = QPushButton("Reset")
            btn_reset.clicked.connect(lambda checked, k=key: self._reset_preset(k))
            group_layout.addWidget(btn_reset, 3, 0, 1, 4)

            self._preset_widgets[key] = {
                "overlap": spin_overlap, 
                "preutter": spin_preutter,
                "consonant": spin_consonant, 
                "cutoff": spin_cutoff, 
                "group": group,
                "name_edit": name_edit,
                "shortcut_edit": shortcut_edit,
            }
            layout.addWidget(group)
            
        layout.addStretch()
    
    def _on_name_changed(self, key: str, text: str) -> None:
        """Atualiza o título do groupbox quando nome muda."""
        if key in self._preset_widgets:
            group = self._preset_widgets[key]["group"]
            group.setTitle(f"Preset {text}")
            self.presetsChanged.emit()

    def _on_active_toggled(self, checked: bool) -> None:
        """Callback quando checkbox de ativo é alterado."""
        self._presets_active = checked
        for key, widgets in self._preset_widgets.items():
            widgets["group"].setEnabled(checked)

    def is_active(self) -> bool:
        """Retorna se os presets estão ativos."""
        return self._presets_active

    def set_active(self, active: bool) -> None:
        """Define se os presets estão ativos."""
        self._presets_active = active
        self._active_checkbox.setChecked(active)

    def _load_from_defaults(self) -> None:
        """Carrega valores padrão dos presets."""
        for key, preset in PRESETS.items():
            if key in self._preset_widgets:
                widgets = self._preset_widgets[key]
                widgets["overlap"].setValue(preset.overlap)
                widgets["preutter"].setValue(preset.preutter)
                widgets["consonant"].setValue(preset.consonant)
                widgets["cutoff"].setValue(preset.cutoff)
                widgets["name_edit"].setText(DEFAULT_PRESET_NAMES.get(key, key.upper()))
                widgets["shortcut_edit"].set_shortcut(DEFAULT_PRESET_SHORTCUTS.get(key, ""))

    def _reset_preset(self, key: str) -> None:
        """Reseta um preset para valores padrão."""
        if key in PRESETS and key in self._preset_widgets:
            preset = PRESETS[key]
            widgets = self._preset_widgets[key]
            widgets["overlap"].setValue(preset.overlap)
            widgets["preutter"].setValue(preset.preutter)
            widgets["consonant"].setValue(preset.consonant)
            widgets["cutoff"].setValue(preset.cutoff)
            widgets["name_edit"].setText(DEFAULT_PRESET_NAMES.get(key, key.upper()))
            widgets["shortcut_edit"].set_shortcut(DEFAULT_PRESET_SHORTCUTS.get(key, ""))

    def get_preset(self, key: str) -> Preset:
        """Retorna preset com valores atuais."""
        if key in self._preset_widgets:
            widgets = self._preset_widgets[key]
            return Preset(
                name=widgets["name_edit"].text() or key.upper(),
                overlap=widgets["overlap"].value(),
                preutter=widgets["preutter"].value(),
                consonant=widgets["consonant"].value(),
                cutoff=widgets["cutoff"].value(),
            )
        return PRESETS.get(key, PRESETS["cv"])
    
    def get_preset_name(self, key: str) -> str:
        """Retorna o nome customizado de um preset."""
        if key in self._preset_widgets:
            return self._preset_widgets[key]["name_edit"].text()
        return DEFAULT_PRESET_NAMES.get(key, key.upper())
    
    def get_preset_shortcut(self, key: str) -> str:
        """Retorna o atalho de um preset."""
        if key in self._preset_widgets:
            return self._preset_widgets[key]["shortcut_edit"].get_shortcut()
        return DEFAULT_PRESET_SHORTCUTS.get(key, "")
    
    def get_all_shortcuts(self) -> dict:
        """Retorna dicionário com todos os atalhos de presets."""
        result = {}
        for key in self._preset_widgets:
            result[key] = self._preset_widgets[key]["shortcut_edit"].get_shortcut()
        return result

    def get_all_presets(self) -> dict:
        """Retorna todos os presets como dicionário."""
        result = {}
        for key in self._preset_widgets:
            widgets = self._preset_widgets[key]
            result[key] = {
                "overlap": widgets["overlap"].value(),
                "preutter": widgets["preutter"].value(),
                "consonant": widgets["consonant"].value(),
                "cutoff": widgets["cutoff"].value(),
                "name": widgets["name_edit"].text(),
                "shortcut": widgets["shortcut_edit"].get_shortcut(),
            }
        result["_active"] = self._presets_active
        return result

    def set_all_presets(self, presets: dict) -> None:
        """Define todos os presets a partir de dicionário."""
        for key, values in presets.items():
            if key == "_active":
                self.set_active(values)
                continue
            if key in self._preset_widgets:
                widgets = self._preset_widgets[key]
                widgets["overlap"].setValue(values.get("overlap", 0))
                widgets["preutter"].setValue(values.get("preutter", 0))
                widgets["consonant"].setValue(values.get("consonant", 0))
                widgets["cutoff"].setValue(values.get("cutoff", 0))
                if "name" in values:
                    widgets["name_edit"].setText(values["name"])
                if "shortcut" in values:
                    widgets["shortcut_edit"].set_shortcut(values["shortcut"])

