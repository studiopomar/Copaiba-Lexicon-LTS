# dialogs/plugin_manager.py
"""
Diálogo para gerenciar plugins do Copaiba Lexikon.
"""

from typing import Dict, List, Type, Optional
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QWidget, QFrame, QGridLayout, QCheckBox
)
from PySide6.QtCore import Qt, QSettings
from PySide6.QtGui import QFont

# Import plugin classes
try:
    from plugins import (
        BasePlugin,
        DuplicateDetectorPlugin,
        ConsistencyCheckerPlugin,
        AliasSorterPlugin,
        BatchRenamePlugin,
        RomajiHiraganaPlugin,
        VVDetectorPlugin,
        PitchAnalyzerPlugin,
        MicTunerPlugin,
    )
    from plugins.base_plugin import PluginCategory
    PLUGINS_AVAILABLE = True
except ImportError:
    PLUGINS_AVAILABLE = False


# Ícones por categoria
CATEGORY_ICONS = {
    "Automação": "🌱",
    "Análise": "📊",
    "Gerenciamento": "📁",
    "Conversão": "🔄",
    "Validação": "✅",
}


class PluginCard(QFrame):
    """Card visual para exibir informações de um plugin"""
    
    def __init__(self, plugin_class: Type[BasePlugin], enabled: bool = True, parent=None):
        super().__init__(parent)
        self.plugin_class = plugin_class
        self._enabled = enabled
        
        self.setFrameStyle(QFrame.Box | QFrame.Raised)
        self.setStyleSheet("""
            PluginCard {
                background-color: #2d2d2d;
                border: 1px solid #444;
                border-radius: 8px;
                padding: 10px;
            }
            PluginCard:hover {
                border-color: #666;
                background-color: #333;
            }
        """)
        
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QGridLayout(self)
        layout.setSpacing(8)
        
        # Ícone da categoria
        category_name = self.plugin_class.CATEGORY.value
        icon = CATEGORY_ICONS.get(category_name, "🔌")
        
        icon_label = QLabel(icon)
        icon_label.setStyleSheet("font-size: 32px;")
        layout.addWidget(icon_label, 0, 0, 2, 1)
        
        # Nome do plugin
        name_label = QLabel(self.plugin_class.NAME)
        name_font = QFont()
        name_font.setBold(True)
        name_font.setPointSize(12)
        name_label.setFont(name_font)
        name_label.setStyleSheet("color: #fff;")
        layout.addWidget(name_label, 0, 1)
        
        # Versão e autor
        info_label = QLabel(f"v{self.plugin_class.VERSION} • {self.plugin_class.AUTHOR}")
        info_label.setStyleSheet("color: #888; font-size: 10px;")
        layout.addWidget(info_label, 0, 2, Qt.AlignRight)
        
        # Descrição
        desc_label = QLabel(self.plugin_class.DESCRIPTION)
        desc_label.setStyleSheet("color: #aaa;")
        desc_label.setWordWrap(True)
        layout.addWidget(desc_label, 1, 1, 1, 2)
        
        # Categoria badge
        category_label = QLabel(f"  {category_name}  ")
        category_label.setStyleSheet("""
            background-color: #444;
            color: #ccc;
            border-radius: 4px;
            padding: 2px 6px;
            font-size: 10px;
        """)
        layout.addWidget(category_label, 2, 1, Qt.AlignLeft)
        
        # Checkbox de ativação
        self.chk_enabled = QCheckBox("Ativado")
        self.chk_enabled.setChecked(self._enabled)
        self.chk_enabled.setStyleSheet("color: #aaa;")
        layout.addWidget(self.chk_enabled, 2, 2, Qt.AlignRight)
        
        layout.setColumnStretch(1, 1)
    
    def is_enabled(self) -> bool:
        return self.chk_enabled.isChecked()
    
    def get_plugin_key(self) -> str:
        """Retorna uma chave única para identificar o plugin"""
        return self.plugin_class.__name__


