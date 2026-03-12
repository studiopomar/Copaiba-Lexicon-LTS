# core/waveform_cache.py
"""
Cache LRU para waveforms carregadas.
Evita recarregar arquivos de áudio do disco repetidamente.
"""

from collections import OrderedDict
from pathlib import Path
from typing import Tuple, Optional
import numpy as np
import threading
import time


class WaveformCache:
    """
    Cache LRU (Least Recently Used) para waveforms.
    
    Mantém arquivos de áudio na memória para acesso rápido,
    com limite de itens e memória para evitar uso excessivo de RAM.
    """
    
    def __init__(self, max_items: int = 20, max_memory_mb: int = 200):
        """
        Inicializa o cache.
        
        Args:
            max_items: Número máximo de waveforms em cache
            max_memory_mb: Limite de memória em megabytes
        """
        self._cache: OrderedDict[str, Tuple[np.ndarray, np.ndarray, float]] = OrderedDict()
        self._max_items = max_items
        self._max_memory = max_memory_mb * 1024 * 1024
        self._lock = threading.Lock()
        self._hits = 0
        self._misses = 0
    
    def get(self, path: Path) -> Optional[Tuple[np.ndarray, np.ndarray]]:
        """
        Obtém waveform do cache.
        
        Args:
            path: Caminho do arquivo de áudio
        
        Returns:
            Tupla (times, data) ou None se não estiver em cache
        """
        key = str(path.resolve())
        with self._lock:
            if key in self._cache:
                # Move para o final (mais recente)
                self._cache.move_to_end(key)
                times, data, _ = self._cache[key]
                self._hits += 1
                return times.copy(), data.copy()
            self._misses += 1
        return None
    
    def put(self, path: Path, times: np.ndarray, data: np.ndarray) -> None:
        """
        Adiciona waveform ao cache.
        
        Args:
            path: Caminho do arquivo de áudio
            times: Array de tempos
            data: Array de amplitudes
        """
        key = str(path.resolve())
        with self._lock:
            # Remove se já existe
            if key in self._cache:
                del self._cache[key]
            
            # Adiciona novo item
            self._cache[key] = (times.copy(), data.copy(), time.time())
            
            # Evita excesso
            self._evict_if_needed()
    
    def _evict_if_needed(self) -> None:
        """Remove itens antigos se necessário."""
        # Limite de itens
        while len(self._cache) > self._max_items:
            self._cache.popitem(last=False)
        
        # Limite de memória
        total_size = self._get_total_memory()
        while total_size > self._max_memory and self._cache:
            self._cache.popitem(last=False)
            total_size = self._get_total_memory()
    
    def _get_total_memory(self) -> int:
        """Retorna memória total usada em bytes."""
        return sum(t.nbytes + d.nbytes for t, d, _ in self._cache.values())
    
    def clear(self) -> None:
        """Limpa todo o cache."""
        with self._lock:
            self._cache.clear()
            self._hits = 0
            self._misses = 0
    
    def invalidate(self, path: Path) -> bool:
        """
        Remove item específico do cache.
        
        Args:
            path: Caminho do arquivo a invalidar
        
        Returns:
            True se o item foi removido, False se não existia
        """
        key = str(path.resolve())
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
        return False
    
    def get_stats(self) -> dict:
        """Retorna estatísticas do cache."""
        with self._lock:
            total_calls = self._hits + self._misses
            hit_rate = self._hits / total_calls if total_calls > 0 else 0
            return {
                'items': len(self._cache),
                'max_items': self._max_items,
                'memory_mb': self._get_total_memory() / (1024 * 1024),
                'max_memory_mb': self._max_memory / (1024 * 1024),
                'hits': self._hits,
                'misses': self._misses,
                'hit_rate': hit_rate,
            }
    
    def __len__(self) -> int:
        return len(self._cache)
    
    def __contains__(self, path: Path) -> bool:
        key = str(path.resolve())
        return key in self._cache
    
    def prefetch(self, path: Path) -> None:
        """
        Pré-carrega um arquivo de áudio em thread separada.
        Se já estiver em cache, não faz nada.
        
        Args:
            path: Caminho do arquivo a pré-carregar
        """
        if path in self:
            return  # Já em cache
        
        def _load_in_background():
            try:
                # Import local para evitar circular import
                from audio_loader import load_waveform_sync
                load_waveform_sync(path, use_cache=True, normalize=True)
            except Exception:
                pass  # Silently ignore prefetch failures
        
        thread = threading.Thread(target=_load_in_background, daemon=True)
        thread.start()
    
    def prefetch_paths(self, paths: list) -> None:
        """
        Pré-carrega múltiplos arquivos em background.
        
        Args:
            paths: Lista de caminhos para pré-carregar
        """
        for path in paths:
            if path and path not in self:
                self.prefetch(path)


# Instância global do cache
waveform_cache = WaveformCache()
