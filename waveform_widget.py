<<<<<<< Updated upstream
# waveform_widget.py

from __future__ import annotations
import time
from pathlib import Path
from collections import OrderedDict
import numpy as np
import pyqtgraph as pg
from PySide6.QtCore import Qt, Signal, QTimer, QEvent
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QSizePolicy, QSplitter
from PySide6.QtGui import QColor

from minimap_widget import MiniMapWidget
from audio_loader import load_waveform_sync
from waveform_plot import WaveformPlotWidget
from marker_manager import MarkerManager
from spectrogram_widget import SpectrogramWidget
from copaiba import OtoEntry

# Tenta importar widget OpenGL acelerado
try:
    from spectrogram_gl_widget import SpectrogramGLWidget
    OPENGL_SPECTROGRAM_AVAILABLE = True
except ImportError:
    OPENGL_SPECTROGRAM_AVAILABLE = False

try:
    from backend_gpu import gpu_enabled

    GPU_BACKEND_AVAILABLE = True
except ImportError:
    GPU_BACKEND_AVAILABLE = False


    def gpu_enabled():
        return False


class WaveformWidget(QWidget):
    aliasStepRequested = Signal(int)
    playSegmentRequested = Signal(float, float)

    # Mapeamento padrão de teclas (pode ser personalizado)
    DEFAULT_MARKER_KEYS = {
        Qt.Key_Q: "offset",
        Qt.Key_W: "overlap",
        Qt.Key_E: "preutter",
        Qt.Key_R: "consonant",
        Qt.Key_T: "cutoff",
    }

    def __init__(self, parent=None):
        super().__init__(parent)

        # Estados Iniciais
        self._show_minimap = True
        self._show_spectrogram = True
        self._current_row = -1
        self._current_entry = None
        self._current_path = None
        self._last_mouse_t = 0.0
        self._active_marker_key = None
        self._snap_enabled = False
        self._snap_mode = "peaks"
        self._keep_zoom_on_alias_changes = True
        self._srp_enabled = False
        self._edit_callback = None
        self._audio_dur = 0.0
        self._normalize_enabled = True  # Normalização de amplitude
        self._sector_playback_enabled = False  # Modo de reprodução por setor
        self._smooth_scroll_enabled = True  # Deslizamento suave na reprodução
        self._saved_zoom_width = None  # Largura do zoom persistente
        self._is_loading_waveform = False  # Flag para bloquear update de zoom durante carregamento
        
        # Mapeamento de teclas personalizável (cópia do padrão)
        self._marker_keys = dict(self.DEFAULT_MARKER_KEYS)


        # Widgets
        self._minimap_widget = MiniMapWidget(self)
        self._plot = WaveformPlotWidget(self)

        # --- Configuração de Interação ---
        # --- Configuração de Interação ---
        # Sobrescreve wheelEvent diretamente para garantir captura
        self._plot.wheelEvent = self._on_plot_wheel_event
        
        self._plot.plotItem.setMouseEnabled(x=False, y=False)
        self._plot.plotItem.vb.disableAutoRange()
        self._plot.plotItem.setMenuEnabled(False)

        # Usa widget OpenGL se disponível, senão fallback para Matplotlib
        if OPENGL_SPECTROGRAM_AVAILABLE:
            self._spectrogram_widget = SpectrogramGLWidget(self)
        else:
            self._spectrogram_widget = SpectrogramWidget(self)
        if self._show_spectrogram:
            self._spectrogram_widget.show()
        else:
            self._spectrogram_widget.hide()
        self._spectrogram_widget.mouseMoved.connect(self._on_spectrogram_mouse_moved)

        # Sincronização com espectrograma via _on_plot_x_range_changed
        # (Matplotlib não suporta setXLink, então fazemos sync manual)

        # Splitter para redimensionar waveform/espectrograma
        self._splitter = QSplitter(Qt.Vertical)
        self._splitter.setHandleWidth(4)
        self._splitter.setStyleSheet("""
            QSplitter::handle {
                background: #444;
            }
            QSplitter::handle:hover {
                background: #666;
            }
        """)
        self._splitter.addWidget(self._plot)
        self._splitter.addWidget(self._spectrogram_widget)
        self._splitter.setSizes([300, 150])  # Proporção inicial
        self._splitter.setCollapsible(0, False)  # Não pode colapsar waveform
        self._splitter.setCollapsible(1, True)   # Pode colapsar espectrograma

        # Layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(1)
        layout.addWidget(self._splitter, 1)
        layout.addWidget(self._minimap_widget)

        self._label = QLabel("Nenhum arquivo carregado", self)
        self._label.setStyleSheet("color: #888; padding: 5px;")
        layout.addWidget(self._label)

        # Foco
        self.setFocusPolicy(Qt.StrongFocus)
        self._plot.setFocusPolicy(Qt.ClickFocus)

        # Dados
        self._wave_times = None
        self._wave_data = None
        self._last_wav_path = None

        # Playback Visual
        self._playhead = pg.InfiniteLine(pos=0, angle=90, pen=pg.mkPen('#FFD700', width=2))
        self._playhead.setZValue(9999)
        self._plot.addItem(self._playhead)
        self._playhead.hide()

        self._playback_timer = QTimer(self)
        self._playback_timer.setInterval(15)
        self._playback_timer.timeout.connect(self._update_playhead)

        # Managers
        self._marker_manager = MarkerManager(self._plot)
        self._marker_manager.set_secondary_plot(self._spectrogram_widget)
        self._spectrogram_widget.markerMoved.connect(self._on_spectrogram_marker_moved)
        if hasattr(self._spectrogram_widget, 'markerDragFinished'):
            self._spectrogram_widget.markerDragFinished.connect(
                lambda: self._marker_manager.commit_marker_drag()
            )
        self._marker_manager.set_edit_callback(self._entry_edited_from_markers)

        # Configurações do Plot
        self._plot.showGrid(x=True, y=True, alpha=0.15) # Grid sutil
        self._plot.scene().sigMouseMoved.connect(self._on_plot_mouse_moved)
        self._plot.scene().sigMouseClicked.connect(self._on_mouse_clicked)
        
        # Monkey patch para suportar drag sem tecla pressionada
        # Injeta handlers de mousePress e mouseRelease no PlotWidget
        self._orig_mouse_press = self._plot.mousePressEvent
        self._orig_mouse_release = self._plot.mouseReleaseEvent
        
        def patched_mouse_press(event):
            self._on_mouse_pressed(event)
            self._orig_mouse_press(event)
            
        def patched_mouse_release(event):
            self._on_mouse_released(event)
            self._orig_mouse_release(event)
            
        self._plot.mousePressEvent = patched_mouse_press
        self._plot.mouseReleaseEvent = patched_mouse_release

        # Sincroniza zoom X
        self._plot.sigRangeChanged.connect(self._update_views_sync)

    # --- Event Filter: Zoom e Navegação ---
    # --- Interação: Zoom e Navegação Direta ---
    def _on_plot_wheel_event(self, event):
        """Manipula eventos de roda do mouse diretamente no plot."""
        modifiers = event.modifiers()
        delta = event.angleDelta().y()

        if delta == 0:
            return

        # CTRL + Roda: Zoom Horizontal
        if modifiers & Qt.ControlModifier:
            factor = 0.8 if delta > 0 else 1.25
            self._apply_zoom_horizontal(factor)
            event.accept()

        # ALT + Roda: Zoom Vertical
        elif modifiers & Qt.AltModifier:
            factor = 0.8 if delta > 0 else 1.25
            self._apply_zoom_vertical(factor)
            event.accept()
        
        # SHIFT + Roda: Pan Horizontal
        elif modifiers & Qt.ShiftModifier:
            self._apply_pan_horizontal(delta)
            event.accept()

        # Apenas Roda: Trocar Alias
        else:
            if delta > 0:
                self.aliasStepRequested.emit(-1)
            elif delta < 0:
                self.aliasStepRequested.emit(1)
            event.accept()

    def _apply_zoom_horizontal(self, factor):
        if self._audio_dur <= 0: return

        try:
            (x1, x2), _ = self._plot.viewRange()
        except:
            return

        current_width = x2 - x1
        new_width = current_width * factor

        center = (x1 + x2) / 2.0
        new_x1 = center - new_width / 2.0
        new_x2 = center + new_width / 2.0

        min_range = 0.01
        if new_x2 - new_x1 < min_range:
            new_x1 = center - min_range / 2.0
            new_x2 = center + min_range / 2.0

        if new_x1 < 0:
            new_x2 -= new_x1
            new_x1 = 0
        if new_x2 > self._audio_dur:
            new_x1 -= (new_x2 - self._audio_dur)
            new_x2 = self._audio_dur
            if new_x1 < 0:
                new_x1 = 0

        self._plot.setXRange(new_x1, new_x2, padding=0)

    def _apply_zoom_vertical(self, factor):
        """Aplica zoom vertical (ganho visual) na Waveform."""
        if self._audio_dur <= 0: return
        
        try:
            _, (y1, y2) = self._plot.viewRange()
        except:
            return
            
        current_height = y2 - y1
        new_height = current_height * factor
        
        # Não permite zoom muito extremo (de -1 a 1 para normalizado, então a altura é ~2)
        if new_height > 10.0: new_height = 10.0
        if new_height < 0.01: new_height = 0.01
        
        center_y = (y1 + y2) / 2.0
        new_y1 = center_y - (new_height / 2.0)
        new_y2 = center_y + (new_height / 2.0)
        
        self._plot.setYRange(new_y1, new_y2, padding=0)
        if current_width <= 0: return

        center = x1 + current_width / 2
        new_width = current_width * factor

        # Limites Horizontal
        if new_width < 0.001: new_width = 0.001
        if new_width > self._audio_dur * 1.5: new_width = self._audio_dur * 1.5

        new_x1 = center - new_width / 2
        new_x2 = center + new_width / 2

        if new_x1 < 0:
            new_x1 = 0
            new_x2 = new_width
        if new_x2 > self._audio_dur:
            new_x2 = self._audio_dur
            new_x1 = self._audio_dur - new_width
            if new_x1 < 0: new_x1 = 0

        self._plot.setXRange(new_x1, new_x2, padding=0)
        
        # Salva a largura do zoom para persistência (só se não estiver carregando waveform)
        if not self._is_loading_waveform:
            self._saved_zoom_width = new_x2 - new_x1
        
        # Atualizar minimap
        if self._show_minimap:
            self._minimap_widget.set_visible_region(new_x1, new_x2)

    def _apply_zoom_vertical(self, factor):
        try:
            _, (y1, y2) = self._plot.viewRange()
        except:
            return

        current_height = y2 - y1
        if current_height <= 0: current_height = 2.0

        new_height = current_height * factor

        # Limites Vertical
        if new_height < 0.05: new_height = 0.05
        if new_height > 50.0: new_height = 50.0

        new_y1 = -new_height / 2
        new_y2 = new_height / 2

        self._plot.setYRange(new_y1, new_y2, padding=0)

    def _apply_pan_horizontal(self, delta):
        """Pan horizontal com SHIFT+Scroll"""
        if self._audio_dur <= 0: return

        try:
            (x1, x2), _ = self._plot.viewRange()
        except:
            return

        current_width = x2 - x1
        if current_width <= 0: return

        # Pan 10% da largura visível por "scroll"
        pan_amount = current_width * 0.1
        
        if delta > 0:
            # Scroll up = mover para esquerda
            new_x1 = x1 - pan_amount
            new_x2 = x2 - pan_amount
        else:
            # Scroll down = mover para direita
            new_x1 = x1 + pan_amount
            new_x2 = x2 + pan_amount
        
        # Limitar aos bounds
        if new_x1 < 0:
            new_x1 = 0
            new_x2 = current_width
        if new_x2 > self._audio_dur:
            new_x2 = self._audio_dur
            new_x1 = max(0, self._audio_dur - current_width)

        self._plot.setXRange(new_x1, new_x2, padding=0)
        
        # Atualizar minimapa
        if self._show_minimap:
            self._minimap_widget.set_visible_region(new_x1, new_x2)

    # --- Lógica Principal ---

    def show_waveform(self, path: Path, entry: OtoEntry, row: int, reset_zoom: bool = True):
        # Marca que está carregando para bloquear updates de zoom
        self._is_loading_waveform = True
        
        self._current_path = path
        self._last_wav_path = path
        self._current_entry = entry
        self._current_row = row

        # Carrega Audio
        t, y = load_waveform_sync(path, normalize=self._normalize_enabled)
        self._wave_times = t
        self._wave_data = y
        self._audio_dur = t[-1] if len(t) > 0 else 0.0

        # Define limites seguros para evitar overflow
        safe_max_x = max(self._audio_dur, 0.01)
        self._plot.getViewBox().setLimits(
            xMin=-safe_max_x,  # Permite valores negativos para centralização
            xMax=safe_max_x * 2,  # Permite margem para centralização no final
            yMin=-5.0,  # Waveform normalizada vai de -1 a 1, margem extra para zoom
            yMax=5.0
        )

        # Desabilita auto-range temporariamente
        vb = self._plot.getViewBox()
        vb.disableAutoRange()
        
        # Plota dados
        self._plot.set_curve_data(t, y)

        # Zoom: reseta X apenas se explicitamente pedido
        if reset_zoom or self._saved_zoom_width is None:
            # Reset zoom - mostra view completa
            self._plot.setXRange(0, safe_max_x, padding=0)
        else:
            # Usa a largura salva, centraliza na preutterance
            target_width = min(self._saved_zoom_width, safe_max_x)
            
            # Posição da preutterance em segundos
            offset_s = (entry.offset if entry else 0) / 1000.0
            preutter_s = (entry.preutter if entry else 0) / 1000.0
            preutterance_pos = offset_s + preutter_s
            
            # Centraliza na preutterance
            new_x1 = preutterance_pos - target_width / 2
            new_x2 = preutterance_pos + target_width / 2
            
            # Ajusta aos limites
            if new_x1 < 0:
                new_x1 = 0
                new_x2 = target_width
            if new_x2 > safe_max_x:
                new_x2 = safe_max_x
                new_x1 = max(0, safe_max_x - target_width)
            
            self._plot.setXRange(new_x1, new_x2, padding=0)
        
        # Y range SEMPRE deve ser -1.05 a 1.05 para mostrar waveform completa
        self._plot.setYRange(-1.05, 1.05, padding=0)

        # Atualiza Marcadores
        self._marker_manager.set_current_entry(entry, row)
        self._marker_manager.set_audio_duration(self._audio_dur * 1000)
        self._marker_manager.update_markers_from_entry(audio_duration_s=self._audio_dur)

        self._label.setText(f"{path.name} : {entry.alias}")

        if self._show_minimap:
            self._minimap_widget.update_minimap()

        self._update_views_sync()

        if self._show_spectrogram:
            self._load_spectrogram_data(path)

        self.setFocus()
        # Libera o bloqueio de loading
        self._is_loading_waveform = False

    def _update_views_sync(self):
        """Sincroniza o range do espectrograma com a waveform."""
        try:
            (x1, x2), _ = self._plot.viewRange()

            if self._spectrogram_widget.isVisible():
                self._spectrogram_widget.set_x_range(x1, x2)
            
            self._minimap_widget.set_visible_region(x1, x2)
        except:
            pass

    def _load_spectrogram_data(self, path):
        import wave
        try:
            # Salva o X range atual ANTES de carregar espectrograma (XLink pode resetar)
            saved_range = self._plot.viewRange()[0]
            
            with wave.open(str(path), 'rb') as wf:
                sr = wf.getframerate()
                frames = wf.readframes(wf.getnframes())
                data_full = np.frombuffer(frames, dtype=np.int16).astype(np.float32) / 32768.0
                if wf.getnchannels() > 1:
                    data_full = data_full.reshape(-1, wf.getnchannels()).mean(axis=1)
                # Passa wav_path para habilitar cache por arquivo
                self._spectrogram_widget.set_audio_data(data_full, sr, self._audio_dur, wav_path=str(path))
            
            # Restaura o X range após carregar espectrograma
            self._plot.setXRange(saved_range[0], saved_range[1], padding=0)
            # Sincroniza explicitamente o range do espectrograma
            self._spectrogram_widget.set_x_range(saved_range[0], saved_range[1])
        except:
            pass

    def _on_plot_x_range_changed(self):
        self._update_views_sync()

    def _on_plot_mouse_moved(self, pos):
        vb = self._plot.getViewBox()
        if vb is None: return
        p = vb.mapSceneToView(pos)
        self._process_mouse_move(p.x())

    # --- NOVO: Lógica de Arraste de Marcador via Mouse ---
    def _on_mouse_pressed(self, event):
        if event.button() == Qt.LeftButton:
            # 0. Prioridade: Alt + Clique (Tocar do tempo do clique até o final)
            if event.modifiers() & Qt.AltModifier:
                pos = event.pos() 
                scene_pos = self._plot.mapToScene(pos)
                vb = self._plot.plotItem.vb
                mouse_point = vb.mapSceneToView(scene_pos)
                time_start_s = mouse_point.x()
                
                # Obter tempo de cutoff visual
                markers = self._marker_manager.get_marker_positions()
                cutoff_s = markers.get('cutoff', self._audio_dur)
                
                if time_start_s < cutoff_s:
                    self.playSegmentRequested.emit(time_start_s * 1000, cutoff_s * 1000)
                    self.start_playback_visualization(time_start_s, cutoff_s)
                event.accept()
                return

             # 1. Prioridade: Arraste de Marcador (Mouse Only)
            if self._active_marker_key is None:
                pos = event.pos() 
                scene_pos = self._plot.mapToScene(pos)
                vb = self._plot.plotItem.vb
                mouse_point = vb.mapSceneToView(scene_pos)
                time_s = mouse_point.x()
                
                # Procura marcador próximo
                markers = self._marker_manager.get_marker_positions()
                if not markers: return

                # Tolerância visual
                pixel_tolerance = 10 
                view_range = vb.viewRange()[0]
                view_width_s = view_range[1] - view_range[0]
                pixel_width = max(1, self._plot.width())
                threshold_s = (pixel_tolerance / pixel_width) * view_width_s
                
                best_marker = None
                min_dist = float('inf')
                
                priority_order = ["preutter", "overlap", "offset", "cutoff", "consonant"]
                
                for name in priority_order:
                    if name in markers:
                        pos_s = markers[name]
                        dist = abs(pos_s - time_s)
                        if dist < threshold_s and dist < min_dist:
                            min_dist = dist
                            best_marker = name
                
                if best_marker:
                    self._active_marker_key = best_marker 
                    self._dragging_marker_mouse = True
                    self.set_marker_at_mouse(self._active_marker_key)
                    # NÃO executamos event.accept() aqui para permitir que o pyqtgraph processe o clique
                    return

    def _on_mouse_released(self, event):
        if event.button() == Qt.LeftButton:
            if hasattr(self, '_dragging_marker_mouse') and self._dragging_marker_mouse:
                self._dragging_marker_mouse = False
                self._active_marker_key = None
                self._marker_manager.commit_marker_drag()
                # Marca timestamp do último drag para inibir clique acidental
                self._last_drag_time = time.time()

    def _on_mouse_clicked(self, event):
        # Verifica se acabamos de soltar um drag (evita tocar logo após arrastar)
        if hasattr(self, '_last_drag_time') and (time.time() - self._last_drag_time) < 0.2:
            return

        # Verifica se foi clique esquerdo e se não estamos arrastando um marcador (via teclado)
        if event.button() == Qt.LeftButton and self._active_marker_key is None:
            if self._sector_playback_enabled:
                self._play_sector_at_mouse()
            else:
                self._play_main_segment()
            event.accept()

    def _on_spectrogram_mouse_moved(self, t_seconds):
        self._process_mouse_move(t_seconds)

    def cleanup(self):
        """Finaliza recursos e threads ativos."""
        if hasattr(self, '_spectrogram_widget') and self._spectrogram_widget:
            # Chama closeEvent manualmente para disparar cancelamento de threads
            self._spectrogram_widget.close()
            
        if self._playback_timer.isActive():
            self._playback_timer.stop()
            
    def _on_spectrogram_marker_moved(self, name: str, time_s: float):
        """Callback quando um marcador é arrastado no espectrograma."""
        self._marker_manager.set_marker_at_mouse(
            name=name,
            mouse_time_s=time_s,
            snap_enabled=self._snap_enabled,
            snap_mode=self._snap_mode,
            wave_times=self._wave_times,
            wave_data=self._wave_data if self._snap_enabled else None
        )

    def _process_mouse_move(self, time_s):
        self._last_mouse_t = float(max(0.0, time_s))
        self._plot.set_cursor_position(self._last_mouse_t)

        if self._active_marker_key and self._current_entry:
            self.set_marker_at_mouse(self._active_marker_key)

    def set_marker_at_mouse(self, marker_name):
        self._marker_manager.set_marker_at_mouse(
            marker_name, self._last_mouse_t, self._snap_enabled,
            self._snap_mode, self._wave_times, self._wave_data,
            srp_enabled=self._srp_enabled
        )

    def keyPressEvent(self, event):
        if event.isAutoRepeat(): return
        key = event.key()

        if key in self._marker_keys:
            self._active_marker_key = self._marker_keys[key]
            self.set_marker_at_mouse(self._active_marker_key)
            event.accept()
            return

        if key == Qt.Key_Space:
            self._play_main_segment()
            event.accept()
            return

        if key == Qt.Key_Up:
            self.aliasStepRequested.emit(-1)
            event.accept()
            return
        elif key == Qt.Key_Down:
            self.aliasStepRequested.emit(1)
            event.accept()
            return

        super().keyPressEvent(event)

    def keyReleaseEvent(self, event):
        if event.isAutoRepeat(): return
        if event.key() in self._marker_keys:
            if self._marker_keys[event.key()] == self._active_marker_key:
                self._active_marker_key = None
                # Commit: envia valor final para tabela (1 undo state por arraste)
                self._marker_manager.commit_marker_drag()
        super().keyReleaseEvent(event)

    def _play_main_segment(self):
        start, end = self.get_segment_times_ms()
        self.playSegmentRequested.emit(start, end)
        self.start_playback_visualization(start / 1000.0, end / 1000.0)

    def _play_sector_at_mouse(self):
        """Toca o setor OTO onde o mouse está posicionado."""
        if not self._current_entry or self._audio_dur <= 0:
            return
        
        mouse_ms = self._last_mouse_t * 1000.0
        total_ms = self._audio_dur * 1000.0
        
        # Parâmetros OTO em ms
        offset = float(self._current_entry.offset)
        overlap = float(self._current_entry.overlap)
        preutter = float(self._current_entry.preutter)
        consonant = float(self._current_entry.consonant)
        cutoff = float(self._current_entry.cutoff)
        
        # Calcular posições absolutas em ms
        overlap_pos = offset + overlap
        preutter_pos = offset + preutter
        consonant_pos = offset + consonant
        
        # Cutoff: se negativo, é relativo ao offset; se positivo, ao final do arquivo
        if cutoff < 0:
            cutoff_pos = offset - cutoff  # offset - (-400) = offset + 400
        else:
            cutoff_pos = total_ms - cutoff
        
        # Identificar setor clicado e definir início/fim
        start, end = 0, 0
        
        if mouse_ms < offset:
            # Setor 1: Pré-offset (silêncio inicial)
            start, end = 0, offset
        elif mouse_ms < overlap_pos:
            # Setor 2: Offset → Overlap
            start, end = offset, overlap_pos
        elif mouse_ms < preutter_pos:
            # Setor 3: Overlap → Preutter
            start, end = overlap_pos, preutter_pos
        elif mouse_ms < consonant_pos:
            # Setor 4: Preutter → Consonant
            start, end = preutter_pos, consonant_pos
        elif mouse_ms < cutoff_pos:
            # Setor 5: Consonant → Cutoff (vogal sustentada)
            start, end = consonant_pos, cutoff_pos
        else:
            # Setor 6: Pós-Cutoff
            start, end = cutoff_pos, total_ms
        
        # Garantir que valores são válidos
        start = max(0, start)
        end = min(total_ms, end)
        if end <= start:
            end = start + 50  # Mínimo de 50ms se o setor for muito pequeno
        
        # Emite sinal para tocar o setor e visualiza
        self.playSegmentRequested.emit(start, end)
        self.start_playback_visualization(start / 1000.0, end / 1000.0)


    def get_segment_times_ms(self):
        if not self._current_entry or self._audio_dur <= 0: return 0, 0

        total_ms = self._audio_dur * 1000.0
        off = float(self._current_entry.offset)
        cut = float(self._current_entry.cutoff)

        start = max(0.0, off)

        # Cutoff negativo: distância a partir do offset (ex: -400 = offset + 400ms)
        # Cutoff positivo: distância a partir do final do arquivo (ex: 400 = total - 400ms)
        if cut < 0:
            end = off - cut  # off - (-400) = off + 400
        else:
            end = total_ms - cut  # Cutoff positivo = distância do final

        end = min(total_ms, end)
        if end <= start:
            end = min(total_ms, start + 100)

        return start, end

    def start_playback_visualization(self, s, e):
        self._playback_start_t = s
        self._playback_end_t = e
        self._playback_wall_start = time.perf_counter()
        self._playhead.show()
        self._playback_timer.start()

    def _update_playhead(self):
        now = time.perf_counter()
        pos = self._playback_start_t + (now - self._playback_wall_start)
        self._playhead.setValue(pos)
        
        # --- Deslizamento Suave (Smooth Scrolling) ---
        if getattr(self, '_smooth_scroll_enabled', True):
            try:
                (x1, x2), _ = self._plot.viewRange()
                view_width = x2 - x1
                # Empurra a view se o playhead cruzar 75% da tela visível
                threshold = x1 + (view_width * 0.75)
                if pos > threshold:
                    shift = pos - threshold
                    new_x1 = x1 + shift
                    new_x2 = x2 + shift
                    
                    # Limita para não rolar infinitamente além do áudio
                    if new_x1 <= self._audio_dur:
                        self._plot.setXRange(new_x1, new_x2, padding=0)
                        self._update_views_sync()  # Sincroniza o minimap e espectrograma
            except Exception:
                pass
        # ---------------------------------------------
        
        # Atualizar cursor no minimapa
        if self._show_minimap:
            self._minimap_widget.set_cursor_position(pos)
        
        if pos >= self._playback_end_t:
            self._playback_timer.stop()
            self._playhead.hide()
            if self._show_minimap:
                self._minimap_widget.hide_cursor()

    def stop_playback_visualization(self):
        self._playback_timer.stop()
        self._playhead.hide()
        if self._show_minimap:
            self._minimap_widget.hide_cursor()

    def _entry_edited_from_markers(self, row, entry):
        self._current_entry = entry
        if self._edit_callback: self._edit_callback(row, entry)

    def set_show_minimap(self, show):
        self._show_minimap = show
        if show:
            self._minimap_widget.show()
            self._minimap_widget.update_minimap()
        else:
            self._minimap_widget.hide()

    def set_show_spectrogram(self, show):
        self._show_spectrogram = show
        if show:
            self._spectrogram_widget.show()
            if self._last_wav_path: self._load_spectrogram_data(self._last_wav_path)
        else:
            self._spectrogram_widget.hide()

    def set_edit_callback(self, cb):
        self._edit_callback = cb

    def set_snap_enabled(self, e):
        self._snap_enabled = e

    def set_snap_mode(self, m):
        self._snap_mode = m

    def get_snap_mode(self):
        return self._snap_mode

    def set_srp_enabled(self, e):
        self._srp_enabled = e
        self._marker_manager.set_srp_enabled(e)

    def set_srna_enabled(self, e):
        """Ativa/desativa SRnA (Snap Relativo a Nada) - movimento independente."""
        self._marker_manager.set_srna_enabled(e)

    def set_persistent_zoom(self, e):
        self._keep_zoom_on_alias_changes = e

    def set_normalize_enabled(self, enabled: bool):
        """Ativa ou desativa a normalização de amplitude da waveform."""
        self._normalize_enabled = enabled

    def set_sector_playback_enabled(self, enabled: bool):
        """Ativa ou desativa o modo de reprodução por setor ao clicar."""
        self._sector_playback_enabled = enabled

    def set_smooth_scroll_enabled(self, enabled: bool):
        """Ativa ou desativa o deslizamento suave durante a reprodução."""
        self._smooth_scroll_enabled = enabled

    def set_wave_colors(self, pen, bg=None):
        self._plot.set_wave_pen(pg.mkPen(pen, width=1))

    def get_current_wav_path(self):
        return self._last_wav_path

    def clear(self):
        self._plot.set_curve_data([], [])
        self._spectrogram_widget.clear()
        self._marker_manager.clear_markers()
        self._wave_times = None
        self._wave_data = None
        self._minimap_widget.update_minimap()

    def zoom_in(self):
        self._apply_zoom_horizontal(0.8)

    def zoom_out(self):
        self._apply_zoom_horizontal(1.25)

    def reset_zoom(self):
        self._plot.setXRange(0, self._audio_dur, padding=0)
        self._plot.setYRange(-1.05, 1.05, padding=0)
        
        # Atualizar minimap
        if self._show_minimap:
            self._minimap_widget.set_visible_region(0, self._audio_dur)

    def set_key_handler(self, cb):
        pass

    def get_keep_zoom_on_alias_changes(self) -> bool:
        return self._keep_zoom_on_alias_changes

    def set_marker_keys(self, mapping: dict):
        """
        Define o mapeamento de teclas para marcadores OTO.
        
        Args:
            mapping: Dict de {nome_param: Qt.Key}, ex: {"offset": Qt.Key_F1, ...}
        """
        # Converte de {param: key} para {key: param}
        self._marker_keys = {key: param for param, key in mapping.items()}
    
    def get_marker_keys(self) -> dict:
        """
        Retorna o mapeamento atual de teclas para marcadores.
        
        Returns:
            Dict de {nome_param: Qt.Key}
        """
        # Converte de {key: param} para {param: key}
        return {param: key for key, param in self._marker_keys.items()}

    def cleanup(self):
        """Limpa recursos e para threads."""
        if hasattr(self, '_spectrogram_widget'):
            self._spectrogram_widget.cleanup()
