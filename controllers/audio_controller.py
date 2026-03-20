# controllers/audio_controller.py
"""
Controller de reprodução de áudio.
Extraído de main.py para melhorar modularidade.
"""

from __future__ import annotations
from typing import TYPE_CHECKING, Optional
from pathlib import Path

from PySide6.QtWidgets import QMessageBox

# Importa a variável global de disponibilidade do sounddevice
try:
    import sounddevice as sd
    SOUNDDEVICE_AVAILABLE = True
except (ImportError, OSError):
    SOUNDDEVICE_AVAILABLE = False

if TYPE_CHECKING:
    from main import MainWindow


class AudioController:
    """
    Gerencia reprodução de áudio e seleção de dispositivos.
    Recebe referência ao MainWindow para acessar widgets e estado.
    """

    def __init__(self, main_window: 'MainWindow'):
        self.mw = main_window

    def on_play_segment_requested(self, start_ms: float, end_ms: float) -> None:
        """Handler para reprodução de segmento solicitada pela waveform."""
        mw = self.mw
        if not SOUNDDEVICE_AVAILABLE or mw._audio_player is None:
            mw.statusBar().showMessage("sounddevice não disponível", 2000)
            return
        wav_path = mw.waveform.get_current_wav_path()
        if wav_path is None or not wav_path.exists():
            return
        mw._audio_player.play_segment(wav_path, start_ms, end_ms)

    def play_segment(self) -> None:
        """Reproduz o segmento atual (entre preutterance e cutoff)."""
        mw = self.mw
        if not SOUNDDEVICE_AVAILABLE or mw._audio_player is None:
            mw.statusBar().showMessage("sounddevice não disponível", 2000)
            return

        wav_path = mw.waveform.get_current_wav_path()
        if wav_path is None or not wav_path.exists():
            return

        start_ms, end_ms = mw.waveform.get_segment_times_ms()
        mw._audio_player.play_segment(wav_path, float(start_ms), float(end_ms))
        mw.waveform.start_playback_visualization(start_ms / 1000.0, end_ms / 1000.0)

    def play_full_audio(self) -> None:
        """Reproduz o áudio completo do arquivo atual."""
        mw = self.mw
        if not SOUNDDEVICE_AVAILABLE or mw._audio_player is None:
            mw.statusBar().showMessage("sounddevice não disponível", 2000)
            return

        wav_path = mw.waveform.get_current_wav_path()
        if wav_path is None or not wav_path.exists():
            return

        mw._audio_player.play_full(wav_path)

        # Mostrar barra de progresso de reprodução
        audio_duration = mw.waveform._audio_dur
        if audio_duration > 0:
            mw.waveform.start_playback_visualization(0, audio_duration)

    def toggle_sector_playback(self, checked: bool) -> None:
        """Ativa/Desativa reprodução de setor ao clicar na waveform."""
        mw = self.mw
        mw.waveform.set_sector_playback_enabled(checked)
        if checked:
            mw.statusBar().showMessage("Modo setor ativado: clique para tocar ~200ms", 2000)
        else:
            mw.statusBar().showMessage("Modo setor desativado", 2000)

    def open_audio_device_dialog(self) -> None:
        """Abre diálogo para selecionar dispositivo de áudio."""
        mw = self.mw
        if not SOUNDDEVICE_AVAILABLE:
            mw.statusBar().showMessage("sounddevice não disponível", 2000)
            return

        # Cria AudioPlayer se não existir
        if mw._audio_player is None:
            from core.audio_player import AudioPlayer
            mw._audio_player = AudioPlayer()

        from dialogs.audio_device_dialog import AudioDeviceDialog
        dialog = AudioDeviceDialog(mw._audio_player, mw)
        dialog.exec()

        # Salva dispositivo selecionado nas configurações
        device_id = dialog.get_selected_device()
        mw.settings.setValue("audio_device", device_id if device_id else -1)
