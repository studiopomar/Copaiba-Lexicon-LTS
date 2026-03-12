# synthesis_test.py
"""
Synthesis Test - Testa aliases com resampler UTAU.
Permite ouvir como a sample vai soar quando sintetizada.

Atalho: Ctrl+Shift+Space
"""

from __future__ import annotations

import os
import subprocess
import tempfile
from pathlib import Path
from typing import Optional, Tuple
from dataclasses import dataclass

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QFileDialog, QMessageBox, QGroupBox, QSpinBox,
    QComboBox, QCheckBox
)
from PySide6.QtCore import Qt, QSettings

# Constantes
DEFAULT_TONE = "C4"
DEFAULT_VELOCITY = 130
DEFAULT_VOLUME = 100
DEFAULT_MODULATION = 0
DEFAULT_TEMPO = 120
DEFAULT_DURATION_MS = 500
DEFAULT_FLAGS = ""


@dataclass
class SynthesisParams:
    """Parâmetros para síntese."""
    input_wav: str
    output_wav: str
    tone: str = DEFAULT_TONE
    velocity: int = DEFAULT_VELOCITY
    flags: str = DEFAULT_FLAGS
    offset: float = 0.0      # ms
    duration: float = DEFAULT_DURATION_MS  # ms
    overlap: float = 0.0     # ms  
    consonant: float = 0.0   # ms
    cutoff: float = 0.0      # ms (negativo = do final)
    volume: int = DEFAULT_VOLUME
    modulation: int = DEFAULT_MODULATION
    tempo: int = DEFAULT_TEMPO
    pitches: str = "AA"      # Pitch flat (Base64)





class SynthesisTest:
    """
    Gerencia o teste de síntese com resampler UTAU.
    """
    
    def __init__(self, settings: QSettings):
        self.settings = settings
        self._temp_dir = Path(tempfile.gettempdir()) / "copaiba_synthesis"
        self._temp_dir.mkdir(exist_ok=True)
        
    def cleanup(self):
        """Limpa arquivos temporários."""
        try:
            for f in self._temp_dir.glob("synthesis_*"):
                try:
                    f.unlink()
                except:
                    pass
        except:
            pass

    # ... métodos existentes (get_resampler_path, etc) mantidos ...
    
    def midi_number_to_note_name(self, midi: int) -> str:
        """Converte número MIDI (60) para nome da nota (C4)."""
        notes = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        octave = (midi // 12) - 1
        note_idx = midi % 12
        return f"{notes[note_idx]}{octave}"



    def get_resampler_path(self) -> Optional[Path]:
        """Retorna o caminho do resampler configurado."""
        path_str = self.settings.value("synthesis_test/resampler_path", "")
        if path_str and Path(path_str).exists():
            return Path(path_str)
        
        # Tenta encontrar worldline no diretório do app
        app_dir = Path(__file__).parent
        bundled = app_dir / "resamplers" / "worldline.exe"
        if bundled.exists():
            return bundled
            
        return None
    
    def set_resampler_path(self, path: str):
        """Define o caminho do resampler."""
        self.settings.setValue("synthesis_test/resampler_path", path)
    
    def get_test_tone(self) -> str:
        """Retorna a nota de teste configurada."""
        return self.settings.value("synthesis_test/tone", DEFAULT_TONE)
    
    def set_test_tone(self, tone: str):
        """Define a nota de teste."""
        self.settings.setValue("synthesis_test/tone", tone)
    
    def get_test_duration(self) -> int:
        """Retorna a duração de teste em ms."""
        return self.settings.value("synthesis_test/duration", DEFAULT_DURATION_MS, type=int)
    
    def set_test_duration(self, duration: int):
        """Define a duração de teste."""
        self.settings.setValue("synthesis_test/duration", duration)
    
    def build_command(self, params: SynthesisParams, resampler_path: Path) -> list:
        """
        Constrói a linha de comando para o resampler.
        
        Formato UTAU:
        resampler.exe "input.wav" "output.wav" <tone> <velocity> "<flags>" 
                      <offset> <duration> <consonant> <cutoff> <volume> 
                      <modulation> !<tempo> <pitches>
        """
        # Calcula duração real considerando offset e cutoff
        # O resampler espera: offset, required_length, consonant, cutoff
        
        cmd = [
            str(resampler_path),
            params.input_wav,
            params.output_wav,
            params.tone,
            str(params.velocity),
            params.flags,
            str(params.offset),           # Offset em ms
            str(params.duration),         # Duração requerida
            str(params.consonant),        # Consonant (fixed region)
            str(params.cutoff),           # Cutoff (negativo = do final)
            str(params.volume),           # Volume
            str(params.modulation),       # Modulation
            f"!{params.tempo}",           # Tempo (com !)
            params.pitches                # Pitch data (Base64)
        ]
        
        return cmd
    
    def synthesize(self, params: SynthesisParams) -> Tuple[bool, str]:
        """
        Executa a síntese.
        
        Returns:
            Tuple (sucesso, mensagem/caminho_output)
        """
        resampler = self.get_resampler_path()
        if not resampler:
            return False, "Resampler não configurado. Configure em Reprodução > Configurar Resampler..."
        
        if not Path(params.input_wav).exists():
            return False, f"Arquivo de entrada não encontrado: {params.input_wav}"
        
        try:
            cmd = self.build_command(params, resampler)
            
            # Executa o resampler
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=10,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )
            
            if result.returncode != 0:
                error_msg = result.stderr or result.stdout or "Erro desconhecido"
                return False, f"Resampler falhou: {error_msg}"
            
            if not Path(params.output_wav).exists():
                return False, "Resampler não gerou arquivo de saída"
            
            return True, params.output_wav
            
        except subprocess.TimeoutExpired:
            return False, "Resampler demorou muito para responder (timeout)"
        except FileNotFoundError:
            return False, f"Resampler não encontrado: {resampler}"
        except Exception as e:
            return False, f"Erro ao executar resampler: {e}"
    
    def create_params_from_oto(
        self, 
        wav_path: Path, 
        offset: float,
        overlap: float,
        preutter: float,
        consonant: float,
        cutoff: float,
        duration_ms: Optional[int] = None
    ) -> SynthesisParams:
        """
        Cria parâmetros de síntese a partir de uma entrada OTO.
        """
        # Limpa arquivos anteriores para evitar acúmulo e cache
        self.cleanup()
        
        # Gera nome único para evitar conflito de arquivo bloqueado e garantir recarregamento
        import uuid
        filename = f"synthesis_{uuid.uuid4().hex[:8]}.wav"
        output_path = self._temp_dir / filename
        
        return SynthesisParams(
            input_wav=str(wav_path),
            output_wav=str(output_path),
            tone=self.get_test_tone(),
            velocity=DEFAULT_VELOCITY,
            flags=DEFAULT_FLAGS,
            offset=offset,
            duration=duration_ms or self.get_test_duration(),
            overlap=overlap,
            consonant=consonant,
            cutoff=cutoff,
            volume=DEFAULT_VOLUME,
            modulation=DEFAULT_MODULATION,
            tempo=DEFAULT_TEMPO,
            pitches="AA"  # Pitch flat
        )
    


