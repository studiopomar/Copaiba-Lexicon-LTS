<<<<<<< Updated upstream
# minimap_widget.py
"""
MiniMap Widget - Visualização miniatura da waveform completa com navegação interativa.

Funcionalidades:
- Mostra a waveform completa em miniatura
- Região destacada mostra a área visível no plot principal
- Arrastar a região navega no plot principal
- Clicar fora da região centraliza naquele ponto
- Acompanha o zoom feito na waveform principal
- Acompanha a reprodução do áudio (playhead)
- Scroll para zoom, Shift+Scroll para pan
"""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
import pyqtgraph as pg
import numpy as np


class MiniMapWidget(QWidget):
    """Widget miniatura da waveform com navegação interativa."""

    # Sinal emitido quando o usuário navega pelo minimap
    navigationRequested = Signal(float, float)

    def __init__(self, parent_waveform):
        super().__init__()
        self.parent_waveform = parent_waveform
        
        # Configuração de tamanho
        self.setFixedHeight(55)
        self.setMinimumHeight(40)
        self.setMaximumHeight(100)

        # Cores
        self._bg_color = QColor(20, 20, 24)
        self._wave_color = QColor(80, 160, 220)
        self._wave_fill_color = QColor(80, 160, 220, 50)
        self._region_color = QColor(255, 255, 255, 30)
        self._region_border_color = QColor(100, 200, 255, 180)
        self._shade_color = QColor(0, 0, 0, 120)
        self._playhead_color = QColor(255, 215, 0)  # Dourado

        # Estados
        self._audio_duration = 0.0
        self._is_ready = False
        self._updating_from_parent = False

        # Cria o plot
        self._plot = pg.PlotWidget(self)
        self._plot.setMenuEnabled(False)
        self._plot.showGrid(x=False, y=False)
        self._plot.setMouseEnabled(x=False, y=False)
        self._plot.setBackground(self._bg_color)
        self._plot.hideAxis('left')
        self._plot.hideAxis('bottom')
        self._plot.setDownsampling(auto=True, mode='peak')
        self._plot.setClipToView(True)
        self._plot.getViewBox().setDefaultPadding(0)

        # Sombra esquerda (área fora da visualização)
        self._left_shade = pg.LinearRegionItem(
            values=[0, 0],
            orientation='vertical',
            brush=pg.mkBrush(self._shade_color),
            pen=pg.mkPen(None),
            movable=False
        )
        self._left_shade.setZValue(5)
        self._plot.addItem(self._left_shade)

        # Sombra direita
        self._right_shade = pg.LinearRegionItem(
            values=[0, 0],
            orientation='vertical',
            brush=pg.mkBrush(self._shade_color),
            pen=pg.mkPen(None),
            movable=False
        )
        self._right_shade.setZValue(5)
        self._plot.addItem(self._right_shade)

        # Região visível (navegável)
        self._view_region = pg.LinearRegionItem(
            values=[0, 1],
            orientation='vertical',
            brush=pg.mkBrush(self._region_color),
            pen=pg.mkPen(self._region_border_color, width=2),
            movable=True,
            swapMode='none'
        )
        self._view_region.setZValue(10)
        self._plot.addItem(self._view_region)
        
        # Conecta eventos da região
        self._view_region.sigRegionChanged.connect(self._on_region_dragged)
        self._view_region.sigRegionChangeFinished.connect(self._on_region_finished)

        # Playhead (cursor de reprodução)
        self._playhead = pg.InfiniteLine(
            angle=90, movable=False,
            pen=pg.mkPen(self._playhead_color, width=2)
        )
        self._playhead.setZValue(15)
        self._plot.addItem(self._playhead)
        self._playhead.hide()

        # Referências para curvas
        self._wave_curve = None
        self._fill_curve = None
        self._marker_lines = {}

        # Layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self._plot)

        # Tooltip
        self.setToolTip("Clique para navegar • Arraste a região • Scroll para zoom")
        self.setCursor(Qt.PointingHandCursor)

    def update_minimap(self):
        """Atualiza o minimap com os dados atuais da waveform."""
        # Obtém dados do parent
        times = self.parent_waveform._wave_times
        data = self.parent_waveform._wave_data
        duration = self.parent_waveform._audio_dur

        # Validação
        if times is None or data is None or len(times) == 0 or len(data) == 0:
            self._is_ready = False
            return

        if duration is None or duration <= 0:
            self._is_ready = False
            return

        self._audio_duration = float(duration)
        self._is_ready = True

        # Remove curvas anteriores
        if self._wave_curve is not None:
            try:
                self._plot.removeItem(self._wave_curve)
            except:
                pass
            self._wave_curve = None

        if self._fill_curve is not None:
            try:
                self._plot.removeItem(self._fill_curve)
            except:
                pass
            self._fill_curve = None

        # Downsample para performance
        max_points = 1500
        if len(times) > max_points:
            step = max(1, len(times) // max_points)
            times_ds = times[::step]
            data_ds = data[::step]
        else:
            times_ds = times
            data_ds = data

        # Limpa NaN e Inf
        valid_mask = np.isfinite(data_ds)
        if not np.all(valid_mask):
            times_ds = times_ds[valid_mask]
            data_ds = data_ds[valid_mask]

        if len(times_ds) == 0:
            self._is_ready = False
            return

        # Cria preenchimento
        self._fill_curve = pg.PlotCurveItem(
            times_ds, data_ds,
            pen=None,
            fillLevel=0,
            brush=pg.mkBrush(self._wave_fill_color)
        )
        self._fill_curve.setZValue(0)
        self._plot.addItem(self._fill_curve)

        # Cria curva principal
        self._wave_curve = self._plot.plot(
            times_ds, data_ds,
            pen=pg.mkPen(self._wave_color, width=1),
            antialias=True
        )
        self._wave_curve.setZValue(1)

        # Define ranges
        self._plot.setXRange(0, self._audio_duration, padding=0)
        
        max_amp = np.nanmax(np.abs(data_ds)) if len(data_ds) > 0 else 1.0
        if np.isfinite(max_amp) and max_amp > 0:
            self._plot.setYRange(-max_amp * 1.1, max_amp * 1.1, padding=0)
        else:
            self._plot.setYRange(-1, 1, padding=0)

        # Define limites da região navegável
        self._view_region.setBounds([0, self._audio_duration])

        # Atualiza estado visual
        self._sync_from_parent()
        self._update_markers()

    def _sync_from_parent(self):
        """Sincroniza a região visível com o plot principal."""
        if not self._is_ready:
            return

        try:
            (x1, x2), _ = self.parent_waveform._plot.viewRange()
        except:
            x1, x2 = 0, self._audio_duration

        # Garante valores válidos
        x1 = max(0, min(x1, self._audio_duration))
        x2 = max(0.001, min(x2, self._audio_duration))
        if x2 <= x1:
            x2 = self._audio_duration

        self._set_region_silent(x1, x2)
        self._update_shades(x1, x2)

    def _set_region_silent(self, x1, x2):
        """Define a região sem disparar callbacks."""
        self._updating_from_parent = True
        try:
            self._view_region.setRegion([x1, x2])
        except:
            pass
        finally:
            self._updating_from_parent = False

    def _update_shades(self, x1, x2):
        """Atualiza as áreas sombreadas fora da região visível."""
        try:
            self._left_shade.setRegion([0, x1])
            self._right_shade.setRegion([x2, self._audio_duration])
        except:
            pass

    def _on_region_dragged(self):
        """Chamado durante o arraste da região."""
        if self._updating_from_parent or not self._is_ready:
            return

        start, end = self._view_region.getRegion()
        
        # Limita aos bounds
        duration = self._audio_duration
        width = end - start
        
        if start < 0:
            start = 0
            end = min(width, duration)
        if end > duration:
            end = duration
            start = max(0, duration - width)

        # Atualiza sombras
        self._update_shades(start, end)
        
        # Navega no plot principal
        self._navigate_parent(start, end)

    def _on_region_finished(self):
        """Chamado ao terminar o arraste."""
        if self._updating_from_parent or not self._is_ready:
            return
        
        start, end = self._view_region.getRegion()
        self._navigate_parent(start, end)

    def _navigate_parent(self, x1, x2):
        """Navega o plot principal para o range especificado."""
        try:
            self.parent_waveform._plot.setXRange(x1, x2, padding=0)
        except:
            pass
        
        self.navigationRequested.emit(x1, x2)

    def set_visible_region(self, start_time, end_time):
        """Define a região visível (chamado pelo parent quando o zoom muda)."""
        if not self._is_ready:
            return

        start_time = max(0, min(start_time, self._audio_duration))
        end_time = max(0.001, min(end_time, self._audio_duration))

        self._set_region_silent(start_time, end_time)
        self._update_shades(start_time, end_time)

    def set_cursor_position(self, time_pos):
        """Define a posição do playhead (cursor de reprodução)."""
        if not self._is_ready:
            return

        if 0 <= time_pos <= self._audio_duration:
            self._playhead.setPos(time_pos)
            self._playhead.show()
        else:
            self._playhead.hide()

    def hide_cursor(self):
        """Esconde o playhead."""
        self._playhead.hide()

    def _update_markers(self):
        """Atualiza os marcadores no minimap usando a mesma lógica do MarkerManager."""
        # Remove marcadores antigos
        for line in self._marker_lines.values():
            try:
                self._plot.removeItem(line)
            except:
                pass
        self._marker_lines.clear()

        if self.parent_waveform._current_entry is None:
            return

        # Usa o MarkerManager para obter posições (garante consistência)
        try:
            marker_manager = self.parent_waveform._marker_manager
            positions = marker_manager.get_marker_positions()
        except:
            return

        # Cores dos marcadores - SINCRONIZADAS com MarkerManager.DEFAULT_STYLES
        colors = {
            "offset": "#4da6ff",      # Azul claro (mesma cor do MarkerManager)
            "overlap": "#00ff00",     # Verde (mesma cor do MarkerManager)
            "preutter": "#ff0000",    # Vermelho (mesma cor do MarkerManager)
            "consonant": "#ff69b4",   # Rosa hot pink (mesma cor do MarkerManager)
            "cutoff": "#4da6ff",      # Azul claro (mesma cor do MarkerManager)
        }

        for name, pos in positions.items():
            if 0 <= pos <= self._audio_duration:
                color = colors.get(name, "#FFCC00")
                line = pg.InfiniteLine(
                    pos=pos, angle=90, movable=False,
                    pen=pg.mkPen(color, width=1)
                )
                line.setZValue(3)
                self._plot.addItem(line)
                self._marker_lines[name] = line

    def mousePressEvent(self, event):
        """Clique para navegar."""
        if event.button() == Qt.LeftButton and self._is_ready:
            self._navigate_to_click(event.position())
        super().mousePressEvent(event)

    def _navigate_to_click(self, widget_pos):
        """Navega para a posição clicada."""
        if self._audio_duration <= 0:
            return

        # Converte posição do widget para tempo
        widget_width = self.width()
        if widget_width <= 0:
            return

        clicked_time = (widget_pos.x() / widget_width) * self._audio_duration
        clicked_time = max(0, min(clicked_time, self._audio_duration))

        # Verifica se clicou dentro da região atual
        current_start, current_end = self._view_region.getRegion()
        if current_start <= clicked_time <= current_end:
            # Clicou dentro, deixa arrastar
            return

        # Mantém a largura atual e centraliza no ponto clicado
        region_width = current_end - current_start
        new_start = clicked_time - region_width / 2
        new_end = clicked_time + region_width / 2

        # Ajusta aos limites
        if new_start < 0:
            new_start = 0
            new_end = min(region_width, self._audio_duration)
        if new_end > self._audio_duration:
            new_end = self._audio_duration
            new_start = max(0, self._audio_duration - region_width)

        self._set_region_silent(new_start, new_end)
        self._update_shades(new_start, new_end)
        self._navigate_parent(new_start, new_end)

    def wheelEvent(self, event):
        """Scroll para zoom/pan no minimap."""
        if not self._is_ready or self._audio_duration <= 0:
            event.ignore()
            return

        delta = event.angleDelta().y()
        if delta == 0:
            event.ignore()
            return

        start, end = self._view_region.getRegion()
        current_width = end - start
        if current_width <= 0:
            current_width = 0.01

        modifiers = event.modifiers()

        if modifiers & Qt.ShiftModifier:
            # SHIFT + Scroll = Pan horizontal
            pan_amount = current_width * 0.1
            if delta > 0:
                new_start = start - pan_amount
                new_end = end - pan_amount
            else:
                new_start = start + pan_amount
                new_end = end + pan_amount
        else:
            # Scroll normal = Zoom
            center = (start + end) / 2.0
            factor = 0.8 if delta > 0 else 1.25
            new_width = current_width * factor

            # Limites
            min_width = self._audio_duration / 100.0
            max_width = self._audio_duration
            new_width = max(min_width, min(new_width, max_width))

            new_start = center - new_width / 2
            new_end = center + new_width / 2

        # Ajusta aos bounds
        if new_start < 0:
            new_start = 0
            new_end = min(new_end - new_start, self._audio_duration)
        if new_end > self._audio_duration:
            new_end = self._audio_duration
            new_start = max(0, new_end - (end - start if modifiers & Qt.ShiftModifier else new_width))

        self._set_region_silent(new_start, new_end)
        self._update_shades(new_start, new_end)
        self._navigate_parent(new_start, new_end)

=======
# minimap_widget.py
"""
MiniMap Widget - Visualização miniatura da waveform completa com navegação interativa.

Funcionalidades:
- Mostra a waveform completa em miniatura
- Região destacada mostra a área visível no plot principal
- Arrastar a região navega no plot principal
- Clicar fora da região centraliza naquele ponto
- Acompanha o zoom feito na waveform principal
- Acompanha a reprodução do áudio (playhead)
- Scroll para zoom, Shift+Scroll para pan
"""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
import pyqtgraph as pg
import numpy as np


class MiniMapWidget(QWidget):
    """Widget miniatura da waveform com navegação interativa."""

    # Sinal emitido quando o usuário navega pelo minimap
    navigationRequested = Signal(float, float)

    def __init__(self, parent_waveform):
        super().__init__()
        self.parent_waveform = parent_waveform
        
        # Configuração de tamanho (permite redimensionar no splitter)
        self.setMinimumHeight(40)
        self.setMaximumHeight(150)

        # Cores
        self._bg_color = QColor(20, 20, 24)
        self._wave_color = QColor(80, 160, 220)
        self._wave_fill_color = QColor(80, 160, 220, 50)
        self._region_color = QColor(255, 255, 255, 30)
        self._region_border_color = QColor(100, 200, 255, 180)
        self._shade_color = QColor(0, 0, 0, 120)
        self._playhead_color = QColor(255, 215, 0)  # Dourado

        # Estados
        self._audio_duration = 0.0
        self._is_ready = False
        self._updating_from_parent = False

        # Cria o plot
        self._plot = pg.PlotWidget(self)
        self._plot.setMenuEnabled(False)
        self._plot.showGrid(x=False, y=False)
        self._plot.setMouseEnabled(x=False, y=False)
        self._plot.setBackground(self._bg_color)
        self._plot.hideAxis('left')
        self._plot.hideAxis('bottom')
        self._plot.setDownsampling(auto=True, mode='peak')
        self._plot.setClipToView(True)
        self._plot.getViewBox().setDefaultPadding(0)

        # Sombra esquerda (área fora da visualização)
        self._left_shade = pg.LinearRegionItem(
            values=[0, 0],
            orientation='vertical',
            brush=pg.mkBrush(self._shade_color),
            pen=pg.mkPen(None),
            movable=False
        )
        self._left_shade.setZValue(5)
        self._plot.addItem(self._left_shade)

        # Sombra direita
        self._right_shade = pg.LinearRegionItem(
            values=[0, 0],
            orientation='vertical',
            brush=pg.mkBrush(self._shade_color),
            pen=pg.mkPen(None),
            movable=False
        )
        self._right_shade.setZValue(5)
        self._plot.addItem(self._right_shade)

        # Região visível (navegável)
        self._view_region = pg.LinearRegionItem(
            values=[0, 1],
            orientation='vertical',
            brush=pg.mkBrush(self._region_color),
            pen=pg.mkPen(self._region_border_color, width=2),
            movable=True,
            swapMode='none'
        )
        self._view_region.setZValue(10)
        self._plot.addItem(self._view_region)
        
        # Conecta eventos da região
        self._view_region.sigRegionChanged.connect(self._on_region_dragged)
        self._view_region.sigRegionChangeFinished.connect(self._on_region_finished)

        # Playhead (cursor de reprodução)
        self._playhead = pg.InfiniteLine(
            angle=90, movable=False,
            pen=pg.mkPen(self._playhead_color, width=2)
        )
        self._playhead.setZValue(15)
        self._plot.addItem(self._playhead)
        self._playhead.hide()

        # Referências para curvas
        self._wave_curve = None
        self._fill_curve = None
        self._marker_lines = {}

        # Layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self._plot)

        # Tooltip
        self.setToolTip("Clique para navegar • Arraste a região • Scroll para zoom")
        self.setCursor(Qt.PointingHandCursor)

    def update_minimap(self):
        """Atualiza o minimap com os dados atuais da waveform."""
        # Obtém dados do parent
        times = self.parent_waveform._wave_times
        data = self.parent_waveform._wave_data
        duration = self.parent_waveform._audio_dur

        # Validação
        if times is None or data is None or len(times) == 0 or len(data) == 0:
            self._is_ready = False
            return

        if duration is None or duration <= 0:
            self._is_ready = False
            return

        self._audio_duration = float(duration)
        self._is_ready = True

        # Downsample para performance
        max_points = 1500
        if len(times) > max_points:
            step = max(1, len(times) // max_points)
            times_ds = times[::step]
            data_ds = data[::step]
        else:
            times_ds = times
            data_ds = data

        # Limpa NaN e Inf
        valid_mask = np.isfinite(data_ds)
        if not np.all(valid_mask):
            times_ds = times_ds[valid_mask]
            data_ds = data_ds[valid_mask]

        if len(times_ds) == 0:
            self._is_ready = False
            return

        # Reutiliza curvas existentes (performance: evita recriar objetos)
        if self._fill_curve is None:
            self._fill_curve = pg.PlotCurveItem(
                times_ds, data_ds,
                pen=None,
                fillLevel=0,
                brush=pg.mkBrush(self._wave_fill_color)
            )
            self._fill_curve.setZValue(0)
            self._plot.addItem(self._fill_curve)
        else:
            self._fill_curve.setData(times_ds, data_ds)

        if self._wave_curve is None:
            self._wave_curve = pg.PlotCurveItem(
                times_ds, data_ds,
                pen=pg.mkPen(self._wave_color, width=1),
            )
            self._wave_curve.setZValue(1)
            self._plot.addItem(self._wave_curve)
        else:
            self._wave_curve.setData(times_ds, data_ds)

        # Define ranges
        self._plot.setXRange(0, self._audio_duration, padding=0)
        
        max_amp = np.nanmax(np.abs(data_ds)) if len(data_ds) > 0 else 1.0
        if np.isfinite(max_amp) and max_amp > 0:
            self._plot.setYRange(-max_amp * 1.1, max_amp * 1.1, padding=0)
        else:
            self._plot.setYRange(-1, 1, padding=0)

        # Define limites da região navegável
        self._view_region.setBounds([0, self._audio_duration])

        # Atualiza estado visual
        self._sync_from_parent()
        self._update_markers()


    def _sync_from_parent(self):
        """Sincroniza a região visível com o plot principal."""
        if not self._is_ready:
            return

        try:
            (x1, x2), _ = self.parent_waveform._plot.viewRange()
        except:
            x1, x2 = 0, self._audio_duration

        # Garante valores válidos
        x1 = max(0, min(x1, self._audio_duration))
        x2 = max(0.001, min(x2, self._audio_duration))
        if x2 <= x1:
            x2 = self._audio_duration

        self._set_region_silent(x1, x2)
        self._update_shades(x1, x2)

    def _set_region_silent(self, x1, x2):
        """Define a região sem disparar callbacks."""
        self._updating_from_parent = True
        try:
            self._view_region.setRegion([x1, x2])
        except:
            pass
        finally:
            self._updating_from_parent = False

    def _update_shades(self, x1, x2):
        """Atualiza as áreas sombreadas fora da região visível."""
        try:
            self._left_shade.setRegion([0, x1])
            self._right_shade.setRegion([x2, self._audio_duration])
        except:
            pass

    def _on_region_dragged(self):
        """Chamado durante o arraste da região."""
        if self._updating_from_parent or not self._is_ready:
            return

        start, end = self._view_region.getRegion()
        
        # Limita aos bounds
        duration = self._audio_duration
        width = end - start
        
        if start < 0:
            start = 0
            end = min(width, duration)
        if end > duration:
            end = duration
            start = max(0, duration - width)

        # Atualiza sombras
        self._update_shades(start, end)
        
        # Navega no plot principal
        self._navigate_parent(start, end)

    def _on_region_finished(self):
        """Chamado ao terminar o arraste."""
        if self._updating_from_parent or not self._is_ready:
            return
        
        start, end = self._view_region.getRegion()
        self._navigate_parent(start, end)

    def _navigate_parent(self, x1, x2):
        """Navega o plot principal para o range especificado."""
        try:
            self.parent_waveform._plot.setXRange(x1, x2, padding=0)
        except:
            pass
        
        self.navigationRequested.emit(x1, x2)

    def set_visible_region(self, start_time, end_time):
        """Define a região visível (chamado pelo parent quando o zoom muda)."""
        if not self._is_ready:
            return

        start_time = max(0, min(start_time, self._audio_duration))
        end_time = max(0.001, min(end_time, self._audio_duration))

        self._set_region_silent(start_time, end_time)
        self._update_shades(start_time, end_time)

    def set_cursor_position(self, time_pos):
        """Define a posição do playhead (cursor de reprodução)."""
        if not self._is_ready:
            return

        if 0 <= time_pos <= self._audio_duration:
            self._playhead.setPos(time_pos)
            self._playhead.show()
        else:
            self._playhead.hide()

    def hide_cursor(self):
        """Esconde o playhead."""
        self._playhead.hide()

    def _update_markers(self):
        """Atualiza os marcadores no minimap usando a mesma lógica do MarkerManager."""
        # Remove marcadores antigos
        for line in self._marker_lines.values():
            try:
                self._plot.removeItem(line)
            except:
                pass
        self._marker_lines.clear()

        if self.parent_waveform._current_entry is None:
            return

        # Usa o MarkerManager para obter posições (garante consistência)
        try:
            marker_manager = self.parent_waveform._marker_manager
            positions = marker_manager.get_marker_positions()
        except:
            return

        # Cores dos marcadores - SINCRONIZADAS com MarkerManager.DEFAULT_STYLES
        colors = {
            "offset": "#4da6ff",      # Azul claro (mesma cor do MarkerManager)
            "overlap": "#00ff00",     # Verde (mesma cor do MarkerManager)
            "preutter": "#ff0000",    # Vermelho (mesma cor do MarkerManager)
            "consonant": "#ff69b4",   # Rosa hot pink (mesma cor do MarkerManager)
            "cutoff": "#4da6ff",      # Azul claro (mesma cor do MarkerManager)
        }

        for name, pos in positions.items():
            if 0 <= pos <= self._audio_duration:
                color = colors.get(name, "#FFCC00")
                line = pg.InfiniteLine(
                    pos=pos, angle=90, movable=False,
                    pen=pg.mkPen(color, width=1)
                )
                line.setZValue(3)
                self._plot.addItem(line)
                self._marker_lines[name] = line

    def mousePressEvent(self, event):
        """Clique para navegar."""
        if event.button() == Qt.LeftButton and self._is_ready:
            self._navigate_to_click(event.position())
        super().mousePressEvent(event)

    def _navigate_to_click(self, widget_pos):
        """Navega para a posição clicada."""
        if self._audio_duration <= 0:
            return

        # Converte posição do widget para tempo
        widget_width = self.width()
        if widget_width <= 0:
            return

        clicked_time = (widget_pos.x() / widget_width) * self._audio_duration
        clicked_time = max(0, min(clicked_time, self._audio_duration))

        # Verifica se clicou dentro da região atual
        current_start, current_end = self._view_region.getRegion()
        if current_start <= clicked_time <= current_end:
            # Clicou dentro, deixa arrastar
            return

        # Mantém a largura atual e centraliza no ponto clicado
        region_width = current_end - current_start
        new_start = clicked_time - region_width / 2
        new_end = clicked_time + region_width / 2

        # Ajusta aos limites
        if new_start < 0:
            new_start = 0
            new_end = min(region_width, self._audio_duration)
        if new_end > self._audio_duration:
            new_end = self._audio_duration
            new_start = max(0, self._audio_duration - region_width)

        self._set_region_silent(new_start, new_end)
        self._update_shades(new_start, new_end)
        self._navigate_parent(new_start, new_end)

    def wheelEvent(self, event):
        """Scroll para zoom/pan no minimap."""
        if not self._is_ready or self._audio_duration <= 0:
            event.ignore()
            return

        delta = event.angleDelta().y()
        if delta == 0:
            event.ignore()
            return

        start, end = self._view_region.getRegion()
        current_width = end - start
        if current_width <= 0:
            current_width = 0.01

        modifiers = event.modifiers()

        if modifiers & Qt.ShiftModifier:
            # SHIFT + Scroll = Pan horizontal
            pan_amount = current_width * 0.1
            if delta > 0:
                new_start = start - pan_amount
                new_end = end - pan_amount
            else:
                new_start = start + pan_amount
                new_end = end + pan_amount
        else:
            # Scroll normal = Zoom
            center = (start + end) / 2.0
            factor = 0.8 if delta > 0 else 1.25
            new_width = current_width * factor

            # Limites
            min_width = self._audio_duration / 100.0
            max_width = self._audio_duration
            new_width = max(min_width, min(new_width, max_width))

            new_start = center - new_width / 2
            new_end = center + new_width / 2

        # Ajusta aos bounds
        if new_start < 0:
            new_start = 0
            new_end = min(new_end - new_start, self._audio_duration)
        if new_end > self._audio_duration:
            new_end = self._audio_duration
            new_start = max(0, new_end - (end - start if modifiers & Qt.ShiftModifier else new_width))

        self._set_region_silent(new_start, new_end)
        self._update_shades(new_start, new_end)
        self._navigate_parent(new_start, new_end)

>>>>>>> Stashed changes
        event.accept()