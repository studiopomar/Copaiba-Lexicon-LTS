# core/__init__.py
"""
Módulo core do Copaiba Lexikon.
Contém lógica central da aplicação.
"""

from .logger import logger, setup_logger
from .waveform_cache import waveform_cache, WaveformCache
from .audio_player import AudioPlayer

__all__ = [
    'logger',
    'setup_logger',
    'waveform_cache',
    'WaveformCache',
    'AudioPlayer',
]
