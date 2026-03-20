# plugins/base_plugin.py
"""
Classe base abstrata para todos os plugins do Copaiba Lexikon.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Any, Dict
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from PySide6.QtWidgets import QDialog, QWidget


class PluginCategory(Enum):
    """Categorias de plugins"""
    AUTOMATION = "Automação"
    ANALYSIS = "Análise"
    MANAGEMENT = "Gerenciamento"
    CONVERSION = "Conversão"
    VALIDATION = "Validação"


@dataclass
class PluginResult:
    """Resultado de execução de um plugin"""
    success: bool
    message: str
    data: Optional[Any] = None
    changes_made: int = 0


@dataclass
class ValidationIssue:
    """Problema encontrado por plugins de validação"""
    severity: str  # "error", "warning", "info"
    message: str
    row: int
    alias: str
    field: Optional[str] = None
    suggested_fix: Optional[Any] = None


class BasePlugin(ABC):
    """
    Classe base abstrata para plugins do Copaiba Lexikon.
    
    Todos os plugins devem herdar desta classe e implementar
    os métodos abstratos.
    """
    
    # Metadados do plugin (sobrescrever nas subclasses)
    NAME: str = "Plugin Base"
    DESCRIPTION: str = "Descrição do plugin"
    CATEGORY: PluginCategory = PluginCategory.AUTOMATION
    VERSION: str = "1.0.0"
    AUTHOR: str = "Pomar LTS proj. Yvyra"
    
    def __init__(self, main_window):
        """
        Inicializa o plugin com referência à janela principal.
        
        Args:
            main_window: Referência para MainWindow do Copaiba
        """
        self.main_window = main_window
        self._is_initialized = False
    
    @property
    def table(self):
        """Acesso à tabela de aliases"""
        return self.main_window.table
    
    @property
    def oto(self):
        """Acesso ao objeto OtoFile"""
        return self.main_window._oto
    
    @property
    def voicebank_dir(self) -> Optional[Path]:
        """Diretório do voicebank atual"""
        return self.main_window._voicebank_dir
    
    @property
    def waveform(self):
        """Acesso ao widget de waveform"""
        return self.main_window.waveform
    
    def get_selected_rows(self) -> List[int]:
        """Retorna lista de linhas selecionadas na tabela"""
        selected = self.table.selectedItems()
        rows = set()
        for item in selected:
            rows.add(item.row())
        return sorted(list(rows))
    
    def get_all_rows(self) -> List[int]:
        """Retorna lista de todas as linhas da tabela"""
        return list(range(self.table.rowCount()))
    
    def get_alias_data(self, row: int) -> Dict[str, Any]:
        """
        Retorna dados de um alias específico.
        
        Args:
            row: Índice da linha
            
        Returns:
            Dicionário com os dados do alias
        """
        if row < 0 or row >= self.table.rowCount():
            return {}
        
        return {
            "row": row,
            "filename": self.table.item(row, 1).text() if self.table.item(row, 1) else "",
            "alias": self.table.item(row, 2).text() if self.table.item(row, 2) else "",
            "offset": float(self.table.item(row, 3).text()) if self.table.item(row, 3) else 0,
            "overlap": float(self.table.item(row, 4).text()) if self.table.item(row, 4) else 0,
            "preutter": float(self.table.item(row, 5).text()) if self.table.item(row, 5) else 0,
            "consonant": float(self.table.item(row, 6).text()) if self.table.item(row, 6) else 0,
            "cutoff": float(self.table.item(row, 7).text()) if self.table.item(row, 7) else 0,
        }
    
    def set_alias_data(self, row: int, field: str, value: Any):
        """
        Define um valor para um campo de um alias.
        
        Args:
            row: Índice da linha
            field: Nome do campo ("alias", "offset", "overlap", etc.)
            value: Novo valor
        """
        col_map = {
            "filename": 1,
            "alias": 2,
            "offset": 3,
            "overlap": 4,
            "preutter": 5,
            "consonant": 6,
            "cutoff": 7,
        }
        
        if field not in col_map:
            return
        
        col = col_map[field]
        item = self.table.item(row, col)
        if item:
            if isinstance(value, float):
                item.setText(f"{value:.2f}")
            else:
                item.setText(str(value))
    
    def get_audio_path(self, row: int) -> Optional[Path]:
        """
        Retorna o caminho do arquivo de áudio para um alias.
        
        Args:
            row: Índice da linha
            
        Returns:
            Path do arquivo ou None se não encontrado
        """
        if not self.voicebank_dir:
            return None
        
        data = self.get_alias_data(row)
        if not data.get("filename"):
            return None
        
        path = self.voicebank_dir / data["filename"]
        if path.exists():
            return path
        return None
    
    def show_message(self, message: str, duration_ms: int = 3000):
        """Mostra mensagem na barra de status"""
        self.main_window.statusBar().showMessage(message, duration_ms)
    
    def mark_dirty(self):
        """Marca o projeto como modificado"""
        self.main_window._dirty = True
        self.main_window._update_title()
    
    @abstractmethod
    def get_dialog(self) -> Optional[QDialog]:
        """
        Retorna o diálogo de configuração do plugin.
        
        Returns:
            QDialog configurado ou None se não precisar de diálogo
        """
        pass
    
    @abstractmethod
    def execute(self, **kwargs) -> PluginResult:
        """
        Executa a funcionalidade principal do plugin.
        
        Args:
            **kwargs: Argumentos específicos do plugin
            
        Returns:
            PluginResult com o resultado da execução
        """
        pass
    
    def cleanup(self):
        """Limpa recursos do plugin (opcional)"""
        pass
