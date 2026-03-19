# plugins/alias_sorter.py
"""
Plugin: Ordenar Aliases
Ordena os aliases da tabela de diferentes formas.
"""

from typing import Optional, List, Tuple
import re

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QRadioButton, QButtonGroup, QGroupBox, QCheckBox, QMessageBox
)
from PySide6.QtCore import Qt

from .base_plugin import BasePlugin, PluginResult, PluginCategory


class AliasSorterDialog(QDialog):
    """Diálogo do Ordenador de Aliases"""
    
    def __init__(self, plugin: 'AliasSorterPlugin', parent=None):
        super().__init__(parent)
        self.plugin = plugin
        self._setup_ui()
    
    def _setup_ui(self):
        self.setWindowTitle("Ordenar Aliases")
        self.setMinimumWidth(400)
        
        layout = QVBoxLayout(self)
        
        # Modo de ordenação
        sort_group = QGroupBox("Modo de Ordenação")
        sort_layout = QVBoxLayout(sort_group)
        
        self.btn_group = QButtonGroup(self)
        
        self.radio_alpha = QRadioButton("Alfabética (A-Z)")
        self.radio_alpha.setChecked(True)
        
        self.radio_alpha_rev = QRadioButton("Alfabética reversa (Z-A)")
        
        self.radio_file = QRadioButton("Por nome do arquivo de áudio")
        
        self.radio_type = QRadioButton("Por tipo de fonema (CV, VCV, VC, VV)")
        
        self.radio_length = QRadioButton("Por comprimento do alias")
        
        self.radio_offset = QRadioButton("Por offset (tempo)")
        
        self.radio_natural = QRadioButton("Ordem natural (a1, a2, a10)")
        self.radio_natural.setToolTip("Ordena números corretamente: a1, a2, a10 em vez de a1, a10, a2")
        
        for i, radio in enumerate([
            self.radio_alpha, self.radio_alpha_rev, self.radio_file,
            self.radio_type, self.radio_length, self.radio_offset, self.radio_natural
        ]):
            self.btn_group.addButton(radio, i)
            sort_layout.addWidget(radio)
        
        layout.addWidget(sort_group)
        
        # Opções adicionais
        options_group = QGroupBox("Opções")
        options_layout = QVBoxLayout(options_group)
        
        self.chk_group_by_file = QCheckBox("Manter agrupado por arquivo")
        self.chk_group_by_file.setToolTip("Ordena dentro de cada grupo de arquivo")
        
        self.chk_completed_first = QCheckBox("Aliases completos primeiro")
        
        options_layout.addWidget(self.chk_group_by_file)
        options_layout.addWidget(self.chk_completed_first)
        layout.addWidget(options_group)
        
        # Botões
        buttons_layout = QHBoxLayout()
        
        btn_preview = QPushButton("Preview")
        btn_preview.clicked.connect(self._preview)
        
        btn_apply = QPushButton("Aplicar Ordenação")
        btn_apply.clicked.connect(self._apply)
        
        btn_close = QPushButton("Fechar")
        btn_close.clicked.connect(self.close)
        
        buttons_layout.addWidget(btn_preview)
        buttons_layout.addWidget(btn_apply)
        buttons_layout.addWidget(btn_close)
        layout.addLayout(buttons_layout)
        
        # Info
        self.info_label = QLabel("")
        layout.addWidget(self.info_label)
    
    def _get_sort_mode(self) -> str:
        modes = ["alpha", "alpha_rev", "file", "type", "length", "offset", "natural"]
        btn_id = self.btn_group.checkedId()
        return modes[btn_id] if 0 <= btn_id < len(modes) else "alpha"
    
    def _preview(self):
        """Mostra preview da ordenação"""
        result = self.plugin.execute(
            mode=self._get_sort_mode(),
            group_by_file=self.chk_group_by_file.isChecked(),
            completed_first=self.chk_completed_first.isChecked(),
            preview_only=True
        )
        
        if result.success:
            # Mostrar primeiros 10 aliases na nova ordem
            new_order = result.data[:10] if result.data else []
            preview_text = "\n".join([f"{i+1}. {alias}" for i, alias in enumerate(new_order)])
            if len(result.data) > 10:
                preview_text += f"\n... e mais {len(result.data) - 10} aliases"
            
            self.info_label.setText(f"Preview:\n{preview_text}")
    
    def _apply(self):
        """Aplica a ordenação"""
        reply = QMessageBox.question(
            self, "Confirmar Ordenação",
            "Deseja aplicar a ordenação?\nEsta ação pode ser desfeita com Ctrl+Z.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        result = self.plugin.execute(
            mode=self._get_sort_mode(),
            group_by_file=self.chk_group_by_file.isChecked(),
            completed_first=self.chk_completed_first.isChecked(),
            preview_only=False
        )
        
        if result.success:
            self.plugin.show_message(f"Ordenados {result.changes_made} aliases")
            self.info_label.setText(f"✅ {result.message}")
        else:
            self.info_label.setText(f"❌ {result.message}")


