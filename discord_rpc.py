# discord_rpc.py
"""
Discord Rich Presence para Copaiba Lexikon.
Mostra status de edição no Discord.
"""

import logging
import time
from typing import Optional
from pathlib import Path

logger = logging.getLogger("copaiba.discord")

# Tenta importar pypresence (opcional)
try:
    from pypresence import Presence, exceptions as rpc_exceptions
    DISCORD_AVAILABLE = True
except ImportError:
    DISCORD_AVAILABLE = False
    logger.debug("pypresence não instalado - Discord RPC desabilitado")


class CopaibaDcordRPC:
    """Gerenciador de Discord Rich Presence para Copaiba Lexikon."""
    
    # Client ID do Discord Developer Portal (você pode criar um próprio)
    CLIENT_ID = "1448674009607569541"  # Copaiba Lexikon - Discord Developer Portal
    
    def __init__(self):
        self._rpc: Optional[Presence] = None
        self._connected = False
        self._current_voicebank: str = ""
        self._current_alias: str = ""
        self._alias_count: int = 0
        self._completed_count: int = 0
        self._start_time: int = int(time.time())  # Timestamp de início
        
    def connect(self) -> bool:
        """Conecta ao Discord RPC."""
        if not DISCORD_AVAILABLE:
            logger.debug("Discord RPC não disponível")
            return False
            
        try:
            self._rpc = Presence(self.CLIENT_ID)
            self._rpc.connect()
            self._connected = True
            print(f"[Discord RPC] Conectado com sucesso ao Discord!")
            logger.info("Discord RPC conectado")
            self._update_presence()
            return True
        except Exception as e:
            print(f"[Discord RPC] Falha ao conectar: {e}")
            logger.info(f"Falha ao conectar Discord RPC: {e}")
            self._connected = False
            return False
    
    def disconnect(self):
        """Desconecta do Discord RPC."""
        if self._rpc and self._connected:
            try:
                self._rpc.close()
            except:
                pass
            self._connected = False
            logger.debug("Discord RPC desconectado")
    
    def set_voicebank(self, voicebank_name: str, alias_count: int = 0):
        """Atualiza o voicebank sendo editado."""
        if voicebank_name:
            self._current_voicebank = Path(voicebank_name).name
        else:
            self._current_voicebank = ""
        self._alias_count = alias_count
        self._update_presence()
    
    def set_alias(self, alias: str, completed: int = 0, total: int = 0):
        """Atualiza o alias atual sendo editado."""
        self._current_alias = alias or ""
        self._completed_count = completed
        if total > 0:
            self._alias_count = total
        self._update_presence()
    
    def set_progress(self, completed: int, total: int):
        """Atualiza o progresso."""
        self._completed_count = completed
        self._alias_count = total
        self._update_presence()
    
    def _update_presence(self):
        """Atualiza o status no Discord."""
        if not self._connected or not self._rpc:
            return
            
        try:
            if self._current_voicebank:
                details = f"Editando: {self._current_voicebank}"
                
                if self._alias_count > 0:
                    state = f"Progresso: {self._completed_count}/{self._alias_count}"
                elif self._current_alias:
                    state = f"Alias: {self._current_alias}"
                else:
                    state = "Configurando parâmetros OTO"
                
                self._rpc.update(
                    details=details,
                    state=state,
                    start=self._start_time,
                    large_image="copaiba_logo",
                    large_text="Copaiba Lexikon - Editor de oto.ini",
                    small_image="editing",
                    small_text="Editando voicebank"
                )
            else:
                self._rpc.update(
                    details="Copaiba Lexikon",
                    state="Aguardando voicebank...",
                    start=self._start_time,
                    large_image="copaiba_logo",
                    large_text="Copaiba Lexikon - Editor de oto.ini"
                )
        except Exception as e:
            logger.debug(f"Erro ao atualizar Discord RPC: {e}")


# Singleton global
_discord_rpc: Optional[CopaibaDcordRPC] = None


def get_discord_rpc() -> CopaibaDcordRPC:
    """Retorna instância global do Discord RPC."""
    global _discord_rpc
    if _discord_rpc is None:
        _discord_rpc = CopaibaDcordRPC()
    return _discord_rpc


def init_discord_rpc() -> bool:
    """Inicializa e conecta o Discord RPC."""
    return get_discord_rpc().connect()


def shutdown_discord_rpc():
    """Desconecta e limpa o Discord RPC."""
    global _discord_rpc
    if _discord_rpc:
        _discord_rpc.disconnect()
        _discord_rpc = None
