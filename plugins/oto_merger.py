import sys
from pathlib import Path
from typing import Optional, Dict, List, Tuple
from dataclasses import dataclass

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QFileDialog,
    QCheckBox, QMessageBox, QAbstractItemView, QWidget
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QColor, QBrush, QIcon

from .base_plugin import BasePlugin, PluginResult, PluginCategory

@dataclass
class OtoEntry:
    filename: str
    alias: str
    offset: float
    consonant: float
    cutoff: float
    preutter: float
    overlap: float

    @staticmethod
    def from_line(line: str) -> Optional['OtoEntry']:
        try:
            parts = line.strip().split('=')
            if len(parts) < 2: return None
            
            lhs = parts[0] # filename
            rhs = parts[1] # alias,offset,consonant,cutoff,preutter,overlap
            
            params = rhs.split(',')
            
            alias = params[0]
            if not alias: alias = ""
            
            def safe_float(idx):
                if idx < len(params) and params[idx]:
                    return float(params[idx])
                return 0.0

            return OtoEntry(
                filename=lhs,
                alias=alias,
                offset=safe_float(1),
                consonant=safe_float(2),
                cutoff=safe_float(3),
                preutter=safe_float(4),
                overlap=safe_float(5)
            )
        except:
            return None

class OtoMergerDialog(QDialog):
    def __init__(self, plugin: 'OtoMergerPlugin', parent=None):
        super().__init__(parent)
        self.plugin = plugin
        self.new_entries: List[OtoEntry] = []
        self._setup_ui()
        
    def _setup_ui(self):
        self.setWindowTitle("Mesclar oto.ini (Plugin de Merge)")
        self.resize(900, 600)
        
        layout = QVBoxLayout(self)
        
        # Header
        header_layout = QHBoxLayout()
        self.lbl_file = QLabel("Arquivo: (nenhum selecionado)")
        self.btn_load = QPushButton("Abrir Arquivo...")
        self.btn_load.clicked.connect(self._load_file)
        
        header_layout.addWidget(self.lbl_file)
        header_layout.addStretch()
        header_layout.addWidget(self.btn_load)
        layout.addLayout(header_layout)
        
        # Options
        opts_layout = QHBoxLayout()
        self.chk_rounding = QCheckBox("Ignorar diferenças de arredondamento (< 0.01)")
        self.chk_rounding.setChecked(True)
        opts_layout.addWidget(self.chk_rounding)
        opts_layout.addStretch()
        layout.addLayout(opts_layout)
        
        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["", "Status", "Arquivo", "Alias", "Diferenças"])
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        layout.addWidget(self.table)
        
        # Bottom controls
        bottom_layout = QHBoxLayout()
        
        btn_select_all = QPushButton("Selecionar Tudo")
        btn_select_all.clicked.connect(self._select_all)
        btn_deselect_all = QPushButton("Desmarcar Tudo")
        btn_deselect_all.clicked.connect(self._deselect_all)
        
        bottom_layout.addWidget(btn_select_all)
        bottom_layout.addWidget(btn_deselect_all)
        bottom_layout.addStretch()
        
        self.btn_merge = QPushButton("Mesclar Selecionados")
        self.btn_merge.clicked.connect(self._do_merge)
        self.btn_merge.setEnabled(False)
        
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.clicked.connect(self.reject)
        
        bottom_layout.addWidget(self.btn_merge)
        bottom_layout.addWidget(btn_cancel)
        
        layout.addLayout(bottom_layout)
        
    def _load_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Abrir oto.ini", "", "Oto Files (*.ini);;All Files (*.*)")
        if not path:
            return
            
        self.lbl_file.setText(f"Arquivo: {Path(path).name}")
        self._analyze_file(path)
        
    def _analyze_file(self, path: str):
        try:
            with open(path, 'r', encoding='utf-8') as f: # Tenta utf-8 primeiro
                lines = f.readlines()
        except UnicodeDecodeError:
             try:
                with open(path, 'r', encoding='shift_jis') as f: # Fallback para JP
                    lines = f.readlines()
             except:
                with open(path, 'r', encoding='latin-1') as f: # Fallback
                    lines = f.readlines()

        external_entries = []
        for line in lines:
            entry = OtoEntry.from_line(line)
            if entry:
                external_entries.append(entry)
                
        # Existing data (filename + alias key)
        existing_data = {}
        for row in range(self.plugin.table.rowCount()):
            data = self.plugin.get_alias_data(row)
            key = (data['filename'], data['alias'])
            existing_data[key] = data
            
        # Compare
        self.table.setRowCount(0)
        self.new_entries = []
        
        row_idx = 0
        updates_count = 0
        new_count = 0
        
        for ext in external_entries:
            key = (ext.filename, ext.alias)
            
            status = ""
            diff_text = ""
            is_diff = False
            
            if key not in existing_data:
                status = "NOVO"
                diff_text = "Novo alias detectado"
                is_diff = True
                new_count += 1
            else:
                # Compare fields
                current = existing_data[key]
                diffs = []
                
                check_fields = ['offset', 'cutoff', 'preutter', 'overlap', 'consonant']
                for field in check_fields:
                    val_curr = current.get(field, 0.0)
                    val_ext = getattr(ext, field)
                    
                    if abs(val_curr - val_ext) > (0.01 if self.chk_rounding.isChecked() else 0.000001):
                        diffs.append(f"{field}: {val_curr} -> {val_ext}")
                
                if diffs:
                    status = "ALTERADO"
                    diff_text = ", ".join(diffs)
                    is_diff = True
                    updates_count += 1
            
            if is_diff:
                self.table.insertRow(row_idx)
                
                # Checkbox
                chk_item = QTableWidgetItem()
                chk_item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
                chk_item.setCheckState(Qt.Checked)
                self.table.setItem(row_idx, 0, chk_item)
                
                # Status
                item_status = QTableWidgetItem(status)
                item_status.setForeground(QBrush(QColor("#4caf50") if status == "NOVO" else QColor("#ff9800")))
                self.table.setItem(row_idx, 1, item_status)
                
                self.table.setItem(row_idx, 2, QTableWidgetItem(ext.filename))
                self.table.setItem(row_idx, 3, QTableWidgetItem(ext.alias))
                self.table.setItem(row_idx, 4, QTableWidgetItem(diff_text))
                
                # Store entry data in hidden role or parallel list
                # Armazenamos o objeto OtoEntry na role UserRole do item de status
                item_status.setData(Qt.UserRole, ext)
                
                row_idx += 1
                
        self.btn_merge.setEnabled(row_idx > 0)
        self.plugin.show_message(f"Análise completa: {new_count} novos, {updates_count} conflitos.")

    def _select_all(self):
        for r in range(self.table.rowCount()):
            self.table.item(r, 0).setCheckState(Qt.Checked)
            
    def _deselect_all(self):
        for r in range(self.table.rowCount()):
            self.table.item(r, 0).setCheckState(Qt.Unchecked)

    def _do_merge(self):
        count = 0
        to_merge = []
        
        for r in range(self.table.rowCount()):
            if self.table.item(r, 0).checkState() == Qt.Checked:
                entry = self.table.item(r, 1).data(Qt.UserRole)
                status = self.table.item(r, 1).text()
                to_merge.append((status, entry))
                
        if not to_merge:
            return

        # Apply changes
        # Para "NOVO", adiciona ao final.
        # Para "ALTERADO", busca e atualiza.
        
        table_widget = self.plugin.table
        
        # Performance optimization: disable updates
        table_widget.setSortingEnabled(False)
        
        # Mapeamento atual para busca rápida se precisar atualizar
        # (na verdade get_alias_data já busca, mas por linha. Precisamos buscar linha por chave?)
        # BasePlugin não tem busca por chave.
        # Vamos iterar para construir mapa (filename, alias) -> row
        existing_map = {}
        for r in range(table_widget.rowCount()):
            fname = table_widget.item(r, 1).text()
            alias = table_widget.item(r, 2).text()
            existing_map[(fname, alias)] = r
            
        added_count = 0
        updated_count = 0
        
        for status, entry in to_merge:
            if status == "NOVO":
                row = table_widget.rowCount()
                table_widget.insertRow(row)
                
                # Checkbox fav
                chk = QTableWidgetItem()
                chk.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
                chk.setCheckState(Qt.Unchecked)
                table_widget.setItem(row, 0, chk)
                
                table_widget.setItem(row, 1, QTableWidgetItem(entry.filename))
                table_widget.setItem(row, 2, QTableWidgetItem(entry.alias))
                table_widget.setItem(row, 3, QTableWidgetItem(str(entry.offset)))
                table_widget.setItem(row, 4, QTableWidgetItem(str(entry.overlap)))
                table_widget.setItem(row, 5, QTableWidgetItem(str(entry.preutter)))
                table_widget.setItem(row, 6, QTableWidgetItem(str(entry.consonant)))
                table_widget.setItem(row, 7, QTableWidgetItem(str(entry.cutoff)))
                
                # New "annotations" col? Defaults to empty
                if table_widget.columnCount() > 8:
                    table_widget.setItem(row, 8, QTableWidgetItem(""))
                
                added_count += 1
                
            elif status == "ALTERADO":
                key = (entry.filename, entry.alias)
                if key in existing_map:
                    row = existing_map[key]
                    table_widget.setItem(row, 3, QTableWidgetItem(str(entry.offset)))
                    table_widget.setItem(row, 4, QTableWidgetItem(str(entry.overlap)))
                    table_widget.setItem(row, 5, QTableWidgetItem(str(entry.preutter)))
                    table_widget.setItem(row, 6, QTableWidgetItem(str(entry.consonant)))
                    table_widget.setItem(row, 7, QTableWidgetItem(str(entry.cutoff)))
                    updated_count += 1
        
        table_widget.setSortingEnabled(True)
        self.plugin.mark_dirty()
        self.plugin.show_message(f"Merge completo: {added_count} adicionados, {updated_count} atualizados.")
        self.accept()


class OtoMergerPlugin(BasePlugin):
    NAME = "Jardineiro - Mesclar OTO"
    DESCRIPTION = "Mescla um arquivo oto.ini externo com o projeto atual."
    CATEGORY = PluginCategory.MANAGEMENT
    VERSION = "1.0.0"
    
    def get_dialog(self) -> Optional[QDialog]:
        return OtoMergerDialog(self, self.main_window)
    
    def execute(self, **kwargs) -> PluginResult:
        return PluginResult(True, "Use o diálogo para mesclar.")
