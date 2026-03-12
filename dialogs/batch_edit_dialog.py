from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QFormLayout, QCheckBox, QSpinBox, 
    QHBoxLayout, QPushButton
)

class BatchEditDialog(QDialog):
    """Diálogo para edição em lote de múltiplos aliases"""

    def __init__(self, parent=None, selected_count: int = 0):
        super().__init__(parent)
        self.setWindowTitle("Edição em Lote")
        self.setMinimumSize(400, 300)

        self.result_values = {}

        layout = QVBoxLayout(self)

        info_label = QLabel(f"Editando {selected_count} alias(es) selecionado(s)")
        info_label.setStyleSheet("font-weight: bold; padding: 10px;")
        layout.addWidget(info_label)

        form_layout = QFormLayout()

        self._enable_offset = QCheckBox()
        self._spin_offset = QSpinBox()
        self._spin_offset.setRange(-10000, 100000)
        self._spin_offset.setSuffix(" ms")
        self._spin_offset.setEnabled(False)
        self._enable_offset.toggled.connect(self._spin_offset.setEnabled)
        offset_layout = QHBoxLayout()
        offset_layout.addWidget(self._enable_offset)
        offset_layout.addWidget(self._spin_offset)
        form_layout.addRow("Offset:", offset_layout)

        self._enable_overlap = QCheckBox()
        self._spin_overlap = QSpinBox()
        self._spin_overlap.setRange(-1000, 1000)
        self._spin_overlap.setSuffix(" ms")
        self._spin_overlap.setEnabled(False)
        self._enable_overlap.toggled.connect(self._spin_overlap.setEnabled)
        overlap_layout = QHBoxLayout()
        overlap_layout.addWidget(self._enable_overlap)
        overlap_layout.addWidget(self._spin_overlap)
        form_layout.addRow("Overlap:", overlap_layout)

        self._enable_preutter = QCheckBox()
        self._spin_preutter = QSpinBox()
        self._spin_preutter.setRange(0, 2000)
        self._spin_preutter.setSuffix(" ms")
        self._spin_preutter.setEnabled(False)
        self._enable_preutter.toggled.connect(self._spin_preutter.setEnabled)
        preutter_layout = QHBoxLayout()
        preutter_layout.addWidget(self._enable_preutter)
        preutter_layout.addWidget(self._spin_preutter)
        form_layout.addRow("Preutter:", preutter_layout)

        self._enable_consonant = QCheckBox()
        self._spin_consonant = QSpinBox()
        self._spin_consonant.setRange(0, 2000)
        self._spin_consonant.setSuffix(" ms")
        self._spin_consonant.setEnabled(False)
        self._enable_consonant.toggled.connect(self._spin_consonant.setEnabled)
        consonant_layout = QHBoxLayout()
        consonant_layout.addWidget(self._enable_consonant)
        consonant_layout.addWidget(self._spin_consonant)
        form_layout.addRow("Consonant:", consonant_layout)

        self._enable_cutoff = QCheckBox()
        self._spin_cutoff = QSpinBox()
        self._spin_cutoff.setRange(-10000, 0)
        self._spin_cutoff.setSuffix(" ms")
        self._spin_cutoff.setEnabled(False)
        self._enable_cutoff.toggled.connect(self._spin_cutoff.setEnabled)
        cutoff_layout = QHBoxLayout()
        cutoff_layout.addWidget(self._enable_cutoff)
        cutoff_layout.addWidget(self._spin_cutoff)
        form_layout.addRow("Cutoff:", cutoff_layout)

        layout.addLayout(form_layout)

        buttons_layout = QHBoxLayout()
        apply_btn = QPushButton("Aplicar")
        apply_btn.clicked.connect(self._apply)
        cancel_btn = QPushButton("Cancelar")
        cancel_btn.clicked.connect(self.reject)
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
