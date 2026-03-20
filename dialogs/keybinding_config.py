# dialogs/keybinding_config.py

"""
Diálogo para configuração de teclas de atalho para parâmetros de oto.ini.
Permite personalizar as teclas Q, W, E, R, T para qualquer outra tecla,
incluindo suporte a presets como SetParam (F1-F5).
"""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QGroupBox, QWidget
)
from PySide6.QtGui import QKeySequence


# Mapeamento padrão (como no Copaiba original)
DEFAULT_KEYBINDINGS = {
    "offset": Qt.Key_Q,
    "overlap": Qt.Key_W,
    "preutter": Qt.Key_E,
    "consonant": Qt.Key_R,
    "cutoff": Qt.Key_T,
}

# Preset SetParam (F1-F5)
SETPARAM_KEYBINDINGS = {
    "offset": Qt.Key_F1,
    "overlap": Qt.Key_F2,
    "preutter": Qt.Key_F3,
    "consonant": Qt.Key_F4,
    "cutoff": Qt.Key_F5,
}

# Nomes amigáveis dos parâmetros
PARAM_LABELS = {
    "offset": "Offset",
    "overlap": "Overlap",
    "preutter": "Preutter",
    "consonant": "Consonant",
    "cutoff": "Cutoff",
}


def key_to_string(key: int) -> str:
    """Converte Qt.Key para string legível."""
    return QKeySequence(key).toString()


def string_to_key(s: str) -> int:
    """Converte string para Qt.Key."""
    seq = QKeySequence.fromString(s)
    if seq.count() > 0:
        return seq[0].key()
    return Qt.Key_unknown


class KeyCaptureButton(QPushButton):
    """Botão que captura teclas pressionadas."""
    
    keyChanged = Signal(int)  # Emite o Qt.Key capturado
    
    def __init__(self, key: int = Qt.Key_unknown, parent=None):
        super().__init__(parent)
        self._key = key
        self._listening = False
        self._update_text()
        self.clicked.connect(self._start_listening)
        self.setMinimumWidth(100)
    
    def _update_text(self):
        if self._listening:
            self.setText("Pressione uma tecla...")
            self.setStyleSheet("background-color: #2a5d7d; color: white;")
        elif self._key != Qt.Key_unknown:
            self.setText(key_to_string(self._key))
            self.setStyleSheet("")
        else:
            self.setText("(Nenhuma)")
            self.setStyleSheet("color: #888;")
    
    def _start_listening(self):
        self._listening = True
        self._update_text()
        self.setFocus()
    
    def keyPressEvent(self, event):
        if self._listening:
            key = event.key()
            # Ignorar teclas modificadoras sozinhas
            if key not in (Qt.Key_Control, Qt.Key_Shift, Qt.Key_Alt, Qt.Key_Meta):
                self._key = key
                self._listening = False
                self._update_text()
                self.keyChanged.emit(key)
                event.accept()
                return
        super().keyPressEvent(event)
    
    def focusOutEvent(self, event):
        if self._listening:
            self._listening = False
            self._update_text()
        super().focusOutEvent(event)
    
    def get_key(self) -> int:
        return self._key
    
    def set_key(self, key: int):
        self._key = key
        self._listening = False
        self._update_text()


class KeybindingConfigDialog(QDialog):
    """Diálogo para configurar teclas de atalho dos parâmetros de oto.ini."""
    
    keybindingsChanged = Signal(dict)  # Emite o novo mapeamento
    
    def __init__(self, current_bindings: dict = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configurar Teclas de Parâmetros")
        self.setMinimumWidth(400)
        
        # Usar bindings atuais ou padrão
        self._bindings = dict(current_bindings) if current_bindings else dict(DEFAULT_KEYBINDINGS)
        self._key_buttons = {}
        
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Instruções
        info_label = QLabel(
            "Configure as teclas usadas para definir os parâmetros de oto.ini.\n"
            "Clique no botão e pressione a tecla desejada."
        )
        info_label.setStyleSheet("color: #aaa; margin-bottom: 10px;")
        layout.addWidget(info_label)
        
        # Grupo de teclas
        keys_group = QGroupBox("Teclas de Parâmetros")
        keys_layout = QGridLayout(keys_group)
        
        # Ordem dos parâmetros
        param_order = ["offset", "overlap", "preutter", "consonant", "cutoff"]
        
        for row, param in enumerate(param_order):
            label = QLabel(f"{PARAM_LABELS[param]}:")
            label.setMinimumWidth(80)
            
            btn = KeyCaptureButton(self._bindings.get(param, Qt.Key_unknown))
            btn.keyChanged.connect(lambda k, p=param: self._on_key_changed(p, k))
            self._key_buttons[param] = btn
            
            keys_layout.addWidget(label, row, 0)
            keys_layout.addWidget(btn, row, 1)
        
        layout.addWidget(keys_group)
        
        # Presets
        presets_group = QGroupBox("Presets")
        presets_layout = QHBoxLayout(presets_group)
        
        btn_default = QPushButton("Padrão (Q W E R T)")
        btn_default.clicked.connect(self._apply_default_preset)
        
        btn_setparam = QPushButton("SetParam (F1-F5)")
        btn_setparam.clicked.connect(self._apply_setparam_preset)
        
        presets_layout.addWidget(btn_default)
        presets_layout.addWidget(btn_setparam)
        
        layout.addWidget(presets_group)
        
        # Botões de ação
        buttons_layout = QHBoxLayout()
        
        btn_apply = QPushButton("Aplicar")
        btn_apply.clicked.connect(self._apply)
        btn_apply.setDefault(True)
        
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.clicked.connect(self.reject)
        
        buttons_layout.addStretch()
        buttons_layout.addWidget(btn_apply)
        buttons_layout.addWidget(btn_cancel)
        
        layout.addLayout(buttons_layout)
    
    def _on_key_changed(self, param: str, key: int):
        self._bindings[param] = key
    
    def _apply_default_preset(self):
        self._bindings = dict(DEFAULT_KEYBINDINGS)
        self._update_buttons()
    
    def _apply_setparam_preset(self):
        self._bindings = dict(SETPARAM_KEYBINDINGS)
        self._update_buttons()
    
    def _update_buttons(self):
        for param, btn in self._key_buttons.items():
            btn.set_key(self._bindings.get(param, Qt.Key_unknown))
    
    def _apply(self):
        # Verificar duplicatas
        keys_used = []
        for param, key in self._bindings.items():
            if key in keys_used:
                from PySide6.QtWidgets import QMessageBox
                QMessageBox.warning(
                    self, "Tecla Duplicada",
                    f"A tecla {key_to_string(key)} foi atribuída a mais de um parâmetro.\n"
                    "Cada parâmetro deve ter uma tecla única."
                )
                return
            keys_used.append(key)
        
        self.keybindingsChanged.emit(self._bindings)
        self.accept()
    
    def get_bindings(self) -> dict:
        """Retorna o mapeamento de teclas atual."""
        return dict(self._bindings)
