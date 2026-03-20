# core/audio_player.py
"""
Reprodução de áudio para Copaiba Lexikon.
"""

import wave
import logging
from pathlib import Path
from typing import Tuple, Optional
import numpy as np

logger = logging.getLogger("copaiba.audio")

# Importa sounddevice se disponível
try:
    import sounddevice as sd
    SOUNDDEVICE_AVAILABLE = True
except ImportError:
    SOUNDDEVICE_AVAILABLE = False
    sd = None


class AudioPlayer:
    """
    Player de áudio com cache e suporte a reprodução de segmentos.
    
    Usa sounddevice para reprodução em background.
    """
    
    def __init__(self):
        self._current_stream = None
        self._audio_cache: dict[str, Tuple[np.ndarray, int]] = {}
        self._cache_max_size = 20
        self._device_id: Optional[int] = None  # None = dispositivo padrão
    
    @property
    def is_available(self) -> bool:
        """Retorna se o player está disponível."""
        return SOUNDDEVICE_AVAILABLE
    
    @staticmethod
    def get_output_devices() -> list[dict]:
        """
        Retorna lista de dispositivos de saída de áudio disponíveis.
        
        Returns:
            Lista de dicionários com 'id', 'name', 'channels'
        """
        if not SOUNDDEVICE_AVAILABLE:
            return []
        
        try:
            devices = sd.query_devices()
            output_devices = []
            for i, device in enumerate(devices):
                if device['max_output_channels'] > 0:
                    output_devices.append({
                        'id': i,
                        'name': device['name'],
                        'channels': device['max_output_channels']
                    })
            return output_devices
        except Exception as e:
            logger.error(f"Erro ao listar dispositivos: {e}")
            return []
    
    @staticmethod
    def get_default_device() -> Optional[int]:
        """Retorna o ID do dispositivo de saída padrão."""
        if not SOUNDDEVICE_AVAILABLE:
            return None
        try:
            return sd.default.device[1]  # [1] é output
        except:
            return None
    
    def set_output_device(self, device_id: Optional[int]):
        """Define o dispositivo de saída. None = padrão do sistema."""
        self._device_id = device_id
        if SOUNDDEVICE_AVAILABLE and device_id is not None:
            try:
                sd.default.device = (sd.default.device[0], device_id)
                logger.info(f"Dispositivo de áudio definido: {device_id}")
            except Exception as e:
                logger.error(f"Erro ao definir dispositivo: {e}")
    
    def get_output_device(self) -> Optional[int]:
        """Retorna o ID do dispositivo de saída atual."""
        return self._device_id

    def stop(self) -> None:
        """Para a reprodução atual."""
        if not SOUNDDEVICE_AVAILABLE:
            return
            
        if self._current_stream is not None:
            try:
                sd.stop()
            except Exception:
                pass
            self._current_stream = None

    def _load_audio(self, path: Path) -> Tuple[np.ndarray, int]:
        """
        Carrega áudio do disco ou do cache.
        
        Args:
            path: Caminho do arquivo de áudio
            
        Returns:
            Tupla (data, framerate)
        """
        key = str(path)
        if key in self._audio_cache:
            return self._audio_cache[key]
            
        try:
            with wave.open(str(path), 'rb') as wf:
                framerate = wf.getframerate()
                n_channels = wf.getnchannels()
                sampwidth = wf.getsampwidth()
                n_frames = wf.getnframes()
                raw = wf.readframes(n_frames)
                
            # Conversão de formato
            if sampwidth == 1:
                data = np.frombuffer(raw, dtype=np.uint8).astype(np.float32)
                data = (data - 128.0) / 128.0
            elif sampwidth == 2:
                data = np.frombuffer(raw, dtype=np.int16).astype(np.float32)
                data /= 32768.0
            else:
                data = np.frombuffer(raw, dtype=np.int16).astype(np.float32)
                max_val = np.max(np.abs(data))
                if max_val > 0:
                    data /= max_val
                    
            # Converter para mono se necessário
            if n_channels > 1:
                data = data.reshape(-1, n_channels)
                
            # Gerenciar cache
            if len(self._audio_cache) >= self._cache_max_size:
                oldest = next(iter(self._audio_cache))
                del self._audio_cache[oldest]
                
            self._audio_cache[key] = (data, framerate)
            return data, framerate
            
        except Exception as e:
            logger.error(f"Erro ao carregar áudio: {e}")
            return np.array([]), 44100

    def play_segment(
        self, 
        path: Path, 
        start_ms: float, 
        end_ms: float
    ) -> bool:
        """
        Reproduz segmento de áudio.
        
        Args:
            path: Caminho do arquivo
            start_ms: Tempo inicial em milissegundos
            end_ms: Tempo final em milissegundos
            
        Returns:
            True se iniciou reprodução, False caso contrário
        """
        if not SOUNDDEVICE_AVAILABLE:
            logger.warning("sounddevice não disponível")
            return False
            
        self.stop()
        data, framerate = self._load_audio(path)
        
        if data.size == 0:
            return False
            
        # Calcular amostras
        start_sample = int(start_ms * framerate / 1000.0)
        end_sample = int(end_ms * framerate / 1000.0)
        start_sample = max(0, start_sample)
        
        if len(data.shape) == 1:
            end_sample = min(len(data), end_sample)
        else:
            end_sample = min(len(data), end_sample)
            
        segment = data[start_sample:end_sample]
        
        if segment.size == 0:
            return False
            
        try:
            sd.play(segment, framerate)
            self._current_stream = True
            return True
        except Exception as e:
            logger.error(f"Erro ao reproduzir: {e}")
            return False

    def play_full(self, path: Path) -> bool:
        """
        Reproduz arquivo de áudio completo.
        
        Args:
            path: Caminho do arquivo
            
        Returns:
            True se iniciou reprodução, False caso contrário
        """
        if not SOUNDDEVICE_AVAILABLE:
            logger.warning("sounddevice não disponível")
            return False
            
        self.stop()
        data, framerate = self._load_audio(path)
        
        if data.size == 0:
            return False
            
        try:
            sd.play(data, framerate)
            self._current_stream = True
            return True
        except Exception as e:
            logger.error(f"Erro ao reproduzir: {e}")
            return False
    
    def clear_cache(self) -> None:
        """Limpa o cache de áudio."""
        self._audio_cache.clear()
