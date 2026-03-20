# plugins/consistency_checker.py
"""
Plugin: Verificador de Consistência
Valida parâmetros e detecta problemas potenciais.
"""

from typing import Optional, List
from pathlib import Path

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QCheckBox, QGroupBox,
    QAbstractItemView, QHeaderView
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor

from .base_plugin import BasePlugin, PluginResult, PluginCategory, ValidationIssue


class ConsistencyCheckerDialog(QDialog):
    """Diálogo do Verificador de Consistência"""
    
    def __init__(self, plugin: 'ConsistencyCheckerPlugin', parent=None):
        super().__init__(parent)
        self.plugin = plugin
        self.issues: List[ValidationIssue] = []
        self._setup_ui()
    
    def _setup_ui(self):
        self.setWindowTitle("Verificador de Consistência")
        self.setMinimumSize(800, 550)
        
        layout = QVBoxLayout(self)
        
        # Opções de verificação
        options_group = QGroupBox("Verificações a Realizar")
        options_layout = QVBoxLayout(options_group)
        
        self.chk_files = QCheckBox("Verificar arquivos de áudio existentes")
        self.chk_files.setChecked(True)
        
        self.chk_offset = QCheckBox("Verificar offset válido")
        self.chk_offset.setChecked(True)
        
        self.chk_cutoff = QCheckBox("Verificar cutoff válido")
        self.chk_cutoff.setChecked(True)
        
        self.chk_overlap = QCheckBox("Verificar overlap vs preutter")
        self.chk_overlap.setChecked(True)
        
        self.chk_consonant = QCheckBox("Verificar consonant vs preutter")
        self.chk_consonant.setChecked(True)
        
        self.chk_empty = QCheckBox("Verificar aliases vazios")
        self.chk_empty.setChecked(True)
        
        self.chk_negative = QCheckBox("Verificar valores negativos inválidos")
        self.chk_negative.setChecked(True)
        
        for chk in [self.chk_files, self.chk_offset, self.chk_cutoff, 
                    self.chk_overlap, self.chk_consonant, self.chk_empty, self.chk_negative]:
            options_layout.addWidget(chk)
        
        layout.addWidget(options_group)
        
        # Botão de análise
        scan_btn = QPushButton("✅ Verificar Consistência")
        scan_btn.clicked.connect(self._run_check)
        layout.addWidget(scan_btn)
        
        # Resumo
        self.summary_label = QLabel("Nenhuma verificação realizada ainda.")
        layout.addWidget(self.summary_label)
        
        # Tabela de resultados
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(5)
        self.results_table.setHorizontalHeaderLabels([
            "Severidade", "Linha", "Alias", "Campo", "Problema"
        ])
        self.results_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.results_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.results_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch)
        self.results_table.doubleClicked.connect(self._go_to_issue)
        layout.addWidget(self.results_table)
        
        # Botões de ação
        actions_layout = QHBoxLayout()
        
        self.btn_go_to = QPushButton("Ir para Problema")
        self.btn_go_to.clicked.connect(self._go_to_selected)
        self.btn_go_to.setEnabled(False)
        
        self.btn_auto_fix = QPushButton("Corrigir Automaticamente")
        self.btn_auto_fix.clicked.connect(self._auto_fix)
        self.btn_auto_fix.setEnabled(False)
        self.btn_auto_fix.setToolTip("Aplica correções automáticas quando possível")
        
        self.btn_close = QPushButton("Fechar")
        self.btn_close.clicked.connect(self.close)
        
        actions_layout.addWidget(self.btn_go_to)
        actions_layout.addWidget(self.btn_auto_fix)
        actions_layout.addStretch()
        actions_layout.addWidget(self.btn_close)
        layout.addLayout(actions_layout)
        
        # Conectar seleção
        self.results_table.itemSelectionChanged.connect(self._on_selection_changed)
    
    def _run_check(self):
        """Executa a verificação de consistência"""
        result = self.plugin.execute(
            check_files=self.chk_files.isChecked(),
            check_offset=self.chk_offset.isChecked(),
            check_cutoff=self.chk_cutoff.isChecked(),
            check_overlap=self.chk_overlap.isChecked(),
            check_consonant=self.chk_consonant.isChecked(),
            check_empty=self.chk_empty.isChecked(),
            check_negative=self.chk_negative.isChecked()
        )
        
        self.issues = result.data if result.data else []
        self._update_results_table()
        
        # Contar por severidade
        errors = sum(1 for i in self.issues if i.severity == "error")
        warnings = sum(1 for i in self.issues if i.severity == "warning")
        infos = sum(1 for i in self.issues if i.severity == "info")
        
        self.summary_label.setText(
            f"🔴 {errors} erro(s) | 🟠 {warnings} aviso(s) | 🔵 {infos} info(s)"
        )
        
        # Habilitar auto-fix se houver correções possíveis
        fixable = sum(1 for i in self.issues if i.suggested_fix is not None)
        self.btn_auto_fix.setEnabled(fixable > 0)
        if fixable > 0:
            self.btn_auto_fix.setText(f"Corrigir Automaticamente ({fixable})")
    
    def _update_results_table(self):
        """Atualiza a tabela de resultados"""
        self.results_table.setRowCount(len(self.issues))
        
        severity_icons = {
            "error": "🔴",
            "warning": "🟠",
            "info": "🔵"
        }
        
        severity_colors = {
            "error": QColor(255, 200, 200),
            "warning": QColor(255, 235, 200),
            "info": QColor(200, 220, 255)
        }
        
        for i, issue in enumerate(self.issues):
            icon = severity_icons.get(issue.severity, "❓")
            
            items = [
                QTableWidgetItem(f"{icon} {issue.severity.upper()}"),
                QTableWidgetItem(str(issue.row + 1)),
                QTableWidgetItem(issue.alias),
                QTableWidgetItem(issue.field or "-"),
                QTableWidgetItem(issue.message)
            ]
            
            color = severity_colors.get(issue.severity)
            for j, item in enumerate(items):
                if color:
                    item.setBackground(color)
                self.results_table.setItem(i, j, item)
        
        self.results_table.resizeColumnsToContents()
    
    def _on_selection_changed(self):
        has_selection = len(self.results_table.selectedItems()) > 0
        self.btn_go_to.setEnabled(has_selection)
    
    def _go_to_issue(self, index):
        row = index.row()
        if 0 <= row < len(self.issues):
            issue = self.issues[row]
            self.plugin.table.selectRow(issue.row)
            self.plugin.table.scrollToItem(self.plugin.table.item(issue.row, 0))
    
    def _go_to_selected(self):
        selected = self.results_table.selectedItems()
        if selected:
            row = selected[0].row()
            if 0 <= row < len(self.issues):
                issue = self.issues[row]
                self.plugin.table.selectRow(issue.row)
                self.plugin.table.scrollToItem(self.plugin.table.item(issue.row, 0))
    
    def _auto_fix(self):
        """Aplica correções automáticas"""
        fixed = 0
        for issue in self.issues:
            if issue.suggested_fix is not None:
                self.plugin.set_alias_data(issue.row, issue.field, issue.suggested_fix)
                fixed += 1
        
        if fixed > 0:
            self.plugin.mark_dirty()
            self.plugin.show_message(f"Corrigidos {fixed} problema(s) automaticamente")
            self._run_check()


