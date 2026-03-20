# dialogs/cheatsheet_dialog.py
from __future__ import annotations
from typing import TYPE_CHECKING

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QScrollArea, QWidget, QFrame, QGridLayout
)
from PySide6.QtGui import QFont, QColor, QPalette

if TYPE_CHECKING:
    from main import MainWindow

class CheatsheetDialog(QDialog):
    """
    Diálogo que exibe os atalhos de teclado e dicas de uso.
    """

    def __init__(self, parent: 'MainWindow' = None):
        super().__init__(parent)
        self.setWindowTitle("Atalhos e Comandos - Copaiba Lexicon LTS")
        self.resize(800, 600)
        self._setup_ui()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # Título
        title_label = QLabel("Manual de Atalhos e Comandos")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)

        # Scroll Area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        
        container = QWidget()
        self.content_layout = QVBoxLayout(container)
        self.content_layout.setSpacing(20)

        # Adicionar seções
        self._add_section("Arquivo e Projetos", [
            ("Abrir voicebank...", "Ctrl + O", "Abre a pasta de um voicebank e carrega a oto.ini"),
            ("Abrir projeto...", "Ctrl + Shift + O", "Abre um arquivo de projeto salvo"),
            ("Salvar projeto", "Ctrl + Shift + P", "Salva o estado atual como projeto"),
            ("Salvar (oto.ini)", "Ctrl + S", "Salva as alterações no arquivo oto.ini"),
            ("Salvar como...", "Ctrl + Shift + S", "Salva a oto.ini com outro nome"),
            ("Recarregar", "Ctrl + F5", "Recarrega as configurações e o arquivo atual"),
            ("Abrir pasta do voicebank", "Ctrl + P", "Abre o explorador de arquivos na pasta do voicebank"),
            ("Configurações Gerais", "Ctrl + ,", "Abre a janela de configurações"),
        ])

        self._add_section("Edição", [
            ("Desfazer", "Ctrl + Z", "Desfaz a última alteração"),
            ("Refazer", "Ctrl + Y", "Refaz a última alteração desfeita"),
            ("Renomear Alias", "Ctrl + R", "Renomeia o alias selecionado"),
            ("Duplicar Alias", "Ctrl + I", "Duplica o alias selecionado"),
            ("Deletar Alias", "Ctrl + D", "Remove o alias selecionado"),
            ("Marcar como Concluído", "Ctrl + M", "Alterna o status de concluído do alias"),
            ("Copiar", "Ctrl + C", "Copia as células selecionadas na tabela"),
            ("Colar", "Ctrl + V", "Cola dados na tabela"),
        ])

        self._add_section("Waveform e Navegação", [
            ("Definir Offset", "Q", "Define o ponto de Offset na posição do mouse"),
            ("Definir Overlap", "W", "Define o ponto de Overlap na posição do mouse"),
            ("Definir Preutterance", "E", "Define o ponto de Preutterance na posição do mouse"),
            ("Definir Consonant", "R", "Define o ponto de Consonant na posição do mouse"),
            ("Definir Cutoff", "T", "Define o ponto de Cutoff na posição do mouse"),
            ("Alias Anterior", "Seta Cima", "Navega para o alias anterior na lista"),
            ("Próximo Alias", "Seta Baixo", "Navega para o próximo alias na lista"),
            ("Navegar Aliases", "Scroll Mouse", "Roda para cima/baixo troca o alias atual"),
            ("Zoom Horizontal", "Ctrl + Scroll", "Aumenta ou diminui o zoom no tempo"),
            ("Zoom Vertical", "Alt + Scroll", "Aumenta ou diminui a braplitude da onda"),
            ("Pan Horizontal", "Shift + Scroll", "Move a waveform para esquerda ou direita"),
        ])

        self._add_section("Reprodução", [
            ("Tocar Segmento", "Espaço", "Toca a região configurada do alias atual"),
            ("Tocar Completo", "Shift + Espaço", "Toca o arquivo de áudio original inteiro"),
            ("Teste de Síntese", "Ctrl + Shift + Espaço", "Sintetiza e toca o alias usando o resampler"),
        ])

        self._add_section("Presets", [
            ("CV", "Ctrl + 1", "Aplica configuração padrão para CV"),
            ("VCV", "Ctrl + 2", "Aplica configuração padrão para VCV"),
            ("VV", "Ctrl + 3", "Aplica configuração padrão para VV"),
            ("VC", "Ctrl + 4", "Aplica configuração padrão para VC"),
            ("Ciclar Tema", "Ctrl + '", "Alterna entre os temas de cores da waveform"),
        ])

        self._add_section("Visualização", [
            ("Resetar Layout", "Ctrl + Shift + R", "Restaura a posição padrão dos painéis"),
        ])

        scroll.setWidget(container)
        main_layout.addWidget(scroll)

        # Botão Fechar
        close_btn = QPushButton("Fechar")
        close_btn.setFixedWidth(100)
        close_btn.clicked.connect(self.accept)
        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(close_btn)
        main_layout.addLayout(btn_layout)

    def _add_section(self, title: str, items: list[tuple[str, str, str]]):
        # Header da seção
        section_frame = QFrame()
        section_frame.setObjectName("SectionFrame")
        section_frame.setStyleSheet("""
            QFrame#SectionFrame { 
                background-color: rgba(255, 255, 255, 8); 
                border: 1px solid rgba(255, 255, 255, 15);
                border-radius: 10px; 
                padding: 10px;
            }
        """)
        
        section_layout = QVBoxLayout(section_frame)
        
        header = QLabel(title.upper())
        header_font = QFont()
        header_font.setPointSize(10)
        header_font.setBold(True)
        header_font.setLetterSpacing(QFont.SpacingType.PercentageSpacing, 110)
        header.setFont(header_font)
        header.setStyleSheet("color: #81C784; margin-bottom: 8px; opacity: 0.9;")
        section_layout.addWidget(header)

        # Grid de atalhos
        grid = QGridLayout()
        grid.setSpacing(10)
        grid.setColumnStretch(2, 1) # Descrição estica
        
        for row, (action, shortcut, desc) in enumerate(items):
            action_lbl = QLabel(action)
            action_lbl.setStyleSheet("color: #EEE; font-weight: 500;")
            
            # Estilo de "tecla" para o atalho
            shortcut_container = QLabel(shortcut)
            shortcut_container.setAlignment(Qt.AlignCenter)
            shortcut_container.setStyleSheet("""
                background-color: #37474F;
                color: #FFD54F;
                border: 1px solid #455A64;
                border-radius: 4px;
                padding: 2px 6px;
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 11px;
            """)
            
            desc_lbl = QLabel(desc)
            desc_lbl.setStyleSheet("color: #90A4AE; font-style: italic;")
            desc_lbl.setWordWrap(True)
            
            grid.addWidget(action_lbl, row, 0)
            grid.addWidget(shortcut_container, row, 1)
            grid.addWidget(desc_lbl, row, 2)
            
        section_layout.addLayout(grid)
        self.content_layout.addWidget(section_frame)
