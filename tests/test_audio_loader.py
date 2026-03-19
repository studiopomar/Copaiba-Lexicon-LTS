# tests/test_audio_loader.py
"""
Testes para o módulo audio_loader.
"""

import pytest
import numpy as np


class TestAudioLoader:
    """Testes para funções de carregamento de áudio."""
    
    def test_import(self):
        """Verifica se o módulo pode ser importado."""
        from audio_loader import load_waveform_sync, read_wav_file
        assert load_waveform_sync is not None
        assert read_wav_file is not None
    
    def test_read_wav_file(self, sample_wav_file):
        """Testa leitura de arquivo WAV."""
        from audio_loader import read_wav_file
        
        data, framerate = read_wav_file(str(sample_wav_file))
        
        assert framerate == 44100
        assert len(data) > 0
        assert data.dtype == np.float32
    
    def test_read_nonexistent_file(self, temp_dir):
        """Testa leitura de arquivo inexistente."""
        from audio_loader import read_wav_file
        
        data, framerate = read_wav_file(str(temp_dir / "nao_existe.wav"))
        
        assert len(data) == 0
        assert framerate == 44100
    
    def test_load_waveform_sync(self, sample_wav_file):
        """Testa carregamento de waveform."""
        from audio_loader import load_waveform_sync
        
        times, values = load_waveform_sync(sample_wav_file)
        
        assert len(times) > 0
        assert len(values) > 0
        assert len(times) == len(values)
    
    def test_load_waveform_cache(self, sample_wav_file):
        """Testa cache de waveform."""
        from audio_loader import load_waveform_sync
        
        # Primeira chamada
        times1, values1 = load_waveform_sync(sample_wav_file, use_cache=True)
        
        # Segunda chamada (deve usar cache)
        times2, values2 = load_waveform_sync(sample_wav_file, use_cache=True)
        
        np.testing.assert_array_equal(times1, times2)
        np.testing.assert_array_equal(values1, values2)


class TestWaveformCache:
    """Testes para o cache de waveforms."""
    
    def test_import(self):
        """Verifica se o cache pode ser importado."""
        from core.waveform_cache import WaveformCache, waveform_cache
        assert WaveformCache is not None
        assert waveform_cache is not None
    
    def test_put_get(self, temp_dir):
        """Testa put e get do cache."""
        from core.waveform_cache import WaveformCache
        
        cache = WaveformCache(max_items=5)
        
        path = temp_dir / "test.wav"
        times = np.array([0.0, 1.0, 2.0], dtype=np.float32)
        values = np.array([0.5, -0.5, 0.0], dtype=np.float32)
        
        cache.put(path, times, values)
        
        result = cache.get(path)
        assert result is not None
        
        cached_times, cached_values = result
        np.testing.assert_array_equal(times, cached_times)
        np.testing.assert_array_equal(values, cached_values)
    
    def test_lru_eviction(self, temp_dir):
        """Testa evicção LRU."""
        from core.waveform_cache import WaveformCache
        
        cache = WaveformCache(max_items=3)
        
        # Adicionar 4 itens (um a mais que o limite)
        for i in range(4):
            path = temp_dir / f"test_{i}.wav"
            times = np.array([float(i)], dtype=np.float32)
            values = np.array([float(i)], dtype=np.float32)
            cache.put(path, times, values)
        
        # O primeiro item deve ter sido removido
        assert cache.get(temp_dir / "test_0.wav") is None
        
        # Os outros devem estar no cache
        assert cache.get(temp_dir / "test_3.wav") is not None
    
    def test_invalidate(self, temp_dir):
        """Testa invalidação de item."""
        from core.waveform_cache import WaveformCache
        
        cache = WaveformCache()
        
        path = temp_dir / "test.wav"
        times = np.array([0.0], dtype=np.float32)
        values = np.array([0.0], dtype=np.float32)
        
        cache.put(path, times, values)
        assert cache.get(path) is not None
        
        cache.invalidate(path)
        assert cache.get(path) is None
