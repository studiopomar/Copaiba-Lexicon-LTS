# spectrogram_widget.py

from __future__ import annotations

import numpy as np
import librosa
import librosa.display
from PySide6.QtWidgets import QWidget, QVBoxLayout, QSizePolicy
from PySide6.QtCore import Qt, Signal, QThread, QTimer
from PySide6.QtGui import QColor
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from matplotlib.lines import Line2D
import matplotlib.pyplot as plt

try:
    from backend_gpu import gpu_enabled, get_gpu_backend

    GPU_AVAILABLE = True
except ImportError:
    GPU_AVAILABLE = False


    def gpu_enabled():
        return False


class SpectrogramWorker(QThread):
    finished = Signal(np.ndarray)
    error = Signal(str)

    def __init__(self, data, sample_rate, config):
        super().__init__()
        self.data = data
        self.sample_rate = sample_rate
        self.config = config
        self._is_cancelled = False

    def cancel(self):
        self._is_cancelled = True
        try:
            self.finished.disconnect()
        except:
            pass
        try:
            self.error.disconnect()
        except:
            pass

    def run(self):
        try:
            if self._is_cancelled: return

            data = self.data
            if len(data.shape) > 1: data = np.mean(data, axis=1)
            data = data.astype(np.float32)

            actual_rate = self.sample_rate

            if self._is_cancelled: return

            n_fft = self.config.get('n_fft', 4096)
            hop_size = self.config.get('hop_size', 256)
            window_size = self.config.get('window_size', 4096)

            # Usa librosa.stft para calcular espectrograma
            S = librosa.stft(
                data,
                n_fft=n_fft,
                hop_length=hop_size,
                win_length=window_size,
                window='hann',
                center=False
            )

            if self._is_cancelled: return

            # Converte para magnitude em dB
            S_mag = np.abs(S)
            S_db = librosa.amplitude_to_db(S_mag, ref=np.max)

            if self._is_cancelled: return

            # Aplica gamma e contraste
            gamma = self.config.get('gamma', 0.8)
            contrast = self.config.get('contrast', 1.2)

            # Normaliza para 0-1
            db_min = S_db.min()
            db_max = S_db.max()
            S_norm = (S_db - db_min) / (db_max - db_min) if db_max > db_min else S_db

            # Aplica gamma
            S_norm = np.power(S_norm, gamma)

            # Aplica contraste
            S_norm = (S_norm - 0.5) * contrast + 0.5
            S_norm = np.clip(S_norm, 0, 1)

            if not self._is_cancelled:
                self.finished.emit(S_norm.astype(np.float32))

        except Exception as e:
            if not self._is_cancelled:
                self.error.emit(str(e))


