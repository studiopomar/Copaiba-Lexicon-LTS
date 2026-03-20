# plugins/mic_tuner.py
"""
Plugin: Afinador em Tempo Real (Mic Tuner)
Captura pitch do microfone em tempo real e exibe como um afinador visual.
"""

from typing import Optional
import numpy as np

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QComboBox
)
from PySide6.QtCore import Qt, QTimer, Signal, QObject
from PySide6.QtGui import QPainter, QPen, QBrush, QColor, QFont, QLinearGradient

from .base_plugin import BasePlugin, PluginResult, PluginCategory

# Tenta importar sounddevice
try:
    import sounddevice as sd
    SOUNDDEVICE_AVAILABLE = True
except ImportError:
    SOUNDDEVICE_AVAILABLE = False

# Tabela de notas musicais
NOTE_NAMES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']

# Tenta importar Numba para otimização
try:
    from numba import njit
    NUMBA_AVAILABLE = True
except ImportError:
    NUMBA_AVAILABLE = False
    def njit(*args, **kwargs):
        """Fallback decorator quando numba não está disponível."""
        def decorator(func):
            return func
        return decorator


@njit(cache=True, fastmath=True)
def _find_pitch_peak_numba(corr: np.ndarray, min_lag: int, max_lag: int, threshold_ratio: float = 0.3) -> int:
    """
    Encontra o pico de autocorrelação usando Numba JIT.
    OTIMIZAÇÃO: ~5-20x mais rápido que numpy puro.
    """
    if max_lag >= len(corr):
        max_lag = len(corr) - 1
    
    if min_lag >= max_lag:
        return -1
    
    threshold = threshold_ratio * corr[0]
    best_idx = min_lag
    best_val = corr[min_lag]
    
    for i in range(min_lag + 1, max_lag):
        if corr[i] > best_val:
            best_val = corr[i]
            best_idx = i
    
    if best_val < threshold:
        return -1
    
    return best_idx


