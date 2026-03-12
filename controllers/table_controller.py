# controllers/table_controller.py
"""
Controller de edição e navegação da tabela de aliases.
Extraído de main.py para melhorar modularidade.
"""

from __future__ import annotations
from typing import TYPE_CHECKING, Union, List

from PySide6.QtWidgets import QTableWidgetItem, QInputDialog, QMessageBox
from PySide6.QtCore import Qt

if TYPE_CHECKING:
    from main import MainWindow, CellEdit, RowEdit


class TableController:
    """
    Gerencia operações de edição na tabela de aliases.
    Recebe referência ao MainWindow para acessar widgets e estado.
    """

    def __init__(self, main_window: 'MainWindow'):
        self.mw = main_window

    # ============================================================
    # Copy / Paste
    # ============================================================

    def copy_selection(self) -> None:
        """Copia células selecionadas para o clipboard interno."""
        mw = self.mw
        selection = mw.table.selectedItems()
        if not selection:
            return

        items_by_position = {}
        cols_used = set()
        for item in selection:
            row, col = item.row(), item.column()
            if row not in items_by_position:
                items_by_position[row] = {}
            items_by_position[row][col] = item.text()
            cols_used.add(col)

        if items_by_position:
            min_row = min(items_by_position.keys())
            max_row = max(items_by_position.keys())
            min_col = min(cols_used)
            max_col = max(cols_used)

            mw._clipboard_data = []
            mw._clipboard_cols = list(range(min_col, max_col + 1))

            for r in range(min_row, max_row + 1):
                row_data = []
                for c in range(min_col, max_col + 1):
                    if r in items_by_position and c in items_by_position[r]:
                        row_data.append(items_by_position[r][c])
                    else:
                        row_data.append("")
                mw._clipboard_data.append(row_data)

            mw.statusBar().showMessage(f"Copiadas {len(selection)} células", 2000)

    def paste_selection(self) -> None:
        """Cola dados do clipboard nas células selecionadas."""
        mw = self.mw
        if not mw._clipboard_data:
            mw.statusBar().showMessage("Clipboard vazio", 2000)
            return

        selection = mw.table.selectedItems()
        if not selection:
            return

        selected_rows = sorted(set(item.row() for item in selection))
        selected_cols = sorted(set(item.column() for item in selection))

        from main import CellEdit
        edits: list[CellEdit] = []
        mw._updating_from_code = True

        try:
            if len(mw._clipboard_data) == 1 and len(mw._clipboard_data[0]) == 1:
                # Colar valor único em múltiplas células
                value = mw._clipboard_data[0][0]
                for item in selection:
                    row, col = item.row(), item.column()
                    if col == mw.COL_FAV:
                        continue
                    old_val = item.text()
                    new_val = value
                    if col in [mw.COL_PREUTTER, mw.COL_CONSONANT]:
                        try:
                            num_val = int(round(float(new_val)))
                            if num_val < 0:
                                new_val = "0"
                        except ValueError:
                            continue
                    if old_val != new_val:
                        edits.append(CellEdit(row, col, old_val, new_val))
                        item.setText(new_val)
                        item.setData(Qt.ItemDataRole.UserRole, new_val)
            else:
                # Colar matriz de valores
                clipboard_width = len(mw._clipboard_data[0]) if mw._clipboard_data else 0
                clipboard_height = len(mw._clipboard_data)

                for idx, target_row in enumerate(selected_rows):
                    clipboard_row_idx = idx % clipboard_height
                    clipboard_row = mw._clipboard_data[clipboard_row_idx]

                    for col_idx, target_col in enumerate(selected_cols):
                        if target_col == mw.COL_FAV:
                            continue
                        clipboard_col_idx = col_idx % clipboard_width
                        value = clipboard_row[clipboard_col_idx] if clipboard_col_idx < len(clipboard_row) else ""
                        if not value:
                            continue

                        item = mw.table.item(target_row, target_col)
                        if item is None:
                            continue

                        old_val = item.text()
                        new_val = value
                        if target_col in [mw.COL_PREUTTER, mw.COL_CONSONANT]:
                            try:
                                num_val = int(round(float(new_val)))
                                if num_val < 0:
                                    new_val = "0"
                            except ValueError:
                                continue

                        if old_val != new_val:
                            edits.append(CellEdit(target_row, target_col, old_val, new_val))
                            item.setText(new_val)
                            item.setData(Qt.ItemDataRole.UserRole, new_val)
        finally:
            mw._updating_from_code = False

        if edits:
            mw._push_undo(edits)
            mw.statusBar().showMessage(f"Colado em {len(edits)} células", 2000)
            mw._load_waveform_for_current_row()

    # ============================================================
    # Presets
    # ============================================================

    def apply_preset(self, preset_key: str) -> None:
        """Aplica um preset aos aliases selecionados."""
        mw = self.mw
        if not mw.preset_config.is_active():
            mw.statusBar().showMessage("Presets estão desativados nas configurações", 2000)
            return

        selected_rows = sorted(set(item.row() for item in mw.table.selectedItems()))
        if not selected_rows:
            mw.statusBar().showMessage("Nenhum alias selecionado", 2000)
            return

        preset = mw.preset_config.get_preset(preset_key)
        from main import CellEdit
        edits = []
        mw._updating_from_code = True

        try:
            for row in selected_rows:
                # Overlap
                item = mw.table.item(row, mw.COL_OVERLAP)
                if item:
                    old_val = item.text()
                    new_val = str(preset.overlap)
                    if old_val != new_val:
                        edits.append(CellEdit(row, mw.COL_OVERLAP, old_val, new_val))
                        item.setText(new_val)
                        item.setData(Qt.ItemDataRole.UserRole, new_val)

                # Preutter
                item = mw.table.item(row, mw.COL_PREUTTER)
                if item:
                    old_val = item.text()
                    new_val = str(preset.preutter)
                    if old_val != new_val:
                        edits.append(CellEdit(row, mw.COL_PREUTTER, old_val, new_val))
                        item.setText(new_val)
                        item.setData(Qt.ItemDataRole.UserRole, new_val)

                # Consonant
                item = mw.table.item(row, mw.COL_CONSONANT)
                if item:
                    old_val = item.text()
                    new_val = str(preset.consonant)
                    if old_val != new_val:
                        edits.append(CellEdit(row, mw.COL_CONSONANT, old_val, new_val))
                        item.setText(new_val)
                        item.setData(Qt.ItemDataRole.UserRole, new_val)

                # Cutoff
                item = mw.table.item(row, mw.COL_CUTOFF)
                if item:
                    old_val = item.text()
                    new_val = str(preset.cutoff)
                    if old_val != new_val:
                        edits.append(CellEdit(row, mw.COL_CUTOFF, old_val, new_val))
                        item.setText(new_val)
                        item.setData(Qt.ItemDataRole.UserRole, new_val)
        finally:
            mw._updating_from_code = False

        if edits:
            mw._push_undo(edits)
            mw._dirty = True
            mw._update_title()
            mw._load_waveform_for_current_row()
            mw.statusBar().showMessage(f"Preset {preset_key.upper()} aplicado a {len(selected_rows)} alias(es)", 2000)

    # ============================================================
    # Undo / Redo
    # ============================================================

    def undo(self) -> None:
        """Desfaz a última operação."""
        mw = self.mw
        if not mw._undo_stack:
            return

        edit = mw._undo_stack.pop()
        mw._in_undo_redo = True
        mw._updating_from_code = True

        try:
            from main import RowEdit
            if isinstance(edit, list):
                for cell_edit in reversed(edit):
                    item = mw.table.item(cell_edit.row, cell_edit.col)
                    if item:
                        item.setText(cell_edit.old)
                        item.setData(Qt.ItemDataRole.UserRole, cell_edit.old)
                mw._redo_stack.append(edit)

            elif isinstance(edit, RowEdit):
                if edit.is_insert:
                    mw.table.removeRow(edit.row)
                else:
                    mw.table.insertRow(edit.row)
                    for col, value in enumerate(edit.data):
                        mw.table.setItem(edit.row, col, QTableWidgetItem(value))
                mw._redo_stack.append(edit)
        finally:
            mw._in_undo_redo = False
            mw._updating_from_code = False

        mw._dirty = True
        mw._update_title()
        mw._update_undo_redo_actions()
        mw._load_waveform_for_current_row()

    def redo(self) -> None:
        """Refaz a última operação desfeita."""
        mw = self.mw
        if not mw._redo_stack:
            return

        edit = mw._redo_stack.pop()
        mw._in_undo_redo = True
        mw._updating_from_code = True

        try:
            from main import RowEdit
            if isinstance(edit, list):
                for cell_edit in edit:
                    item = mw.table.item(cell_edit.row, cell_edit.col)
                    if item:
                        item.setText(cell_edit.new)
                        item.setData(Qt.ItemDataRole.UserRole, cell_edit.new)
                mw._undo_stack.append(edit)

            elif isinstance(edit, RowEdit):
                if edit.is_insert:
                    mw.table.insertRow(edit.row)
                    for col, value in enumerate(edit.data):
                        mw.table.setItem(edit.row, col, QTableWidgetItem(value))
                else:
                    mw.table.removeRow(edit.row)
                mw._undo_stack.append(edit)
        finally:
            mw._in_undo_redo = False
            mw._updating_from_code = False

        mw._dirty = True
        mw._update_title()
        mw._update_undo_redo_actions()
        mw._load_waveform_for_current_row()

    # ============================================================
    # Alias Operations
    # ============================================================

    def rename_alias(self) -> None:
        """Renomeia o alias atual."""
        mw = self.mw
        row = mw.table.currentRow()
        if row < 0:
            return

        alias_item = mw.table.item(row, mw.COL_ALIAS)
        if not alias_item:
            return

        old_alias = alias_item.text()
        new_alias, ok = QInputDialog.getText(
            mw, "Renomear Alias", "Novo nome:", text=old_alias
        )

        if ok and new_alias and new_alias != old_alias:
            mw._updating_from_code = True
            alias_item.setText(new_alias)
            alias_item.setData(Qt.ItemDataRole.UserRole, new_alias)
            mw._updating_from_code = False

            from main import CellEdit
            edit = CellEdit(row, mw.COL_ALIAS, old_alias, new_alias)
            mw._push_undo([edit])
            mw._dirty = True
            mw._update_title()
            mw._load_waveform_for_current_row()

    def delete_alias(self) -> None:
        """Exclui o alias atual."""
        mw = self.mw
        row = mw.table.currentRow()
        if row < 0:
            return

        reply = QMessageBox.question(
            mw, "Confirmar Exclusão",
            f"Deseja realmente excluir o alias da linha {row + 1}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            row_data = []
            for col in range(mw.table.columnCount()):
                item = mw.table.item(row, col)
                row_data.append(item.text() if item else "")

            mw.table.removeRow(row)

            from main import RowEdit
            edit = RowEdit(row, row_data, is_insert=False)
            mw._push_undo(edit)
            mw._dirty = True
            mw._update_title()
            mw._load_waveform_for_current_row()

    def duplicate_alias(self) -> None:
        """Duplica o alias atual."""
        mw = self.mw
        row = mw.table.currentRow()
        if row < 0:
            return

        row_data = []
        for col in range(mw.table.columnCount()):
            item = mw.table.item(row, col)
            row_data.append(item.text() if item else "")

        new_row = row + 1
        mw.table.insertRow(new_row)

        mw._updating_from_code = True
        for col, value in enumerate(row_data):
            if col == mw.COL_FAV:
                fav_item = QTableWidgetItem()
                fav_item.setFlags(
                    Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsUserCheckable)
                fav_item.setCheckState(Qt.CheckState.Unchecked)
                mw.table.setItem(new_row, col, fav_item)
            elif col == mw.COL_FILENAME:
                fn_item = QTableWidgetItem(value)
                fn_item.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)
                mw.table.setItem(new_row, col, fn_item)
            else:
                item = QTableWidgetItem(value)
                item.setData(Qt.ItemDataRole.UserRole, value)
                mw.table.setItem(new_row, col, item)
        mw._updating_from_code = False

        alias_item = mw.table.item(new_row, mw.COL_ALIAS)
        if alias_item:
            old_alias = alias_item.text()
            new_alias = self._get_next_numbered_alias(old_alias)
            alias_item.setText(new_alias)

        from main import RowEdit
        edit = RowEdit(new_row, row_data, is_insert=True)
        mw._push_undo(edit)
        mw._dirty = True
        mw._update_title()
        mw.table.setCurrentCell(new_row, mw.COL_ALIAS)

    def _get_next_numbered_alias(self, base_alias: str) -> str:
        """
        Encontra o próximo número disponível para o alias.
        Ex: "da" -> "da 2", "da 2" -> "da 3", etc.
        """
        import re
        mw = self.mw
        
        # Remove número existente do final (ex: "da 2" -> "da")
        match = re.match(r'^(.+?)\s+(\d+)$', base_alias)
        if match:
            base_name = match.group(1)
        else:
            base_name = base_alias
        
        # Encontra todos os aliases existentes que correspondem ao padrão
        existing_numbers = {1}  # O original conta como "1"
        pattern = re.compile(rf'^{re.escape(base_name)}\s+(\d+)$')
        
        for row in range(mw.table.rowCount()):
            item = mw.table.item(row, mw.COL_ALIAS)
            if item:
                alias = item.text()
                # Verifica se é exatamente o alias base (sem número)
                if alias == base_name:
                    existing_numbers.add(1)
                else:
                    # Verifica se corresponde ao padrão "base N"
                    m = pattern.match(alias)
                    if m:
                        existing_numbers.add(int(m.group(1)))
        
        # Encontra o próximo número disponível
        next_num = 2
        while next_num in existing_numbers:
            next_num += 1
        
        return f"{base_name} {next_num}"

    # ============================================================
    # Filter
    # ============================================================

    def filter_table(self, text: str) -> None:
        """Filtra a tabela pelo texto fornecido."""
        mw = self.mw
        for row in range(mw.table.rowCount()):
            should_show = True
            if text.strip():
                alias_item = mw.table.item(row, mw.COL_ALIAS)
                filename_item = mw.table.item(row, mw.COL_FILENAME)

                alias_text = alias_item.text() if alias_item else ""
                filename_text = filename_item.text() if filename_item else ""

                should_show = (text.lower() in alias_text.lower() or
                               text.lower() in filename_text.lower())

            mw.table.setRowHidden(row, not should_show)
