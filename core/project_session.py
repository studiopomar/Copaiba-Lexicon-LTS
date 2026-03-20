from typing import Optional, List, Dict, Union
from pathlib import Path

from PySide6.QtWidgets import QWidget, QTableWidget, QLineEdit, QVBoxLayout
from PySide6.QtCore import Qt

from copaiba import OtoFile
from waveform_widget import WaveformWidget
from core.types import CellEdit, RowEdit

class ProjectSession:
    """
    Encapsulates the state and UI elements for a single opened oto.ini (voicebank).
    Allows Copaiba to support multiple tabs.
    """
    
    def __init__(self, main_window):
        self.mw = main_window
        
        self.oto = OtoFile()
        self.current_path: Optional[Path] = None
        self.voicebank_dir: Optional[Path] = None
        
        self.dirty: bool = False
        self.undo_stack: List[Union[List[CellEdit], RowEdit]] = []
        self.redo_stack: List[Union[List[CellEdit], RowEdit]] = []
        
        self.completed_aliases: set[str] = set()
        self.notes_data: Dict[str, str] = {}
        
        self.last_selected_row: Optional[int] = None
        self.last_shift_click_row: Optional[int] = None
        
        self.clipboard_data: List[List[str]] = []
        self.clipboard_cols: List[int] = []
        
        # UI Elements specific to this session
        self.table = QTableWidget(main_window)
        self.filter_bar = QLineEdit(main_window)
        self.waveform = WaveformWidget(main_window)
        
        # Container widget for table and filter_bar (used in QStackedWidget)
        self.table_container = QWidget()
        layout = QVBoxLayout(self.table_container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.filter_bar)
        layout.addWidget(self.table)
        
        self._setup_ui_elements()
        
    def _setup_ui_elements(self):
        # Configure Table
        self.table.setColumnCount(len(self.mw.COLUMN_HEADERS))
        self.table.setHorizontalHeaderLabels(self.mw.COLUMN_HEADERS)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.ExtendedSelection)
        self.table.setEditTriggers(
            QTableWidget.EditTrigger.DoubleClicked |
            QTableWidget.EditTrigger.SelectedClicked |
            QTableWidget.EditTrigger.EditKeyPressed
        )
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setShowGrid(True)
        
        self.table.setColumnWidth(self.mw.COL_FAV, 30)
        self.table.setColumnWidth(self.mw.COL_FILENAME, 220)
        self.table.setColumnWidth(self.mw.COL_ALIAS, 120)
        self.table.setColumnWidth(self.mw.COL_NOTES, 150)
        
        self.table.setDragDropMode(QTableWidget.DragDropMode.NoDragDrop)
        self.table.setStyleSheet("""
            QTableWidget::item:selected { background-color: #ffe9a3; color: black; }
            QTableWidget::item { padding: 2px; }
        """)
        
        self.table.setFont(self.mw.table.font() if hasattr(self.mw, 'table') and isinstance(self.mw.table, QTableWidget) else self.mw.font())
        
        # Connect signals (routed through main window to preserve existing logic)
        self.table.itemChanged.connect(self.mw._on_item_changed)
        self.table.itemSelectionChanged.connect(self.mw._on_selection_changed)
        self.table.currentCellChanged.connect(self.mw._on_current_cell_changed)
        self.table.installEventFilter(self.mw)
        self.table.mousePressEvent = self.mw._table_mouse_press_event
        self.table.mouseReleaseEvent = self.mw._table_mouse_release_event
        
        # Filter bar
        self.filter_bar.setPlaceholderText("Filtrar aliases...")
        self.filter_bar.textChanged.connect(self.mw._filter_table)
        
        # Waveform
        self.waveform.set_snap_enabled(False)
        self.waveform.set_edit_callback(self.mw._entry_edited_from_waveform)
        self.waveform.aliasStepRequested.connect(self.mw._step_alias)
        self.waveform.set_key_handler(self.mw._handle_waveform_key)
        self.waveform.playSegmentRequested.connect(self.mw._on_play_segment_requested)