class PluginManagerDialog(QDialog):
    """Diálogo principal do gerenciador de plugins"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Gerenciador de Plugins - Pomar")
        self.setMinimumSize(700, 500)
        
        self.settings = QSettings("MiSC Labs", "Copaiba")
        self.plugin_cards: List[PluginCard] = []
        
        self._setup_ui()
        self._load_plugins()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Header
        header_layout = QHBoxLayout()
        
        title = QLabel("🔌 Gerenciador de Plugins")
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(16)
        title.setFont(title_font)
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # Contador
        self.lbl_count = QLabel("")
        self.lbl_count.setStyleSheet("color: #888;")
        header_layout.addWidget(self.lbl_count)
        
        layout.addLayout(header_layout)
        
        # Descrição
        desc = QLabel("Gerencie os plugins instalados. Desative plugins que você não usa para simplificar os menus.")
        desc.setStyleSheet("color: #888; margin-bottom: 10px;")
        desc.setWordWrap(True)
        layout.addWidget(desc)
        
        # Área de scroll para os cards
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("background: transparent;")
        
        self.cards_container = QWidget()
        self.cards_layout = QVBoxLayout(self.cards_container)
        self.cards_layout.setSpacing(10)
        self.cards_layout.addStretch()
        
        scroll.setWidget(self.cards_container)
        layout.addWidget(scroll)
        
        # Botões
        buttons_layout = QHBoxLayout()
        
        btn_enable_all = QPushButton("Ativar Todos")
        btn_enable_all.clicked.connect(self._enable_all)
        buttons_layout.addWidget(btn_enable_all)
        
        btn_disable_all = QPushButton("Desativar Todos")
        btn_disable_all.clicked.connect(self._disable_all)
        buttons_layout.addWidget(btn_disable_all)
        
        buttons_layout.addStretch()
        
        btn_save = QPushButton("💾 Salvar")
        btn_save.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 8px 20px;
                border: none;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #45a049; }
        """)
        btn_save.clicked.connect(self._save_and_close)
        buttons_layout.addWidget(btn_save)
        
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.clicked.connect(self.reject)
        buttons_layout.addWidget(btn_cancel)
        
        layout.addLayout(buttons_layout)
    
    def _load_plugins(self):
        if not PLUGINS_AVAILABLE:
            error_label = QLabel("⚠️ Sistema de plugins não disponível")
            error_label.setStyleSheet("color: #f44336; font-size: 14px;")
            self.cards_layout.insertWidget(0, error_label)
            return
        
        # Lista de classes de plugins disponíveis
        plugin_classes = [
            VVDetectorPlugin,
            PitchAnalyzerPlugin,
            MicTunerPlugin,
            BatchRenamePlugin,
            AliasSorterPlugin,
            RomajiHiraganaPlugin,
            DuplicateDetectorPlugin,
            ConsistencyCheckerPlugin,
        ]
        
        # Carregar estado de ativação
        disabled_plugins = self.settings.value("disabled_plugins", [], type=list)
        
        for plugin_class in plugin_classes:
            key = plugin_class.__name__
            enabled = key not in disabled_plugins
            
            card = PluginCard(plugin_class, enabled=enabled)
            self.plugin_cards.append(card)
            self.cards_layout.insertWidget(self.cards_layout.count() - 1, card)
        
        self._update_count()
    
    def _update_count(self):
        total = len(self.plugin_cards)
        enabled = sum(1 for card in self.plugin_cards if card.is_enabled())
        self.lbl_count.setText(f"{enabled}/{total} plugins ativos")
    
    def _enable_all(self):
        for card in self.plugin_cards:
            card.chk_enabled.setChecked(True)
        self._update_count()
    
    def _disable_all(self):
        for card in self.plugin_cards:
            card.chk_enabled.setChecked(False)
        self._update_count()
    
    def _save_and_close(self):
        # Salvar lista de plugins desativados
        disabled = []
        for card in self.plugin_cards:
            if not card.is_enabled():
                disabled.append(card.get_plugin_key())
        
        self.settings.setValue("disabled_plugins", disabled)
        self.accept()
    
    def closeEvent(self, event):
        self._update_count()
        super().closeEvent(event)
