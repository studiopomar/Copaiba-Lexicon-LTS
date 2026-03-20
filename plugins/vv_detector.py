# plugins/vv_detector.py
"""
Plugin: Detector de Transições VV
Analisa áudios VV para detectar o ponto ideal de transição entre vogais.
"""

from typing import Optional, List, Dict
from pathlib import Path
import numpy as np

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QSlider, QGroupBox, QCheckBox, QProgressBar, QSpinBox,
    QTableWidget, QTableWidgetItem, QAbstractItemView, QMessageBox
)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QColor

from .base_plugin import BasePlugin, PluginResult, PluginCategory

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from audio_loader import read_wav_file


class VVDetectorWorker(QThread):
    """Thread para processar detecção de transições VV"""
    progress = Signal(int, int)
    result = Signal(list)
    
    def __init__(self, plugin, rows, window_ms, sensitivity, overlap_before, consonant_after):
        super().__init__()
        self.plugin = plugin
        self.rows = rows
        self.window_ms = window_ms
        self.sensitivity = sensitivity
        self.overlap_before = overlap_before  # ms antes da transição para o overlap
        self.consonant_after = consonant_after  # ms depois da transição para o consonant
    
    def run(self):
        results = []
        vowels = set('aiueoアイウエオあいうえお')
        
        for i, row in enumerate(self.rows):
            self.progress.emit(i + 1, len(self.rows))
            
            data = self.plugin.get_alias_data(row)
            alias = data["alias"].lower().strip()
            
            # Verificar se é um alias VV (vogal + vogal)
            # Padrões comuns: "a i", "a あ", "あ い", etc.
            is_vv = False
            
            # Remover espaços para verificar
            clean_alias = alias.replace(' ', '').replace('-', '')
            
            # Verificar se tem pelo menos 2 caracteres que são vogais
            vowel_count = sum(1 for c in clean_alias if c in vowels)
            if vowel_count >= 2 and len(clean_alias) >= 2:
                # Verificar se começa e termina com vogal (ou é só vogais)
                first_vowel = None
                last_vowel = None
                for c in clean_alias:
                    if c in vowels:
                        if first_vowel is None:
                            first_vowel = c
                        last_vowel = c
                
                if first_vowel and last_vowel and first_vowel != last_vowel:
                    is_vv = True
                elif vowel_count == 2:  # Exatamente 2 vogais
                    is_vv = True
            
            if not is_vv:
                continue
            
            audio_path = self.plugin.get_audio_path(row)
            if not audio_path:
                continue
            
            try:
                full_audio, sample_rate = read_wav_file(str(audio_path))
                if len(full_audio) == 0:
                    continue
                
                total_duration_ms = (len(full_audio) / sample_rate) * 1000
                
                # Obter offset e cutoff atuais para definir a região do alias
                current_offset = data["offset"]
                current_cutoff = data["cutoff"]
                
                # Calcular região do alias em samples
                start_sample = int(current_offset * sample_rate / 1000)
                
                # Cutoff: se negativo = distância do fim, se positivo = distância do offset
                if current_cutoff <= 0:
                    end_sample = int((total_duration_ms + current_cutoff) * sample_rate / 1000)
                else:
                    end_sample = int((current_offset + current_cutoff) * sample_rate / 1000)
                
                # Garantir limites válidos
                start_sample = max(0, min(start_sample, len(full_audio) - 1))
                end_sample = max(start_sample + 100, min(end_sample, len(full_audio)))
                
                # Extrair região do alias
                alias_audio = full_audio[start_sample:end_sample]
                alias_duration_ms = (len(alias_audio) / sample_rate) * 1000
                
                if len(alias_audio) < 100:
                    continue
                
                # Calcular envelope de energia na região do alias
                window_samples = int(sample_rate * self.window_ms / 1000)
                if window_samples < 1:
                    window_samples = 1
                
                n_windows = len(alias_audio) // window_samples
                if n_windows < 5:
                    continue
                
                # Calcular energia por janela (RMS)
                energy = np.zeros(n_windows)
                for j in range(n_windows):
                    start = j * window_samples
                    end = start + window_samples
                    window_data = alias_audio[start:end]
                    energy[j] = np.sqrt(np.mean(window_data ** 2))
                
                # Suavizar para reduzir ruído
                kernel_size = max(3, self.sensitivity)
                smoothed = np.convolve(energy, np.ones(kernel_size) / kernel_size, mode='same')
                
                # Normalizar
                if smoothed.max() > 0:
                    smoothed = smoothed / smoothed.max()
                
                # Encontrar a transição (ponto de menor energia entre dois picos)
                # Dividir em terços para encontrar os picos das vogais
                third = len(smoothed) // 3
                
                # Primeiro pico (primeira vogal) - primeiro terço
                if third < 1:
                    continue
                peak1_idx = np.argmax(smoothed[:third * 2])
                
                # Segundo pico (segunda vogal) - último terço
                peak2_start = max(peak1_idx + 1, third)
                peak2_idx = peak2_start + np.argmax(smoothed[peak2_start:])
                
                if peak1_idx >= peak2_idx:
                    continue
                
                # Encontrar mínimo entre os picos (ponto de transição)
                transition_region = smoothed[peak1_idx:peak2_idx]
                if len(transition_region) < 1:
                    continue
                
                local_min_idx = np.argmin(transition_region)
                transition_idx = peak1_idx + local_min_idx
                
                # Converter para ms RELATIVO ao início da região do alias
                ms_per_window = (window_samples / sample_rate) * 1000
                transition_local_ms = transition_idx * ms_per_window
                
                # Posição absoluta da transição no arquivo
                transition_absolute_ms = current_offset + transition_local_ms
                
                # === CÁLCULO DOS PARÂMETROS ===
                # Preutter: posição da transição RELATIVA ao offset
                preutter_ms = transition_local_ms
                preutter_ms = max(10, preutter_ms)  # Mínimo 10ms
                
                # Overlap: antes da preutter (para suavizar a transição)
                overlap_ms = max(0, preutter_ms - self.overlap_before)
                
                # Consonant: depois da preutter (marca o fim da zona de transição)
                consonant_ms = preutter_ms + self.consonant_after
                # Não pode ultrapassar a duração do alias
                consonant_ms = min(consonant_ms, alias_duration_ms - 10)
                
                # Cutoff: manter o atual se fizer sentido, ou calcular novo
                # Encontrar onde a energia cai após o segundo pico
                end_region = smoothed[peak2_idx:]
                new_cutoff = current_cutoff  # Manter o atual por padrão
                
                if len(end_region) > 2:
                    threshold = smoothed[peak2_idx] * 0.15
                    end_idx = len(smoothed) - 1
                    for j in range(len(end_region) - 1, -1, -1):
                        if end_region[j] > threshold:
                            end_idx = peak2_idx + j + 2
                            break
                    
                    end_local_ms = end_idx * ms_per_window
                    # Novo cutoff negativo (distância do fim)
                    new_cutoff = -(alias_duration_ms - end_local_ms)
                    new_cutoff = min(-10, new_cutoff)  # Pelo menos -10ms
                
                # Calcular confiança
                if smoothed[transition_idx] > 0:
                    avg_peaks = (smoothed[peak1_idx] + smoothed[peak2_idx]) / 2
                    confidence = 1.0 - (smoothed[transition_idx] / max(avg_peaks, 0.001))
                    confidence = max(0, min(1, confidence))
                else:
                    confidence = 0.5
                
                results.append({
                    "row": row,
                    "alias": data["alias"],
                    "transition_ms": round(transition_absolute_ms, 2),
                    "offset": round(current_offset, 2),
                    "preutter": round(preutter_ms, 2),
                    "overlap": round(overlap_ms, 2),
                    "consonant": round(consonant_ms, 2),
                    "cutoff": round(new_cutoff, 2),
                    "confidence": round(confidence, 2)
                })
                
            except Exception as e:
                print(f"[VV Detector] Erro na linha {row}: {e}")
                import traceback
                traceback.print_exc()
                continue

        
        self.result.emit(results)