class ResamplerConfigDialog(QDialog):
    """Diálogo para configurar o resampler."""
    
    def __init__(self, synthesis_test: SynthesisTest, parent=None):
        super().__init__(parent)
        self.synthesis_test = synthesis_test
        self._setup_ui()
        self._load_settings()
    
    def _setup_ui(self):
        self.setWindowTitle("Configurar Synthesis Test")
        self.setMinimumWidth(500)
        
        layout = QVBoxLayout(self)
        
        # Grupo: Resampler
        group_resampler = QGroupBox("Resampler")
        resampler_layout = QVBoxLayout(group_resampler)
        
        path_layout = QHBoxLayout()
        path_layout.addWidget(QLabel("Caminho:"))
        self.edit_path = QLineEdit()
        self.edit_path.setPlaceholderText("Selecione o resampler.exe...")
        path_layout.addWidget(self.edit_path)
        
        self.btn_browse = QPushButton("📂 Procurar")
        self.btn_browse.clicked.connect(self._browse_resampler)
        path_layout.addWidget(self.btn_browse)
        
        resampler_layout.addLayout(path_layout)
        
        # Dica sobre worldline
        tip_label = QLabel(
            "💡 Recomendado: <a href='https://github.com/stakira/OpenUtau'>worldline.exe</a> do OpenUtau"
        )
        tip_label.setOpenExternalLinks(True)
        tip_label.setStyleSheet("color: #888; font-size: 11px;")
        resampler_layout.addWidget(tip_label)
        
        layout.addWidget(group_resampler)
        
        # Grupo: Parâmetros de Teste
        group_params = QGroupBox("Parâmetros de Teste")
        params_layout = QHBoxLayout(group_params)
        
        params_layout.addWidget(QLabel("Nota:"))
        self.combo_tone = QComboBox()
        notes = ["C3", "D3", "E3", "F3", "G3", "A3", "B3",
                 "C4", "D4", "E4", "F4", "G4", "A4", "B4",
                 "C5", "D5", "E5"]
        self.combo_tone.addItems(notes)
        self.combo_tone.setCurrentText("C4")
        params_layout.addWidget(self.combo_tone)
        
        params_layout.addSpacing(20)
        
        params_layout.addWidget(QLabel("Duração:"))
        self.spin_duration = QSpinBox()
        self.spin_duration.setRange(100, 2000)
        self.spin_duration.setValue(500)
        self.spin_duration.setSuffix(" ms")
        params_layout.addWidget(self.spin_duration)
        
        params_layout.addStretch()
        
        layout.addWidget(group_params)
        
        # Botões
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()
        
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.clicked.connect(self.reject)
        buttons_layout.addWidget(btn_cancel)
        
        btn_save = QPushButton("💾 Salvar")
        btn_save.setDefault(True)
        btn_save.clicked.connect(self._save_and_close)
        buttons_layout.addWidget(btn_save)
        
        layout.addLayout(buttons_layout)
    
    def _load_settings(self):
        """Carrega configurações atuais."""
        path = self.synthesis_test.get_resampler_path()
        if path:
            self.edit_path.setText(str(path))
        
        self.combo_tone.setCurrentText(self.synthesis_test.get_test_tone())
        self.spin_duration.setValue(self.synthesis_test.get_test_duration())
    
    def _browse_resampler(self):
        """Abre diálogo para selecionar resampler."""
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Selecionar Resampler",
            "",
            "Executáveis (*.exe);;Todos (*.*)"
        )
        if path:
            self.edit_path.setText(path)
    
    def _save_and_close(self):
        """Salva configurações e fecha."""
        path = self.edit_path.text().strip()
        if path and not Path(path).exists():
            QMessageBox.warning(
                self, 
                "Arquivo não encontrado",
                f"O arquivo não existe:\n{path}"
            )
            return
        
        self.synthesis_test.set_resampler_path(path)
        self.synthesis_test.set_test_tone(self.combo_tone.currentText())
        self.synthesis_test.set_test_duration(self.spin_duration.value())
        
        self.accept()
