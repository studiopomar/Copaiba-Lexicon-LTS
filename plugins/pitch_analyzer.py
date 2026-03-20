# plugins/pitch_analyzer.py
"""
Plugin: Análise de Pitch
Mostra a frequência fundamental do áudio em tempo real.
"""

from typing import Optional, List, Tuple
from pathlib import Path
import numpy as np

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGroupBox, QSlider, QSpinBox, QComboBox
)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QColor, QPainter, QPen, QFont
import pyqtgraph as pg

from .base_plugin import BasePlugin, PluginResult, PluginCategory

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from audio_loader import read_wav_file


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


def freq_to_note(freq: float) -> str:
    """Converte frequência para nome da nota musical"""
    if freq <= 0:
        return "-"
    
    # A4 = 440 Hz
    a4 = 440.0
    c0 = a4 * pow(2, -4.75)
    
    if freq < c0:
        return "-"
    
    h = round(12 * np.log2(freq / c0))
    octave = h // 12
    note_idx = h % 12
    
    return f"{NOTE_NAMES[note_idx]}{octave}"


@njit(cache=True, fastmath=True)
def _find_pitch_peak_numba(corr: np.ndarray, min_lag: int, max_lag: int, threshold_ratio: float = 0.3) -> int:
    """
    Encontra o pico de autocorrelação usando Numba JIT.
    OTIMIZAÇÃO: ~5-20x mais rápido que numpy puro para arrays pequenos.
    
    Returns:
        Índice do pico (lag), ou -1 se não encontrado
    """
    if max_lag >= len(corr):
        max_lag = len(corr) - 1
    
    if min_lag >= max_lag:
        return -1
    
    # Threshold baseado no pico central
    threshold = threshold_ratio * corr[0]
    
    # Encontra o máximo na região de busca
    best_idx = min_lag
    best_val = corr[min_lag]
    
    for i in range(min_lag + 1, max_lag):
        if corr[i] > best_val:
            best_val = corr[i]
            best_idx = i
    
    # Verifica se o pico é significativo
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
    
    # Calcular autocorrelação (numpy otimizado com BLAS)
    corr = np.correlate(signal, signal, mode='full')
    corr = corr[len(corr) // 2:]
    
    # Limitar busca às frequências de interesse
    min_lag = int(sample_rate / max_freq)
    max_lag = int(sample_rate / min_freq)
    
    # Usa versão Numba JIT se disponível
    if NUMBA_AVAILABLE:
        lag = _find_pitch_peak_numba(corr.astype(np.float64), min_lag, max_lag, 0.3)
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
        
        lag = min_lag + peak_idx
    
    if lag <= 0:
        return 0
    
    # Converter para frequência
    freq = sample_rate / lag
    
    return freq


class PitchAnalyzerWorker(QThread):
    """Thread para analisar pitch"""
    progress = Signal(int, int)
    result = Signal(list, list, float)  # times, pitches, sample_rate
    
    def __init__(self, audio_path: str, window_ms: int, offset_ms: float = 0, cutoff_ms: float = 0):
        super().__init__()
        self.audio_path = audio_path
        self.window_ms = window_ms
        self.offset_ms = offset_ms
        self.cutoff_ms = cutoff_ms
    
    def run(self):
        try:
            # Importar librosa aqui para evitar delay na carga do plugin
            import librosa
            
            data, sample_rate = read_wav_file(self.audio_path)
            if len(data) == 0:
                self.result.emit([], [], sample_rate)
                return
            
            # Converter para float32 se necessário
            if data.dtype != np.float32:
                data = data.astype(np.float32)
                if np.max(np.abs(data)) > 1.0:
                    data = data / 32768.0

            # --- CROP AUDIO (OFFSET -> CUTOFF) ---
            # Se offset e cutoff forem válidos, recorta o áudio
            start_sample = 0
            end_sample = len(data)
            
            if self.offset_ms > 0:
                start_sample = int(self.offset_ms * sample_rate / 1000)
            
            if self.cutoff_ms != 0:
                # Cutoff positivo: distancia do final (ignore se for o caso do UTAU clássico onde cutoff positivo tira do fim)
                # Cutoff negativo: distancia do offset (ignore tambem)
                # O WaveformWidget trata cutoff como posição absoluta visual ou relativa?
                # No UTAU: 
                # Cutoff > 0: Tempo a ser cortado do *final* (duração - cutoff)
                # Cutoff < 0: Duração absoluta a partir do offset (offset + abs(cutoff))
                # Mas aqui self.cutoff_ms veio do self._current_entry.cutoff que é o valor cru do OTO.
                
                # Vamos simplificar: se cutoff > 0, end = len - cutoff
                # se cutoff < 0, end = offset + abs(cutoff)
                
                # MAS, no main.py, passamos apenas valores crus.
                # Precisamos da lógica de UTAU real.
                
                total_samples = len(data)
                
                if self.cutoff_ms > 0:
                    # Cutoff positivo = retira do final
                    samples_to_cut = int(self.cutoff_ms * sample_rate / 1000)
                    end_sample = total_samples - samples_to_cut
                elif self.cutoff_ms < 0:
                    # Cutoff negativo = duração fixa a partir do offset
                    duration_ms = abs(self.cutoff_ms)
                    duration_samples = int(duration_ms * sample_rate / 1000)
                    end_sample = start_sample + duration_samples
            
            # Garante limites
            start_sample = max(0, min(start_sample, len(data)))
            end_sample = max(start_sample, min(end_sample, len(data)))
            
            # Recorta
            if start_sample < end_sample:
                data = data[start_sample:end_sample]
            else:
                 # Se inválido, analisa tudo ou retorna vazio? Retorna vazio para evitar erro.
                self.result.emit([], [], sample_rate)
                return

            # Calcular parâmetros baseados na janela
            frame_length = int(sample_rate * self.window_ms / 1000)
            if frame_length < 2048: frame_length = 2048 # pyin precisa de buffer
            hop_length = frame_length // 4
            
            # Usar pyin (Probabilistic YIN) - Robusto contra erros de oitava
            f0, voiced_flag, voiced_probs = librosa.pyin(
                data,
                fmin=librosa.note_to_hz('C2'),
                fmax=librosa.note_to_hz('C6'),
                sr=sample_rate,
                frame_length=frame_length,
                hop_length=hop_length,
                center=True
            )
            
            # Gerar tempos
            times = librosa.times_like(f0, sr=sample_rate, hop_length=hop_length) * 1000 # ms
            
            # Ajustar tempos para serem relativos ao início do arquivo original (para bater com waveform)?
            # O usuário pediu "analisar somente a parte...".  Visualmente, se ele quer ver o pitch DAQUELA parte, 
            # talvez ele queira que o gráfico comece em 0 (relativo ao recorte) ou no tempo real.
            # Se mostrarmos tempo real, ajuda a comparar. 
            # Vamos somar o offset_ms aos tempos.
            times = times + self.offset_ms
            
            # Limpar NaNs
            pitches = np.nan_to_num(f0)
            
            self.result.emit(times.tolist(), pitches.tolist(), sample_rate)
            
        except Exception as e:
            print(f"[Pitch Analyzer] Erro: {e}")
            self.result.emit([], [], 0)


class PitchAnalyzerDialog(QDialog):
    """Diálogo do Analisador de Pitch"""
    
    def __init__(self, plugin: 'PitchAnalyzerPlugin', parent=None):
        super().__init__(parent)
        self.plugin = plugin
        self.worker = None
        self.times = []
        self.pitches = []
        self._setup_ui()
    
    def _setup_ui(self):
        self.setWindowTitle("Análise de Pitch")
        self.setMinimumSize(750, 500)
        
        layout = QVBoxLayout(self)
        
        # Configurações
        config_layout = QHBoxLayout()
        
        config_layout.addWidget(QLabel("Janela de análise:"))
        self.spin_window = QSpinBox()
        self.spin_window.setRange(20, 100)
        self.spin_window.setValue(50)
        self.spin_window.setSuffix(" ms")
        config_layout.addWidget(self.spin_window)
        
        config_layout.addWidget(QLabel("Escala:"))
        self.combo_scale = QComboBox()
        self.combo_scale.addItems(["Linear (Hz)", "Logarítmica"])
        self.combo_scale.currentIndexChanged.connect(self._update_plot)
        config_layout.addWidget(self.combo_scale)
        
        config_layout.addStretch()
        
        self.btn_analyze = QPushButton("🎵 Analisar Alias Atual")
        self.btn_analyze.clicked.connect(self._analyze_current)
        config_layout.addWidget(self.btn_analyze)
        
        layout.addLayout(config_layout)
        
        # Gráfico de pitch
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground('#1e1e1e')
        self.plot_widget.setLabel('left', 'Frequência', units='Hz')
        self.plot_widget.setLabel('bottom', 'Tempo', units='ms')
        self.plot_widget.showGrid(x=True, y=True, alpha=0.3)
        
        self.pitch_curve = self.plot_widget.plot([], [], pen=pg.mkPen('#00ff00', width=2))
        
        layout.addWidget(self.plot_widget)
        
        # Info de pitch
        info_layout = QHBoxLayout()
        
        self.lbl_pitch_info = QLabel("Selecione um alias e clique em 'Analisar'")
        self.lbl_pitch_info.setStyleSheet("font-size: 16px; font-weight: bold;")
        info_layout.addWidget(self.lbl_pitch_info)
        
        info_layout.addStretch()
        
        self.lbl_stats = QLabel("")
        info_layout.addWidget(self.lbl_stats)
        
        layout.addLayout(info_layout)
        
        # Linhas de referência de notas
        self.note_lines = []
        
        # Progresso
        self.progress_label = QLabel("")
        layout.addWidget(self.progress_label)
        
        # Botões
        buttons_layout = QHBoxLayout()
        
        btn_close = QPushButton("Fechar")
        btn_close.clicked.connect(self.close)
        
        buttons_layout.addStretch()
        buttons_layout.addWidget(btn_close)
        layout.addLayout(buttons_layout)
    
    def _analyze_current(self):
        """Analisa o alias atualmente selecionado"""
        selected = self.plugin.get_selected_rows()
        if not selected:
            self.lbl_pitch_info.setText("Nenhum alias selecionado")
            return
        
        row = selected[0]
        audio_path = self.plugin.get_audio_path(row)
        
        if not audio_path:
            self.lbl_pitch_info.setText("Arquivo de áudio não encontrado")
            return
        
        data = self.plugin.get_alias_data(row)
        self.lbl_pitch_info.setText(f"Analisando: {data['alias']}...")
        
        self.btn_analyze.setEnabled(False)
        
        offset = 0
        cutoff = 0
        try:
            # Tenta pegar do plugin se disponível, ou da main window se acessível
            # O plugin tem self.plugin.main_window? Sim, passado no construtor do dialog.
            mw = self.plugin.main_window
            if hasattr(mw, '_current_entry') and mw._current_entry:
                offset = float(mw._current_entry.offset)
                cutoff = float(mw._current_entry.cutoff)
        except:
            pass

        self.worker = PitchAnalyzerWorker(str(audio_path), self.spin_window.value(), offset, cutoff)
        self.worker.progress.connect(self._on_progress)
        self.worker.result.connect(self._on_result)
        self.worker.start()
    
    def _on_progress(self, current, total):
        self.progress_label.setText(f"Processando: {current}/{total} frames")
    
    def _on_result(self, times, pitches, sample_rate):
        """Recebe os resultados da análise"""
        self.btn_analyze.setEnabled(True)
        self.progress_label.setText("")
        
        self.times = times
        self.pitches = pitches
        
        if not times:
            self.lbl_pitch_info.setText("Não foi possível analisar o áudio")
            return
        
        self._update_plot()
        self._update_stats()
    
    def _update_plot(self):
        """Atualiza o gráfico de pitch"""
        if not self.times:
            return
        
        # Filtrar zeros (silêncio)
        valid_times = []
        valid_pitches = []
        
        for t, p in zip(self.times, self.pitches):
            if p > 0:
                valid_times.append(t)
                valid_pitches.append(p)
        
        self.pitch_curve.setData(valid_times, valid_pitches)
        
        # Ajustar escala
        if self.combo_scale.currentIndex() == 1:  # Logarítmica
            self.plot_widget.setLogMode(x=False, y=True)
        else:
            self.plot_widget.setLogMode(x=False, y=False)
        
        # Auto-range
        self.plot_widget.autoRange()
    
    def _update_stats(self):
        """Atualiza estatísticas de pitch"""
        valid_pitches = [p for p in self.pitches if p > 0]
        
        if not valid_pitches:
            self.lbl_stats.setText("Sem pitch detectado")
            return
        
        avg_pitch = np.mean(valid_pitches)
        min_pitch = np.min(valid_pitches)
        max_pitch = np.max(valid_pitches)
        
        avg_note = freq_to_note(avg_pitch)
        min_note = freq_to_note(min_pitch)
        max_note = freq_to_note(max_pitch)
        
        self.lbl_pitch_info.setText(f"Pitch médio: {avg_pitch:.1f} Hz ({avg_note})")
        self.lbl_stats.setText(
            f"Min: {min_pitch:.1f} Hz ({min_note}) | "
            f"Max: {max_pitch:.1f} Hz ({max_note})"
        )


class PitchAnalyzerPlugin(BasePlugin):
    """Plugin para análise de pitch"""
    
    NAME = "Colheita - Análise de Pitch"
    DESCRIPTION = "Mostra a frequência fundamental do áudio"
    CATEGORY = PluginCategory.ANALYSIS
    VERSION = "1.0.0"
    
    def get_dialog(self) -> Optional[QDialog]:
        return PitchAnalyzerDialog(self, self.main_window)
    
    def execute(self, **kwargs) -> PluginResult:
        return PluginResult(
            success=True,
            message="Use o diálogo para analisar pitch"
        )