class ConsistencyCheckerPlugin(BasePlugin):
    """Plugin para verificar consistência dos parâmetros"""
    
    NAME = "Inspetor - Verificador de Consistência"
    DESCRIPTION = "Valida parâmetros e detecta problemas potenciais"
    CATEGORY = PluginCategory.VALIDATION
    VERSION = "1.0.0"
    
    def get_dialog(self) -> Optional[QDialog]:
        return ConsistencyCheckerDialog(self, self.main_window)
    
    def execute(self, check_files=True, check_offset=True, check_cutoff=True,
                check_overlap=True, check_consonant=True, check_empty=True,
                check_negative=True, **kwargs) -> PluginResult:
        """Executa a verificação de consistência"""
        issues: List[ValidationIssue] = []
        rows = self.get_all_rows()
        
        if not rows:
            return PluginResult(False, "Nenhum alias na tabela", [])
        
        for row in rows:
            data = self.get_alias_data(row)
            alias = data["alias"]
            filename = data["filename"]
            offset = data["offset"]
            overlap = data["overlap"]
            preutter = data["preutter"]
            consonant = data["consonant"]
            cutoff = data["cutoff"]
            
            # Verificar arquivo existe
            if check_files and self.voicebank_dir:
                audio_path = self.voicebank_dir / filename
                if not audio_path.exists():
                    issues.append(ValidationIssue(
                        severity="error",
                        message=f"Arquivo não encontrado: {filename}",
                        row=row,
                        alias=alias,
                        field="filename"
                    ))
            
            # Verificar alias vazio
            if check_empty and not alias.strip():
                issues.append(ValidationIssue(
                    severity="warning",
                    message="Alias vazio",
                    row=row,
                    alias=alias or "(vazio)",
                    field="alias"
                ))
            
            # Verificar offset negativo
            if check_negative and offset < 0:
                issues.append(ValidationIssue(
                    severity="error",
                    message=f"Offset negativo: {offset}ms",
                    row=row,
                    alias=alias,
                    field="offset",
                    suggested_fix=0.0
                ))
            
            # Verificar preutter negativo
            if check_negative and preutter < 0:
                issues.append(ValidationIssue(
                    severity="error",
                    message=f"Preutter negativo: {preutter}ms",
                    row=row,
                    alias=alias,
                    field="preutter",
                    suggested_fix=0.0
                ))
            
            # Verificar consonant negativo
            if check_negative and consonant < 0:
                issues.append(ValidationIssue(
                    severity="error",
                    message=f"Consonant negativo: {consonant}ms",
                    row=row,
                    alias=alias,
                    field="consonant",
                    suggested_fix=0.0
                ))
            
            # Verificar overlap maior que preutter (pode causar problemas)
            if check_overlap and overlap > preutter and preutter > 0:
                issues.append(ValidationIssue(
                    severity="warning",
                    message=f"Overlap ({overlap}ms) maior que Preutter ({preutter}ms)",
                    row=row,
                    alias=alias,
                    field="overlap"
                ))
            
            # Verificar consonant menor que preutter
            if check_consonant and consonant < preutter and consonant > 0:
                issues.append(ValidationIssue(
                    severity="info",
                    message=f"Consonant ({consonant}ms) menor que Preutter ({preutter}ms)",
                    row=row,
                    alias=alias,
                    field="consonant"
                ))
            
            # Verificar cutoff resulta em duração negativa
            if check_cutoff and cutoff < 0:
                # Cutoff negativo: duração = offset - cutoff
                duration = offset - cutoff
                if duration < preutter:
                    issues.append(ValidationIssue(
                        severity="warning",
                        message=f"Cutoff resulta em duração ({duration}ms) menor que Preutter ({preutter}ms)",
                        row=row,
                        alias=alias,
                        field="cutoff"
                    ))
        
        return PluginResult(
            success=True,
            message=f"Encontrados {len(issues)} problemas",
            data=issues,
            changes_made=0
        )
