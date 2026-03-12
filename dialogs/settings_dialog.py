from __future__ import annotations
from typing import TYPE_CHECKING
import sys

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget,
    QLabel, QComboBox, QCheckBox, QGroupBox, QFormLayout,
    QPushButton, QMessageBox, QScrollArea
)
from PySide6.QtMultimedia import QMediaDevices

from core.translator import get_translator, tr
from PySide6.QtWidgets import QColorDialog, QLineEdit, QFileDialog
from PySide6.QtGui import QColor, QAction, QIcon

if TYPE_CHECKING:
    from main import MainWindow

class SettingsDialog(QDialog):
    """
    Diálogo unificado de configurações (Geral, Áudio, etc).
    Substitui menus dispersos de Encoding, Idioma, etc.
    """

    def __init__(self, main_window: 'MainWindow'):
        super().__init__(main_window)
        self.mw = main_window
        self.setWindowTitle("Configurações Gerais")
        self.resize(600, 450)
        
        self.translator = get_translator()
        
        self._setup_ui()
        self._load_current_values()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)
        
        # --- Tab Geral ---
        self.tab_general = QWidget()
        self._setup_general_tab()
        self.tabs.addTab(self.tab_general, "Geral")
        
        # --- Tab Áudio ---
        self.tab_audio = QWidget()
        self._setup_audio_tab()
        self.tabs.addTab(self.tab_audio, "Áudio")

        # --- Tab Aparência ---
        self.tab_appearance = QWidget()
        self._setup_appearance_tab()
        self.tabs.addTab(self.tab_appearance, "Aparência")
        
        # --- Botões Inferiores ---
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        self.btn_close = QPushButton("Fechar")
        self.btn_close.clicked.connect(self.accept)
        btn_layout.addWidget(self.btn_close)
        
        layout.addLayout(btn_layout)

    def _setup_general_tab(self):
        layout = QVBoxLayout(self.tab_general)
        
        # Grupo Interface
        grp_interface = QGroupBox("Interface")
        form_interface = QFormLayout(grp_interface)
        
        # Idioma
        self.combo_language = QComboBox()
        for lang in self.translator.get_available_languages():
            self.combo_language.addItem(lang["name"], lang["code"])
        self.combo_language.currentIndexChanged.connect(self._on_language_changed)
        form_interface.addRow("Idioma:", self.combo_language)
        
        # Tema removido daqui (movido para Aparência)
        # self.chk_dark_mode = QCheckBox("Modo Escuro")
        # self.chk_dark_mode.toggled.connect(self.mw._toggle_app_theme)
        # form_interface.addRow("Tema:", self.chk_dark_mode)
        
        layout.addWidget(grp_interface)
        
        # Grupo Arquivos
        grp_files = QGroupBox("Arquivos e Projetos")
        form_files = QFormLayout(grp_files)
        
        # Encoding
        self.combo_encoding = QComboBox()
        encodings = [
            ("Auto (detectar)", "auto"),
            ("UTF-8 (OpenUTAU moderno)", "utf-8"),
            ("UTF-8 BOM (OpenUTAU compatível)", "utf-8-sig"),
            ("Shift-JIS / CP932 (UTAU japonês)", "cp932"),
            ("EUC-JP (UTAU Unix/Linux)", "euc-jp"),
            ("ANSI / Windows-1252 (Ocidental)", "cp1252"),
            ("Latin-1 / ISO-8859-1 (Europeu)", "latin-1"),
            ("GBK / CP936 (Chinês simplificado)", "gbk"),
            ("EUC-KR / CP949 (Coreano)", "euc-kr"),
        ]
        for name, code in encodings:
            self.combo_encoding.addItem(name, code)
        self.combo_encoding.currentIndexChanged.connect(self._on_encoding_changed)
        form_files.addRow("Encoding Padrão:", self.combo_encoding)
        
        layout.addWidget(grp_files)
        
        layout.addStretch()

    def _setup_audio_tab(self):
        layout = QVBoxLayout(self.tab_audio)
        
        # --- Resampler (Síntese) ---
        # Layout horizontal: Label | Input | Button
        resampler_layout = QHBoxLayout()
        resampler_layout.addWidget(QLabel("Resampler (Síntese):"))
        
        self.edit_resampler = QLineEdit()
        self.edit_resampler.setPlaceholderText("Selecione o resampler.exe...")
        resampler_layout.addWidget(self.edit_resampler)
        
        btn_browse = QPushButton("Procurar...")
        btn_browse.setFixedWidth(100)
        btn_browse.setStyleSheet("background-color: #2a5d7d; color: white;") # Azulzinho estilo screenshot?
        btn_browse.clicked.connect(self._browse_resampler)
        resampler_layout.addWidget(btn_browse)
        
        layout.addLayout(resampler_layout)
        layout.addSpacing(10)

        # --- Dispositivo de Saída ---
        # Layout horizontal: Label | Combobox
        device_layout = QHBoxLayout()
        device_layout.addWidget(QLabel("Dispositivo de Saída:"))
        
        self.combo_audio_devices = QComboBox()
        self.combo_audio_devices.currentIndexChanged.connect(self._on_device_changed)
        device_layout.addWidget(self.combo_audio_devices, 1) # Stretch para ocupar espaço
        
        layout.addLayout(device_layout)
        
        # Botão atualizar (full width abaixo ou menor?)
        # Screenshot mostra botão "Atualizar lista de dispositivos" largo
        btn_refresh = QPushButton("Atualizar lista de dispositivos")
        btn_refresh.clicked.connect(self._refresh_audio_devices)
        layout.addWidget(btn_refresh)
        
        layout.addStretch()
        
        self._refresh_audio_devices()

    def _setup_appearance_tab(self):
        layout = QFormLayout(self.tab_appearance)
        layout.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)
        layout.setFormAlignment(Qt.AlignLeft | Qt.AlignTop)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Tema do Aplicativo
        # self.chk_dark_mode = QCheckBox("Modo Escuro (Dark Theme)")
        # layout.addRow("Tema do Aplicativo:", self.chk_dark_mode)
        
        # Cor da Waveform
        # Row com Combobox E Botão de cor customizada
        wave_color_layout = QHBoxLayout()
        
        self.combo_wave_theme = QComboBox()
        self.combo_wave_theme.setMinimumWidth(200)
        # Popula temas
        themes = [
            ("Azul suave", "blue"), ("Verde digital", "green"), ("Branco sobre preto", "mono"),
            ("Laranja amber", "orange"), ("Roxo synthwave", "purple"), ("Ciano terminal", "cyan"),
            ("Rosa neon", "pink"), ("Dourado clássico", "gold"), ("Vermelho intenso", "red"),
            ("Teal escuro", "dark_teal"), ("Slate suave", "dark_slate"), ("Azul meia-noite", "midnight"),
            ("Navy elegante", "dark_navy"), ("Verde floresta", "forest"), ("Oceano profundo", "ocean"),
            ("Pôr do sol", "sunset"), ("Lavanda suave", "lavender")
        ]
        for name, code in themes:
            self.combo_wave_theme.addItem(name, code)
        
        wave_color_layout.addWidget(self.combo_wave_theme)
        layout.addRow("Cor da Waveform:", wave_color_layout)

        # Botão Escolher Cor (indentado ou na mesma linha?)
        # Screenshot mostra botão "Escolher Cor..." com ícone de paleta, abaixo do combo?
        # Screenshot 2: "Cor da Waveform: [Combo]" e na linha de baixo [Square Color] [Escolher Cor...]
        
        custom_color_layout = QHBoxLayout()
        self.btn_color_indicator = QPushButton()
        self.btn_color_indicator.setFixedSize(24, 24)
        self.btn_color_indicator.setStyleSheet("background-color: blue; border: none;") # Placeholder
        
        btn_pick_color = QPushButton("Escolher Cor...")
        btn_pick_color.setIcon(QIcon.fromTheme("color-picker")) # Se tiver icone
        btn_pick_color.clicked.connect(self._pick_custom_color)
        
        custom_color_layout.addWidget(self.btn_color_indicator)
        custom_color_layout.addWidget(btn_pick_color)
        custom_color_layout.addStretch()
        
        layout.addRow("", custom_color_layout)
        
        # Visualização
        # Checkboxes verticais
        viz_layout = QVBoxLayout()
        self.chk_spectrogram = QCheckBox("Mostrar Espectrograma")
        self.chk_minimap = QCheckBox("Mostrar Mini Mapa")
        
        viz_layout.addWidget(self.chk_spectrogram)
        viz_layout.addWidget(self.chk_minimap)
        
        layout.addRow("Visualização:", viz_layout)
        
        # Conexões
        self.combo_wave_theme.currentIndexChanged.connect(self._on_wave_theme_changed)
        # self.chk_dark_mode.clicked.connect(lambda: self.mw._toggle_app_theme())
        self.chk_spectrogram.clicked.connect(lambda: self.mw.act_show_spectrogram.trigger())
        self.chk_minimap.clicked.connect(lambda: self.mw.act_show_minimap.trigger())

    def _load_current_values(self):
        # Idioma
        current_lang_code = self.translator.get_current_language()
        idx = self.combo_language.findData(current_lang_code)
        if idx >= 0:
            self.combo_language.setCurrentIndex(idx)
            
        # Tema (baseado no estado da action existente, já que é toggle)
        # Assumindo que o MW tem o estado. Mas o MW usa _toggle_app_theme que inverte.
        # Precisamos saber o estado atual. O MW não expõe fácil, mas podemos checar o palette ou uma var.
        # Vamos assumir que o MW tem uma verify_dark_mode ou checamos a action se acessível.
        # Tema (removido conforme solicitação)
        pass

        # Resampler
        resampler_path = self.mw.synthesis_test.get_resampler_path()
        if resampler_path:
            self.edit_resampler.setText(str(resampler_path))
            
        # Aparência
        # Waveform Theme
        # Precisamos pegar o tema atual. O MW não expõe isso facilmente selecionado...
        # Mas podemos ver qual action do grupo wave_color_group está checked.
        if hasattr(self.mw, 'wave_color_group'):
            checked = self.mw.wave_color_group.checkedAction()
            if checked:
                # Mapear action text para index do combo ou data?
                # Vamos tentar pelo texto ou manter sincronia manual
                # Mais fácil: vamos assumir que o usuário seleciona aqui e muda.
                pass
                
        # Visualização
        if hasattr(self.mw, 'act_show_spectrogram'):
            self.chk_spectrogram.setChecked(self.mw.act_show_spectrogram.isChecked())
        if hasattr(self.mw, 'act_show_minimap'):
            self.chk_minimap.setChecked(self.mw.act_show_minimap.isChecked())
            
        # Encoding
        # O encoding atual não é exposto publicamente como propriedade fácil, mas está em self.mw._encoding
        if hasattr(self.mw, '_encoding'):
            idx = self.combo_encoding.findData(self.mw._encoding)
            if idx >= 0:
                self.combo_encoding.setCurrentIndex(idx)

    def _on_language_changed(self, index):
        code = self.combo_language.itemData(index)
        if code:
            self.mw._change_language(code)
            QMessageBox.information(self, "Idioma Alterado", "A alteração de idioma requer reinicialização do aplicativo para ter efeito completo.")

    def _browse_resampler(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Selecionar Resampler", "", "Executáveis (*.exe);;Todos (*.*)"
        )
        if path:
            self.edit_resampler.setText(path)
            self.mw.synthesis_test.set_resampler_path(path)

    def _on_wave_theme_changed(self, index):
        theme_code = self.combo_wave_theme.itemData(index)
        if theme_code:
            self.mw._set_wave_theme(theme_code)
            # Atualiza indicador de cor
            # (Simplificação: pega a cor do tema definido no MW se acessível, ou hardcoded map)
            pass

    def _pick_custom_color(self):
        # Cor inicial (poderia pegar a atual, mas azul padrão serve)
        initial = QColor(self.mw.waveform._wave_color_base) if hasattr(self.mw, 'waveform') else Qt.blue
        
        color = QColorDialog.getColor(initial, self, "Escolher cor da waveform")
        
        if color.isValid():
            hex_color = color.name()
            self.btn_color_indicator.setStyleSheet(f"background-color: {hex_color}; border: none;")
            
            # Aplica diretamente na waveform
            if hasattr(self.mw, 'waveform'):
                self.mw.waveform.set_wave_colors(hex_color)
                
            # Opcional: Salvar como preferência "custom" ou atualizar a action se possível
            # Por hora, apenas visual.
            pass

    def _on_encoding_changed(self, index):
        code = self.combo_encoding.itemData(index)
        if code:
            self.mw._set_encoding(code)

    def _refresh_audio_devices(self):
        self.combo_audio_devices.blockSignals(True)
        self.combo_audio_devices.clear()
        
        # Padrão
        self.combo_audio_devices.addItem("Padrão do Sistema", None)
        
        devices = QMediaDevices.audioOutputs()
        current_device = self.mw._audio_output.device() if hasattr(self.mw, '_audio_output') else None
        
        current_index = 0
        for i, device in enumerate(devices):
            self.combo_audio_devices.addItem(device.description(), device)
            if current_device and device.id() == current_device.id():
                current_index = i + 1  # +1 por causa do "Padrão"
                # self.label_current_device.setText(f"Atual: {device.description()}") # Removido label redundante
        
        self.combo_audio_devices.setCurrentIndex(current_index)
        self.combo_audio_devices.blockSignals(False)

    def _on_device_changed(self, index):
        device = self.combo_audio_devices.itemData(index)
        if hasattr(self.mw, '_audio_output'):
            if device:
                self.mw._audio_output.setDevice(device)
            else:
                self.mw._audio_output.setDevice(QMediaDevices.defaultAudioOutput())
