#backend_gpu.py
"""
Backend de aceleração GPU para Copaiba Lexikon.
Detecta automaticamente: NVIDIA (CUDA), AMD (ROCm/OpenCL), Intel (OpenCL), ou fallback CPU.
"""

from __future__ import annotations

import os
import sys
import platform
import logging
from typing import Tuple, Optional, Dict, Any
from dataclasses import dataclass
from enum import Enum
import numpy as np

# Logger para este módulo
logger = logging.getLogger("copaiba.gpu")


class GPUVendor(Enum):
    """Tipos de GPU suportados"""
    NVIDIA = "nvidia"
    AMD = "amd"
    INTEL = "intel"
    CPU = "cpu"


@dataclass
class GPUInfo:
    """Informações sobre o dispositivo GPU"""
    vendor: GPUVendor
    name: str
    memory_gb: float
    compute_capability: str
    backend: str
    available: bool

    def __str__(self):
        if self.vendor == GPUVendor.CPU:
            return f"CPU ({platform.processor() or 'Unknown'})"
        return f"{self.name} ({self.memory_gb:.1f}GB) [{self.backend}]"


class GPUBackend:
    """
    Backend unificado para processamento GPU.
    Detecta automaticamente o melhor backend disponível.
    """

    def __init__(self):
        self._enabled = False
        self._gpu_info: Optional[GPUInfo] = None
        self._xp = np  # Array library (numpy, cupy, etc.)
        self._backend_name = "numpy"

        # Cache para arrays GPU
        self._array_cache: Dict[str, Any] = {}
        self._cache_max_size = 100

        # Lazy loading - detecção acontece quando precisar
        self._detected_info: Optional[GPUInfo] = None
        self._detection_done = False

    @property
    def detected_info(self) -> GPUInfo:
        """Retorna info da GPU detectada (lazy loading)"""
        if not self._detection_done:
            self._detected_info = self._detect_gpu()
            self._detection_done = True
        return self._detected_info

    def _detect_gpu(self) -> GPUInfo:
        """Detecta automaticamente a GPU disponível"""
        logger.debug("Iniciando detecção de GPU...")

        # 1. Tenta NVIDIA (CuPy - CUDA)
        nvidia_info = self._try_nvidia()
        if nvidia_info and nvidia_info.available:
            logger.info(f"GPU NVIDIA detectada: {nvidia_info.name}")
            return nvidia_info

        # 2. Tenta AMD (PyOpenCL com ROCm ou OpenCL)
        amd_info = self._try_amd()
        if amd_info and amd_info.available:
            logger.info(f"GPU AMD detectada: {amd_info.name}")
            return amd_info

        # 3. Tenta Intel (PyOpenCL)
        intel_info = self._try_intel()
        if intel_info and intel_info.available:
            logger.info(f"GPU Intel detectada: {intel_info.name}")
            return intel_info

        # 4. Fallback para CPU
        logger.info("Nenhuma GPU compatível encontrada, usando CPU como fallback")
        return GPUInfo(
            vendor=GPUVendor.CPU,
            name=platform.processor() or "CPU",
            memory_gb=0,
            compute_capability="N/A",
            backend="numpy",
            available=True
        )

    def _try_nvidia(self) -> Optional[GPUInfo]:
        """Tenta detectar e inicializar NVIDIA GPU via CuPy"""
        try:
            import cupy as cp
            
            # Verifica se CUDA está disponível
            try:
                device_count = cp.cuda.runtime.getDeviceCount()
                if device_count == 0:
                    logger.debug("Nenhum dispositivo CUDA encontrado")
                    return None
            except:
                logger.debug("CUDA runtime não disponível")
                return None
            
            device = cp.cuda.Device(0)
            
            # Método 1: Usar device.attributes (mais moderno e confiável)
            try:
                attrs = device.attributes
                name = attrs.get('Name', 'NVIDIA GPU')
                if isinstance(name, bytes):
                    name = name.decode('utf-8')
                
                # Memória total em bytes
                total_mem = attrs.get('TotalGlobalMem', 0)
                if total_mem == 0:
                    # Fallback: tentar obter via memGetInfo
                    try:
                        free_mem, total_mem = cp.cuda.runtime.memGetInfo()
                    except:
                        total_mem = 0
                memory_gb = total_mem / (1024 ** 3)
                
                # Compute capability
                major = attrs.get('ComputeCapabilityMajor', 0)
                minor = attrs.get('ComputeCapabilityMinor', 0)
                compute_cap = f"{major}.{minor}"
                
                logger.info(f"NVIDIA GPU detectada: {name} ({memory_gb:.1f}GB, CC {compute_cap})")
                
                return GPUInfo(
                    vendor=GPUVendor.NVIDIA,
                    name=name,
                    memory_gb=memory_gb,
                    compute_capability=compute_cap,
                    backend="cupy",
                    available=True
                )
                
            except Exception as e1:
                logger.debug(f"Falha ao usar device.attributes: {e1}")
                
                # Método 2: Fallback para getDeviceProperties
                try:
                    props = cp.cuda.runtime.getDeviceProperties(device.id)
                    
                    # props pode ser um objeto com atributos ou uma struct
                    # Tenta diferentes formas de acesso
                    if hasattr(props, 'name'):
                        name = props.name
                        if isinstance(name, bytes):
                            name = name.decode('utf-8')
                    else:
                        name = "NVIDIA GPU"
                    
                    if hasattr(props, 'totalGlobalMem'):
                        memory_gb = props.totalGlobalMem / (1024 ** 3)
                    else:
                        try:
                            free_mem, total_mem = cp.cuda.runtime.memGetInfo()
                            memory_gb = total_mem / (1024 ** 3)
                        except:
                            memory_gb = 0.0
                    
                    if hasattr(props, 'major') and hasattr(props, 'minor'):
                        major = props.major
                        minor = props.minor
                        compute_cap = f"{major}.{minor}"
                    else:
                        compute_cap = "Unknown"
                    
                    logger.info(f"NVIDIA GPU detectada (fallback): {name} ({memory_gb:.1f}GB)")
                    
                    return GPUInfo(
                        vendor=GPUVendor.NVIDIA,
                        name=name,
                        memory_gb=memory_gb,
                        compute_capability=compute_cap,
                        backend="cupy",
                        available=True
                    )
                    
                except Exception as e2:
                    logger.debug(f"Falha ao usar getDeviceProperties: {e2}")
                    raise
            
        except ImportError:
            logger.debug("CuPy não instalado")
            return None
        except Exception as e:
            logger.warning(f"NVIDIA não disponível: {e}")
            return None


    def _try_amd(self) -> Optional[GPUInfo]:
        """Tenta detectar AMD GPU via PyOpenCL"""
        try:
            import pyopencl as cl
            logger.debug("PyOpenCL importado com sucesso")

            platforms = cl.get_platforms()
            logger.debug(f"Plataformas OpenCL encontradas: {[p.name for p in platforms]}")
            
            for platform_obj in platforms:
                platform_name = platform_obj.name.lower()
                platform_vendor = platform_obj.vendor.lower() if hasattr(platform_obj, 'vendor') else ''
                logger.debug(f"Verificando plataforma: {platform_obj.name}, vendor: {platform_vendor}")

                # Verifica plataformas AMD: ROCm, AMD proprietário, rusticl/Mesa
                is_amd_platform = any(x in platform_name for x in ['amd', 'rocm', 'rusticl', 'mesa'])
                is_amd_vendor = 'amd' in platform_vendor or 'advanced micro' in platform_vendor
                
                if is_amd_platform or is_amd_vendor:
                    logger.debug(f"Plataforma AMD detectada: {platform_obj.name}")
                    try:
                        devices = platform_obj.get_devices(device_type=cl.device_type.GPU)
                        logger.debug(f"Dispositivos GPU encontrados: {[d.name for d in devices]}")
                    except cl.RuntimeError as e:
                        logger.debug(f"Erro ao obter dispositivos: {e}")
                        continue

                    for device in devices:
                        device_name = device.name.lower()
                        logger.debug(f"Verificando dispositivo: {device.name} (lower: {device_name})")
                        
                        # Verifica se é uma GPU AMD pelo nome do dispositivo
                        # 'gfx' é o prefixo usado pelos drivers AMD no Windows (ex: gfx1012 = RX 5500 XT)
                        is_amd_device = ('radeon' in device_name or 
                                        'amd' in device_name or 
                                        device_name.startswith('gfx') or
                                        'gfx' in device_name)  # Também verifica se contém 'gfx'
                        
                        logger.debug(f"É dispositivo AMD? {is_amd_device}")
                        
                        if is_amd_device:
                            name = device.name
                            # Traduz códigos gfx para nomes amigáveis
                            if 'gfx' in name.lower():
                                name = f"AMD Radeon ({device.name.split(':')[0]})"
                            memory_gb = device.global_mem_size / (1024 ** 3)
                            
                            logger.info(f"GPU AMD encontrada: {name} ({memory_gb:.1f}GB)")

                            return GPUInfo(
                                vendor=GPUVendor.AMD,
                                name=name,
                                memory_gb=memory_gb,
                                compute_capability=device.version,
                                backend="pyopencl",
                                available=True
                            )

            logger.debug("Nenhuma GPU AMD encontrada")
            return None
        except ImportError as e:
            logger.debug(f"PyOpenCL não instalado: {e}")
            return None
        except Exception as e:
            logger.warning(f"Erro ao detectar AMD: {e}")
            return None

    def _try_intel(self) -> Optional[GPUInfo]:
        """Tenta detectar Intel GPU via PyOpenCL"""
        try:
            import pyopencl as cl

            platforms = cl.get_platforms()
            for platform_obj in platforms:
                platform_name = platform_obj.name.lower()

                if 'intel' in platform_name:
                    devices = platform_obj.get_devices(device_type=cl.device_type.GPU)

                    if devices:
                        device = devices[0]
                        name = device.name
                        memory_gb = device.global_mem_size / (1024 ** 3)

                        return GPUInfo(
                            vendor=GPUVendor.INTEL,
                            name=name,
                            memory_gb=memory_gb,
                            compute_capability=device.version,
                            backend="pyopencl",
                            available=True
                        )

            return None
        except Exception as e:
            logger.debug(f"Intel não disponível: {e}")
            return None

    def enable(self) -> bool:
        """Ativa aceleração GPU"""
        info = self.detected_info  # Usa a propriedade para lazy loading
        
        if info.vendor == GPUVendor.CPU:
            logger.info("Nenhuma GPU detectada, usando CPU")
            self._enabled = False
            return False

        try:
            if info.vendor == GPUVendor.NVIDIA:
                import cupy as cp
                self._xp = cp
                self._backend_name = "cupy"

            elif info.vendor in (GPUVendor.AMD, GPUVendor.INTEL):
                # Para AMD/Intel, usamos PyOpenCL com wrapper
                self._xp = np  # Mantém numpy, mas usa OpenCL para operações pesadas
                self._backend_name = "pyopencl"
                self._init_opencl()

            self._gpu_info = info
            self._enabled = True
            logger.info(f"GPU ativada: {self._gpu_info}")
            return True

        except Exception as e:
            logger.error(f"Erro ao ativar GPU: {e}")
            self._enabled = False
            return False

    def disable(self):
        """Desativa aceleração GPU"""
        self._enabled = False
        self._xp = np
        self._backend_name = "numpy"
        self._array_cache.clear()
        logger.info("GPU desativada, usando CPU")

    def _init_opencl(self):
        """Inicializa contexto OpenCL para AMD/Intel"""
        try:
            import pyopencl as cl

            # Encontra a plataforma e dispositivo corretos
            platforms = cl.get_platforms()
            target_vendor = self._detected_info.vendor
            
            logger.debug(f"Procurando dispositivo OpenCL para {target_vendor.value}")
            logger.debug(f"Plataformas disponíveis: {[p.name for p in platforms]}")

            for platform_obj in platforms:
                platform_name = platform_obj.name.lower()
                
                # Verifica plataformas compatíveis
                is_compatible = any(x in platform_name for x in ['amd', 'rocm', 'rusticl', 'mesa', 'intel'])
                
                if is_compatible:
                    try:
                        devices = platform_obj.get_devices(device_type=cl.device_type.GPU)
                        logger.debug(f"Plataforma {platform_obj.name}: {len(devices)} GPU(s)")
                    except cl.RuntimeError as e:
                        logger.debug(f"Erro ao obter dispositivos de {platform_obj.name}: {e}")
                        continue
                    
                    for device in devices:
                        device_name = device.name.lower()
                        logger.debug(f"Verificando dispositivo: {device.name}")
                        
                        # Verifica se o dispositivo corresponde ao vendor detectado
                        # 'gfx' é o prefixo usado pelos drivers AMD no Windows
                        is_amd_device = ('radeon' in device_name or 
                                        'amd' in device_name or 
                                        device_name.startswith('gfx'))
                        is_intel_device = 'intel' in device_name
                        
                        if target_vendor == GPUVendor.AMD and is_amd_device:
                            logger.info(f"Inicializando contexto OpenCL para AMD: {device.name}")
                            self._cl_context = cl.Context([device])
                            self._cl_queue = cl.CommandQueue(self._cl_context)
                            self._cl_device = device
                            logger.info("Contexto OpenCL AMD inicializado com sucesso")
                            return
                        elif target_vendor == GPUVendor.INTEL and is_intel_device:
                            logger.info(f"Inicializando contexto OpenCL para Intel: {device.name}")
                            self._cl_context = cl.Context([device])
                            self._cl_queue = cl.CommandQueue(self._cl_context)
                            self._cl_device = device
                            logger.info("Contexto OpenCL Intel inicializado com sucesso")
                            return

            raise RuntimeError(f"Dispositivo OpenCL não encontrado para {target_vendor.value}")

        except ImportError as e:
            logger.error(f"PyOpenCL não instalado: {e}")
            raise
        except Exception as e:
            logger.error(f"Erro ao inicializar OpenCL: {e}")
            raise

    @property
    def is_enabled(self) -> bool:
        return self._enabled

    @property
    def info(self) -> GPUInfo:
        return self._gpu_info or self.detected_info

    @property
    def xp(self):
        """Retorna a biblioteca de array atual (numpy ou cupy)"""
        return self._xp

    def to_gpu(self, arr: np.ndarray) -> Any:
        """Move array para GPU se habilitado"""
        if not self._enabled:
            return arr

        if self._backend_name == "cupy":
            import cupy as cp
            return cp.asarray(arr)

        return arr

    def to_cpu(self, arr: Any) -> np.ndarray:
        """Move array para CPU"""
        if not self._enabled:
            return arr if isinstance(arr, np.ndarray) else np.asarray(arr)

        if self._backend_name == "cupy":
            import cupy as cp
            if isinstance(arr, cp.ndarray):
                return cp.asnumpy(arr)

        return arr if isinstance(arr, np.ndarray) else np.asarray(arr)

    def process_audio(
        self,
        raw_data: bytes,
        n_channels: int,
        sampwidth: int,
        framerate: int,
        max_points: int = 8000
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Processa dados de áudio brutos.
        Usa GPU se disponível, senão CPU.
        """
        xp = self._xp

        # Converte bytes para array
        if sampwidth == 1:
            data = xp.frombuffer(raw_data, dtype=xp.uint8)
            data = (data.astype(xp.float32) - 128.0) * (1.0 / 128.0)
        elif sampwidth == 2:
            data = xp.frombuffer(raw_data, dtype=xp.int16)
            data = data.astype(xp.float32) * (1.0 / 32768.0)
        else:
            data = xp.frombuffer(raw_data, dtype=xp.int16).astype(xp.float32)
            max_val = xp.max(xp.abs(data))
            if max_val > 0:
                data = data * (1.0 / max_val)

        # Converte para mono
        if n_channels > 1:
            data = data.reshape(-1, n_channels).mean(axis=1)

        total = data.size
        if total == 0 or framerate <= 0:
            return np.array([], dtype=np.float32), np.array([], dtype=np.float32)

        # Downsampling
        step = max(1, total // max_points)

        if step > 1:
            data_ds = self._peak_downsample(data, step)
        else:
            data_ds = data

        n = data_ds.size
        times = xp.arange(n, dtype=xp.float32) * (step / float(framerate))

        # Normalização
        max_amp = xp.max(xp.abs(data_ds)) if n > 0 else 1.0
        if max_amp > 0:
            values = data_ds * (1.0 / max_amp)
        else:
            values = data_ds

        # Converte para CPU
        return self.to_cpu(times), self.to_cpu(values)

    def _peak_downsample(self, data, step: int):
        """Downsampling preservando picos"""
        xp = self._xp

        n_blocks = len(data) // step
        if n_blocks == 0:
            return data

        truncated = data[:n_blocks * step]
        blocks = truncated.reshape(n_blocks, step)

        # Pega valor com maior magnitude em cada bloco
        max_indices = xp.argmax(xp.abs(blocks), axis=1)
        result = blocks[xp.arange(n_blocks), max_indices]

        return result

    def find_peaks(
        self,
        data: np.ndarray,
        times: np.ndarray,
        center_idx: int,
        window_size: int = 100
    ) -> float:
        """Encontra pico mais próximo"""
        left = max(0, center_idx - window_size)
        right = min(len(data), center_idx + window_size)

        if right <= left:
            return float(times[center_idx]) if center_idx < len(times) else 0.0

        if self._enabled and self._backend_name == "cupy":
            import cupy as cp
            window = cp.asarray(data[left:right])
            rel_idx = int(cp.argmax(cp.abs(window)))
        else:
            window = np.abs(data[left:right])
            rel_idx = int(np.argmax(window))

        return float(times[left + rel_idx])

    def find_zero_crossings(
        self,
        data: np.ndarray,
        times: np.ndarray,
        center_time: float,
        window_size: int = 50
    ) -> float:
        """Encontra cruzamento de zero mais próximo"""
        center_idx = int(np.searchsorted(times, center_time))
        left = max(0, center_idx - window_size)
        right = min(len(data), center_idx + window_size)

        if right <= left:
            return center_time

        if self._enabled and self._backend_name == "cupy":
            import cupy as cp
            window = cp.asarray(data[left:right])
            signs = cp.sign(window)
            diff_signs = cp.diff(signs)
            crossings = cp.where(diff_signs != 0)[0]

            if len(crossings) > 0:
                target = center_idx - left
                rel_idx = int(crossings[cp.argmin(cp.abs(crossings - target))])
                return float(times[left + rel_idx])
        else:
            signs = np.sign(data[left:right])
            crossings = np.where(np.diff(signs) != 0)[0]

            if len(crossings) > 0:
                target = center_idx - left
                rel_idx = int(crossings[np.argmin(np.abs(crossings - target))])
                return float(times[left + rel_idx])

        return center_time


# ============================================================
# Singleton Global
# ============================================================

_gpu_backend: Optional[GPUBackend] = None


def get_gpu_backend() -> GPUBackend:
    """Retorna a instância global do backend GPU"""
    global _gpu_backend
    if _gpu_backend is None:
        _gpu_backend = GPUBackend()
    return _gpu_backend


def gpu_available() -> bool:
    """Verifica se alguma GPU está disponível"""
    backend = get_gpu_backend()
    return backend.detected_info.vendor != GPUVendor.CPU


def gpu_enabled() -> bool:
    """Verifica se GPU está habilitada"""
    return get_gpu_backend().is_enabled


def enable_gpu() -> bool:
    """Ativa aceleração GPU"""
    return get_gpu_backend().enable()


def disable_gpu():
    """Desativa aceleração GPU"""
    get_gpu_backend().disable()


def get_gpu_info() -> GPUInfo:
    """Retorna informações da GPU detectada"""
    return get_gpu_backend().detected_info


def get_device_name() -> str:
    """Retorna nome do dispositivo atual"""
    backend = get_gpu_backend()
    if backend.is_enabled:
        return str(backend.info)
    return str(backend.detected_info)