def detect_pitch_autocorr(signal: np.ndarray, sample_rate: int,
                          min_freq: float = 50, max_freq: float = 1000) -> float:
    """
    Detecta pitch usando autocorrelação.
    OTIMIZAÇÃO: Usa Numba JIT para busca de pico quando disponível.
    
    Args:
        signal: Sinal de áudio
        sample_rate: Taxa de amostragem
        min_freq: Frequência mínima a detectar
        max_freq: Frequência máxima a detectar
    
    Returns:
        Frequência fundamental em Hz, ou 0 se não detectado
    """
    if len(signal) < 100:
        return 0
    
    # Normalizar
    signal = signal - np.mean(signal)
    
    # Verificar energia mínima (silêncio)
    rms = np.sqrt(np.mean(signal ** 2))
    if rms < 0.01:
        return 0
    
    # Calcular autocorrelação (numpy otimizado com BLAS)
    corr = np.correlate(signal, signal, mode='full')
    corr = corr[len(corr) // 2:]
    
    # Limites de lag para frequência
    min_lag = int(sample_rate / max_freq)
    max_lag = int(sample_rate / min_freq)
    
    # Usa versão Numba JIT se disponível
    if NUMBA_AVAILABLE:
        peak_idx_global = _find_pitch_peak_numba(corr.astype(np.float64), min_lag, max_lag, 0.3)
        if peak_idx_global <= 0:
            return 0
        lag = float(peak_idx_global)
    else:
        # Fallback numpy
        if max_lag >= len(corr):
            max_lag = len(corr) - 1
        
        if min_lag >= max_lag:
            return 0
        
        corr_search = corr[min_lag:max_lag]
        
        if len(corr_search) < 3:
            return 0
        
        peak_idx = np.argmax(corr_search)
        
        if corr_search[peak_idx] < 0.3 * corr[0]:
            return 0
        
        # Interpolação parabólica para precisão sub-sample
        if 0 < peak_idx < len(corr_search) - 1:
            y0 = corr_search[peak_idx - 1]
            y1 = corr_search[peak_idx]
            y2 = corr_search[peak_idx + 1]
            
            denom = y0 - 2 * y1 + y2
            if abs(denom) > 1e-10:
                delta = 0.5 * (y0 - y2) / denom
                peak_idx += delta
        
        lag = min_lag + peak_idx
    
    # Converter para frequência
    freq = sample_rate / lag
    
    return freq


def freq_to_note_and_cents(freq: float) -> tuple:
    """
    Converte frequência para nota musical e cents de desvio.
    
    Returns:
        (nome_da_nota, oitava, cents) ou ("-", 0, 0) se inválido
    """
    if freq <= 0:
        return "-", 0, 0
    
    # A4 = 440 Hz
    a4 = 440.0
    
    # Calcula semitons a partir de A4
    semitones_from_a4 = 12 * np.log2(freq / a4)
    
    # Nota mais próxima (arredonda para inteiro)
    nearest_semitone = round(semitones_from_a4)
    
    # Cents de diferença (-50 a +50)
    cents = (semitones_from_a4 - nearest_semitone) * 100
    
    # Calcula nota e oitava
    # A4 é o índice 9 na escala (C=0, C#=1, ..., A=9, A#=10, B=11)
    note_index = (9 + nearest_semitone) % 12
    octave = 4 + (9 + nearest_semitone) // 12
    
    return NOTE_NAMES[note_index], octave, cents


class TunerNeedleWidget(QFrame):
    """Widget visual do afinador com agulha"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(400, 200)
        self.setFrameStyle(QFrame.Box | QFrame.Raised)
        
        self._cents = 0.0
        self._note = "-"
        self._octave = 0
        self._freq = 0.0
        self._active = False
    
    def set_values(self, note: str, octave: int, cents: float, freq: float, active: bool = True):
        self._note = note
        self._octave = octave
        self._cents = max(-50, min(50, cents))
        self._freq = freq
        self._active = active
        self.update()
    
    def paintEvent(self, event):
        super().paintEvent(event)
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        w = self.width()
        h = self.height()
        cx = w // 2
        
        # Fundo gradiente
        gradient = QLinearGradient(0, 0, 0, h)
        gradient.setColorAt(0, QColor(30, 30, 40))
        gradient.setColorAt(1, QColor(20, 20, 30))
        painter.fillRect(self.rect(), gradient)
        
        # Escala de cents (-50 a +50)
        scale_y = h - 60
        scale_height = 30
        
        # Zona verde (afinado: -5 a +5 cents)
        green_width = int(w * 0.1)
        painter.fillRect(cx - green_width // 2, scale_y, green_width, scale_height, QColor(50, 180, 80))
        
        # Zonas amarelas
        yellow_width = int(w * 0.15)
        painter.fillRect(cx - green_width // 2 - yellow_width, scale_y, yellow_width, scale_height, QColor(200, 180, 50))
        painter.fillRect(cx + green_width // 2, scale_y, yellow_width, scale_height, QColor(200, 180, 50))
        
        # Zonas vermelhas
        red_left_width = cx - green_width // 2 - yellow_width
        red_right_start = cx + green_width // 2 + yellow_width
        painter.fillRect(0, scale_y, red_left_width, scale_height, QColor(180, 50, 50))
        painter.fillRect(red_right_start, scale_y, w - red_right_start, scale_height, QColor(180, 50, 50))
        
        # Marcas de escala
        painter.setPen(QPen(Qt.white, 1))
        font_small = QFont("Segoe UI", 8)
        painter.setFont(font_small)
        
        for cents_mark in [-50, -25, 0, 25, 50]:
            x = cx + int((cents_mark / 50.0) * (w / 2 - 20))
            painter.drawLine(x, scale_y - 5, x, scale_y)
            painter.drawText(x - 15, scale_y - 8, 30, 15, Qt.AlignCenter, str(cents_mark))
        
        # Símbolos bemol e sustenido
        font_symbol = QFont("Segoe UI", 14, QFont.Bold)
        painter.setFont(font_symbol)
        painter.drawText(20, scale_y + scale_height // 2 + 5, "♭")
        painter.drawText(w - 30, scale_y + scale_height // 2 + 5, "♯")
        
        # Indicador/Agulha
        if self._active and self._note != "-":
            needle_x = cx + int((self._cents / 50.0) * (w / 2 - 20))
            
            # Cor da agulha baseada no desvio
            if abs(self._cents) <= 5:
                needle_color = QColor(100, 255, 100)
            elif abs(self._cents) <= 15:
                needle_color = QColor(255, 230, 100)
            else:
                needle_color = QColor(255, 100, 100)
            
            # Desenhar agulha triangular
            painter.setBrush(QBrush(needle_color))
            painter.setPen(QPen(Qt.black, 1))
            
            from PySide6.QtGui import QPolygon
            from PySide6.QtCore import QPoint
            
            triangle = QPolygon([
                QPoint(needle_x, scale_y - 10),
                QPoint(needle_x - 8, scale_y + scale_height + 10),
                QPoint(needle_x + 8, scale_y + scale_height + 10)
            ])
            painter.drawPolygon(triangle)
        
        # Nota principal
        font_note = QFont("Segoe UI", 48, QFont.Bold)
        painter.setFont(font_note)
        
        if self._active and self._note != "-":
            painter.setPen(QColor(255, 255, 255))
            note_text = f"{self._note}{self._octave}"
        else:
            painter.setPen(QColor(100, 100, 100))
            note_text = "-"
        
        painter.drawText(0, 20, w, 80, Qt.AlignCenter, note_text)
        
        # Frequência
        font_freq = QFont("Segoe UI", 14)
        painter.setFont(font_freq)
        painter.setPen(QColor(180, 180, 180))
        
        if self._freq > 0:
            freq_text = f"{self._freq:.1f} Hz"
        else:
            freq_text = "-- Hz"
        
        painter.drawText(0, 85, w, 25, Qt.AlignCenter, freq_text)
        
        # Cents
        if self._active and self._note != "-":
            cents_text = f"{self._cents:+.0f} cents"
            painter.drawText(0, 105, w, 25, Qt.AlignCenter, cents_text)


class MicTunerDialog(QDialog):
    """Janela flutuante do afinador"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Pomar Afinador")
        self.setWindowFlags(
            Qt.Window |
            Qt.WindowStaysOnTopHint |
            Qt.WindowCloseButtonHint
        )
        self.setMinimumSize(450, 300)
        
        self._stream = None
        self._sample_rate = 44100
        self._buffer_size = 2048
        self._audio_buffer = np.zeros(self._buffer_size, dtype=np.float32)
        
        self._setup_ui()
        
        # Timer para atualização visual
        self._update_timer = QTimer(self)
        self._update_timer.timeout.connect(self._update_display)
        
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        
        # Controles
        controls_layout = QHBoxLayout()
        
        self.btn_start = QPushButton("▶ Iniciar")
        self.btn_start.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 8px 16px;
                border: none;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #45a049; }
            QPushButton:disabled { background-color: #666; }
        """)
        self.btn_start.clicked.connect(self._toggle_listening)
        controls_layout.addWidget(self.btn_start)
        
        controls_layout.addStretch()
        
        # Seletor de dispositivo
        controls_layout.addWidget(QLabel("Microfone:"))
        self.combo_device = QComboBox()
        self.combo_device.setMinimumWidth(200)
        self._populate_devices()
        controls_layout.addWidget(self.combo_device)
        
        layout.addLayout(controls_layout)
        
        # Widget do afinador
        self.tuner_widget = TunerNeedleWidget()
        layout.addWidget(self.tuner_widget)
        
        # Status
        self.lbl_status = QLabel("Clique em 'Iniciar' para começar")
        self.lbl_status.setAlignment(Qt.AlignCenter)
        self.lbl_status.setStyleSheet("color: #888; padding: 5px;")
        layout.addWidget(self.lbl_status)
    
    def _populate_devices(self):
        if not SOUNDDEVICE_AVAILABLE:
            self.combo_device.addItem("sounddevice não disponível")
            self.combo_device.setEnabled(False)
            self.btn_start.setEnabled(False)
            return
        
        try:
            devices = sd.query_devices()
            default_input = sd.default.device[0]
            
            for i, dev in enumerate(devices):
                if dev['max_input_channels'] > 0:
                    name = dev['name']
                    if i == default_input:
                        name += " (Padrão)"
                    self.combo_device.addItem(name, i)
        except Exception as e:
            self.combo_device.addItem(f"Erro: {e}")
            self.btn_start.setEnabled(False)
    
    def _toggle_listening(self):
        if self._stream is None:
            self._start_listening()
        else:
            self._stop_listening()
    
    def _start_listening(self):
        if not SOUNDDEVICE_AVAILABLE:
            return
        
        try:
            device_idx = self.combo_device.currentData()
            
            self._stream = sd.InputStream(
                device=device_idx,
                channels=1,
                samplerate=self._sample_rate,
                blocksize=self._buffer_size,
                callback=self._audio_callback
            )
            self._stream.start()
            
            self._update_timer.start(50)  # 20 FPS
            
            self.btn_start.setText("⏹ Parar")
            self.btn_start.setStyleSheet("""
                QPushButton {
                    background-color: #f44336;
                    color: white;
                    padding: 8px 16px;
                    border: none;
                    border-radius: 4px;
                    font-weight: bold;
                }
                QPushButton:hover { background-color: #da190b; }
            """)
            self.combo_device.setEnabled(False)
            self.lbl_status.setText("Ouvindo... Cante ou toque uma nota!")
            
        except Exception as e:
            self.lbl_status.setText(f"Erro: {e}")
    
    def _stop_listening(self):
        self._update_timer.stop()
        
        if self._stream:
            self._stream.stop()
            self._stream.close()
            self._stream = None
        
        self.btn_start.setText("▶ Iniciar")
        self.btn_start.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 8px 16px;
                border: none;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #45a049; }
        """)
        self.combo_device.setEnabled(True)
        self.lbl_status.setText("Parado")
        self.tuner_widget.set_values("-", 0, 0, 0, False)
    
    def _audio_callback(self, indata, frames, time_info, status):
        """Callback chamado pelo sounddevice com novos dados de áudio"""
        self._audio_buffer = indata[:, 0].copy()
    
    def _update_display(self):
        """Atualiza a exibição do afinador"""
        freq = detect_pitch_autocorr(
            self._audio_buffer,
            self._sample_rate,
            min_freq=60,
            max_freq=1200
        )
        
        if freq > 0:
            note, octave, cents = freq_to_note_and_cents(freq)
            self.tuner_widget.set_values(note, octave, cents, freq, True)
        else:
            self.tuner_widget.set_values("-", 0, 0, 0, True)
    
    def closeEvent(self, event):
        self._stop_listening()
        super().closeEvent(event)


class MicTunerPlugin(BasePlugin):
    """Plugin de afinador em tempo real via microfone"""
    
    NAME = "Pomar - Afinador"
    DESCRIPTION = "Afinador em tempo real que captura pitch do microfone"
    CATEGORY = PluginCategory.ANALYSIS
    VERSION = "1.0.0"
    
    def get_dialog(self) -> Optional[QDialog]:
        return MicTunerDialog(self.main_window)
    
    def execute(self, **kwargs) -> PluginResult:
        # Este plugin é apenas visual - não executa ação em lote
        return PluginResult(
            success=True,
            message="Use o diálogo para afinação em tempo real",
            changes_made=0
        )
