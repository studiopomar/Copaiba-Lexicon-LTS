# core/logger.py
"""
Sistema de logging centralizado para Copaiba Lexikon.
"""

import logging
import sys
from pathlib import Path
from typing import Optional


def setup_logger(
    name: str = "copaiba",
    level: int = logging.INFO,
    log_to_file: bool = True,
    log_dir: Optional[Path] = None
) -> logging.Logger:
    """
    Configura logger com formatação padronizada.
    
    Args:
        name: Nome do logger
        level: Nível de logging (DEBUG, INFO, WARNING, ERROR)
        log_to_file: Se True, também salva logs em arquivo
        log_dir: Diretório para arquivo de log
    
    Returns:
        Logger configurado
    """
    logger = logging.getLogger(name)
    
    # Evitar duplicação de handlers
    if logger.handlers:
        return logger
    
    logger.setLevel(level)
    
    # Formatação para console (colorida e concisa)
    console_format = logging.Formatter(
        '[%(levelname)s] %(message)s'
    )
    
    # Console handler
    console = logging.StreamHandler(sys.stdout)
    console.setLevel(level)
    console.setFormatter(console_format)
    logger.addHandler(console)
    
    # File handler (opcional)
    if log_to_file:
        if log_dir is None:
            log_dir = Path.home() / ".copaiba"
        
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / "copaiba.log"
        
        file_format = logging.Formatter(
            '%(asctime)s [%(levelname)s] %(name)s: %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)  # Arquivo recebe tudo
        file_handler.setFormatter(file_format)
        logger.addHandler(file_handler)
    
    return logger


def get_logger(name: str = "copaiba") -> logging.Logger:
    """Retorna logger existente ou cria novo."""
    return logging.getLogger(name)


# Logger global - configurado na primeira importação
logger = setup_logger()


# Atalhos para níveis comuns
def debug(msg: str, *args, **kwargs):
    """Log mensagem de debug."""
    logger.debug(msg, *args, **kwargs)


def info(msg: str, *args, **kwargs):
    """Log mensagem informativa."""
    logger.info(msg, *args, **kwargs)


def warning(msg: str, *args, **kwargs):
    """Log mensagem de aviso."""
    logger.warning(msg, *args, **kwargs)


def error(msg: str, *args, **kwargs):
    """Log mensagem de erro."""
    logger.error(msg, *args, **kwargs)


def exception(msg: str, *args, **kwargs):
    """Log exceção com traceback."""
    logger.exception(msg, *args, **kwargs)
