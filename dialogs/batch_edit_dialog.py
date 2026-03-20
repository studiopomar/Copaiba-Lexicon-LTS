from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QFormLayout, QCheckBox, QDoubleSpinBox, 
    QHBoxLayout, QPushButton
)
from PySide6.QtCore import Qt

class BatchEditDialog(QDialog):
    """Diálogo para edição em lote de múltiplos aliases"""

    def __init__(self, parent=None, selected_count: int = 0):
        super().__init__(parent)
        self.setWindowTitle("Edição em Lote")
        self.setMinimumSize(420, 340)
        self.setStyleSheet("""
            QDialog { background: #1a1a1e; }
            QLabel { color: #e0e0e0; }
            QCheckBox { color: #e0e0e0; }
            QDoubleSpinBox {
                background: #2a2a30;
                color: #e0e0e0;
                border: 1px solid #444;
                border-radius: 4px;
                padding: 4px 8px;
                min-width: 120px;
            }
            QDoubleSpinBox:disabled { color: #666; }
            QPushButton {
                background: #3a3a44;
                color: #e0e0e0;
                border: 1px solid #555;
                border-radius: 4px;
                padding: 6px 20px;
            }
            QPushButton:hover { background: #4a4a55; }
        """)

        self.result_values = {}

        layout = QVBoxLayout(self)

        info_label = QLabel(f"✏️  Editando {selected_count} alias(es) selecionado(s)")
        info_label.setStyleSheet("font-weight: bold; padding: 10px; font-size: 13px; color: #FFD700;")
        layout.addWidget(info_label)

        form_layout = QFormLayout()
        form_layout.setVerticalSpacing(10)

        # Helper para criar cada campo
        def make_field(label, min_val, max_val, suffix=" ms", decimals=1):
            cb = QCheckBox()
            spin = QDoubleSpinBox()
            spin.setRange(min_val, max_val)
            spin.setDecimals(decimals)
            spin.setSuffix(suffix)
            spin.setEnabled(False)
            cb.toggled.connect(spin.setEnabled)
            row = QHBoxLayout()
            row.addWidget(cb)
            row.addWidget(spin)
            form_layout.addRow(f"{label}:", row)
            return cb, spin

        self._enable_offset, self._spin_offset = make_field("Offset", -10000, 100000)
        self._enable_overlap, self._spin_overlap = make_field("Overlap", -1000, 1000)
        self._enable_preutter, self._spin_preutter = make_field("Preutter", 0, 5000)
        self._enable_consonant, self._spin_consonant = make_field("Consonant", 0, 5000)
        self._enable_cutoff, self._spin_cutoff = make_field("Cutoff", -10000, 10000)

        layout.addLayout(form_layout)
        layout.addSpacing(12)

        buttons_layout = QHBoxLayout()
        apply_btn = QPushButton("✅ Aplicar")
        apply_btn.clicked.connect(self._apply)
        cancel_btn = QPushButton("Cancelar")
        cancel_btn.clicked.connect(self.reject)
        buttons_layout.addStretch()
        buttons_layout.addWidget(apply_btn)
        buttons_layout.addWidget(cancel_btn)
        layout.addLayout(buttons_layout)

    def _apply(self):
        if self._enable_offset.isChecked():
            self.result_values["offset"] = self._spin_offset.value()
        if self._enable_overlap.isChecked():
            self.result_values["overlap"] = self._spin_overlap.value()
        if self._enable_preutter.isChecked():
            self.result_values["preutter"] = self._spin_preutter.value()
        if self._enable_consonant.isChecked():
            self.result_values["consonant"] = self._spin_consonant.value()
        if self._enable_cutoff.isChecked():
            self.result_values["cutoff"] = self._spin_cutoff.value()
        self.accept()

    def get_values(self) -> dict:
        return self.result_values

