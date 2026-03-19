# audio_loader.py

from __future__ import annotations
import wave
import logging
from pathlib import Path
from typing import Tuple, Optional
import numpy as np
from PySide6.QtCore import QThread, Signal

# Logger
logger = logging.getLogger("copaiba.audio")

try:
    from backend_gpu import get_gpu_backend, gpu_enabled

    GPU_BACKEND_AVAILABLE = True
except ImportError:
    GPU_BACKEND_AVAILABLE = False


    def gpu_enabled():
        return False


# Cache de waveforms
try:
    from core.waveform_cache import waveform_cache
    CACHE_AVAILABLE = True
except ImportError:
    CACHE_AVAILABLE = False
    waveform_cache = None


def read_wav_file(path: str) -> Tuple[np.ndarray, int]:
    """Lê arquivo WAV de forma robusta, lidando com diferentes bit depths e erros de caminho."""
    p = Path(path)

    if not p.exists() or not p.is_file():
        logger.warning(f"Arquivo não encontrado: {p}")
        return np.array([], dtype=np.float32), 44100

    try:
        with wave.open(str(p), "rb") as wf:
            n_channels = wf.getnchannels()
            n_frames = wf.getnframes()
            sampwidth = wf.getsampwidth()
            framerate = wf.getframerate()
            raw = wf.readframes(n_frames)
    except Exception as e:
        logger.error(f"Erro ao abrir WAV ({p.name}): {e}")
        return np.array([], dtype=np.float32), 44100

    # Decodificação baseada em largura de bits
    if sampwidth == 1:
        data = np.frombuffer(raw, dtype=np.uint8)
        data = (data.astype(np.float32) - 128.0) / 128.0
    elif sampwidth == 2:
        data = np.frombuffer(raw, dtype=np.int16)
        data = data.astype(np.float32) / 32768.0
    elif sampwidth == 3:
        # 24-bit fallback
        temp = np.frombuffer(raw, dtype=np.uint8)
        trim = temp.size - (temp.size % 3)
        temp = temp[:trim]
        if temp.size > 0:
            temp = temp.reshape(-1, 3)
            msb = temp[:, 2].astype(np.int16) * 256
            mid = temp[:, 1].astype(np.int16)
            data = (msb + mid).astype(np.float32) / 32768.0
        else:
            data = np.zeros(n_frames, dtype=np.float32)
    elif sampwidth == 4:
        try:
            data = np.frombuffer(raw, dtype=np.float32)
        except:
            data = np.frombuffer(raw, dtype=np.int32).astype(np.float32) / 2147483648.0
    else:
        return np.array([], dtype=np.float32), framerate

    # Converte Estéreo para Mono
    if n_channels > 1:
        limit = (data.size // n_channels) * n_channels
        data = data[:limit]
        data = data.reshape(-1, n_channels).mean(axis=1)

    return data, framerate


def load_waveform_sync(
    path: Path, 
    max_points: int = 8000,
    use_cache: bool = True,
    normalize: bool = True
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Carrega waveform de forma síncrona.
    
    Args:
        path: Caminho do arquivo de áudio
        max_points: Número máximo de pontos para downsampling
        use_cache: Se True, usa cache de waveforms
        normalize: Se True, normaliza a amplitude para visualização
    
    Returns:
        Tupla (times, values) como arrays numpy
    """
    # Verificar cache primeiro (somente se normalize=True, pois cache é normalizado)
    if use_cache and normalize and CACHE_AVAILABLE and waveform_cache is not None:
        cached = waveform_cache.get(path)
        if cached is not None:
            logger.debug(f"Cache hit: {path.name}")
            return cached
    
    # Carregar do disco
    logger.debug(f"Carregando: {path.name}")
    data, framerate = read_wav_file(str(path))
    total_samples = data.size

    if total_samples == 0:
        return np.array([], dtype=np.float32), np.array([], dtype=np.float32)

    # Usa GPU se disponível
    if GPU_BACKEND_AVAILABLE and gpu_enabled():
        backend = get_gpu_backend()
        xp = backend.xp
        
        # Move dados para GPU
        data_gpu = backend.to_gpu(data)
        
        # --- NORMALIZAÇÃO PARA VISUALIZAÇÃO (GPU) ---
        if normalize:
            max_amp = float(xp.max(xp.abs(data_gpu)))
            if max_amp > 0:
                data_gpu = data_gpu / max_amp
        
        # Algoritmo Min/Max Intercalado (Visualização Sólida) - GPU
        if total_samples > max_points:
            step = max(1, int(total_samples // max_points))
            n_usable = (total_samples // step) * step
            truncated = data_gpu[:n_usable]
            blocks = truncated.reshape(-1, step)

            mins = xp.min(blocks, axis=1)
            maxs = xp.max(blocks, axis=1)

            values = xp.empty(mins.size * 2, dtype=xp.float32)
            values[0::2] = mins
            values[1::2] = maxs

            t_steps = (xp.arange(len(blocks)) * step) / float(framerate)
            times = xp.empty(values.size, dtype=xp.float32)
            times[0::2] = t_steps
            times[1::2] = t_steps
        else:
            values = data_gpu
            times = xp.arange(total_samples, dtype=xp.float32) / float(framerate)
        
        # Move de volta para CPU
        times_cpu = backend.to_cpu(times)
        values_cpu = backend.to_cpu(values)
        
        # Salvar no cache (somente se normalizado)
        if use_cache and normalize and CACHE_AVAILABLE and waveform_cache is not None:
            waveform_cache.put(path, times_cpu, values_cpu)
        
        return times_cpu, values_cpu
    
    # Fallback CPU
    # --- NORMALIZAÇÃO PARA VISUALIZAÇÃO ---
    if normalize:
        max_amp = np.max(np.abs(data))
        if max_amp > 0:
            data = data / max_amp

    # Algoritmo Min/Max Intercalado (Visualização Sólida)
    if total_samples > max_points:
        step = max(1, int(total_samples // max_points))
        n_usable = (total_samples // step) * step
        truncated = data[:n_usable]
        blocks = truncated.reshape(-1, step)

        mins = blocks.min(axis=1)
        maxs = blocks.max(axis=1)

        values = np.empty(mins.size * 2, dtype=np.float32)
        values[0::2] = mins
        values[1::2] = maxs

        t_steps = (np.arange(len(blocks)) * step) / float(framerate)
        times = np.empty(values.size, dtype=np.float32)
        times[0::2] = t_steps
        times[1::2] = t_steps
    else:
        values = data
        times = np.arange(total_samples, dtype=np.float32) / float(framerate)

    # Salvar no cache (somente se normalizado)
    if use_cache and normalize and CACHE_AVAILABLE and waveform_cache is not None:
        waveform_cache.put(path, times, values)

    return times, values


class WaveformLoaderThread(QThread):
    finished = Signal(np.ndarray, np.ndarray, str)

    def __init__(self, path: Path, max_points: int, cache_key: str):
        super().__init__()
        self.path = path
        self.max_points = max_points
        self.cache_key = cache_key

    def run(self):
        times, values = load_waveform_sync(self.path, self.max_points)
        self.finished.emit(times, values, self.cache_key)