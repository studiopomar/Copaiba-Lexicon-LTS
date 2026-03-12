# dialogs/audio_device_dialog.py
"""
Diálogo para seleção de dispositivo de áudio de saída.
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QComboBox, QPushButton, QGroupBox
)
from PySide6.QtCore import Qt


class AudioDeviceDialog(QDialog):
    """Diálogo para selecionar dispositivo de áudio de saída."""
    
    def __init__(self, audio_player, parent=None):
        super().__init__(parent)
        self.audio_player = audio_player
        self._selected_device_id = audio_player.get_output_device()
        self._setup_ui()
        
    def _setup_ui(self):
        self.setWindowTitle("Dispositivo de Áudio")
        self.setMinimumWidth(400)
        
        layout = QVBoxLayout(self)
        
        # Grupo de seleção
        group = QGroupBox("Dispositivo de Saída")
        group_layout = QVBoxLayout(group)
        
        # Label informativo
        info_label = QLabel(
            "Selecione o dispositivo de áudio para reprodução.\n"
            "Deixe em 'Padrão do Sistema' para usar o dispositivo padrão."
        )
        info_label.setWordWrap(True)
        info_label.setStyleSheet("color: #888;")
        group_layout.addWidget(info_label)
        
        # ComboBox de dispositivos
        self.device_combo = QComboBox()
        self.device_combo.addItem("Padrão do Sistema", None)
        
        # Carrega dispositivos disponíveis
        devices = self.audio_player.get_output_devices()
        current_device = self.audio_player.get_output_device()
        
        for device in devices:
            self.device_combo.addItem(
                f"{device['name']} ({device['channels']}ch)", 
                device['id']
            )
            if device['id'] == current_device:
                self.device_combo.setCurrentIndex(self.device_combo.count() - 1)
        
        group_layout.addWidget(self.device_combo)
        layout.addWidget(group)
        
        # Status
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #4CAF50;")
        layout.addWidget(self.status_label)
        
        # Botões
        btn_layout = QHBoxLayout()
        
        btn_test = QPushButton("Testar")
        btn_test.clicked.connect(self._test_device)
        
        btn_apply = QPushButton("Aplicar")
        btn_apply.clicked.connect(self._apply)
        
        btn_close = QPushButton("Fechar")
        btn_close.clicked.connect(self.close)
        
        btn_layout.addWidget(btn_test)
        btn_layout.addStretch()
        btn_layout.addWidget(btn_apply)
        btn_layout.addWidget(btn_close)
        layout.addLayout(btn_layout)
    
    def _test_device(self):
        """Testa o dispositivo selecionado."""
        device_id = self.device_combo.currentData()
        
        # Temporariamente define o dispositivo e toca um som de teste
        try:
            import sounddevice as sd
            import numpy as np
            
            # Salva dispositivo atual
            old_device = self.audio_player.get_output_device()
            
            # Define novo dispositivo temporariamente
            self.audio_player.set_output_device(device_id)
            
            # Gera tom de teste (440Hz por 0.3s)
            duration = 0.3
            sample_rate = 44100
            t = np.linspace(0, duration, int(sample_rate * duration), False)
            tone = 0.3 * np.sin(2 * np.pi * 440 * t)
            
            # Fade in/out
            fade = int(sample_rate * 0.05)
            tone[:fade] *= np.linspace(0, 1, fade)
            tone[-fade:] *= np.linspace(1, 0, fade)
            
            sd.play(tone.astype(np.float32), sample_rate)
            
            self.status_label.setText("Reproduzindo tom de teste...")
            self.status_label.setStyleSheet("color: #4CAF50;")
            
        except Exception as e:
            self.status_label.setText(f"Erro: {str(e)[:50]}")
            self.status_label.setStyleSheet("color: #f44336;")
    
    def _apply(self):
        """Aplica o dispositivo selecionado."""
        device_id = self.device_combo.currentData()
        self.audio_player.set_output_device(device_id)
        
        device_name = self.device_combo.currentText()
        self.status_label.setText(f"Dispositivo alterado: {device_name}")
        self.status_label.setStyleSheet("color: #4CAF50;")
        
        self._selected_device_id = device_id
    
    def get_selected_device(self):
        """Retorna o ID do dispositivo selecionado."""
        return self._selected_device_id
