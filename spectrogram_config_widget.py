# spectrogram_config_widget.py

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
    QLabel, QSlider, QComboBox, QCheckBox, QPushButton,
    QSpinBox, QFormLayout, QColorDialog, QFrame, QDockWidget, QDialog
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QPalette


class ColorPreviewButton(QPushButton):
    """Botão que mostra uma prévia da cor selecionada."""

    def __init__(self, color: QColor = QColor(0, 0, 0), parent=None):
        super().__init__(parent)
        self._color = color
        self.setFixedSize(60, 30)
        self._update_style()

    def set_color(self, color: QColor):
        self._color = color
        self._update_style()

    def get_color(self) -> QColor:
        return self._color

    def _update_style(self):
        hex_color = self._color.name()
        luminance = (0.299 * self._color.red() +
                     0.587 * self._color.green() +
                     0.114 * self._color.blue()) / 255
        text_color = "#000000" if luminance > 0.5 else "#ffffff"

        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {hex_color};
                color: {text_color};
                border: 2px solid #555;
                border-radius: 4px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                border: 2px solid #888;
            }}
            QPushButton:pressed {{
                border: 2px solid #aaa;
            }}
        """)
        self.setText(hex_color.upper())


class SpectrogramConfigWidget(QWidget):
    """Widget de configuração do espectrograma com controles de cor."""

    gammaChanged = Signal(float)
    contrastChanged = Signal(float)
    colormapChanged = Signal(str)
    freqRangeChanged = Signal(int, int)
    gpuChanged = Signal(bool)
    colorBackgroundChanged = Signal(QColor)
    fftParamsChanged = Signal(int, int, int) # n_fft, hop_size, window_size

    def __init__(self, parent=None):
        super().__init__(parent)
        self._background_color = QColor(0, 0, 0)
        self._spectrum_color = QColor(0, 255, 128)
        self._init_ui()

    # ... (skipping unchanged code) ...

    def _on_freq_changed(self):
        min_freq = self._min_freq_spin.value()
        max_freq = self._max_freq_spin.value()
        if min_freq < max_freq:
            self.freqRangeChanged.emit(min_freq, max_freq)

    def _on_fft_params_changed(self):
        window_size = int(self._window_size_combo.currentData())
        hop_size = int(self._hop_size_combo.currentData())
        n_fft = int(self._n_fft_combo.currentData())
        self.fftParamsChanged.emit(n_fft, hop_size, window_size)

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(15)
        
        self.setMinimumWidth(350)
        # self.setMinimumHeight(500) # Remove fixed min height to allow resizing

        # === GRUPO: VISUALIZAÇÃO ===
        viz_group = QGroupBox("Visualização")
        viz_layout = QFormLayout(viz_group)
        viz_layout.setSpacing(10)

        # Intensidade (Slider)
        # Screenshot: "Intensidade: [Slider] 1.14"
        contrast_container = QHBoxLayout()
        self._contrast_slider = QSlider(Qt.Horizontal)
        self._contrast_slider.setRange(50, 300) # 0.5 to 3.0
        self._contrast_slider.setValue(114)     # Default to screenshot 1.14 approx
        self._contrast_label = QLabel("1.14")
        self._contrast_label.setMinimumWidth(40)
        self._contrast_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        
        contrast_container.addWidget(self._contrast_slider)
        contrast_container.addWidget(self._contrast_label)
        
        viz_layout.addRow("Intensidade:", contrast_container)
        self._contrast_slider.valueChanged.connect(self._on_contrast_changed)

        # Paleta de Cores
        self._colormap_combo = QComboBox()
        self._colormap_combo.addItem("Personalizado", "custom")
        self._colormap_combo.addItem("Inferno", "inferno")
        self._colormap_combo.addItem("Viridis", "viridis")
        self._colormap_combo.addItem("Magma", "magma")
        self._colormap_combo.addItem("Plasma", "plasma")
        self._colormap_combo.addItem("Hot", "hot")
        self._colormap_combo.addItem("Cool", "cool")
        self._colormap_combo.addItem("Cinza", "gray")
        self._colormap_combo.setCurrentText("Inferno") # Default matches screenshot
        self._colormap_combo.currentIndexChanged.connect(self._on_colormap_changed)
        viz_layout.addRow("Paleta de Cores:", self._colormap_combo)

        layout.addWidget(viz_group)

        # === GRUPO: AVANÇADO ===
        adv_group = QGroupBox("Avançado")
        adv_layout = QVBoxLayout(adv_group)
        
        self._gpu_checkbox = QCheckBox("Aceleração GPU (se disponível)")
        self._gpu_checkbox.toggled.connect(self.gpuChanged.emit)
        adv_layout.addWidget(self._gpu_checkbox)
        
        layout.addWidget(adv_group)

        # === GRUPO: PERSONALIZAR CORES ===
        color_group = QGroupBox("Personalizar Cores")
        color_layout = QVBoxLayout(color_group) # Vertical, screenshot shows big button
        
        # Cor de Fundo Button
        self._bg_color_btn = QPushButton("Cor de Fundo")
        self._bg_color_btn.setFixedHeight(40) # Taller button
        self._bg_color_btn.setStyleSheet("""
            QPushButton {
                background-color: #2a5d7d; 
                color: white; 
                border-radius: 4px;
                font-size: 12px;
            }
            QPushButton:hover { background-color: #3e7fa6; }
        """)
        self._bg_color_btn.clicked.connect(self._choose_background_color)
        color_layout.addWidget(self._bg_color_btn)
        
        layout.addWidget(color_group)

        # === GRUPO: PARÂMETROS DE ÁUDIO (FFT) ===
        audio_group = QGroupBox("Parâmetros de Áudio (FFT)")
        audio_layout = QFormLayout(audio_group)
        audio_layout.setSpacing(10)

        # Window Size
        self._window_size_combo = QComboBox()
        for size in [512, 1024, 2048, 4096, 8192]:
            self._window_size_combo.addItem(str(size), size)
        self._window_size_combo.setCurrentText("512")
        self._window_size_combo.currentIndexChanged.connect(self._on_fft_params_changed)
        audio_layout.addRow("Tamanho da Janela:", self._window_size_combo)

        # Hop Size
        self._hop_size_combo = QComboBox()
        for size in [64, 128, 256, 512, 1024]:
            self._hop_size_combo.addItem(str(size), size)
        self._hop_size_combo.setCurrentText("64")
        self._hop_size_combo.currentIndexChanged.connect(self._on_fft_params_changed)
        audio_layout.addRow("Hop Size (Passo):", self._hop_size_combo)

        # N_FFT
        self._n_fft_combo = QComboBox()
        for size in [512, 1024, 2048, 4096, 8192]:
            self._n_fft_combo.addItem(str(size), size)
        self._n_fft_combo.setCurrentText("1024")
        self._n_fft_combo.currentIndexChanged.connect(self._on_fft_params_changed)
        audio_layout.addRow("N_FFT:", self._n_fft_combo)

        layout.addWidget(audio_group)

        # === GRUPO: FAIXA DE FREQUÊNCIA ===
        freq_group = QGroupBox("Faixa de Frequência (Hz)")
        freq_layout = QHBoxLayout(freq_group)
        
        self._min_freq_spin = QSpinBox()
        self._min_freq_spin.setRange(0, 22050)
        self._min_freq_spin.setValue(0)
        self._min_freq_spin.setSuffix(" Hz")
        self._min_freq_spin.valueChanged.connect(self._on_freq_changed)

        self._max_freq_spin = QSpinBox()
        self._max_freq_spin.setRange(0, 22050)
        self._max_freq_spin.setValue(22000)
        self._max_freq_spin.setSuffix(" Hz")
        self._max_freq_spin.valueChanged.connect(self._on_freq_changed)
        
        freq_layout.addWidget(QLabel("Min:"))
        freq_layout.addWidget(self._min_freq_spin)
        freq_layout.addWidget(QLabel("Max:"))
        freq_layout.addWidget(self._max_freq_spin)

        layout.addWidget(freq_group)

        # === GRUPO: AJUSTES VISUAIS EXTRAS ===
        extra_viz_group = QGroupBox("Ajustes Precisos")
        extra_viz_layout = QFormLayout(extra_viz_group)
        
        # Gamma
        gamma_container = QHBoxLayout()
        self._gamma_slider = QSlider(Qt.Horizontal)
        self._gamma_slider.setRange(1, 200) # 0.01 to 2.0
        self._gamma_slider.setValue(80)     # Default 0.8
        self._gamma_label = QLabel("0.80")
        self._gamma_label.setMinimumWidth(40)
        self._gamma_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        
        gamma_container.addWidget(self._gamma_slider)
        gamma_container.addWidget(self._gamma_label)
        
        extra_viz_layout.addRow("Gamma (Brilho):", gamma_container)
        self._gamma_slider.valueChanged.connect(self._on_gamma_changed)

        layout.addWidget(extra_viz_group)

        layout.addStretch()
        
        # Close button at bottom right (usually handled by Dialog wrapper, but if widget is standalone...)
        # Screenshot shows "Close" button.
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        self.btn_close = QPushButton("Close")
        self.btn_close.clicked.connect(self._close_parent)
        btn_layout.addWidget(self.btn_close)
        layout.addLayout(btn_layout)

    def _close_parent(self):
        # Tenta fechar o DockWidget ou Dialog que contém este widget
        parent = self.parent()
        while parent:
            if isinstance(parent, (QDockWidget, QDialog)):
                parent.hide() # Usar hide() é mais seguro para Docks persistentes
                return
            parent = parent.parent()
        self.hide() # Fallback


    def _choose_background_color(self):
        color = QColorDialog.getColor(self._background_color, self, "Escolher Cor",
                                      QColorDialog.ColorDialogOption.ShowAlphaChannel)
        if color.isValid():
            self._background_color = color
            self._bg_color_btn.set_color(color)
            self._colormap_combo.setCurrentIndex(0)
            self.colorBackgroundChanged.emit(color)

    def _choose_spectrum_color(self):
        color = QColorDialog.getColor(self._spectrum_color, self, "Escolher Cor",
                                      QColorDialog.ColorDialogOption.ShowAlphaChannel)
        if color.isValid():
            self._spectrum_color = color
            self._spectrum_color_btn.set_color(color)
            self._colormap_combo.setCurrentIndex(0)
            self.colorSpectrumChanged.emit(color)

    def _apply_color_preset(self, bg_hex: str, spectrum_hex: str):
        bg_color = QColor(bg_hex)
        spectrum_color = QColor(spectrum_hex)
        self._background_color = bg_color
        self._spectrum_color = spectrum_color
        self._bg_color_btn.set_color(bg_color)
        self._spectrum_color_btn.set_color(spectrum_color)
        self._colormap_combo.setCurrentIndex(0)
        # Emitir colormap primeiro para que SpectrogramWidget saiba usar cores custom
        self.colormapChanged.emit("custom")
        self.colorBackgroundChanged.emit(bg_color)
        self.colorSpectrumChanged.emit(spectrum_color)

    def _on_colormap_changed(self, index: int):
        colormap_name = self._colormap_combo.currentData()
        if colormap_name and colormap_name != "custom":
            self.colormapChanged.emit(colormap_name)
        elif colormap_name == "custom":
            self.colorBackgroundChanged.emit(self._background_color)
            self.colorSpectrumChanged.emit(self._spectrum_color)
            self.colormapChanged.emit("custom")

    def _on_gamma_changed(self, value):
        gamma = value / 100.0
        self._gamma_label.setText(f"{gamma:.2f}")
        self.gammaChanged.emit(gamma)

    def _on_contrast_changed(self, value):
        contrast = value / 100.0
        self._contrast_label.setText(f"{contrast:.2f}")
        self.contrastChanged.emit(contrast)

    def _on_freq_changed(self):
        min_freq = self._min_freq_spin.value()
        max_freq = self._max_freq_spin.value()
        if min_freq < max_freq:
            self.freqRangeChanged.emit(min_freq, max_freq)

    def _on_fft_params_changed(self):
        window_size = int(self._window_size_combo.currentData())
        hop_size = int(self._hop_size_combo.currentData())
        n_fft = int(self._n_fft_combo.currentData())
        self.fftParamsChanged.emit(n_fft, hop_size, window_size)


    def _reset_to_default(self):
        self._background_color = QColor(0, 0, 0)
        self._spectrum_color = QColor(0, 255, 128)
        self._bg_color_btn.set_color(self._background_color)
        self._spectrum_color_btn.set_color(self._spectrum_color)
        self._colormap_combo.setCurrentIndex(0)
        self._gamma_slider.setValue(50)
        self._contrast_slider.setValue(100)
        self._min_freq_spin.setValue(0)
        self._gpu_checkbox.setChecked(False)
        self.colorBackgroundChanged.emit(self._background_color)
        self.colorSpectrumChanged.emit(self._spectrum_color)
        self.colormapChanged.emit("custom")
        self.gammaChanged.emit(0.5)
        self.contrastChanged.emit(1.0)
        self.freqRangeChanged.emit(0, 4000)
        self.gpuChanged.emit(False)

    def set_gpu_available(self, available: bool):
        self._gpu_checkbox.setEnabled(available)
        if not available:
            self._gpu_checkbox.setChecked(False)

    def get_settings(self) -> dict:
        return {
            "background_color": self._background_color.name(),
            "spectrum_color": self._spectrum_color.name(),
            "colormap": self._colormap_combo.currentData(),
            "gamma": self._gamma_slider.value() / 100.0,
            "contrast": self._contrast_slider.value() / 100.0,
            "min_freq": self._min_freq_spin.value(),
            "max_freq": self._max_freq_spin.value(),
            "use_gpu": self._gpu_checkbox.isChecked(),
        }

    def set_settings(self, settings: dict):
        if "background_color" in settings:
            color = QColor(settings["background_color"])
            self._background_color = color
            self._bg_color_btn.set_color(color)
        if "spectrum_color" in settings:
            color = QColor(settings["spectrum_color"])
            self._spectrum_color = color
            self._spectrum_color_btn.set_color(color)
        if "colormap" in settings:
            index = self._colormap_combo.findData(settings["colormap"])
            if index >= 0: self._colormap_combo.setCurrentIndex(index)
        if "gamma" in settings:
            self._gamma_slider.setValue(int(settings["gamma"] * 100))
        if "contrast" in settings:
            self._contrast_slider.setValue(int(settings["contrast"] * 100))
        if "min_freq" in settings:
            self._min_freq_spin.setValue(settings["min_freq"])
        if "max_freq" in settings:
            self._max_freq_spin.setValue(settings["max_freq"])
        if "use_gpu" in settings:
            self._gpu_checkbox.setChecked(settings["use_gpu"])