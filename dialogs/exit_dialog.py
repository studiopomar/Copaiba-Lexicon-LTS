# dialogs/exit_dialog.py
"""
Diálogo avançado de saída do Copaiba Lexikon.
"""

from pathlib import Path
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QPushButton, QFrame, QHBoxLayout
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QKeySequence


class AdvancedExitDialog(QDialog):
    """
    Diálogo avançado para confirmação de saída do programa.
    
    Mostra informações sobre o projeto e oferece opções para:
    - Salvar alterações
    - Criar backup e salvar
    - Descartar alterações
    - Cancelar e continuar editando
    """
    
    def __init__(
        self, 
        parent, 
        oto_path: Path, 
        has_changes: bool,
        completed_count: int, 
        total_count: int, 
        last_saved: str = "Nunca"
    ):
        super().__init__(parent)
        self.oto_path = oto_path
        self.has_changes = has_changes
        self.result_action = "cancel"

        self.setWindowTitle("Confirmar Saída - Copaiba Lexikon")
        self.setMinimumWidth(450)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)

        # Título
        title_label = QLabel("⚠️ Confirmar Saída do Programa")
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(14)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("color: #ff6b35; padding: 10px;")
        layout.addWidget(title_label)

        # Frame de informações
        info_frame = QFrame()
        info_frame.setFrameStyle(QFrame.Shape.Box)
        info_frame.setStyleSheet("""
            QFrame {
                background-color: #2a2a2a;
                border: 1px solid #555;
                border-radius: 8px;
                padding: 10px;
            }
        """)
        info_layout = QVBoxLayout(info_frame)

        # Informações do projeto
        progress_percent = (completed_count / total_count * 100) if total_count > 0 else 0
        project_info = QLabel(f"""
<b>📁 Arquivo:</b> {oto_path.name}<br>
<b>📂 Local:</b> {oto_path.parent}<br>
<b>⏰ Último salvamento:</b> {last_saved}<br>
<b>✅ Progresso:</b> {completed_count}/{total_count} aliases concluídos ({progress_percent:.1f}%)
        """)
        project_info.setWordWrap(True)
        info_layout.addWidget(project_info)

        # Status de alterações
        if has_changes:
            changes_label = QLabel("🔴 <b>ATENÇÃO:</b> Existem alterações não salvas!")
            changes_label.setStyleSheet(
                "color: #ff4444; font-weight: bold; padding: 8px; "
                "background-color: #442222; border-radius: 4px;"
            )
        else:
            changes_label = QLabel("✅ <b>OK:</b> Todas as alterações foram salvas.")
            changes_label.setStyleSheet(
                "color: #44ff44; font-weight: bold; padding: 8px; "
                "background-color: #224422; border-radius: 4px;"
            )

        changes_label.setWordWrap(True)
        info_layout.addWidget(changes_label)
        layout.addWidget(info_frame)

        # Frame de recomendação (só se houver alterações)
        if has_changes:
            recommend_frame = QFrame()
            recommend_frame.setFrameStyle(QFrame.Shape.Box)
            recommend_frame.setStyleSheet("""
                QFrame {
                    background-color: #2a2a42;
                    border: 1px solid #4169e1;
                    border-radius: 8px;
                    padding: 10px;
                }
            """)
            recommend_layout = QVBoxLayout(recommend_frame)
            recommend_label = QLabel("""
<b>💡 Recomendação:</b><br>
• <b>Salvar:</b> Preserva todo o seu trabalho<br>
• <b>Backup + Salvar:</b> Cria cópia de segurança antes de salvar<br>
• <b>Descartar:</b> Perde todas as alterações desde o último salvamento<br>
• <b>Cancelar:</b> Retorna ao programa para continuar editando
            """)
            recommend_label.setWordWrap(True)
            recommend_layout.addWidget(recommend_label)
            layout.addWidget(recommend_frame)

        # Botões
        buttons_layout = QVBoxLayout()
        buttons_layout.setSpacing(8)

        if has_changes:
            # Botão de backup + salvar
            backup_save_btn = QPushButton("🛡️ Backup + Salvar (Recomendado)")
            backup_save_btn.setStyleSheet(
                "QPushButton { background-color: #4CAF50; color: white; "
                "font-weight: bold; padding: 12px; border-radius: 6px; font-size: 14px; } "
                "QPushButton:hover { background-color: #5CBF60; }"
            )
            backup_save_btn.clicked.connect(lambda: self._set_result("backup"))
            buttons_layout.addWidget(backup_save_btn)

            # Botão de salvar
            save_btn = QPushButton("💾 Salvar Alterações")
            save_btn.setStyleSheet(
                "QPushButton { background-color: #2196F3; color: white; "
                "font-weight: bold; padding: 10px; border-radius: 6px; } "
                "QPushButton:hover { background-color: #1976D2; }"
            )
            save_btn.clicked.connect(lambda: self._set_result("save"))
            buttons_layout.addWidget(save_btn)

            # Separador
            separator = QFrame()
            separator.setFrameShape(QFrame.Shape.HLine)
            separator.setStyleSheet("color: #666;")
            buttons_layout.addWidget(separator)

            # Botão de descartar
            discard_btn = QPushButton("🗑️ Descartar Alterações e Sair")
            discard_btn.setStyleSheet(
                "QPushButton { background-color: #FF5722; color: white; "
                "padding: 10px; border-radius: 6px; } "
                "QPushButton:hover { background-color: #E64A19; }"
            )
            discard_btn.clicked.connect(lambda: self._set_result("discard"))
            buttons_layout.addWidget(discard_btn)
        else:
            # Botão de sair
            exit_btn = QPushButton("✅ Sair do Programa")
            exit_btn.setStyleSheet(
                "QPushButton { background-color: #4CAF50; color: white; "
                "font-weight: bold; padding: 12px; border-radius: 6px; font-size: 14px; } "
                "QPushButton:hover { background-color: #5CBF60; }"
            )
            exit_btn.clicked.connect(lambda: self._set_result("save"))
            buttons_layout.addWidget(exit_btn)

        # Botão de cancelar
        cancel_btn = QPushButton("❌ Cancelar (Continuar Editando)")
        cancel_btn.setStyleSheet(
            "QPushButton { background-color: #9E9E9E; color: white; "
            "padding: 10px; border-radius: 6px; } "
            "QPushButton:hover { background-color: #757575; }"
        )
        cancel_btn.clicked.connect(lambda: self._set_result("cancel"))
        buttons_layout.addWidget(cancel_btn)

        layout.addLayout(buttons_layout)
        self.setModal(True)

        # Atalhos
        if has_changes:
            backup_save_btn.setShortcut(QKeySequence("Ctrl+S"))
            save_btn.setShortcut(QKeySequence("S"))
            discard_btn.setShortcut(QKeySequence("D"))
        cancel_btn.setShortcut(QKeySequence("Escape"))
        
        # Ajusta o tamanho automaticamente ao conteúdo
        self.adjustSize()

    def _set_result(self, action: str) -> None:
        """Define o resultado e fecha o diálogo."""
        self.result_action = action
        self.accept()

    def get_action(self) -> str:
        """Retorna a ação selecionada pelo usuário."""
        return self.result_action
