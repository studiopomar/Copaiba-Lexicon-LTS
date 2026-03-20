# plugins/batch_rename.py
"""
Plugin: Renomear em Massa
Renomeia múltiplos aliases com padrões flexíveis.
"""

from typing import Optional, List, Tuple
import re

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QCheckBox, QGroupBox, QRadioButton, QButtonGroup,
    QTableWidget, QTableWidgetItem, QAbstractItemView, QComboBox,
    QMessageBox, QSpinBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor

from .base_plugin import BasePlugin, PluginResult, PluginCategory


class BatchRenameDialog(QDialog):
    """Diálogo do Renomear em Massa"""
    
    def __init__(self, plugin: 'BatchRenamePlugin', parent=None):
        super().__init__(parent)
        self.plugin = plugin
        self.preview_data: List[Tuple[int, str, str]] = []  # (row, old, new)
        self._setup_ui()
    
    def _setup_ui(self):
        self.setWindowTitle("Renomear em Massa")
        self.setMinimumSize(600, 500)
        
        layout = QVBoxLayout(self)
        
        # Escopo
        scope_group = QGroupBox("Aplicar a")
        scope_layout = QHBoxLayout(scope_group)
        
        self.radio_selected = QRadioButton("Aliases selecionados")
        self.radio_all = QRadioButton("Todos os aliases")
        self.radio_selected.setChecked(True)
        
        scope_layout.addWidget(self.radio_selected)
        scope_layout.addWidget(self.radio_all)
        scope_layout.addStretch()
        layout.addWidget(scope_group)
        
        # Modo de renomeação
        mode_group = QGroupBox("Modo de Renomeação")
        mode_layout = QVBoxLayout(mode_group)
        
        self.mode_group = QButtonGroup(self)
        
        # Buscar e substituir
        self.radio_replace = QRadioButton("Buscar e substituir")
        self.radio_replace.setChecked(True)
        self.mode_group.addButton(self.radio_replace, 0)
        mode_layout.addWidget(self.radio_replace)
        
        replace_layout = QHBoxLayout()
        replace_layout.addWidget(QLabel("Buscar:"))
        self.txt_search = QLineEdit()
        self.txt_search.setPlaceholderText("Texto a buscar")
        self.txt_search.textChanged.connect(self._update_preview)
        replace_layout.addWidget(self.txt_search)
        replace_layout.addWidget(QLabel("Substituir:"))
        self.txt_replace = QLineEdit()
        self.txt_replace.setPlaceholderText("Texto de substituição")
        self.txt_replace.textChanged.connect(self._update_preview)
        replace_layout.addWidget(self.txt_replace)
        mode_layout.addLayout(replace_layout)
        
        self.chk_regex = QCheckBox("Usar expressão regular")
        self.chk_regex.stateChanged.connect(self._update_preview)
        mode_layout.addWidget(self.chk_regex)
        
        self.chk_case_sensitive = QCheckBox("Diferencia maiúsculas/minúsculas")
        self.chk_case_sensitive.setChecked(True)
        self.chk_case_sensitive.stateChanged.connect(self._update_preview)
        mode_layout.addWidget(self.chk_case_sensitive)
        
        mode_layout.addWidget(QLabel(""))  # Espaçador
        
        # Prefixo/Sufixo
        self.radio_affix = QRadioButton("Adicionar prefixo/sufixo")
        self.mode_group.addButton(self.radio_affix, 1)
        mode_layout.addWidget(self.radio_affix)
        
        affix_layout = QHBoxLayout()
        affix_layout.addWidget(QLabel("Prefixo:"))
        self.txt_prefix = QLineEdit()
        self.txt_prefix.textChanged.connect(self._update_preview)
        affix_layout.addWidget(self.txt_prefix)
        affix_layout.addWidget(QLabel("Sufixo:"))
        self.txt_suffix = QLineEdit()
        self.txt_suffix.textChanged.connect(self._update_preview)
        affix_layout.addWidget(self.txt_suffix)
        mode_layout.addLayout(affix_layout)
        
        mode_layout.addWidget(QLabel(""))  # Espaçador
        
        # Transformação
        self.radio_transform = QRadioButton("Transformação de texto")
        self.mode_group.addButton(self.radio_transform, 2)
        mode_layout.addWidget(self.radio_transform)
        
        transform_layout = QHBoxLayout()
        transform_layout.addWidget(QLabel("Transformar para:"))
        self.combo_transform = QComboBox()
        self.combo_transform.addItems([
            "minúsculas",
            "MAIÚSCULAS", 
            "Primeira Maiúscula",
            "Primeira de cada palavra"
        ])
        self.combo_transform.currentIndexChanged.connect(self._update_preview)
        transform_layout.addWidget(self.combo_transform)
        transform_layout.addStretch()
        mode_layout.addLayout(transform_layout)
        
        mode_layout.addWidget(QLabel(""))  # Espaçador
        
        # Numeração
        self.radio_number = QRadioButton("Numeração sequencial")
        self.mode_group.addButton(self.radio_number, 3)
        mode_layout.addWidget(self.radio_number)
        
        num_layout = QHBoxLayout()
        num_layout.addWidget(QLabel("Padrão:"))
        self.txt_num_pattern = QLineEdit("{alias}_{n}")
        self.txt_num_pattern.setToolTip("{alias} = nome original, {n} = número")
        self.txt_num_pattern.textChanged.connect(self._update_preview)
        num_layout.addWidget(self.txt_num_pattern)
        num_layout.addWidget(QLabel("Início:"))
        self.spin_start = QSpinBox()
        self.spin_start.setRange(0, 9999)
        self.spin_start.setValue(1)
        self.spin_start.valueChanged.connect(self._update_preview)
        num_layout.addWidget(self.spin_start)
        mode_layout.addLayout(num_layout)
        
        layout.addWidget(mode_group)
        
        # Conectar mudança de modo
        self.mode_group.buttonClicked.connect(self._update_preview)
        
        # Preview
        preview_group = QGroupBox("Preview das Alterações")
        preview_layout = QVBoxLayout(preview_group)
        
        self.preview_table = QTableWidget()
        self.preview_table.setColumnCount(3)
        self.preview_table.setHorizontalHeaderLabels(["Linha", "Original", "Novo"])
        self.preview_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        preview_layout.addWidget(self.preview_table)
        
        self.preview_count = QLabel("")
        preview_layout.addWidget(self.preview_count)
        
        layout.addWidget(preview_group)
        
        # Botões
        buttons_layout = QHBoxLayout()
        
        btn_apply = QPushButton("✏️ Aplicar Renomeação")
        btn_apply.clicked.connect(self._apply)
        
        btn_close = QPushButton("Fechar")
        btn_close.clicked.connect(self.close)
        
        buttons_layout.addWidget(btn_apply)
        buttons_layout.addStretch()
        buttons_layout.addWidget(btn_close)
        layout.addLayout(buttons_layout)
        
        # Atualizar preview inicial
        self._update_preview()
    
    def _get_target_rows(self) -> List[int]:
        """Retorna as linhas alvo baseado no escopo selecionado"""
        if self.radio_selected.isChecked():
            rows = self.plugin.get_selected_rows()
            if not rows:
                return self.plugin.get_all_rows()
            return rows
        return self.plugin.get_all_rows()
    
    def _update_preview(self):
        """Atualiza o preview das renomeações"""
        rows = self._get_target_rows()
        mode = self.mode_group.checkedId()
        
        self.preview_data = []
        
        for row in rows:
            data = self.plugin.get_alias_data(row)
            old_alias = data["alias"]
            new_alias = old_alias
            
            if mode == 0:  # Buscar e substituir
                new_alias = self._apply_replace(old_alias)
            elif mode == 1:  # Prefixo/Sufixo
                new_alias = self._apply_affix(old_alias)
            elif mode == 2:  # Transformação
                new_alias = self._apply_transform(old_alias)
            elif mode == 3:  # Numeração
                n = self.spin_start.value() + len(self.preview_data)
                new_alias = self._apply_numbering(old_alias, n)
            
            if new_alias != old_alias:
                self.preview_data.append((row, old_alias, new_alias))
        
        # Atualizar tabela
        self.preview_table.setRowCount(len(self.preview_data))
        for i, (row, old, new) in enumerate(self.preview_data):
            self.preview_table.setItem(i, 0, QTableWidgetItem(str(row + 1)))
            self.preview_table.setItem(i, 1, QTableWidgetItem(old))
            
            new_item = QTableWidgetItem(new)
            new_item.setBackground(QColor(200, 255, 200))
            self.preview_table.setItem(i, 2, new_item)
        
        self.preview_table.resizeColumnsToContents()
        self.preview_count.setText(f"📝 {len(self.preview_data)} alias(es) serão modificados")
    
    def _apply_replace(self, alias: str) -> str:
        """Aplica buscar e substituir"""
        search = self.txt_search.text()
        replace = self.txt_replace.text()
        
        if not search:
            return alias
        
        try:
            if self.chk_regex.isChecked():
                flags = 0 if self.chk_case_sensitive.isChecked() else re.IGNORECASE
                return re.sub(search, replace, alias, flags=flags)
            else:
                if self.chk_case_sensitive.isChecked():
                    return alias.replace(search, replace)
                else:
                    # Case insensitive replace
                    pattern = re.compile(re.escape(search), re.IGNORECASE)
                    return pattern.sub(replace, alias)
        except re.error:
            return alias
    
    def _apply_affix(self, alias: str) -> str:
        """Aplica prefixo e sufixo"""
        prefix = self.txt_prefix.text()
        suffix = self.txt_suffix.text()
        return f"{prefix}{alias}{suffix}"
    
    def _apply_transform(self, alias: str) -> str:
        """Aplica transformação de texto"""
        transform = self.combo_transform.currentIndex()
        
        if transform == 0:
            return alias.lower()
        elif transform == 1:
            return alias.upper()
        elif transform == 2:
            return alias.capitalize()
        elif transform == 3:
            return alias.title()
        return alias
    
    def _apply_numbering(self, alias: str, n: int) -> str:
        """Aplica numeração sequencial"""
        pattern = self.txt_num_pattern.text()
        return pattern.replace("{alias}", alias).replace("{n}", str(n))
    
    def _apply(self):
        """Aplica as renomeações"""
        if not self.preview_data:
            QMessageBox.information(self, "Info", "Nenhuma alteração a aplicar.")
            return
        
        reply = QMessageBox.question(
            self, "Confirmar Renomeação",
            f"Deseja renomear {len(self.preview_data)} alias(es)?\n\n"
            "Esta ação pode ser desfeita com Ctrl+Z.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        # Aplicar renomeações
        for row, old, new in self.preview_data:
            self.plugin.set_alias_data(row, "alias", new)
        
        self.plugin.mark_dirty()
        self.plugin.show_message(f"Renomeados {len(self.preview_data)} alias(es)")
        
        # Atualizar preview
        self._update_preview()


class BatchRenamePlugin(BasePlugin):
    """Plugin para renomear aliases em massa"""
    
    NAME = "Enxertia - Renomear em Massa"
    DESCRIPTION = "Renomeia múltiplos aliases com padrões flexíveis"
    CATEGORY = PluginCategory.MANAGEMENT
    VERSION = "1.0.0"
    
    def get_dialog(self) -> Optional[QDialog]:
        return BatchRenameDialog(self, self.main_window)
    
    def execute(self, **kwargs) -> PluginResult:
        """Este plugin usa o diálogo para execução interativa"""
        return PluginResult(
            success=True,
            message="Use o diálogo para renomear aliases"
        )
