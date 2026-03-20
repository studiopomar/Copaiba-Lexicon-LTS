# plugins/readme_generator.py
"""
Plugin: Gerador de README
Gera um arquivo readme.txt padronizado para o Voicebank.
"""

from typing import Optional
from pathlib import Path

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QTextEdit, QComboBox, QMessageBox, QFileDialog,
    QGroupBox, QFormLayout
)

from .base_plugin import BasePlugin, PluginResult, PluginCategory


class ReadmeGeneratorDialog(QDialog):
    """Diálogo do Gerador de README"""
    
    def __init__(self, plugin: 'ReadmeGeneratorPlugin', parent=None):
        super().__init__(parent)
        self.plugin = plugin
        self._setup_ui()
    
    def _setup_ui(self):
        self.setWindowTitle("Gerador de README")
        self.setMinimumWidth(500)
        
        layout = QVBoxLayout(self)
        
        # Grupo de Informações Básicas
        info_group = QGroupBox("Informações Básicas")
        form_layout = QFormLayout(info_group)
        
        self.input_name = QLineEdit()
        self.input_author = QLineEdit()
        self.input_version = QLineEdit("1.0")
        
        self.combo_type = QComboBox()
        self.combo_type.addItems(["CV", "VCV", "CVVC", "VCCV", "Arpasing", "Outro"])
        
        self.input_language = QLineEdit()
        self.input_website = QLineEdit()
        
        form_layout.addRow("Nome do Voicebank:", self.input_name)
        form_layout.addRow("Autor:", self.input_author)
        form_layout.addRow("Versão:", self.input_version)
        form_layout.addRow("Tipo de Banco:", self.combo_type)
        form_layout.addRow("Idioma:", self.input_language)
        form_layout.addRow("Website / Contato:", self.input_website)
        
        layout.addWidget(info_group)
        
        # Descrição e Termos
        text_group = QGroupBox("Detalhes Adicionais")
        text_layout = QVBoxLayout(text_group)
        
        text_layout.addWidget(QLabel("Descrição / Notas:"))
        self.input_description = QTextEdit()
        self.input_description.setMaximumHeight(80)
        text_layout.addWidget(self.input_description)
        
        text_layout.addWidget(QLabel("Termos de Uso:"))
        self.input_terms = QTextEdit()
        self.input_terms.setMaximumHeight(80)
        text_layout.addWidget(self.input_terms)
        
        layout.addWidget(text_group)
        
        # Botões
        buttons_layout = QHBoxLayout()
        
        # Se não houver voicebank carregado, o botão padrão será "Salvar em..."
        if self.plugin.voicebank_dir:
            btn_generate = QPushButton("Gerar no Voicebank")
            btn_generate.clicked.connect(self._generate_default)
            buttons_layout.addWidget(btn_generate)
            
            btn_save_as = QPushButton("Salvar em...")
            btn_save_as.clicked.connect(self._generate_save_as)
            buttons_layout.addWidget(btn_save_as)
        else:
            btn_save_as = QPushButton("Salvar em...")
            btn_save_as.clicked.connect(self._generate_save_as)
            buttons_layout.addWidget(btn_save_as)
        
        btn_close = QPushButton("Fechar")
        btn_close.clicked.connect(self.close)
        buttons_layout.addWidget(btn_close)
        
        layout.addLayout(buttons_layout)
        
        # Pré-preencher com nome da pasta se possível
        if self.plugin.voicebank_dir:
            self.input_name.setText(self.plugin.voicebank_dir.name)
    
    def _collect_data(self) -> dict:
        return {
            "name": self.input_name.text().strip(),
            "author": self.input_author.text().strip(),
            "version": self.input_version.text().strip(),
            "type": self.combo_type.currentText(),
            "language": self.input_language.text().strip(),
            "website": self.input_website.text().strip(),
            "description": self.input_description.toPlainText().strip(),
            "terms": self.input_terms.toPlainText().strip()
        }

    def _generate_default(self):
        if not self.plugin.voicebank_dir:
            QMessageBox.warning(self, "Aviso", "Nenhum voicebank aberto para salvar diretamente.")
            return
            
        target_path = self.plugin.voicebank_dir / "readme.txt"
        self._execute_generation(target_path)
        
    def _generate_save_as(self):
        start_dir = str(self.plugin.voicebank_dir) if self.plugin.voicebank_dir else ""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Salvar README",
            start_dir + "/readme.txt" if start_dir else "readme.txt",
            "Text Files (*.txt);;All Files (*)"
        )
        
        if file_path:
            self._execute_generation(Path(file_path))
            
    def _execute_generation(self, target_path: Path):
        data = self._collect_data()
        
        if not data["name"]:
            QMessageBox.warning(self, "Aviso", "O nome do Voicebank é obrigatório.")
            return
            
        result = self.plugin.execute(target_path=target_path, data=data)
        
        if result.success:
            QMessageBox.information(self, "Sucesso", result.message)
            self.accept()
        else:
            QMessageBox.critical(self, "Erro", result.message)


class ReadmeGeneratorPlugin(BasePlugin):
    """Plugin para gerar readme.txt"""
    
    NAME = "Gerenciamento - Gerador de README"
    DESCRIPTION = "Gera um arquivo readme.txt padronizado para o Voicebank."
    CATEGORY = PluginCategory.MANAGEMENT
    VERSION = "1.0.0"
    
    def get_dialog(self) -> Optional[QDialog]:
        return ReadmeGeneratorDialog(self, self.main_window)
    
    def execute(self, target_path: Optional[Path] = None, data: Optional[dict] = None, **kwargs) -> PluginResult:
        if not target_path or not data:
            return PluginResult(False, "Dados insuficientes para gerar o README.")
            
        try:
            content = []
            content.append(f"=========================================")
            content.append(f"  {data.get('name', 'Voicebank')}")
            content.append(f"=========================================\n")
            
            content.append("[ INFORMAÇÕES BÁSICAS ]")
            content.append(f"Nome: {data.get('name', '')}")
            if data.get('author'):
                content.append(f"Autor/Criador: {data.get('author')}")
            if data.get('version'):
                content.append(f"Versão: {data.get('version')}")
            if data.get('type'):
                content.append(f"Tipo/Banco: {data.get('type')}")
            if data.get('language'):
                content.append(f"Idioma: {data.get('language')}")
            if data.get('website'):
                content.append(f"Website/Contato: {data.get('website')}")
            content.append("")
            
            if data.get('description'):
                content.append("[ DESCRIÇÃO ]")
                content.append(data['description'])
                content.append("")
                
            if data.get('terms'):
                content.append("[ TERMOS DE USO ]")
                content.append(data['terms'])
                content.append("")
                
            content.append("-----------------------------------------")
            content.append("Gerado pelo Copaiba Lexikon (Plugin Gerador de README)")
            
            text_content = "\n".join(content)
            
            # Tentar utf-8, fallback para outros encodings se necessário
            with open(target_path, "w", encoding="utf-8") as f:
                f.write(text_content)
                
            return PluginResult(
                success=True,
                message=f"Arquivo README gerado com sucesso em:\n{target_path}",
                changes_made=1
            )
            
        except Exception as e:
            return PluginResult(False, f"Erro ao gerar README: {str(e)}")