class AliasSorterPlugin(BasePlugin):
    """Plugin para ordenar aliases"""
    
    NAME = "Seleção - Ordenar Aliases"
    DESCRIPTION = "Ordena os aliases da tabela de diferentes formas"
    CATEGORY = PluginCategory.MANAGEMENT
    VERSION = "1.0.0"
    
    def get_dialog(self) -> Optional[QDialog]:
        return AliasSorterDialog(self, self.main_window)
    
    def execute(self, mode="alpha", group_by_file=False, 
                completed_first=False, preview_only=False, **kwargs) -> PluginResult:
        """
        Executa a ordenação.
        
        Args:
            mode: Modo de ordenação (alpha, alpha_rev, file, type, length, offset, natural)
            group_by_file: Manter agrupados por arquivo
            completed_first: Aliases completos primeiro
            preview_only: Apenas retornar nova ordem sem aplicar
        """
        rows = self.get_all_rows()
        
        if not rows:
            return PluginResult(False, "Nenhum alias na tabela", [])
        
        # Coletar dados
        row_data = []
        for row in rows:
            data = self.get_alias_data(row)
            # Verificar se está completo (coluna 0 marcada)
            is_complete = False
            item = self.table.item(row, 0)
            if item and item.text() == "✓":
                is_complete = True
            data["is_complete"] = is_complete
            data["original_row"] = row
            row_data.append(data)
        
        # Função de ordenação natural
        def natural_sort_key(s):
            return [int(c) if c.isdigit() else c.lower() for c in re.split(r'(\d+)', s)]
        
        # Detectar tipo de fonema
        def detect_phoneme_type(alias: str) -> int:
            alias_lower = alias.lower().strip()
            
            # VCV: vogal + consoante + vogal (ex: "a ka", "i ki")
            if re.match(r'^[aiueo]\s*[^aiueo\s]+\s*[aiueo]', alias_lower):
                return 1  # VCV
            
            # VV: vogal + vogal (ex: "a a", "a i")
            if re.match(r'^[aiueo]\s+[aiueo]$', alias_lower):
                return 2  # VV
            
            # VC: vogal + consoante (ex: "a k", "i s")
            if re.match(r'^[aiueo]\s+[^aiueo\s]+$', alias_lower):
                return 3  # VC
            
            # CV: consoante + vogal (ex: "ka", "ki")
            if re.match(r'^[^aiueo\s]*[aiueo]$', alias_lower):
                return 0  # CV
            
            return 4  # Outros
        
        # Criar chave de ordenação
        def sort_key(item):
            keys = []
            
            # Completos primeiro/último
            if completed_first:
                keys.append(0 if item["is_complete"] else 1)
            
            # Agrupar por arquivo
            if group_by_file:
                keys.append(item["filename"])
            
            # Modo principal
            alias = item["alias"]
            if mode == "alpha":
                keys.append(alias.lower())
            elif mode == "alpha_rev":
                keys.append(alias.lower())  # Será revertido depois
            elif mode == "file":
                keys.append(item["filename"])
                keys.append(item["offset"])
            elif mode == "type":
                keys.append(detect_phoneme_type(alias))
                keys.append(alias.lower())
            elif mode == "length":
                keys.append(len(alias))
                keys.append(alias.lower())
            elif mode == "offset":
                keys.append(item["filename"])
                keys.append(item["offset"])
            elif mode == "natural":
                keys.append(natural_sort_key(alias))
            else:
                keys.append(alias.lower())
            
            return tuple(keys)
        
        # Ordenar
        sorted_data = sorted(row_data, key=sort_key, reverse=(mode == "alpha_rev"))
        
        # Preview: retornar lista de aliases na nova ordem
        if preview_only:
            return PluginResult(
                success=True,
                message="Preview gerado",
                data=[d["alias"] for d in sorted_data]
            )
        
        # Aplicar ordenação na tabela
        # Salvar dados de todas as linhas
        all_row_contents = []
        for data in sorted_data:
            row = data["original_row"]
            row_content = []
            for col in range(self.table.columnCount()):
                item = self.table.item(row, col)
                row_content.append(item.text() if item else "")
            all_row_contents.append(row_content)
        
        # Reescrever tabela na nova ordem
        self.main_window._updating_from_code = True
        for new_row, content in enumerate(all_row_contents):
            for col, text in enumerate(content):
                item = self.table.item(new_row, col)
                if item:
                    item.setText(text)
        self.main_window._updating_from_code = False
        
        self.mark_dirty()
        
        return PluginResult(
            success=True,
            message=f"Aliases ordenados por {mode}",
            changes_made=len(sorted_data)
        )
