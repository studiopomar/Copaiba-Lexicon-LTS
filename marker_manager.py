# marker_manager.py

from typing import Dict, Optional, Callable
from dataclasses import replace
import numpy as np
import pyqtgraph as pg
from PySide6.QtCore import Qt
from copaiba import OtoEntry

# Tenta importar backend GPU
try:
    from backend_gpu import get_gpu_backend, gpu_enabled

    GPU_BACKEND_AVAILABLE = True
except ImportError:
    GPU_BACKEND_AVAILABLE = False


    def gpu_enabled():
        return False


class MarkerManager:
    """
    Gerencia os marcadores (offset, overlap, preutter, consonant, cutoff)
    e regiões preenchidas no WaveformPlotWidget E no SpectrogramWidget.
    """
    MARKER_ORDER = ["offset", "overlap", "preutter", "consonant", "cutoff"]
    DEFAULT_STYLES = {
        "offset": {"color": "#4da6ff", "fill": True},
        "overlap": {"color": "#00ff00", "fill": False},
        "preutter": {"color": "#ff0000", "fill": False},
        "consonant": {"color": "#ff69b4", "fill": True},
        "cutoff": {"color": "#4da6ff", "fill": True},
    }

    def __init__(self, primary_plot):
        self.primary_plot = primary_plot
        self.secondary_plot = None

        self._marker_lines_primary: Dict[str, pg.InfiniteLine] = {}
        self._marker_lines_secondary: Dict[str, pg.InfiniteLine] = {}
        self._filled_regions: list[pg.LinearRegionItem] = []

        self._current_entry: Optional[OtoEntry] = None
        self._current_row: Optional[int] = None
        self._edit_callback: Optional[Callable] = None
        self._audio_duration_ms: float = 0.0

        self._srp_enabled: bool = False
        self._srna_enabled: bool = False

        # Drag state: entry antes do início do arraste (para undo)
        self._pre_drag_entry: Optional[OtoEntry] = None
        self._is_dragging: bool = False

    def set_secondary_plot(self, plot_widget):
        self.secondary_plot = plot_widget

    def set_edit_callback(self, cb):
        self._edit_callback = cb

    def set_current_entry(self, entry: OtoEntry, row: int):
        self._current_entry = entry
        self._current_row = row

    def set_srp_enabled(self, enabled: bool):
        self._srp_enabled = enabled

    def set_srna_enabled(self, enabled: bool):
        """Ativa/desativa SRnA (Snap Relativo a Nada) - movimento totalmente independente."""
        self._srna_enabled = enabled

    def set_audio_duration(self, duration_ms: float):
        self._audio_duration_ms = duration_ms

    def get_marker_positions(self) -> Dict[str, float]:
        """Calcula a posição visual (em segundos) de cada marcador."""
        if self._current_entry is None:
            return {}

        e = self._current_entry
        dur_ms = self._audio_duration_ms
        offset_ms = float(e.offset)
        cutoff_val = float(e.cutoff)

        # --- LÓGICA DE CUTOFF CORRIGIDA ---
        if cutoff_val > 0:
            # Cutoff Positivo: Distância a partir do FINAL do arquivo
            # Visual = Total - Cutoff
            visual_cutoff = dur_ms - cutoff_val
        else:
            # Cutoff Negativo: Duração a partir do OFFSET
            # Visual = Offset - Cutoff (como cutoff é negativo, isso soma)
            visual_cutoff = offset_ms - cutoff_val

        pos = {
            "offset": offset_ms,
            "preutter": offset_ms + float(e.preutter),
            "overlap": offset_ms + float(e.overlap),
            "consonant": offset_ms + float(e.consonant),
            "cutoff": visual_cutoff
        }

        # Converte para segundos para o pyqtgraph
        final_pos = {}
        for k, v in pos.items():
            # Garante que não seja negativo visualmente
            val = max(0.0, v)
            final_pos[k] = val / 1000.0

        return final_pos

    def update_markers_from_entry(self, skip_marker: Optional[str] = None, audio_duration_s: float = 0.0):
        if self._current_entry is None:
            return

        # Atualiza duração interna se fornecida
        if audio_duration_s > 0:
            self._audio_duration_ms = audio_duration_s * 1000.0

        mapping = self.get_marker_positions()

        self._update_plot_lines(self.primary_plot, self._marker_lines_primary, mapping)
        if self.secondary_plot:
            # Novo comportamento: se for objeto SpectrogramWidget (Matplotlib), chama método específico
            if hasattr(self.secondary_plot, 'update_markers'):
                self.secondary_plot.update_markers(mapping)
            else:
                # Comportamento antigo para PyQtGraph
                self._update_plot_lines(self.secondary_plot, self._marker_lines_secondary, mapping)

        self._update_filled_regions(mapping, self._audio_duration_ms / 1000.0)

    def _update_plot_lines(self, plot, lines_dict, mapping):
        for name, t_s in mapping.items():
            style = self.DEFAULT_STYLES.get(name, {"color": "#ffcc00"})

            if name not in lines_dict:
                line = pg.InfiniteLine(
                    pos=t_s,
                    angle=90,
                    movable=False,
                    pen=pg.mkPen(style["color"], width=2, style=Qt.SolidLine),
                )
                plot.addItem(line)
                lines_dict[name] = line
            else:
                lines_dict[name].setPos(t_s)
                lines_dict[name].show()

    def _update_filled_regions(self, mapping: Dict[str, float], dur_s: float):
        # Otimização: atualizar regiões existentes em vez de recriar
        styles = self.DEFAULT_STYLES
        
        # Calcular valores das 3 regiões
        region_data = []
        
        if "offset" in mapping and styles["offset"]["fill"]:
            region_data.append((0.0, mapping["offset"], styles["offset"]["color"]))
        
        if "offset" in mapping and "consonant" in mapping and styles["consonant"]["fill"]:
            region_data.append((mapping["offset"], mapping["consonant"], styles["consonant"]["color"]))
        
        if "cutoff" in mapping and styles["cutoff"]["fill"]:
            region_data.append((mapping["cutoff"], dur_s, styles["cutoff"]["color"]))
        
        # Se temos mais regiões do que precisamos, remover excesso
        while len(self._filled_regions) > len(region_data):
            region = self._filled_regions.pop()
            self.primary_plot.removeItem(region)
        
        # Atualizar ou criar regiões
        for i, (start, end, color_hex) in enumerate(region_data):
            if end > start + 0.0001:
                if i < len(self._filled_regions):
                    # Reutilizar região existente
                    self._filled_regions[i].setRegion((start, end))
                else:
                    # Criar nova região
                    brush_color = color_hex + "30"
                    region = pg.LinearRegionItem(
                        values=(start, end),
                        orientation='vertical',
                        brush=pg.mkBrush(brush_color),
                        movable=False
                    )
                    region.lines[0].setPen(pg.mkPen(None))
                    region.lines[1].setPen(pg.mkPen(None))
                    self.primary_plot.addItem(region)
                    self._filled_regions.append(region)


    def clear_markers(self):
        for line in self._marker_lines_primary.values():
            self.primary_plot.removeItem(line)
        self._marker_lines_primary.clear()

        if self.secondary_plot:
            for line in self._marker_lines_secondary.values():
                self.secondary_plot.removeItem(line)
            self._marker_lines_secondary.clear()

        for region in self._filled_regions:
            self.primary_plot.removeItem(region)
        self._filled_regions.clear()

        self._current_entry = None
        self._current_row = None

    def set_marker_at_mouse(
            self,
            name: str,
            mouse_time_s: float,
            snap_enabled: bool,
            snap_mode: str,
            wave_times: Optional[np.ndarray],
            wave_data: Optional[np.ndarray],
            srp_enabled: Optional[bool] = None
    ) -> bool:
        if self._current_entry is None:
            return False

        if snap_enabled and wave_times is not None and wave_data is not None:
            mouse_time_s = self._apply_snap(mouse_time_s, snap_mode, wave_times, wave_data)

        dur_ms = self._audio_duration_ms
        mouse_time_ms = max(0.0, mouse_time_s * 1000.0)

        e = self._current_entry
        offset_ms = float(e.offset)

        use_srp = srp_enabled if srp_enabled is not None else self._srp_enabled
        new_entry = None

        if use_srp and name == "preutter":
            new_entry = self._apply_srp_movement(mouse_time_ms, dur_ms)
        elif self._srna_enabled and name == "offset":
            # SRnA: Mover offset mantendo posições VISUAIS dos outros marcadores fixas
            # Apenas em SRnA o cutoff NÃO acompanha o offset
            new_entry = self._apply_srna_offset_movement(mouse_time_ms, dur_ms)
        else:
            if name == "offset":
                # Modo padrão: mover offset faz cutoff acompanhar (manter posição visual relativa)
                new_entry = self._apply_default_offset_movement(mouse_time_ms, dur_ms)
            elif name == "preutter":
                val = max(0.0, mouse_time_ms - offset_ms)
                new_entry = replace(e, preutter=val)
            elif name == "overlap":
                val = mouse_time_ms - offset_ms
                new_entry = replace(e, overlap=val)
            elif name == "consonant":
                val = max(0.0, mouse_time_ms - offset_ms)
                new_entry = replace(e, consonant=val)
            elif name == "cutoff":
                # --- LÓGICA DE ARRASTE DO CUTOFF ---
                # Se o cutoff original era positivo, mantemos a lógica positiva (distância do fim)
                # Se era negativo, mantemos a lógica negativa (distância do offset)
                current_cutoff_val = float(e.cutoff)

                if current_cutoff_val > 0:
                    # Modo Positivo: Cutoff = Total - Visual
                    val = max(0.0, dur_ms - mouse_time_ms)
                else:
                    # Modo Negativo: Cutoff = Offset - Visual
                    # (Resultado será negativo se Visual > Offset, que é o esperado)
                    val = offset_ms - mouse_time_ms

                new_entry = replace(e, cutoff=val)

        if new_entry:
            # Salva entry pré-arraste na primeira chamada de um arraste
            if not self._is_dragging:
                self._pre_drag_entry = self._current_entry
                self._is_dragging = True

            self._current_entry = new_entry
            # Atualiza APENAS visual (linhas + regiões), SEM callback para tabela
            self.update_markers_from_entry(audio_duration_s=dur_ms / 1000.0)
            return True

        return False

    def commit_marker_drag(self):
        """
        Finaliza o arraste: envia o valor final para a tabela (edit_callback).
        Deve ser chamado no keyRelease / mouseRelease.
        """
        if self._is_dragging and self._current_entry is not None:
            self._is_dragging = False
            if self._edit_callback:
                self._edit_callback(self._current_row, self._current_entry)
            self._pre_drag_entry = None

    def _apply_default_offset_movement(self, new_offset_ms: float, dur_ms: float) -> OtoEntry:
        """
        Modo padrão: mover offset faz o CUTOFF SEGUIR (mover junto).
        A posição visual do cutoff move pelo mesmo delta que o offset.
        Os outros marcadores (overlap, preutter, consonant) NÃO acompanham -
        mantêm seus valores relativos, então suas posições visuais mudam junto.
        """
        e = self._current_entry
        old_offset = float(e.offset)
        delta = new_offset_ms - old_offset
        
        if abs(delta) < 0.001:
            return replace(e, offset=new_offset_ms)
        
        # Cutoff MOVE junto com offset (mesma direção e quantidade)
        cutoff_val = float(e.cutoff)
        if cutoff_val <= 0:
            # Cutoff negativo: posição visual = offset - cutoff
            # Nova posição visual = old_visual + delta
            # new_offset - new_cutoff = (old_offset - cutoff) + delta
            # new_cutoff = new_offset - old_offset + cutoff - delta = cutoff (pois new_offset = old_offset + delta)
            # Simplificando: cutoff negativo mantém o mesmo valor (pois é relativo ao offset)
            new_cutoff = cutoff_val
        else:
            # Cutoff positivo: posição visual = dur_ms - cutoff
            # Nova posição visual = old_visual + delta = dur_ms - cutoff + delta
            # new_cutoff = dur_ms - (dur_ms - cutoff + delta) = cutoff - delta
            new_cutoff = max(0.0, cutoff_val - delta)
        
        return replace(e, offset=new_offset_ms, cutoff=new_cutoff)

    def _apply_srna_offset_movement(self, new_offset_ms: float, dur_ms: float) -> OtoEntry:
        """
        SRnA: Mover offset mantém posições VISUAIS dos outros marcadores fixas.
        Ajusta os valores relativos para compensar a mudança do offset.
        O CUTOFF também fica fixo visualmente (único modo onde isso acontece).
        """
        e = self._current_entry
        old_offset = float(e.offset)
        delta = new_offset_ms - old_offset
        
        if abs(delta) < 0.001:
            return e
        
        # Posições visuais atuais (absolutas)
        old_overlap_visual = old_offset + float(e.overlap)
        old_preutter_visual = old_offset + float(e.preutter)
        old_consonant_visual = old_offset + float(e.consonant)
        
        # Novos valores relativos (para manter posição visual fixa)
        new_overlap = old_overlap_visual - new_offset_ms
        new_preutter = max(0.0, old_preutter_visual - new_offset_ms)
        new_consonant = max(0.0, old_consonant_visual - new_offset_ms)
        
        # Cutoff também fica fixo visualmente em SRnA
        cutoff_val = float(e.cutoff)
        if cutoff_val <= 0:
            # Cutoff negativo: posição visual = offset - cutoff
            old_cutoff_visual = old_offset - cutoff_val
            # Novo cutoff = new_offset - old_visual
            new_cutoff = new_offset_ms - old_cutoff_visual
        else:
            # Cutoff positivo: posição visual = dur - cutoff (não depende do offset)
            new_cutoff = cutoff_val
        
        return replace(e, offset=new_offset_ms, overlap=new_overlap, 
                      preutter=new_preutter, consonant=new_consonant, cutoff=new_cutoff)

    def _apply_srp_movement(self, new_preutter_abs_ms: float, dur_ms: float) -> OtoEntry:
        """
        Aplica movimento SRP: mover preutterance move TODOS os parâmetros
        (offset, overlap, consonant, cutoff) mantendo suas posições relativas.
        """
        e = self._current_entry
        offset_ms = float(e.offset)
        preutter_rel = float(e.preutter)
        overlap_rel = float(e.overlap)
        consonant_rel = float(e.consonant)

        old_preutter_abs = offset_ms + preutter_rel
        delta = new_preutter_abs_ms - old_preutter_abs

        if abs(delta) < 0.001:
            return e

        # Move o offset junto com o delta
        new_offset = max(0, offset_ms + delta)
        
        # Overlap e Consonant são relativos ao offset, então suas posições
        # absolutas se movem automaticamente quando offset muda.
        # Para manter posições RELATIVAS ao preutter (não ao offset),
        # precisamos ajustar os valores relativos.
        
        # Calcular novas posições absolutas (mantendo distância do preutter)
        old_overlap_abs = offset_ms + overlap_rel
        old_consonant_abs = offset_ms + consonant_rel
        
        new_overlap_abs = old_overlap_abs + delta
        new_consonant_abs = old_consonant_abs + delta
        
        # Converter para valores relativos ao novo offset
        new_overlap = new_overlap_abs - new_offset
        new_consonant = max(0, new_consonant_abs - new_offset)

        # Ajusta cutoff mantendo a posição visual
        cutoff_val = float(e.cutoff)
        if cutoff_val > 0:
            # Positivo: Posição visual = Total - Cutoff
            old_visual_cutoff = dur_ms - cutoff_val
            new_visual_cutoff = old_visual_cutoff + delta
            new_cutoff = dur_ms - new_visual_cutoff
        else:
            # Negativo: Posição visual = Offset - Cutoff
            old_visual_cutoff = offset_ms - cutoff_val
            new_visual_cutoff = old_visual_cutoff + delta
            new_cutoff = new_offset - new_visual_cutoff

        return replace(e, offset=new_offset, overlap=new_overlap, 
                      consonant=new_consonant, cutoff=new_cutoff)

    def _apply_snap(self, t, mode, times, data):
        if mode == "none" or len(times) == 0: return t

        if mode == "peaks":
            if GPU_BACKEND_AVAILABLE and gpu_enabled():
                backend = get_gpu_backend()
                idx = int(np.searchsorted(times, t))
                t = backend.find_peaks(data, times, idx, 100)
            else:
                idx = int(np.searchsorted(times, t))
                left, right = max(0, idx - 100), min(len(times), idx + 100)
                if right > left:
                    window = np.abs(data[left:right])
                    if len(window) > 0:
                        t = float(times[left + np.argmax(window)])

        elif mode == "zero_crossing":
            if GPU_BACKEND_AVAILABLE and gpu_enabled():
                backend = get_gpu_backend()
                t = backend.find_zero_crossings(data, times, t, 50)
            else:
                idx = int(np.searchsorted(times, t))
                if 0 < idx < len(data):
                    if data[idx - 1] * data[idx] < 0:
                        t = float(times[idx] if abs(t - times[idx]) < abs(t - times[idx - 1]) else times[idx - 1])
        return t