class VVDetectorDialog(QDialog):
    """Diálogo do Detector de Transições VV"""
    
    def __init__(self, plugin: 'VVDetectorPlugin', parent=None):
        super().__init__(parent)
        self.plugin = plugin
        self.results: List[Dict] = []
        self.worker = None
        self._setup_ui()
    
    def _setup_ui(self):
        self.setWindowTitle("Detector de Transições VV")
        self.setMinimumSize(850, 600)
        
        layout = QVBoxLayout(self)
        
        # Info
        info_label = QLabel(
            "Este plugin analisa aliases VV (vogal+vogal) para detectar "
            "o ponto de transição entre as duas vogais. A PREUTTER será posicionada "
            "exatamente no ponto de transição detectado."
        )
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # Configurações
        config_group = QGroupBox("Configurações de Detecção")
        config_layout = QVBoxLayout(config_group)
        
        # Linha 1: Janela e Sensibilidade
        row1_layout = QHBoxLayout()
        row1_layout.addWidget(QLabel("Janela de análise:"))
        self.spin_window = QSpinBox()
        self.spin_window.setRange(5, 50)
        self.spin_window.setValue(10)
        self.spin_window.setSuffix(" ms")
        self.spin_window.setToolTip("Tamanho da janela para análise de energia")
        row1_layout.addWidget(self.spin_window)
        
        row1_layout.addWidget(QLabel("Sensibilidade:"))
        self.slider_sens = QSlider(Qt.Horizontal)
        self.slider_sens.setRange(1, 10)
        self.slider_sens.setValue(5)
        self.slider_sens.setMaximumWidth(100)
        row1_layout.addWidget(self.slider_sens)
        self.lbl_sens = QLabel("5")
        self.slider_sens.valueChanged.connect(lambda v: self.lbl_sens.setText(str(v)))
        row1_layout.addWidget(self.lbl_sens)
        row1_layout.addStretch()
        config_layout.addLayout(row1_layout)
        
        # Linha 2: Parâmetros de posicionamento
        row2_layout = QHBoxLayout()
        row2_layout.addWidget(QLabel("Overlap (antes da transição):"))
        self.spin_overlap = QSpinBox()
        self.spin_overlap.setRange(0, 200)
        self.spin_overlap.setValue(50)
        self.spin_overlap.setSuffix(" ms")
        self.spin_overlap.setToolTip("Quanto ANTES da preutter o overlap será posicionado")
        row2_layout.addWidget(self.spin_overlap)
        
        row2_layout.addWidget(QLabel("Consonant (após transição):"))
        self.spin_consonant = QSpinBox()
        self.spin_consonant.setRange(0, 200)
        self.spin_consonant.setValue(50)
        self.spin_consonant.setSuffix(" ms")
        self.spin_consonant.setToolTip("Quanto DEPOIS da preutter o consonant será posicionado")
        row2_layout.addWidget(self.spin_consonant)
        row2_layout.addStretch()
        config_layout.addLayout(row2_layout)
        
        layout.addWidget(config_group)
        
        # Progresso
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Botão de análise
        self.btn_analyze = QPushButton("🔀 Detectar Transições VV")
        self.btn_analyze.clicked.connect(self._start_detection)
        layout.addWidget(self.btn_analyze)
        
        # Resultados
        results_group = QGroupBox("Transições Detectadas (Preutter = Ponto de Transição)")
        results_layout = QVBoxLayout(results_group)
        
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(8)
        self.results_table.setHorizontalHeaderLabels([
            "Linha", "Alias", "Transição", "Preutter", "Overlap", "Consonant", "Cutoff", "Confiança"
        ])
        self.results_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.results_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.results_table.doubleClicked.connect(self._go_to_alias)
        results_layout.addWidget(self.results_table)
        
        layout.addWidget(results_group)
        
        # Botões de ação
        actions_layout = QHBoxLayout()
        
        self.btn_apply = QPushButton("✅ Aplicar Sugestões")
        self.btn_apply.clicked.connect(self._apply_suggestions)
        self.btn_apply.setEnabled(False)
        
        self.btn_apply_selected = QPushButton("Aplicar Selecionados")
        self.btn_apply_selected.clicked.connect(self._apply_selected)
        self.btn_apply_selected.setEnabled(False)
        
        btn_close = QPushButton("Fechar")
        btn_close.clicked.connect(self.close)
        
        actions_layout.addWidget(self.btn_apply)
        actions_layout.addWidget(self.btn_apply_selected)
        actions_layout.addStretch()
        actions_layout.addWidget(btn_close)
        layout.addLayout(actions_layout)
    
    def _start_detection(self):
        """Inicia a detecção de transições"""
        rows = self.plugin.get_all_rows()
        
        if not rows:
            QMessageBox.warning(self, "Aviso", "Nenhum alias para analisar.")
            return
        
        self.btn_analyze.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, len(rows))
        
        self.worker = VVDetectorWorker(
            self.plugin,
            rows,
            self.spin_window.value(),
            self.slider_sens.value(),
            self.spin_overlap.value(),
            self.spin_consonant.value()
        )
        self.worker.progress.connect(self._on_progress)
        self.worker.result.connect(self._on_result)
        self.worker.start()
    
    def _on_progress(self, current, total):
        self.progress_bar.setValue(current)
    
    def _on_result(self, results):
        """Recebe os resultados"""
        self.results = results
        self.btn_analyze.setEnabled(True)
        self.progress_bar.setVisible(False)
        
        # Preencher tabela
        self.results_table.setRowCount(len(results))
        
        for i, r in enumerate(results):
            self.results_table.setItem(i, 0, QTableWidgetItem(str(r["row"] + 1)))
            self.results_table.setItem(i, 1, QTableWidgetItem(r["alias"]))
            self.results_table.setItem(i, 2, QTableWidgetItem(f"{r['transition_ms']:.1f}"))
            self.results_table.setItem(i, 3, QTableWidgetItem(f"{r['preutter']:.1f}"))
            self.results_table.setItem(i, 4, QTableWidgetItem(f"{r['overlap']:.1f}"))
            self.results_table.setItem(i, 5, QTableWidgetItem(f"{r['consonant']:.1f}"))
            self.results_table.setItem(i, 6, QTableWidgetItem(f"{r['cutoff']:.1f}"))
            
            # Colorir confiança
            conf_item = QTableWidgetItem(f"{r['confidence'] * 100:.0f}%")
            if r['confidence'] > 0.7:
                conf_item.setBackground(QColor(200, 255, 200))
            elif r['confidence'] > 0.4:
                conf_item.setBackground(QColor(255, 255, 200))
            else:
                conf_item.setBackground(QColor(255, 200, 200))
            self.results_table.setItem(i, 7, conf_item)
        
        self.results_table.resizeColumnsToContents()
        
        self.btn_apply.setEnabled(len(results) > 0)
        self.btn_apply_selected.setEnabled(len(results) > 0)
        
        self.plugin.show_message(f"Detectadas {len(results)} transições VV")
    
    def _go_to_alias(self, index):
        """Vai para o alias clicado"""
        row = index.row()
        if 0 <= row < len(self.results):
            alias_row = self.results[row]["row"]
            self.plugin.table.selectRow(alias_row)
            self.plugin.table.scrollToItem(self.plugin.table.item(alias_row, 0))
    
    def _apply_suggestions(self):
        """Aplica todas as sugestões"""
        if not self.results:
            return
        
        reply = QMessageBox.question(
            self, "Confirmar",
            f"Deseja aplicar sugestões a {len(self.results)} alias(es) VV?\n\n"
            "Serão aplicados: Preutter, Overlap, Consonant e Cutoff",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        for r in self.results:
            self.plugin.set_alias_data(r["row"], "preutter", r["preutter"])
            self.plugin.set_alias_data(r["row"], "overlap", r["overlap"])
            self.plugin.set_alias_data(r["row"], "consonant", r["consonant"])
            self.plugin.set_alias_data(r["row"], "cutoff", r["cutoff"])
        
        self.plugin.mark_dirty()
        self.plugin.show_message(f"Aplicadas sugestões a {len(self.results)} alias(es) VV")
    
    def _apply_selected(self):
        """Aplica sugestões apenas aos selecionados"""
        selected_rows = set()
        for item in self.results_table.selectedItems():
            selected_rows.add(item.row())
        
        if not selected_rows:
            QMessageBox.information(self, "Info", "Selecione os alias(es) a aplicar.")
            return
        
        for table_row in selected_rows:
            if table_row < len(self.results):
                r = self.results[table_row]
                self.plugin.set_alias_data(r["row"], "preutter", r["preutter"])
                self.plugin.set_alias_data(r["row"], "overlap", r["overlap"])
                self.plugin.set_alias_data(r["row"], "consonant", r["consonant"])
                self.plugin.set_alias_data(r["row"], "cutoff", r["cutoff"])
        
        self.plugin.mark_dirty()
        self.plugin.show_message(f"Aplicadas sugestões a {len(selected_rows)} alias(es)")


class VVDetectorPlugin(BasePlugin):
    """Plugin para detectar transições VV"""
    
    NAME = "Maturação - Detector VV"
    DESCRIPTION = "Analisa áudios VV para detectar transições entre vogais"
    CATEGORY = PluginCategory.ANALYSIS
    VERSION = "1.0.0"
    
    def get_dialog(self) -> Optional[QDialog]:
        return VVDetectorDialog(self, self.main_window)
    
    def execute(self, **kwargs) -> PluginResult:
        return PluginResult(
            success=True,
            message="Use o diálogo para detectar transições VV"
        )
