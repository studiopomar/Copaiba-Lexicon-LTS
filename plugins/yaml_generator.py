# plugins/yaml_generator.py
"""
Plugin: Gerador de character.yaml
Gera um arquivo character.yaml para o Voicebank (uso no OpenUtau).
"""

from typing import Optional
from pathlib import Path
import os

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QMessageBox, QFileDialog, QGroupBox, QFormLayout
)

from .base_plugin import BasePlugin, PluginResult, PluginCategory


class YamlGeneratorDialog(QDialog):
    """Diálogo do Gerador de character.yaml"""
    
    def __init__(self, plugin: 'YamlGeneratorPlugin', parent=None):
        super().__init__(parent)
        self.plugin = plugin
        self._setup_ui()
    
    def _setup_ui(self):
        self.setWindowTitle("Gerador de character.yaml (OpenUtau)")
        self.setMinimumWidth(400)
        
        layout = QVBoxLayout(self)
        
        info_group = QGroupBox("Configurações do Character")
        form_layout = QFormLayout(info_group)
        
        self.input_text = QLineEdit()
        self.input_text.setToolTip("Nome a ser exibido no OpenUtau")
        
        self.input_portrait = QLineEdit()
        self.input_portrait.setToolTip("Nome do arquivo de imagem do personagem (ex: portrait.png)")
        
        self.input_author = QLineEdit()
        
        self.input_web = QLineEdit()
        self.input_web.setToolTip("URL do criador ou do voicebank")
        
        form_layout.addRow("Nome (text):", self.input_text)
        form_layout.addRow("Retrato (portrait):", self.input_portrait)
        form_layout.addRow("Autor (author):", self.input_author)
        form_layout.addRow("Website (web):", self.input_web)
        
        layout.addWidget(info_group)
        
        # Botões
        buttons_layout = QHBoxLayout()
        
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
        
        # Auto-preenchimento
        if self.plugin.voicebank_dir:
            self.input_text.setText(self.plugin.voicebank_dir.name)
            # Tentar achar imagem na raiz
            for ext in ["png", "jpg", "jpeg", "bmp"]:
                img_path = self.plugin.voicebank_dir / f"portrait.{ext}"
                if img_path.exists():
                    self.input_portrait.setText(f"portrait.{ext}")
                    break
    
    def _collect_data(self) -> dict:
        return {
            "text": self.input_text.text().strip(),
            "portrait": self.input_portrait.text().strip(),
            "author": self.input_author.text().strip(),
            "web": self.input_web.text().strip()
        }

    def _generate_default(self):
        if not self.plugin.voicebank_dir:
            QMessageBox.warning(self, "Aviso", "Nenhum voicebank aberto para salvar diretamente.")
            return
            
        target_path = self.plugin.voicebank_dir / "character.yaml"
        self._execute_generation(target_path)
        
    def _generate_save_as(self):
        start_dir = str(self.plugin.voicebank_dir) if self.plugin.voicebank_dir else ""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Salvar character.yaml",
            start_dir + "/character.yaml" if start_dir else "character.yaml",
            "YAML Files (*.yaml *.yml);;All Files (*)"
        )
        
        if file_path:
            self._execute_generation(Path(file_path))

    def _execute_generation(self, target_path: Path):
        data = self._collect_data()
        
        if not data["text"]:
            QMessageBox.warning(self, "Aviso", "O nome (text) é obrigatório.")
            return
            
        result = self.plugin.execute(target_path=target_path, data=data)
        
        if result.success:
            QMessageBox.information(self, "Sucesso", result.message)
            self.accept()
        else:
            QMessageBox.critical(self, "Erro", result.message)


class YamlGeneratorPlugin(BasePlugin):
    """Plugin para gerar character.yaml"""
    
    NAME = "Gerenciamento - Gerador de Character YAML"
    DESCRIPTION = "Gera um arquivo character.yaml para uso no OpenUtau."
    CATEGORY = PluginCategory.MANAGEMENT
    VERSION = "1.0.0"
    
    def get_dialog(self) -> Optional[QDialog]:
        return YamlGeneratorDialog(self, self.main_window)
    
    def execute(self, target_path: Optional[Path] = None, data: Optional[dict] = None, **kwargs) -> PluginResult:
        if not target_path or not data:
            return PluginResult(False, "Dados insuficientes para gerar o character.yaml.")
            
        try:
            content = []
            
            # character.yaml requer o campo text e os outros se aplicáveis
            # Utilizamos formatação yaml básica para evitar dependência extra
            if data.get('text'):
                # Usar escape se houver aspas duplas, algo simples:
                text_val = data['text'].replace('"', '\\"')
                content.append(f'text: "{text_val}"')
            
            if data.get('portrait'):
                port_val = data['portrait'].replace('"', '\\"')
                content.append(f'portrait: "{port_val}"')
                
            if data.get('author'):
                auth_val = data['author'].replace('"', '\\"')
                content.append(f'author: "{auth_val}"')
                
            if data.get('web'):
                web_val = data['web'].replace('"', '\\"')
                content.append(f'web: "{web_val}"')
                
            # Pode-se adicionar subbanks vazios
            # content.append("subbanks: []")
            
            yaml_content = "\n".join(content) + "\n"
            
            with open(target_path, "w", encoding="utf-8") as f:
                f.write(yaml_content)
                
            return PluginResult(
                success=True,
                message=f"Arquivo character.yaml gerado com sucesso em:\n{target_path}",
                changes_made=1
            )
            
        except Exception as e:
            return PluginResult(False, f"Erro ao gerar character.yaml: {str(e)}")
