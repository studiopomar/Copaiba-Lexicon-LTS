# plugins/__init__.py
"""
Sistema de Plugins do Copaiba Lexikon
"""

from .base_plugin import BasePlugin
from .duplicate_detector import DuplicateDetectorPlugin
from .consistency_checker import ConsistencyCheckerPlugin
from .alias_sorter import AliasSorterPlugin
from .batch_rename import BatchRenamePlugin
from .romaji_hiragana import RomajiHiraganaPlugin
from .vv_detector import VVDetectorPlugin
from .pitch_analyzer import PitchAnalyzerPlugin
from .mic_tuner import MicTunerPlugin
from .oto_merger import OtoMergerPlugin

__all__ = [
    'BasePlugin',
    'DuplicateDetectorPlugin',
    'ConsistencyCheckerPlugin',
    'AliasSorterPlugin',
    'BatchRenamePlugin',
    'RomajiHiraganaPlugin',
    'VVDetectorPlugin',
    'PitchAnalyzerPlugin',
    'MicTunerPlugin',
    'OtoMergerPlugin',
]