class SpectrogramWidget(QWidget):
    """
    Widget para exibir espectrograma usando Matplotlib.
    Sincroniza com a waveform principal via sinais.
    """
    mouseMoved = Signal(float)
    markerMoved = Signal(str, float) # name, new_time_s

    def __init__(self, parent=None):
        super().__init__(parent)

        self._wave_data = None
        # ... (unchanged) ...
        self._marker_lines = {}
        self._current_marker_positions = {}
        self._dragging_marker = None
        self._sample_rate = 44100
        self._audio_duration = 0.0

        # Configurações Padrão
        self._window_size = 4096
        self._hop_size = 256
        self._n_fft = 4096
        self._max_freq = 22000
        self._min_freq = 0
        self._gamma = 0.8
        self._contrast = 1.2
        self._resolution_quality = 'ultra'
        self._use_gpu = False

        self._background_color = QColor(0, 0, 0)
        self._spectrum_color = QColor(255, 180, 0)
        self._colormap_name = 'inferno'

        self._spectrogram_cache = None
        self._cache_valid = False
        self._current_wav_path = None
        self._spectrogram_cache = None
        self._cache_valid = False
        self._current_wav_path = None
        self._worker = None
        self._running_workers = []  # Lista para manter workers antigos vivos até terminarem

        # Timer para debounce
        self._debounce_timer = QTimer(self)
        self._debounce_timer.setSingleShot(True)
        self._debounce_timer.setInterval(100)
        self._debounce_timer.timeout.connect(self._do_compute_spectrogram)

        # Matplotlib Figure e Canvas
        self.figure = Figure(figsize=(10, 2), facecolor='#000000')
        self.canvas = FigureCanvasQTAgg(self.figure)
        self.ax = self.figure.add_subplot(111)

        # Remove margens para alinhamento perfeito com waveform (sem eixo Y)
        self.figure.subplots_adjust(left=0, right=1, top=1, bottom=0, hspace=0, wspace=0)
        self.ax.set_axis_off()  # Remove eixos visuais (grids, labels)
        self.ax.set_aspect('auto')  # Permite stretch automático

        # Define fundo preto
        self.ax.set_facecolor('#000000')
        self.figure.patch.set_facecolor('#000000')

        # Layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.canvas)

        self.setMinimumHeight(80)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self._needs_update = False
        self._img_plot = None  # Referência para a imagem plotada

        # Conecta movimento do mouse e cliques
        self.canvas.mpl_connect('motion_notify_event', self._on_mouse_motion)
        self.canvas.mpl_connect('button_press_event', self._on_mouse_press)
        self.canvas.mpl_connect('button_release_event', self._on_mouse_release)

    # === MARCADORES E INTERAÇÃO ===
    
    def update_markers(self, positions: dict):
        """
        Recebe posições dos marcadores (em segundos) e desenha linhas verticais.
        positions: {'offset': 0.1, 'overlap': 0.15, ...}
        """
        self._current_marker_positions = positions
        
        # Limpa linhas antigas
        for line in self._marker_lines.values():
            if line in self.ax.lines:
                line.remove()
        self._marker_lines.clear()
        
        # Cores (hardcoded similar ao WaveformWidget/MarkerManager por enquanto)
        styles = {
            "offset": "#4da6ff",
            "overlap": "#00ff00", 
            "preutter": "#ff0000",
            "consonant": "#ff69b4", 
            "cutoff": "#4da6ff"
        }
        
        # Desenha novas linhas
        for name, pos_s in positions.items():
            color = styles.get(name, "#ffffff")
            # Usa Line2D do matplotlib via axvline
            # ZORDER alto (100) garante que fique na frente do imshow
            line = self.ax.axvline(x=pos_s, color=color, linewidth=2, alpha=0.9, zorder=100)
            self._marker_lines[name] = line
            
        self.canvas.draw_idle()

    def _on_mouse_press(self, event):
        if event.inaxes != self.ax or event.button != 1:
            return
            
        x_click = event.xdata
        if x_click is None: return
        
        closest_dist = float('inf')
        closest_name = None
        # Tolerância aumentada para facilitar clique (0.1s)
        tolerance = 0.1 
        
        for name, pos in self._current_marker_positions.items():
            dist = abs(pos - x_click)
            if dist < closest_dist and dist < tolerance:
                closest_dist = dist
                closest_name = name
                
        if closest_name:
            self._dragging_marker = closest_name
            # print(f"[DEBUG_SPEC] Dragging marker: {closest_name}")
            
    def _on_mouse_release(self, event):
        if self._dragging_marker:
            self._dragging_marker = None

    def _on_mouse_motion(self, event):
        """Emite sinal de posição do mouse e gerencia arraste."""
        if event.inaxes == self.ax and event.xdata is not None:
            self.mouseMoved.emit(event.xdata)
            
            # Se estiver arrastando um marcador
            if self._dragging_marker:
                self.markerMoved.emit(self._dragging_marker, event.xdata)

    def get_plot_item(self):
        """Retorna o axes do matplotlib para compatibilidade."""
        return self.ax

    def set_audio_data(self, wave_data: np.ndarray, sample_rate: int, duration: float, wav_path: str = None):
        """
        Define os dados de áudio para o espectrograma.
        """
        print(f"[DEBUG] set_audio_data chamado: shape={wave_data.shape if wave_data is not None else None}, sr={sample_rate}, duration={duration:.3f}s, visible={self.isVisible()}")
        
        # Verifica cache por caminho de arquivo
        if wav_path and wav_path == self._current_wav_path and self._cache_valid:
            print(f"[DEBUG] Cache válido para {wav_path}, reutilizando")
            if self.isVisible() and self._spectrogram_cache is not None:
                self._update_display()
            return

        # Novo arquivo - precisa recalcular
        self._wave_data = wave_data
        self._sample_rate = sample_rate
        self._audio_duration = duration
        self._current_wav_path = wav_path
        self._cache_valid = False
        self._needs_update = True
        if self.isVisible():
            self._do_compute_spectrogram()

    def _request_compute(self):
        """Solicita recálculo com debounce."""
        self._debounce_timer.start()

    def _do_compute_spectrogram(self):
        if self._wave_data is None or len(self._wave_data) == 0:
            return

        # Gerencia thread anterior com segurança (evita crash QThread destroyed while running)
        if self._worker is not None:
            old_worker = self._worker
            self._worker = None # Remove referência principal imediatamente
            
            if old_worker.isRunning():
                old_worker.cancel()
                self._running_workers.append(old_worker)
                # Conecta sinal para auto-remoção da lista quando terminar
                # Lambda captura old_worker por valor padrão para evitar closure tardio
                old_worker.finished.connect(lambda _, w=old_worker: self._cleanup_worker(w))
                old_worker.error.connect(lambda _, w=old_worker: self._cleanup_worker(w))
            else:
                # Se não estiver rodando, apenas limpa
                old_worker.deleteLater()

        config = {
            'n_fft': self._n_fft,
            'hop_size': self._hop_size,
            'window_size': self._window_size,
            'resolution_quality': self._resolution_quality,
            'use_gpu': self._use_gpu,
            'gamma': self._gamma,
            'contrast': self._contrast,
            'min_freq': self._min_freq,
            'max_freq': self._max_freq,
        }

        self._worker = SpectrogramWorker(self._wave_data, self._sample_rate, config)
        self._worker.finished.connect(self._on_spectrogram_ready)
        self._worker.error.connect(self._on_spectrogram_error)
        self._worker.start()

    def _compute_spectrogram(self):
        """Wrapper para compatibilidade."""
        self._do_compute_spectrogram()

    def _on_spectrogram_ready(self, spectrogram_data):
        print(f"[DEBUG] Espectrograma pronto! Shape: {spectrogram_data.shape}, Min: {spectrogram_data.min():.3f}, Max: {spectrogram_data.max():.3f}")
        self._spectrogram_cache = spectrogram_data
        self._cache_valid = True
        self._update_display()
        self._worker = None

    def _on_spectrogram_error(self, error_msg):
        print(f"[ERROR] Erro no espectrograma: {error_msg}")
        self._spectrogram_cache = None
        self._cache_valid = False
        self._worker = None

    def _update_display(self):
        """Renderiza o espectrograma usando matplotlib imshow."""
        if self._spectrogram_cache is None:
            return

        # Salva o zoom atual (xlim) antes de limpar, se já houver plot
        current_xlim = self.ax.get_xlim() if self.ax.has_data() else None

        self.ax.clear()
        self.ax.set_axis_off()
        self.ax.set_facecolor('#000000')

        # Os dados já vêm normalizados (0-1) do worker
        # Converte para dB para melhor visualização
        S_db = librosa.amplitude_to_db(self._spectrogram_cache, ref=np.max)

        # Calcula extent: [x_min, x_max, y_min, y_max]
        n_freqs, n_frames = self._spectrogram_cache.shape
        duration = self._audio_duration
        
        # Extent define os limites da imagem em coordenadas de dados
        extent = [0, duration, 0, self._sample_rate / 2]
        
        # Usa imshow diretamente para controle total
        self._img_plot = self.ax.imshow(
            S_db,
            origin='lower',
            aspect='auto',
            extent=extent,
            cmap=self._colormap_name,
            vmin=-80,
            vmax=0
        )
        
        # Restaura zoom ou define padrão
        if current_xlim and current_xlim != (0.0, 1.0): # 0.0, 1.0 é o default do mpl sem dados
             self.ax.set_xlim(current_xlim)
        else:
             self.ax.set_xlim(0, duration)
             
        self.ax.set_ylim(0, min(self._max_freq, self._sample_rate / 2))

        # Redesenha os marcadores que foram apagados pelo ax.clear()
        if self._current_marker_positions:
            self.update_markers(self._current_marker_positions)
        else:
            self.canvas.draw_idle()

    def set_x_range(self, start_time: float, end_time: float):
        """Define o range visível do eixo X (sincronização com waveform)."""
        if self._cache_valid and self._img_plot is not None:
            self.ax.set_xlim(start_time, end_time)
            self.canvas.draw_idle()

    def set_visible_region(self, start_time: float, end_time: float):
        """Compatibilidade com código antigo."""
        self.set_x_range(start_time, end_time)

    def showEvent(self, event):
        super().showEvent(event)
        if self._needs_update and not self._cache_valid:
            self._compute_spectrogram()

    def clear(self):
        if self._worker is not None:
            old_worker = self._worker
            self._worker = None
            if old_worker.isRunning():
                old_worker.cancel()
                self._running_workers.append(old_worker)
                old_worker.finished.connect(lambda _, w=old_worker: self._cleanup_worker(w))
                old_worker.error.connect(lambda _, w=old_worker: self._cleanup_worker(w))
            else:
                old_worker.deleteLater()

        self._wave_data = None
        self._spectrogram_cache = None
        self._cache_valid = False
        self._needs_update = False
        self.ax.clear()
        self.ax.set_axis_off()
        self.canvas.draw_idle()

    def _cleanup_worker(self, worker):
        """Remove worker da lista de ativos após término."""
        if worker in self._running_workers:
            self._running_workers.remove(worker)
        worker.deleteLater()

    def closeEvent(self, event):
        """Garante que todas as threads sejam finalizadas ao fechar."""
        # Cancela workers ativos
        if self._worker:
            self._worker.cancel()
            self._worker.wait(500)
            
        for w in self._running_workers:
            w.cancel()
            w.wait(200) # Tenta esperar um pouco
            
        super().closeEvent(event)

    def cleanup(self):
        self.clear()
        # Garante limpeza extra
        if self._worker:
            self._worker.cancel()
            self._worker.wait(500)

    def set_height(self, height: int):
        self.setFixedHeight(max(80, min(height, 600)))

    # --- Configurações ---

    def set_colormap(self, name: str):
        self._colormap_name = name
        if self._cache_valid:
            self._update_display()

    def set_background_color(self, color: QColor):
        if isinstance(color, str):
            color = QColor(color)
        self._background_color = color
        hex_color = color.name()
        self.ax.set_facecolor(hex_color)
        self.figure.patch.set_facecolor(hex_color)
        self.canvas.draw_idle()

    def set_spectrum_color(self, color: QColor):
        """Mantido para compatibilidade, mas não usado (colormap controla cores)."""
        if isinstance(color, str):
            color = QColor(color)
        self._spectrum_color = color

    def set_fft_params(self, n_fft: int, hop_size: int, window_size: int):
        """Atualiza parâmetros da FFT e recalcula."""
        if (self._n_fft != n_fft or 
            self._hop_size != hop_size or 
            self._window_size != window_size):
            
            self._n_fft = n_fft
            self._hop_size = hop_size
            self._window_size = window_size
            self._cache_valid = False
            if self._wave_data is not None and self.isVisible():
                self._request_compute()

    def set_gamma(self, gamma: float):
        self._gamma = max(0.1, min(3.0, gamma))
        self._cache_valid = False
        if self._wave_data is not None and self.isVisible():
            self._request_compute()

    def set_contrast(self, contrast: float):
        self._contrast = max(0.1, min(5.0, contrast))
        self._cache_valid = False
        if self._wave_data is not None and self.isVisible():
            self._request_compute()

    def set_freq_range(self, min_freq: int, max_freq: int):
        self._min_freq = max(0, min_freq)
        self._max_freq = min(max_freq, self._sample_rate // 2)
        self._cache_valid = False
        if self._wave_data is not None and self.isVisible():
            self._compute_spectrogram()

    def set_resolution_quality(self, quality: str):
        self._resolution_quality = quality

        if quality == 'low':
            self._n_fft = 1024
            self._hop_size = 512
            self._window_size = 1024
        elif quality == 'medium':
            self._n_fft = 2048
            self._hop_size = 512
            self._window_size = 2048
        elif quality == 'high':
            self._n_fft = 4096
            self._hop_size = 256
            self._window_size = 4096
        else:  # ULTRA
            self._n_fft = 4096
            self._hop_size = 128
            self._window_size = 4096

        self._cache_valid = False
        if self._wave_data is not None and self.isVisible():
            self._compute_spectrogram()

    def set_use_gpu(self, use_gpu: bool):
        self._use_gpu = use_gpu and GPU_AVAILABLE and gpu_enabled()
        self._cache_valid = False

    def get_background_color(self) -> QColor:
        return self._background_color

    def get_spectrum_color(self) -> QColor:
        return self._spectrum_color