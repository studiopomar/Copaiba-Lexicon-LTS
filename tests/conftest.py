# tests/conftest.py
"""
Configurações e fixtures para pytest.
"""

import pytest
from pathlib import Path
import tempfile
import shutil


@pytest.fixture
def temp_dir():
    """Cria diretório temporário para testes."""
    d = tempfile.mkdtemp()
    yield Path(d)
    shutil.rmtree(d, ignore_errors=True)


@pytest.fixture
def sample_oto_content():
    """Conteúdo de exemplo de um arquivo oto.ini."""
    return """a.wav=a,0,100,50,30,-100
i.wav=i,10,150,60,40,-120
u.wav=u,20,200,70,50,-150
e.wav=e,5,120,55,35,-110
o.wav=o,15,180,65,45,-130"""


@pytest.fixture
def temp_oto_file(temp_dir, sample_oto_content):
    """Cria arquivo oto.ini temporário."""
    oto_path = temp_dir / "oto.ini"
    oto_path.write_text(sample_oto_content, encoding="utf-8")
    return oto_path


@pytest.fixture
def sample_wav_file(temp_dir):
    """Cria arquivo WAV temporário (silêncio)."""
    import wave
    import numpy as np
    
    wav_path = temp_dir / "test.wav"
    
    sample_rate = 44100
    duration = 0.5  # 500ms
    samples = int(sample_rate * duration)
    
    # Gerar onda senoidal simples
    t = np.linspace(0, duration, samples, dtype=np.float32)
    data = (np.sin(2 * np.pi * 440 * t) * 32767).astype(np.int16)
    
    with wave.open(str(wav_path), 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(data.tobytes())
    
    return wav_path
