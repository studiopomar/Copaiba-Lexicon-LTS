# core/translator.py
"""
Sistema de internacionalização (i18n) para Copaiba Lexikon.
Carrega arquivos de tradução da pasta translations/ e permite
troca dinâmica de idioma em tempo real.
"""

from __future__ import annotations
from pathlib import Path
from typing import Dict, Optional, List, Callable
import re


class Translator:
    """
    Gerencia traduções do aplicativo.
    Singleton: use get_translator() para obter a instância.
    """
    
    _instance: Optional['Translator'] = None
    
    def __init__(self):
        self._translations: Dict[str, str] = {}
        self._current_language: str = "pt_BR"
        self._translations_dir: Path = Path(__file__).parent.parent / "translations"
        self._listeners: List[Callable[[], None]] = []
        
        # Carrega idioma padrão
        self.load_language("pt_BR")
    
    @classmethod
    def get_instance(cls) -> 'Translator':
        """Retorna a instância singleton do Translator."""
        if cls._instance is None:
            cls._instance = Translator()
        return cls._instance
    
    def get_translations_dir(self) -> Path:
        """Retorna o diretório de traduções."""
        return self._translations_dir
    
    def get_available_languages(self) -> List[Dict[str, str]]:
        """
        Retorna lista de idiomas disponíveis.
        Cada item é um dict com 'code', 'name' e 'file'.
        """
        languages = []
        
        if not self._translations_dir.exists():
            return languages
        
        for file in self._translations_dir.glob("*.txt"):
            lang_code = file.stem
            lang_name = self._get_language_name(file)
            languages.append({
                "code": lang_code,
                "name": lang_name,
                "file": str(file)
            })
        
        # Ordena por nome, mas mantém pt_BR primeiro
        languages.sort(key=lambda x: (x["code"] != "pt_BR", x["name"]))
        return languages
    
    def _get_language_name(self, file: Path) -> str:
        """Extrai o nome do idioma do arquivo de tradução."""
        try:
            with open(file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("language.name"):
                        parts = line.split("=", 1)
                        if len(parts) == 2:
                            return parts[1].strip()
        except Exception:
            pass
        
        # Fallback: usa o nome do arquivo
        return file.stem
    
    def load_language(self, lang_code: str) -> bool:
        """
        Carrega um arquivo de tradução.
        Retorna True se carregou com sucesso.
        """
        lang_file = self._translations_dir / f"{lang_code}.txt"
        
        if not lang_file.exists():
            print(f"[Translator] Arquivo não encontrado: {lang_file}")
            return False
        
        try:
            self._translations.clear()
            
            with open(lang_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    
                    # Ignora comentários e linhas vazias
                    if not line or line.startswith("#"):
                        continue
                    
                    # Parse key = value
                    if "=" in line:
                        key, value = line.split("=", 1)
                        key = key.strip()
                        value = value.strip()
                        self._translations[key] = value
            
            self._current_language = lang_code
            print(f"[Translator] Idioma carregado: {lang_code} ({len(self._translations)} chaves)")
            
            # Notifica listeners sobre mudança de idioma
            self._notify_listeners()
            return True
            
        except Exception as e:
            print(f"[Translator] Erro ao carregar {lang_file}: {e}")
            return False
    
    def get_current_language(self) -> str:
        """Retorna o código do idioma atual."""
        return self._current_language
    
    def tr(self, key: str, **kwargs) -> str:
        """
        Traduz uma chave.
        Suporta placeholders como {name} que são substituídos por kwargs.
        """
        text = self._translations.get(key, key)
        
        # Substitui placeholders
        if kwargs:
            for k, v in kwargs.items():
                text = text.replace(f"{{{k}}}", str(v))
        
        return text
    
    def add_listener(self, callback: Callable[[], None]) -> None:
        """Adiciona um listener para mudanças de idioma."""
        if callback not in self._listeners:
            self._listeners.append(callback)
    
    def remove_listener(self, callback: Callable[[], None]) -> None:
        """Remove um listener."""
        if callback in self._listeners:
            self._listeners.remove(callback)
    
    def _notify_listeners(self) -> None:
        """Notifica todos os listeners sobre mudança de idioma."""
        for callback in self._listeners:
            try:
                callback()
            except Exception as e:
                print(f"[Translator] Erro em listener: {e}")


# Função global de conveniência
def get_translator() -> Translator:
    """Retorna a instância singleton do Translator."""
    return Translator.get_instance()


def tr(key: str, **kwargs) -> str:
    """Função global de tradução."""
    return get_translator().tr(key, **kwargs)
