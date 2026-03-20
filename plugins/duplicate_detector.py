# plugins/duplicate_detector.py
"""
Plugin: Detector de Duplicatas
Encontra aliases duplicados ou muito similares.
"""

from typing import Optional, List, Dict, Tuple
from dataclasses import dataclass

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QCheckBox, QGroupBox,
    QRadioButton, QButtonGroup, QMessageBox, QAbstractItemView
)
from PySide6.QtCore import Qt

from .base_plugin import BasePlugin, PluginResult, PluginCategory


@dataclass
class Duplicate:
    """Representa um par de duplicatas encontrado"""
    row1: int
    row2: int
    alias1: str
    alias2: str
    match_type: str  # "exact", "case", "similar", "functional"
    similarity: float  # 0.0 a 1.0


class DuplicateDetectorDialog(QDialog):
    """Diálogo do Detector de Duplicatas"""
    
    def __init__(self, plugin: 'DuplicateDetectorPlugin', parent=None):
        super().__init__(parent)
        self.plugin = plugin
        self.duplicates: List[Duplicate] = []
        self._setup_ui()
    
    def _setup_ui(self):
        self.setWindowTitle("Detector de Duplicatas")
        self.setMinimumSize(700, 500)
        
        layout = QVBoxLayout(self)
        
        # Opções de detecção
        options_group = QGroupBox("Tipos de Duplicatas a Detectar")
        options_layout = QVBoxLayout(options_group)
        
        self.chk_exact = QCheckBox("Duplicatas exatas (mesmo alias)")
        self.chk_exact.setChecked(True)
        self.chk_exact.setToolTip("Aliases idênticos em diferentes linhas")
        
        self.chk_case = QCheckBox("Ignorar maiúsculas/minúsculas")
        self.chk_case.setChecked(True)
        self.chk_case.setToolTip("'Ka' e 'ka' são considerados duplicatas")
        
        self.chk_functional = QCheckBox("Duplicatas funcionais (mesmo arquivo + offset)")
        self.chk_functional.setChecked(True)
        self.chk_functional.setToolTip("Aliases diferentes apontando para o mesmo trecho de áudio")
        
        self.chk_similar = QCheckBox("Aliases similares (diferença de 1-2 caracteres)")
        self.chk_similar.setChecked(False)
        self.chk_similar.setToolTip("Pode encontrar erros de digitação")
        
        options_layout.addWidget(self.chk_exact)
        options_layout.addWidget(self.chk_case)
        options_layout.addWidget(self.chk_functional)
        options_layout.addWidget(self.chk_similar)
        layout.addWidget(options_group)
        
        # Botão de análise
        scan_btn = QPushButton("🔍 Analisar Duplicatas")
        scan_btn.clicked.connect(self._scan_duplicates)
        layout.addWidget(scan_btn)
        
        # Tabela de resultados
        self.results_label = QLabel("Nenhuma análise realizada ainda.")
        layout.addWidget(self.results_label)
        
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(5)
        self.results_table.setHorizontalHeaderLabels([
            "Tipo", "Alias 1", "Linha 1", "Alias 2", "Linha 2"
        ])
        self.results_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.results_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.results_table.doubleClicked.connect(self._go_to_duplicate)
        layout.addWidget(self.results_table)
        
        # Botões de ação
        actions_layout = QHBoxLayout()
        
        self.btn_go_to = QPushButton("Ir para Selecionado")
        self.btn_go_to.clicked.connect(self._go_to_selected)
        self.btn_go_to.setEnabled(False)
        
        self.btn_delete_second = QPushButton("Deletar Segunda Ocorrência")
        self.btn_delete_second.clicked.connect(self._delete_second)
        self.btn_delete_second.setEnabled(False)
        
        self.btn_close = QPushButton("Fechar")
        self.btn_close.clicked.connect(self.close)
        
        actions_layout.addWidget(self.btn_go_to)
        actions_layout.addWidget(self.btn_delete_second)
        actions_layout.addStretch()
        actions_layout.addWidget(self.btn_close)
        layout.addLayout(actions_layout)
        
        # Conectar seleção
        self.results_table.itemSelectionChanged.connect(self._on_selection_changed)
    
    def _scan_duplicates(self):
        """Executa a análise de duplicatas"""
        result = self.plugin.execute(
            check_exact=self.chk_exact.isChecked(),
            check_case=self.chk_case.isChecked(),
            check_functional=self.chk_functional.isChecked(),
            check_similar=self.chk_similar.isChecked()
        )
        
        self.duplicates = result.data if result.data else []
        self._update_results_table()
        
        if result.success:
            self.results_label.setText(f"✅ Encontradas {len(self.duplicates)} duplicata(s)")
        else:
            self.results_label.setText(f"⚠️ {result.message}")
    
    def _update_results_table(self):
        """Atualiza a tabela de resultados"""
        self.results_table.setRowCount(len(self.duplicates))
        
        type_names = {
            "exact": "Exata",
            "case": "Maiúsc./Minúsc.",
            "functional": "Funcional",
            "similar": "Similar"
        }
        
        for i, dup in enumerate(self.duplicates):
            self.results_table.setItem(i, 0, QTableWidgetItem(type_names.get(dup.match_type, dup.match_type)))
            self.results_table.setItem(i, 1, QTableWidgetItem(dup.alias1))
            self.results_table.setItem(i, 2, QTableWidgetItem(str(dup.row1 + 1)))
            self.results_table.setItem(i, 3, QTableWidgetItem(dup.alias2))
            self.results_table.setItem(i, 4, QTableWidgetItem(str(dup.row2 + 1)))
        
        self.results_table.resizeColumnsToContents()
    
    def _on_selection_changed(self):
        """Atualiza estado dos botões baseado na seleção"""
        has_selection = len(self.results_table.selectedItems()) > 0
        self.btn_go_to.setEnabled(has_selection)
        self.btn_delete_second.setEnabled(has_selection)
    
    def _go_to_duplicate(self, index):
        """Vai para o alias clicado"""
        row = index.row()
        if 0 <= row < len(self.duplicates):
            dup = self.duplicates[row]
            self.plugin.table.selectRow(dup.row1)
            self.plugin.table.scrollToItem(self.plugin.table.item(dup.row1, 0))
    
    def _go_to_selected(self):
        """Vai para o alias selecionado"""
        selected = self.results_table.selectedItems()
        if selected:
            row = selected[0].row()
            if 0 <= row < len(self.duplicates):
                dup = self.duplicates[row]
                self.plugin.table.selectRow(dup.row1)
                self.plugin.table.scrollToItem(self.plugin.table.item(dup.row1, 0))
    
    def _delete_second(self):
        """Deleta a segunda ocorrência das duplicatas selecionadas"""
        selected_rows = set()
        for item in self.results_table.selectedItems():
            selected_rows.add(item.row())
        
        if not selected_rows:
            return
        
        # Confirmar
        reply = QMessageBox.question(
            self, "Confirmar Exclusão",
            f"Deseja deletar {len(selected_rows)} alias(es) duplicados?\n\n"
            "Apenas a segunda ocorrência de cada par será deletada.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        # Coletar linhas para deletar (segunda ocorrência)
        rows_to_delete = []
        for table_row in selected_rows:
            if table_row < len(self.duplicates):
                rows_to_delete.append(self.duplicates[table_row].row2)
        
        # Deletar em ordem reversa para não afetar índices
        rows_to_delete = sorted(set(rows_to_delete), reverse=True)
        for row in rows_to_delete:
            self.plugin.table.removeRow(row)
        
        self.plugin.mark_dirty()
        self.plugin.show_message(f"Deletados {len(rows_to_delete)} alias(es) duplicados")
        
        # Re-analisar
        self._scan_duplicates()


class DuplicateDetectorPlugin(BasePlugin):
    """Plugin para detectar aliases duplicados"""
    
    NAME = "Podador - Detector de Duplicatas"
    DESCRIPTION = "Encontra aliases duplicados ou muito similares"
    CATEGORY = PluginCategory.VALIDATION
    VERSION = "1.0.0"
    
    def get_dialog(self) -> Optional[QDialog]:
        return DuplicateDetectorDialog(self, self.main_window)
    
    def execute(self, check_exact=True, check_case=True, 
                check_functional=True, check_similar=False, **kwargs) -> PluginResult:
        """
        Executa a detecção de duplicatas.
        
        Args:
            check_exact: Verificar duplicatas exatas
            check_case: Ignorar maiúsculas/minúsculas
            check_functional: Verificar duplicatas funcionais
            check_similar: Verificar aliases similares
        """
        duplicates: List[Duplicate] = []
        rows = self.get_all_rows()
        
        if not rows:
            return PluginResult(False, "Nenhum alias na tabela", [])
        
        # Coletar dados
        aliases_data = []
        for row in rows:
            data = self.get_alias_data(row)
            aliases_data.append(data)
        
        # Verificar duplicatas
        seen_exact = {}
        seen_case = {}
        seen_functional = {}
        
        for i, data in enumerate(aliases_data):
            alias = data["alias"]
            
            # Duplicatas exatas
            if check_exact:
                if alias in seen_exact:
                    duplicates.append(Duplicate(
                        row1=seen_exact[alias],
                        row2=i,
                        alias1=alias,
                        alias2=alias,
                        match_type="exact",
                        similarity=1.0
                    ))
                else:
                    seen_exact[alias] = i
            
            # Ignorar case
            if check_case and not check_exact:
                alias_lower = alias.lower()
                if alias_lower in seen_case:
                    original_row = seen_case[alias_lower]
                    original_alias = aliases_data[original_row]["alias"]
                    if original_alias != alias:  # Não é exata
                        duplicates.append(Duplicate(
                            row1=original_row,
                            row2=i,
                            alias1=original_alias,
                            alias2=alias,
                            match_type="case",
                            similarity=0.95
                        ))
                else:
                    seen_case[alias_lower] = i
            
            # Duplicatas funcionais
            if check_functional:
                key = (data["filename"], data["offset"], data["cutoff"])
                if key in seen_functional:
                    original_row = seen_functional[key]
                    original_alias = aliases_data[original_row]["alias"]
                    if original_alias != alias:  # Aliases diferentes
                        duplicates.append(Duplicate(
                            row1=original_row,
                            row2=i,
                            alias1=original_alias,
                            alias2=alias,
                            match_type="functional",
                            similarity=1.0
                        ))
                else:
                    seen_functional[key] = i
            
            # Aliases similares (distância de Levenshtein)
            if check_similar:
                for j, other_data in enumerate(aliases_data[:i]):
                    other_alias = other_data["alias"]
                    dist = self._levenshtein_distance(alias, other_alias)
                    if 0 < dist <= 2:  # Diferença de 1-2 caracteres
                        similarity = 1.0 - (dist / max(len(alias), len(other_alias)))
                        duplicates.append(Duplicate(
                            row1=j,
                            row2=i,
                            alias1=other_alias,
                            alias2=alias,
                            match_type="similar",
                            similarity=similarity
                        ))
        
        return PluginResult(
            success=True,
            message=f"Encontradas {len(duplicates)} duplicatas",
            data=duplicates,
            changes_made=0
        )
    
    def _levenshtein_distance(self, s1: str, s2: str) -> int:
        """Calcula a distância de Levenshtein entre duas strings"""
        if len(s1) < len(s2):
            return self._levenshtein_distance(s2, s1)
        
        if len(s2) == 0:
            return len(s1)
        
        previous_row = range(len(s2) + 1)
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row
        
        return previous_row[-1]