=======
# waveform_widget.py

from __future__ import annotations
import time
from pathlib import Path
from collections import OrderedDict
import numpy as np
import pyqtgraph as pg
from PySide6.QtCore import Qt, Signal, QTimer, QEvent
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QSizePolicy, QSplitter
from PySide6.QtGui import QColor

from minimap_widget import MiniMapWidget
from audio_loader import load_waveform_sync, FullAudioLoaderWorker
from waveform_plot import WaveformPlotWidget
from marker_manager import MarkerManager
from spectrogram_widget import SpectrogramWidget
from copaiba import OtoEntry

# Tenta importar widget OpenGL acelerado
try:
    from spectrogram_gl_widget import SpectrogramGLWidget
    OPENGL_SPECTROGRAM_AVAILABLE = True
except ImportError:
    OPENGL_SPECTROGRAM_AVAILABLE = False

try:
    from backend_gpu import gpu_enabled

    GPU_BACKEND_AVAILABLE = True
except ImportError:
    GPU_BACKEND_AVAILABLE = False


    def gpu_enabled():
        return False


class WaveformWidget(QWidget):
    aliasStepRequested = Signal(int)
    playSegmentRequested = Signal(float, float)

    # Mapeamento padrão de teclas (pode ser personalizado)
    DEFAULT_MARKER_KEYS = {
        Qt.Key_Q: "offset",
        Qt.Key_W: "overlap",
        Qt.Key_E: "preutter",
        Qt.Key_R: "consonant",
        Qt.Key_T: "cutoff",
    }

    def __init__(self, parent=None):
        super().__init__(parent)

        # Estados Iniciais
        self._show_minimap = True
        self._show_spectrogram = True
        self._current_row = -1
        self._current_entry = None
        self._current_path = None
        self._last_mouse_t = 0.0
        self._active_marker_key = None
        self._snap_enabled = False
        self._snap_mode = "peaks"
        self._keep_zoom_on_alias_changes = True
        self._srp_enabled = False
        self._edit_callback = None
        self._audio_dur = 0.0
        self._normalize_enabled = True  # Normalização de amplitude
        self._sector_playback_enabled = False  # Modo de reprodução por setor
        self._smooth_scroll_enabled = True  # Deslizamento suave na reprodução
        self._saved_zoom_width = None  # Largura do zoom persistente
        self._is_loading_waveform = False  # Flag para bloquear update de zoom durante carregamento
        
        # Mapeamento de teclas personalizável (cópia do padrão)
        self._marker_keys = dict(self.DEFAULT_MARKER_KEYS)


        # Widgets
        self._minimap_widget = MiniMapWidget(self)
        self._plot = WaveformPlotWidget(self)

        # --- Configuração de Interação ---
        # --- Configuração de Interação ---
        # Sobrescreve wheelEvent diretamente para garantir captura
        self._plot.wheelEvent = self._on_plot_wheel_event
        
        self._plot.plotItem.setMouseEnabled(x=False, y=False)
        self._plot.plotItem.vb.disableAutoRange()
        self._plot.plotItem.setMenuEnabled(False)

        # Usa widget OpenGL se disponível, senão fallback para Matplotlib
        if OPENGL_SPECTROGRAM_AVAILABLE:
            self._spectrogram_widget = SpectrogramGLWidget(self)
        else:
            self._spectrogram_widget = SpectrogramWidget(self)
        if self._show_spectrogram:
            self._spectrogram_widget.show()
        else:
            self._spectrogram_widget.hide()
        self._spectrogram_widget.mouseMoved.connect(self._on_spectrogram_mouse_moved)

        # Sincronização com espectrograma via _on_plot_x_range_changed
        # (Matplotlib não suporta setXLink, então fazemos sync manual)

        # Splitter para redimensionar waveform/minimap
        # (Espectrograma fica FORA do splitter — QOpenGLWidget causa
        #  access violation quando colocado dentro de QSplitter)
        self._splitter = QSplitter(Qt.Vertical)
        self._splitter.setHandleWidth(4)
        self._splitter.setStyleSheet("""
            QSplitter::handle {
                background: #444;
            }
            QSplitter::handle:hover {
                background: #666;
            }
        """)
        self._splitter.addWidget(self._plot)
        self._splitter.addWidget(self._minimap_widget)

        # Proporção inicial [Waveform, Minimap]
        self._splitter.setSizes([350, 50])
        
        # Bloqueia colapsos indesejados
        self._splitter.setCollapsible(0, False) # Waveform deve ser visível
        self._splitter.setCollapsible(1, False) # Minimap deve ser visível

        # Layout Final
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(1)
        layout.addWidget(self._splitter, 3)
        layout.addWidget(self._spectrogram_widget, 2)

        self._label = QLabel("Nenhum arquivo carregado", self)
        self._label.setStyleSheet("color: #888; padding: 5px;")
        layout.addWidget(self._label)

        # Foco
        self.setFocusPolicy(Qt.StrongFocus)
        self._plot.setFocusPolicy(Qt.ClickFocus)

        # Dados
        self._wave_times = None
        self._wave_data = None
        self._last_wav_path = None

    # Playback Visual
        self._playhead = pg.InfiniteLine(pos=0, angle=90, pen=pg.mkPen('#FFD700', width=2))
        self._playhead.setZValue(9999)
        self._plot.addItem(self._playhead)
        self._playhead.hide()

        self._playback_timer = QTimer(self)
        self._playback_timer.setInterval(15)
        self._playback_timer.timeout.connect(self._update_playhead)

        # Worker de carregamento asíncrono
        self._audio_worker = None

        # Managers
        self._marker_manager = MarkerManager(self._plot)
        self._marker_manager.set_secondary_plot(self._spectrogram_widget)
        self._spectrogram_widget.markerMoved.connect(self._on_spectrogram_marker_moved)
        if hasattr(self._spectrogram_widget, 'markerDragFinished'):
            self._spectrogram_widget.markerDragFinished.connect(
                lambda: self._marker_manager.commit_marker_drag()
            )
        self._marker_manager.set_edit_callback(self._entry_edited_from_markers)

        # Configurações do Plot
        self._plot.showGrid(x=True, y=True, alpha=0.15) # Grid sutil
        self._plot.scene().sigMouseMoved.connect(self._on_plot_mouse_moved)
        self._plot.scene().sigMouseClicked.connect(self._on_mouse_clicked)
        
        # Monkey patch para suportar drag sem tecla pressionada
        # Injeta handlers de mousePress e mouseRelease no PlotWidget
        self._orig_mouse_press = self._plot.mousePressEvent
        self._orig_mouse_release = self._plot.mouseReleaseEvent
        
        def patched_mouse_press(event):
            self._on_mouse_pressed(event)
            self._orig_mouse_press(event)
            
        def patched_mouse_release(event):
            self._on_mouse_released(event)
            self._orig_mouse_release(event)
            
        self._plot.mousePressEvent = patched_mouse_press
        self._plot.mouseReleaseEvent = patched_mouse_release

        # Sincroniza zoom X
        self._plot.sigRangeChanged.connect(self._update_views_sync)

    # --- Event Filter: Zoom e Navegação ---
    # --- Interação: Zoom e Navegação Direta ---
    def _on_plot_wheel_event(self, event):
        """Manipula eventos de roda do mouse diretamente no plot."""
        modifiers = event.modifiers()
        delta = event.angleDelta().y()

        if delta == 0:
            return

        # CTRL + Roda: Zoom Horizontal
        if modifiers & Qt.ControlModifier:
            factor = 0.8 if delta > 0 else 1.25
            self._apply_zoom_horizontal(factor)
            event.accept()

        # ALT + Roda: Zoom Vertical
        elif modifiers & Qt.AltModifier:
            factor = 0.8 if delta > 0 else 1.25
            self._apply_zoom_vertical(factor)
            event.accept()
        
        # SHIFT + Roda: Pan Horizontal
        elif modifiers & Qt.ShiftModifier:
            self._apply_pan_horizontal(delta)
            event.accept()

        # Apenas Roda: Trocar Alias
        else:
            if delta > 0:
                self.aliasStepRequested.emit(-1)
            elif delta < 0:
                self.aliasStepRequested.emit(1)
            event.accept()

    def _apply_zoom_horizontal(self, factor):
        if self._audio_dur <= 0: return

        try:
            (x1, x2), _ = self._plot.viewRange()
        except:
            return

        current_width = x2 - x1
        new_width = current_width * factor

        center = (x1 + x2) / 2.0
        new_x1 = center - new_width / 2.0
        new_x2 = center + new_width / 2.0

        min_range = 0.001
        if new_x2 - new_x1 < min_range:
            new_x1 = center - min_range / 2.0
            new_x2 = center + min_range / 2.0

        if new_x1 < 0:
            new_x1 = 0
            new_x2 = min(new_width, self._audio_dur)
        if new_x2 > self._audio_dur:
            new_x2 = self._audio_dur
            new_x1 = max(0, self._audio_dur - new_width)

        self._plot.setXRange(new_x1, new_x2, padding=0)
        
        if not self._is_loading_waveform:
            self._saved_zoom_width = new_x2 - new_x1

    def _apply_zoom_vertical(self, factor):
        """Aplica zoom vertical (ganho visual) na Waveform."""
        if self._audio_dur <= 0: return
        
        try:
            _, (y1, y2) = self._plot.viewRange()
        except:
            return
            
        current_height = y2 - y1
        if current_height <= 0: current_height = 2.0
        new_height = current_height * factor
        
        # Limites Vertical (ganho visual)
        if new_height > 20.0: new_height = 20.0
        if new_height < 0.01: new_height = 0.01
        
        # Centraliza em zero para waveforms espelhadas
        new_y1 = -new_height / 2
        new_y2 = new_height / 2
        
        self._plot.setYRange(new_y1, new_y2, padding=0)

    def _apply_pan_horizontal(self, delta):
        """Pan horizontal com SHIFT+Scroll"""
        if self._audio_dur <= 0: return

        try:
            (x1, x2), _ = self._plot.viewRange()
        except:
            return

        current_width = x2 - x1
        if current_width <= 0: return

        # Pan 10% da largura visível por "scroll"
        pan_amount = current_width * 0.1
        
        if delta > 0:
            # Scroll up = mover para esquerda
            new_x1 = x1 - pan_amount
            new_x2 = x2 - pan_amount
        else:
            # Scroll down = mover para direita
            new_x1 = x1 + pan_amount
            new_x2 = x2 + pan_amount
        
        # Limitar aos bounds
        if new_x1 < 0:
            new_x1 = 0
            new_x2 = current_width
        if new_x2 > self._audio_dur:
            new_x2 = self._audio_dur
            new_x1 = max(0, self._audio_dur - current_width)

        self._plot.setXRange(new_x1, new_x2, padding=0)
        
        # Atualizar minimapa
        if self._show_minimap:
            self._minimap_widget.set_visible_region(new_x1, new_x2)

    # --- Lógica Principal ---

    def show_waveform(self, path: Path, entry: OtoEntry, row: int, reset_zoom: bool = True):
        # 1. Limpeza de estado anterior
        self._is_loading_waveform = True
        self._current_path = path
        self._last_wav_path = path
        self._current_entry = entry
        self._current_row = row
        self._reset_zoom_next = reset_zoom

        # Cancela carregamento anterior se houver
        if self._audio_worker and self._audio_worker.isRunning():
            self._audio_worker.finished.disconnect()
            self._audio_worker.error.disconnect()
            self._audio_worker.quit()
            self._audio_worker.wait(500)

        # Inicia novo carregamento em segundo plano
        self._audio_worker = FullAudioLoaderWorker(path, normalize=self._normalize_enabled)
        self._audio_worker.finished.connect(self._on_audio_loaded)
        self._audio_worker.error.connect(lambda e: self._label.setText(f"Erro: {e}"))
        self._audio_worker.start()

        self._label.setText(f"Carregando {path.name}...")

    def _on_audio_loaded(self, result: dict):
        """Callback após carregamento em segundo plano."""
        # Extrai dados do resultado
        path = result["path"]
        data_full = result["full_data"]
        t_plot = result["times"]
        v_plot = result["values"]
        sr = result["sample_rate"]
        duration = result["duration"]
        
        self._audio_dur = duration
        self._wave_times = t_plot
        self._wave_data = v_plot

        # Define limites seguros no ViewBox
        safe_max_x = max(duration, 0.01)
        # padding extra no X para permitir scroll confortável até o final
        self._plot.getViewBox().setLimits(
            xMin=0, 
            xMax=safe_max_x,
            yMin=-10.0, 
            yMax=10.0
        )

        # Atualiza curvas
        self._plot.set_curve_data(t_plot, v_plot)

        # Gerenciamento de ZOOM
        (x1, x2), _ = self._plot.viewRange()
        
        if getattr(self, '_reset_zoom_next', True) or self._saved_zoom_width is None:
            new_x1, new_x2 = 0, safe_max_x
        else:
            # Zoom persistente: centraliza na preutterance
            target_w = min(self._saved_zoom_width, safe_max_x)
            offset_s = (self._current_entry.offset if self._current_entry else 0) / 1000.0
            pre_s = (self._current_entry.preutter if self._current_entry else 0) / 1000.0
            center = offset_s + pre_s
            
            new_x1 = max(0, center - target_w / 2)
            new_x2 = min(safe_max_x, new_x1 + target_w)
            if new_x2 == safe_max_x:
                new_x1 = max(0, safe_max_x - target_w)

        self._plot.setXRange(new_x1, new_x2, padding=0)
        self._plot.setYRange(-1.05, 1.05, padding=0)

        # Atualiza Marcadores
        self._marker_manager.set_current_entry(self._current_entry, self._current_row)
        self._marker_manager.set_audio_duration(duration * 1000)
        self._marker_manager.update_markers_from_entry(audio_duration_s=duration)

        # Atualiza Espectrograma
        if self._show_spectrogram:
            self._spectrogram_widget.set_audio_data(data_full, sr, duration, wav_path=str(path))
            self._spectrogram_widget.set_x_range(new_x1, new_x2)

        # Atualiza Minimap
        if self._show_minimap:
            self._minimap_widget.update_minimap()
            self._minimap_widget.set_visible_region(new_x1, new_x2)

        self._label.setText(f"{path.name} : {self._current_entry.alias if self._current_entry else ''}")
        self._is_loading_waveform = False
        self.setFocus()

    def _update_views_sync(self):
        """Sincroniza o range do espectrograma com a waveform."""
        try:
            (x1, x2), _ = self._plot.viewRange()

            if self._spectrogram_widget.isVisible():
                self._spectrogram_widget.set_x_range(x1, x2)
            
            self._minimap_widget.set_visible_region(x1, x2)
        except:
            pass


    def _on_plot_x_range_changed(self):
        self._update_views_sync()

    def _on_plot_mouse_moved(self, pos):
        vb = self._plot.getViewBox()
        if vb is None: return
        p = vb.mapSceneToView(pos)
        self._process_mouse_move(p.x())

    # --- NOVO: Lógica de Arraste de Marcador via Mouse ---
    def _on_mouse_pressed(self, event):
        if event.button() == Qt.LeftButton:
            # 0. Prioridade: Alt + Clique (Tocar do tempo do clique até o final)
            if event.modifiers() & Qt.AltModifier:
                pos = event.pos() 
                scene_pos = self._plot.mapToScene(pos)
                vb = self._plot.plotItem.vb
                mouse_point = vb.mapSceneToView(scene_pos)
                time_start_s = mouse_point.x()
                
                # Obter tempo de cutoff visual
                markers = self._marker_manager.get_marker_positions()
                cutoff_s = markers.get('cutoff', self._audio_dur)
                
                if time_start_s < cutoff_s:
                    self.playSegmentRequested.emit(time_start_s * 1000, cutoff_s * 1000)
                    self.start_playback_visualization(time_start_s, cutoff_s)
                event.accept()
                return

             # 1. Prioridade: Arraste de Marcador (Mouse Only)
            if self._active_marker_key is None:
                pos = event.pos() 
                scene_pos = self._plot.mapToScene(pos)
                vb = self._plot.plotItem.vb
                mouse_point = vb.mapSceneToView(scene_pos)
                time_s = mouse_point.x()
                
                # Procura marcador próximo
                markers = self._marker_manager.get_marker_positions()
                if not markers: return

                # Tolerância visual
                pixel_tolerance = 10 
                view_range = vb.viewRange()[0]
                view_width_s = view_range[1] - view_range[0]
                pixel_width = max(1, self._plot.width())
                threshold_s = (pixel_tolerance / pixel_width) * view_width_s
                
                best_marker = None
                min_dist = float('inf')
                
                priority_order = ["preutter", "overlap", "offset", "cutoff", "consonant"]
                
                for name in priority_order:
                    if name in markers:
                        pos_s = markers[name]
                        dist = abs(pos_s - time_s)
                        if dist < threshold_s and dist < min_dist:
                            min_dist = dist
                            best_marker = name
                
                if best_marker:
                    self._active_marker_key = best_marker 
                    self._dragging_marker_mouse = True
                    self.set_marker_at_mouse(self._active_marker_key)
                    # NÃO executamos event.accept() aqui para permitir que o pyqtgraph processe o clique
                    return

    def _on_mouse_released(self, event):
        if event.button() == Qt.LeftButton:
            if hasattr(self, '_dragging_marker_mouse') and self._dragging_marker_mouse:
                self._dragging_marker_mouse = False
                self._active_marker_key = None
                self._marker_manager.commit_marker_drag()
                # Marca timestamp do último drag para inibir clique acidental
                self._last_drag_time = time.time()

    def _on_mouse_clicked(self, event):
        # Verifica se acabamos de soltar um drag (evita tocar logo após arrastar)
        if hasattr(self, '_last_drag_time') and (time.time() - self._last_drag_time) < 0.2:
            return

        # Verifica se foi clique esquerdo e se não estamos arrastando um marcador (via teclado)
        if event.button() == Qt.LeftButton and self._active_marker_key is None:
            if self._sector_playback_enabled:
                self._play_sector_at_mouse()
            else:
                self._play_main_segment()
            event.accept()

    def _on_spectrogram_mouse_moved(self, t_seconds):
        self._process_mouse_move(t_seconds)

    def cleanup(self):
        """Finaliza recursos e threads ativos."""
        if hasattr(self, '_spectrogram_widget') and self._spectrogram_widget:
            # Chama closeEvent manualmente para disparar cancelamento de threads
            self._spectrogram_widget.close()
            
        if self._playback_timer.isActive():
            self._playback_timer.stop()
            
    def _on_spectrogram_marker_moved(self, name: str, time_s: float):
        """Callback quando um marcador é arrastado no espectrograma."""
        self._marker_manager.set_marker_at_mouse(
            name=name,
            mouse_time_s=time_s,
            snap_enabled=self._snap_enabled,
            snap_mode=self._snap_mode,
            wave_times=self._wave_times,
            wave_data=self._wave_data if self._snap_enabled else None
        )

    def _process_mouse_move(self, time_s):
        self._last_mouse_t = float(max(0.0, time_s))
        self._plot.set_cursor_position(self._last_mouse_t)

        if self._active_marker_key and self._current_entry:
            self.set_marker_at_mouse(self._active_marker_key)

    def set_marker_at_mouse(self, marker_name):
        self._marker_manager.set_marker_at_mouse(
            marker_name, self._last_mouse_t, self._snap_enabled,
            self._snap_mode, self._wave_times, self._wave_data,
            srp_enabled=self._srp_enabled
        )

    def keyPressEvent(self, event):
        if event.isAutoRepeat(): return
        key = event.key()

        if key in self._marker_keys:
            self._active_marker_key = self._marker_keys[key]
            self.set_marker_at_mouse(self._active_marker_key)
            event.accept()
            return

        if key == Qt.Key_Space:
            self._play_main_segment()
            event.accept()
            return

        if key == Qt.Key_Up:
            self.aliasStepRequested.emit(-1)
            event.accept()
            return
        elif key == Qt.Key_Down:
            self.aliasStepRequested.emit(1)
            event.accept()
            return

        super().keyPressEvent(event)

    def keyReleaseEvent(self, event):
        if event.isAutoRepeat(): return
        if event.key() in self._marker_keys:
            if self._marker_keys[event.key()] == self._active_marker_key:
                self._active_marker_key = None
                # Commit: envia valor final para tabela (1 undo state por arraste)
                self._marker_manager.commit_marker_drag()
        super().keyReleaseEvent(event)

    def _play_main_segment(self):
        start, end = self.get_segment_times_ms()
        self.playSegmentRequested.emit(start, end)
        self.start_playback_visualization(start / 1000.0, end / 1000.0)

    def _play_sector_at_mouse(self):
        """Toca o setor OTO onde o mouse está posicionado."""
        if not self._current_entry or self._audio_dur <= 0:
            return
        
        mouse_ms = self._last_mouse_t * 1000.0
        total_ms = self._audio_dur * 1000.0
        
        # Parâmetros OTO em ms
        offset = float(self._current_entry.offset)
        overlap = float(self._current_entry.overlap)
        preutter = float(self._current_entry.preutter)
        consonant = float(self._current_entry.consonant)
        cutoff = float(self._current_entry.cutoff)
        
        # Calcular posições absolutas em ms
        overlap_pos = offset + overlap
        preutter_pos = offset + preutter
        consonant_pos = offset + consonant
        
        # Cutoff: se negativo, é relativo ao offset; se positivo, ao final do arquivo
        if cutoff < 0:
            cutoff_pos = offset - cutoff  # offset - (-400) = offset + 400
        else:
            cutoff_pos = total_ms - cutoff
        
        # Identificar setor clicado e definir início/fim
        start, end = 0, 0
        
        if mouse_ms < offset:
            # Setor 1: Pré-offset (silêncio inicial)
            start, end = 0, offset
        elif mouse_ms < overlap_pos:
            # Setor 2: Offset → Overlap
            start, end = offset, overlap_pos
        elif mouse_ms < preutter_pos:
            # Setor 3: Overlap → Preutter
            start, end = overlap_pos, preutter_pos
        elif mouse_ms < consonant_pos:
            # Setor 4: Preutter → Consonant
            start, end = preutter_pos, consonant_pos
        elif mouse_ms < cutoff_pos:
            # Setor 5: Consonant → Cutoff (vogal sustentada)
            start, end = consonant_pos, cutoff_pos
        else:
            # Setor 6: Pós-Cutoff
            start, end = cutoff_pos, total_ms
        
        # Garantir que valores são válidos
        start = max(0, start)
        end = min(total_ms, end)
        if end <= start:
            end = start + 50  # Mínimo de 50ms se o setor for muito pequeno
        
        # Emite sinal para tocar o setor e visualiza
        self.playSegmentRequested.emit(start, end)
        self.start_playback_visualization(start / 1000.0, end / 1000.0)


    def get_segment_times_ms(self):
        if not self._current_entry or self._audio_dur <= 0: return 0, 0

        total_ms = self._audio_dur * 1000.0
        off = float(self._current_entry.offset)
        cut = float(self._current_entry.cutoff)

        start = max(0.0, off)

        # Cutoff negativo: distância a partir do offset (ex: -400 = offset + 400ms)
        # Cutoff positivo: distância a partir do final do arquivo (ex: 400 = total - 400ms)
        if cut < 0:
            end = off - cut  # off - (-400) = off + 400
        else:
            end = total_ms - cut  # Cutoff positivo = distância do final

        end = min(total_ms, end)
        if end <= start:
            end = min(total_ms, start + 100)

        return start, end

    def start_playback_visualization(self, s, e):
        self._playback_start_t = s
        self._playback_end_t = e
        self._playback_wall_start = time.perf_counter()
        self._playhead.show()
        self._playback_timer.start()

    def _update_playhead(self):
        now = time.perf_counter()
        pos = self._playback_start_t + (now - self._playback_wall_start)
        self._playhead.setValue(pos)
        
        # --- Deslizamento Suave (Smooth Scrolling) ---
        if getattr(self, '_smooth_scroll_enabled', True):
            try:
                (x1, x2), _ = self._plot.viewRange()
                view_width = x2 - x1
                # Empurra a view se o playhead cruzar 75% da tela visível
                threshold = x1 + (view_width * 0.75)
                if pos > threshold:
                    shift = pos - threshold
                    new_x1 = x1 + shift
                    new_x2 = x2 + shift
                    
                    # Limita para não rolar infinitamente além do áudio
                    if new_x1 <= self._audio_dur:
                        self._plot.setXRange(new_x1, new_x2, padding=0)
                        self._update_views_sync()  # Sincroniza o minimap e espectrograma
            except Exception:
                pass
        # ---------------------------------------------
        
        # Atualizar cursor no minimapa
        if self._show_minimap:
            self._minimap_widget.set_cursor_position(pos)
        
        if pos >= self._playback_end_t:
            self._playback_timer.stop()
            self._playhead.hide()
            if self._show_minimap:
                self._minimap_widget.hide_cursor()

    def stop_playback_visualization(self):
        self._playback_timer.stop()
        self._playhead.hide()
        if self._show_minimap:
            self._minimap_widget.hide_cursor()

    def _entry_edited_from_markers(self, row, entry):
        self._current_entry = entry
        if self._edit_callback: self._edit_callback(row, entry)

    def set_show_minimap(self, show):
        self._show_minimap = show
        if show:
            self._minimap_widget.show()
            self._minimap_widget.update_minimap()
        else:
            self._minimap_widget.hide()

    def set_show_spectrogram(self, show):
        self._show_spectrogram = show
        if show:
            self._spectrogram_widget.show()
            # Recarrega dados via async loader se tiver áudio carregado
            if self._last_wav_path and self._audio_dur > 0:
                self.show_waveform(
                    self._last_wav_path, 
                    self._current_entry, 
                    self._current_row, 
                    reset_zoom=False
                )
        else:
            self._spectrogram_widget.hide()

    def set_edit_callback(self, cb):
        self._edit_callback = cb

    def set_snap_enabled(self, e):
        self._snap_enabled = e

    def set_snap_mode(self, m):
        self._snap_mode = m

    def get_snap_mode(self):
        return self._snap_mode

    def set_srp_enabled(self, e):
        self._srp_enabled = e
        self._marker_manager.set_srp_enabled(e)

    def set_srna_enabled(self, e):
        """Ativa/desativa SRnA (Snap Relativo a Nada) - movimento independente."""
        self._marker_manager.set_srna_enabled(e)

    def set_persistent_zoom(self, e):
        self._keep_zoom_on_alias_changes = e

    def set_normalize_enabled(self, enabled: bool):
        """Ativa ou desativa a normalização de amplitude da waveform."""
        self._normalize_enabled = enabled

    def set_sector_playback_enabled(self, enabled: bool):
        """Ativa ou desativa o modo de reprodução por setor ao clicar."""
        self._sector_playback_enabled = enabled

    def set_smooth_scroll_enabled(self, enabled: bool):
        """Ativa ou desativa o deslizamento suave durante a reprodução."""
        self._smooth_scroll_enabled = enabled

    def set_wave_colors(self, pen, bg=None):
        self._plot.set_wave_pen(pg.mkPen(pen, width=1))

    def get_current_wav_path(self):
        return self._last_wav_path

    def clear(self):
        self._plot.set_curve_data([], [])
        self._spectrogram_widget.clear()
        self._marker_manager.clear_markers()
        self._wave_times = None
        self._wave_data = None
        self._minimap_widget.update_minimap()

    def zoom_in(self):
        self._apply_zoom_horizontal(0.8)

    def zoom_out(self):
        self._apply_zoom_horizontal(1.25)

    def reset_zoom(self):
        self._plot.setXRange(0, self._audio_dur, padding=0)
        self._plot.setYRange(-1.05, 1.05, padding=0)
        
        # Atualizar minimap
        if self._show_minimap:
            self._minimap_widget.set_visible_region(0, self._audio_dur)

    def set_key_handler(self, cb):
        pass

    def get_keep_zoom_on_alias_changes(self) -> bool:
        return self._keep_zoom_on_alias_changes

    def set_marker_keys(self, mapping: dict):
        """
        Define o mapeamento de teclas para marcadores OTO.
        
        Args:
            mapping: Dict de {nome_param: Qt.Key}, ex: {"offset": Qt.Key_F1, ...}
        """
        # Converte de {param: key} para {key: param}
        self._marker_keys = {key: param for param, key in mapping.items()}
    
    def get_marker_keys(self) -> dict:
        """
        Retorna o mapeamento atual de teclas para marcadores.
        
        Returns:
            Dict de {nome_param: Qt.Key}
        """
        # Converte de {key: param} para {param: key}
        return {param: key for key, param in self._marker_keys.items()}

    def cleanup(self):
        """Limpa recursos e para threads."""
        # Para o worker de áudio
        if self._audio_worker and self._audio_worker.isRunning():
            self._audio_worker.quit()
            self._audio_worker.wait(500)
        if hasattr(self, '_spectrogram_widget'):
            self._spectrogram_widget.cleanup()
>>>>>>> Stashed changes
