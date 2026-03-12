# views/menu_builder.py
"""
Builder de menus, ações e toolbar para MainWindow.
Extraído de main.py para melhorar modularidade.
"""

from __future__ import annotations
from typing import TYPE_CHECKING, Dict, Any

from PySide6.QtWidgets import QToolBar, QLabel, QMenuBar
from PySide6.QtGui import QKeySequence, QAction, QActionGroup
from PySide6.QtCore import Qt

from core.translator import tr

if TYPE_CHECKING:
    from main import MainWindow


class MenuBuilder:
    """
    Responsável por criar todas as ações, menus e toolbars da MainWindow.
    Recebe referência ao MainWindow para conectar os handlers.
    """
    
    def __init__(self, main_window: 'MainWindow'):
        self.mw = main_window
        self._preset_actions: Dict[str, QAction] = {}
    
    def create_all(self):
        """Cria ações, menus e toolbar em ordem."""
        self.create_actions()
        self.create_menus()
        self.create_toolbar()
    
    def create_actions(self):
        """Cria todas as QActions e as armazena no MainWindow."""
        mw = self.mw
        
        # === ARQUIVO ===
        mw.act_open_voicebank = QAction("Abrir voicebank...", mw)
        mw.act_open_voicebank.triggered.connect(mw.open_voicebank_folder)

        mw.act_open_oto = QAction("Abrir oto.ini...", mw)
        mw.act_open_oto.setShortcut(QKeySequence("Ctrl+O"))
        mw.act_open_oto.triggered.connect(mw.open_oto)

        mw.act_open_project = QAction("Abrir projeto...", mw)
        mw.act_open_project.setShortcut(QKeySequence("Ctrl+Shift+O"))
        mw.act_open_project.triggered.connect(mw.open_project)

        mw.act_save_project = QAction("Salvar projeto", mw)
        mw.act_save_project.setShortcut(QKeySequence("Ctrl+Shift+P"))
        mw.act_save_project.triggered.connect(mw.save_project)

        mw.act_reveal_voicebank = QAction("Abrir pasta do voicebank", mw)
        mw.act_reveal_voicebank.setShortcut(QKeySequence("Ctrl+P"))
        mw.act_reveal_voicebank.triggered.connect(mw.reveal_voicebank)

        mw.act_save = QAction("Salvar", mw)
        mw.act_save.setShortcut(QKeySequence("Ctrl+S"))
        mw.act_save.triggered.connect(mw.save_oto)

        mw.act_save_as = QAction("Salvar como...", mw)
        mw.act_save_as.setShortcut(QKeySequence("Ctrl+Shift+S"))
        mw.act_save_as.triggered.connect(mw.save_oto_as)

        mw.act_reload = QAction("Recarregar (Ctrl+F5)", mw)
        mw.act_reload.setShortcut(QKeySequence("Ctrl+F5"))
        mw.act_reload.triggered.connect(mw.reload_oto)

        mw.act_quit = QAction("Sair", mw)
        mw.act_quit.triggered.connect(mw.close)

        # === ZOOM ===
        mw.act_zoom_in = QAction("Zoom +", mw)
        mw.act_zoom_in.triggered.connect(mw.zoom_in)

        mw.act_zoom_out = QAction("Zoom -", mw)
        mw.act_zoom_out.triggered.connect(mw.zoom_out)

        mw.act_zoom_reset = QAction("Reset zoom", mw)
        mw.act_zoom_reset.triggered.connect(mw.reset_zoom)

        # === AUTO-SAVE ===
        mw.act_toggle_auto_save = QAction("Salvar automaticamente", mw)
        mw.act_toggle_auto_save.setCheckable(True)
        mw.act_toggle_auto_save.triggered.connect(mw._toggle_auto_save)

        # === EDIÇÃO ===
        mw.act_batch_edit = QAction("Editar em lote...", mw)
        mw.act_batch_edit.triggered.connect(mw._open_batch_edit_dialog)

        # === REPRODUÇÃO ===
        mw.act_play_segment = QAction("Tocar segmento (Espaço)", mw)
        mw.act_play_segment.setShortcut(QKeySequence(Qt.Key_Space))
        mw.act_play_segment.triggered.connect(mw._play_segment)

        mw.act_play_full = QAction("Tocar áudio completo (Shift+Espaço)", mw)
        mw.act_play_full.setShortcut(QKeySequence("Shift+Space"))
        mw.act_play_full.triggered.connect(mw._play_full_audio)

        mw.act_sector_playback = QAction("Tocar setor ao clicar", mw)
        mw.act_sector_playback.setCheckable(True)
        mw.act_sector_playback.setChecked(False)
        mw.act_sector_playback.setToolTip("Quando ativo, clicar na waveform toca um pequeno setor (200ms) ao redor do ponto clicado")
        mw.act_sector_playback.triggered.connect(mw._toggle_sector_playback)

        mw.act_audio_device = QAction("Dispositivo de áudio...", mw)
        mw.act_audio_device.setToolTip("Seleciona o dispositivo de saída de áudio")
        mw.act_audio_device.triggered.connect(mw._open_audio_device_dialog)

        # Synthesis Test
        mw.act_synthesis_test = QAction("Teste de Síntese (Ctrl+Shift+Espaço)", mw)
        mw.act_synthesis_test.setShortcut(QKeySequence("Ctrl+Shift+Space"))
        mw.act_synthesis_test.setToolTip("Testa o alias atual com resampler UTAU")
        mw.act_synthesis_test.triggered.connect(mw._run_synthesis_test)

        mw.act_synthesis_config = QAction("Configurar Resampler...", mw)
        mw.act_synthesis_config.setToolTip("Configura o resampler para Synthesis Test")
        mw.act_synthesis_config.triggered.connect(mw._open_synthesis_config)



        # === PRESETS ===
        mw.act_preset_cv = QAction("CV", mw)
        mw.act_preset_cv.setShortcut(QKeySequence("Ctrl+1"))
        mw.act_preset_cv.triggered.connect(lambda: mw.apply_preset("cv"))

        mw.act_preset_vcv = QAction("VCV", mw)
        mw.act_preset_vcv.setShortcut(QKeySequence("Ctrl+2"))
        mw.act_preset_vcv.triggered.connect(lambda: mw.apply_preset("vcv"))

        mw.act_preset_vv = QAction("VV", mw)
        mw.act_preset_vv.setShortcut(QKeySequence("Ctrl+3"))
        mw.act_preset_vv.triggered.connect(lambda: mw.apply_preset("vv"))

        mw.act_preset_vc = QAction("VC", mw)
        mw.act_preset_vc.setShortcut(QKeySequence("Ctrl+4"))
        mw.act_preset_vc.triggered.connect(lambda: mw.apply_preset("vc"))

        mw.act_preset_minus_v = QAction("-V", mw)
        mw.act_preset_minus_v.setShortcut(QKeySequence("Ctrl+5"))
        mw.act_preset_minus_v.triggered.connect(lambda: mw.apply_preset("minus_v"))

        # Dicionário para facilitar atualização de shortcuts
        mw._preset_actions = {
            "cv": mw.act_preset_cv,
            "vcv": mw.act_preset_vcv,
            "vv": mw.act_preset_vv,
            "vc": mw.act_preset_vc,
            "minus_v": mw.act_preset_minus_v,
        }

        mw.act_general_settings = QAction("Configurações Gerais...", mw)
        mw.act_general_settings.setShortcut(QKeySequence("Ctrl+,"))
        mw.act_general_settings.triggered.connect(mw._open_general_settings)

        mw.act_show_preset_config = QAction("Configurar Presets...", mw)
        mw.act_show_preset_config.triggered.connect(mw._toggle_preset_dock)

        # === SNAP ===
        mw.act_snap = QAction("Snap em picos", mw)
        mw.act_snap.setCheckable(True)
        mw.act_snap.setChecked(False)
        mw.act_snap.triggered.connect(mw.set_snap_enabled)

        mw.act_snap_peaks = QAction("Picos", mw, checkable=True)
        mw.act_snap_zero_crossing = QAction("Cruzamento de zero", mw, checkable=True)
        mw.act_snap_none = QAction("Nenhum", mw, checkable=True)

        mw.snap_mode_group = QActionGroup(mw)
        mw.snap_mode_group.setExclusive(True)
        for act in [mw.act_snap_peaks, mw.act_snap_zero_crossing, mw.act_snap_none]:
            mw.snap_mode_group.addAction(act)
        mw.act_snap_peaks.setChecked(True)
        mw.act_snap_peaks.triggered.connect(lambda: mw.set_snap_mode("peaks"))
        mw.act_snap_zero_crossing.triggered.connect(lambda: mw.set_snap_mode("zero_crossing"))
        mw.act_snap_none.triggered.connect(lambda: mw.set_snap_mode("none"))

        # === ENCODINGS ===
        mw.act_encoding_auto = QAction("Auto (detectar)", mw, checkable=True)
        mw.act_encoding_auto.setToolTip("Detecta automaticamente o encoding do arquivo")
        
        mw.act_encoding_utf8 = QAction("UTF-8 (OpenUTAU moderno)", mw, checkable=True)
        mw.act_encoding_utf8.setToolTip("Padrão do OpenUTAU - suporta todos os idiomas")
        mw.act_encoding_utf8_bom = QAction("UTF-8 BOM (OpenUTAU compatível)", mw, checkable=True)
        mw.act_encoding_utf8_bom.setToolTip("UTF-8 com BOM - melhor compatibilidade com editores Windows")
        
        mw.act_encoding_cp932 = QAction("Shift-JIS / CP932 (UTAU japonês)", mw, checkable=True)
        mw.act_encoding_cp932.setToolTip("Padrão do UTAU clássico japonês - necessário para voicebanks JP")
        mw.act_encoding_eucjp = QAction("EUC-JP (UTAU Unix/Linux)", mw, checkable=True)
        mw.act_encoding_eucjp.setToolTip("Encoding japonês alternativo - comum em sistemas Unix")
        
        mw.act_encoding_ansi = QAction("ANSI / Windows-1252 (Ocidental)", mw, checkable=True)
        mw.act_encoding_ansi.setToolTip("Encoding padrão Windows para idiomas ocidentais")
        mw.act_encoding_latin1 = QAction("Latin-1 / ISO-8859-1 (Europeu)", mw, checkable=True)
        mw.act_encoding_latin1.setToolTip("Encoding para idiomas europeus ocidentais")
        mw.act_encoding_gbk = QAction("GBK / CP936 (Chinês simplificado)", mw, checkable=True)
        mw.act_encoding_gbk.setToolTip("Encoding para voicebanks em chinês simplificado")
        mw.act_encoding_euckr = QAction("EUC-KR / CP949 (Coreano)", mw, checkable=True)
        mw.act_encoding_euckr.setToolTip("Encoding para voicebanks em coreano")

        mw.encoding_group = QActionGroup(mw)
        mw.encoding_group.setExclusive(True)
        for act in [mw.act_encoding_auto, mw.act_encoding_utf8, mw.act_encoding_utf8_bom,
                    mw.act_encoding_cp932, mw.act_encoding_eucjp, mw.act_encoding_ansi,
                    mw.act_encoding_latin1, mw.act_encoding_gbk, mw.act_encoding_euckr]:
            mw.encoding_group.addAction(act)
        mw.act_encoding_auto.setChecked(True)
        
        mw.act_encoding_auto.triggered.connect(lambda: mw._set_encoding("auto"))
        mw.act_encoding_utf8.triggered.connect(lambda: mw._set_encoding("utf-8"))
        mw.act_encoding_utf8_bom.triggered.connect(lambda: mw._set_encoding("utf-8-sig"))
        mw.act_encoding_cp932.triggered.connect(lambda: mw._set_encoding("cp932"))
        mw.act_encoding_eucjp.triggered.connect(lambda: mw._set_encoding("euc-jp"))
        mw.act_encoding_ansi.triggered.connect(lambda: mw._set_encoding("cp1252"))
        mw.act_encoding_latin1.triggered.connect(lambda: mw._set_encoding("latin-1"))
        mw.act_encoding_gbk.triggered.connect(lambda: mw._set_encoding("gbk"))
        mw.act_encoding_euckr.triggered.connect(lambda: mw._set_encoding("euc-kr"))

        # === TEMAS DE ONDA ===
        mw.act_wave_blue = QAction("Azul suave", mw, checkable=True)
        mw.act_wave_green = QAction("Verde digital", mw, checkable=True)
        mw.act_wave_mono = QAction("Branco sobre preto", mw, checkable=True)
        mw.act_wave_orange = QAction("Laranja amber", mw, checkable=True)
        mw.act_wave_purple = QAction("Roxo synthwave", mw, checkable=True)
        mw.act_wave_cyan = QAction("Ciano terminal", mw, checkable=True)
        mw.act_wave_pink = QAction("Rosa neon", mw, checkable=True)
        mw.act_wave_gold = QAction("Dourado clássico", mw, checkable=True)
        mw.act_wave_red = QAction("Vermelho intenso", mw, checkable=True)
        # Temas escuros (melhor contraste)
        mw.act_wave_dark_teal = QAction("Teal escuro", mw, checkable=True)
        mw.act_wave_dark_slate = QAction("Slate suave", mw, checkable=True)
        mw.act_wave_midnight = QAction("Azul meia-noite", mw, checkable=True)
        mw.act_wave_dark_navy = QAction("Navy elegante", mw, checkable=True)
        mw.act_wave_forest = QAction("Verde floresta", mw, checkable=True)
        mw.act_wave_ocean = QAction("Oceano profundo", mw, checkable=True)
        mw.act_wave_sunset = QAction("Pôr do sol", mw, checkable=True)
        mw.act_wave_lavender = QAction("Lavanda suave", mw, checkable=True)

        mw.wave_color_group = QActionGroup(mw)
        mw.wave_color_group.setExclusive(True)
        for act in [mw.act_wave_blue, mw.act_wave_green, mw.act_wave_mono,
                    mw.act_wave_orange, mw.act_wave_purple, mw.act_wave_cyan,
                    mw.act_wave_pink, mw.act_wave_gold, mw.act_wave_red,
                    mw.act_wave_dark_teal, mw.act_wave_dark_slate, mw.act_wave_midnight,
                    mw.act_wave_dark_navy, mw.act_wave_forest, mw.act_wave_ocean,
                    mw.act_wave_sunset, mw.act_wave_lavender]:
            mw.wave_color_group.addAction(act)
        mw.act_wave_blue.setChecked(True)
        
        mw.act_wave_blue.triggered.connect(lambda: mw._set_wave_theme("blue"))
        mw.act_wave_green.triggered.connect(lambda: mw._set_wave_theme("green"))
        mw.act_wave_mono.triggered.connect(lambda: mw._set_wave_theme("mono"))
        mw.act_wave_orange.triggered.connect(lambda: mw._set_wave_theme("orange"))
        mw.act_wave_purple.triggered.connect(lambda: mw._set_wave_theme("purple"))
        mw.act_wave_cyan.triggered.connect(lambda: mw._set_wave_theme("cyan"))
        mw.act_wave_pink.triggered.connect(lambda: mw._set_wave_theme("pink"))
        mw.act_wave_gold.triggered.connect(lambda: mw._set_wave_theme("gold"))
        mw.act_wave_red.triggered.connect(lambda: mw._set_wave_theme("red"))
        # Temas escuros
        mw.act_wave_dark_teal.triggered.connect(lambda: mw._set_wave_theme("dark_teal"))
        mw.act_wave_dark_slate.triggered.connect(lambda: mw._set_wave_theme("dark_slate"))
        mw.act_wave_midnight.triggered.connect(lambda: mw._set_wave_theme("midnight"))
        mw.act_wave_dark_navy.triggered.connect(lambda: mw._set_wave_theme("dark_navy"))
        mw.act_wave_forest.triggered.connect(lambda: mw._set_wave_theme("forest"))
        mw.act_wave_ocean.triggered.connect(lambda: mw._set_wave_theme("ocean"))
        mw.act_wave_sunset.triggered.connect(lambda: mw._set_wave_theme("sunset"))
        mw.act_wave_lavender.triggered.connect(lambda: mw._set_wave_theme("lavender"))

        mw.act_cycle_wave_theme = QAction("Ciclar tema de onda", mw)
        mw.act_cycle_wave_theme.setShortcut(QKeySequence(Qt.CTRL | Qt.Key_Apostrophe))
        mw.act_cycle_wave_theme.triggered.connect(mw._cycle_wave_theme)

        # === UNDO/REDO ===
        mw.act_undo = QAction("Desfazer", mw)
        mw.act_undo.setShortcut(QKeySequence("Ctrl+Z"))
        mw.act_undo.setShortcutContext(Qt.ApplicationShortcut)
        mw.act_undo.triggered.connect(mw.undo)

        mw.act_redo = QAction("Refazer", mw)
        mw.act_redo.setShortcut(QKeySequence("Ctrl+Y"))
        mw.act_redo.setShortcutContext(Qt.ApplicationShortcut)
        mw.act_redo.triggered.connect(mw.redo)

        # === ALIAS ===
        mw.act_rename_alias = QAction("Renomear alias", mw)
        mw.act_rename_alias.setShortcut(QKeySequence("Ctrl+R"))
        mw.act_rename_alias.triggered.connect(mw.rename_alias)

        mw.act_delete_alias = QAction("Deletar alias", mw)
        mw.act_delete_alias.setShortcut(QKeySequence("Ctrl+D"))
        mw.act_delete_alias.triggered.connect(mw.delete_alias)

        mw.act_duplicate_alias = QAction("Duplicar alias", mw)
        mw.act_duplicate_alias.setShortcut(QKeySequence("Ctrl+I"))
        mw.act_duplicate_alias.triggered.connect(mw.duplicate_alias)

        mw.act_mark_complete = QAction("Marcar como concluído", mw)
        mw.act_mark_complete.setShortcut(QKeySequence("Ctrl+M"))
        mw.act_mark_complete.triggered.connect(mw._toggle_complete_current)

        # === VISUALIZAÇÃO ===
        mw.act_show_minimap = QAction("Mostrar mini mapa", mw)
        mw.act_show_minimap.setCheckable(True)
        mw.act_show_minimap.setChecked(False)
        mw.act_show_minimap.triggered.connect(mw.toggle_minimap)

        mw.act_show_spectrogram = QAction("Mostrar espectrograma", mw)
        mw.act_show_spectrogram.setCheckable(True)
        mw.act_show_spectrogram.setChecked(False)
        mw.act_show_spectrogram.triggered.connect(mw._toggle_spectrogram)

        mw.act_spectrogram_config = QAction("Configurar Espectrograma...", mw)
        mw.act_spectrogram_config.triggered.connect(mw._toggle_spectrogram_config_dock)

        # GPU é agora gerenciada automaticamente nos bastidores
        # Ações removidas: act_toggle_gpu, act_gpu_info
        # A GPU é ativada automaticamente quando disponível

        # mw.act_manage_plugins removido

        
        mw.act_plugin_vv_detector = QAction("Maturação - Detector VV...", mw)
        mw.act_plugin_vv_detector.setToolTip("Detecta transições entre vogais em aliases VV")
        mw.act_plugin_vv_detector.triggered.connect(lambda: mw._open_plugin("vv_detector"))
        
        mw.act_plugin_pitch = QAction("Colheita - Análise de Pitch...", mw)
        mw.act_plugin_pitch.setToolTip("Mostra a frequência fundamental do áudio")
        mw.act_plugin_pitch.triggered.connect(lambda: mw._open_plugin("pitch"))
        
        mw.act_plugin_mic_tuner = QAction("Pomar - Afinador...", mw)
        mw.act_plugin_mic_tuner.setToolTip("Afinador em tempo real usando microfone")
        mw.act_plugin_mic_tuner.triggered.connect(lambda: mw._open_plugin("mic_tuner"))
        
        mw.act_plugin_rename = QAction("Enxertia - Renomear em Massa...", mw)
        mw.act_plugin_rename.setToolTip("Renomeia múltiplos aliases de uma vez")
        mw.act_plugin_rename.triggered.connect(lambda: mw._open_plugin("rename"))
        
        mw.act_plugin_sort = QAction("Seleção - Ordenar Aliases...", mw)
        mw.act_plugin_sort.setToolTip("Ordena aliases por diferentes critérios")
        mw.act_plugin_sort.triggered.connect(lambda: mw._open_plugin("sort"))
        
        mw.act_plugin_romaji = QAction("Polinizador - Romaji ↔ Hiragana...", mw)
        mw.act_plugin_romaji.setToolTip("Converte aliases entre Romaji e Hiragana/Katakana")
        mw.act_plugin_romaji.triggered.connect(lambda: mw._open_plugin("romaji"))
        
        mw.act_plugin_duplicates = QAction("Podador - Detector de Duplicatas...", mw)
        mw.act_plugin_duplicates.setToolTip("Encontra aliases duplicados")
        mw.act_plugin_duplicates.triggered.connect(lambda: mw._open_plugin("duplicates"))
        
        mw.act_plugin_consistency = QAction("Inspetor - Verificador de Consistência...", mw)
        mw.act_plugin_consistency.setToolTip("Valida parâmetros e detecta problemas")
        mw.act_plugin_consistency.triggered.connect(lambda: mw._open_plugin("consistency"))

        mw.act_plugin_oto_merger = QAction("Jardineiro - Mesclar oto.ini...", mw)
        mw.act_plugin_oto_merger.setToolTip("Mescla um arquivo oto.ini externo com o projeto atual")
        mw.act_plugin_oto_merger.triggered.connect(lambda: mw._open_plugin("oto_merger"))

        # === LAYOUT ===
        mw.act_reset_layout = QAction("Resetar layout dos painéis", mw)
        mw.act_reset_layout.setShortcut(QKeySequence("Ctrl+Shift+R"))
        mw.act_reset_layout.triggered.connect(mw._reset_layout)

        # === TEMA ===
        mw.act_toggle_theme = QAction("🌙 Modo Escuro", mw)
        mw.act_toggle_theme.setCheckable(True)
        mw.act_toggle_theme.setChecked(True)  # Inicia no modo escuro
        mw.act_toggle_theme.triggered.connect(mw._toggle_app_theme)

        # === MODOS DE EDIÇÃO ===
        mw.act_toggle_srp = QAction("SRP - Snap Relativo de Preutterance", mw)
        mw.act_toggle_srp.setCheckable(True)
        mw.act_toggle_srp.setChecked(False)
        mw.act_toggle_srp.setShortcut(QKeySequence("Shift+1"))
        mw.act_toggle_srp.setToolTip("Quando ativo, mover a preutterance move o offset e cutoff proporcionalmente. (Shift+1)")
        mw.act_toggle_srp.triggered.connect(mw._toggle_srp)

        mw.act_toggle_srna = QAction("SRnA - Snap Relativo a Nada", mw)
        mw.act_toggle_srna.setCheckable(True)
        mw.act_toggle_srna.setChecked(False)
        mw.act_toggle_srna.setShortcut(QKeySequence("Shift+2"))
        mw.act_toggle_srna.setToolTip("Quando ativo, cada parâmetro pode ser movido independentemente. (Shift+2)")
        mw.act_toggle_srna.triggered.connect(mw._toggle_srna)

        mw.act_persistent_zoom = QAction("Zoom persistente", mw)
        mw.act_persistent_zoom.setCheckable(True)
        mw.act_persistent_zoom.setChecked(False)
        mw.act_persistent_zoom.setToolTip("Mantém o nível de zoom ao trocar de alias")
        mw.act_persistent_zoom.triggered.connect(mw._toggle_persistent_zoom)

        mw.act_normalize_waveform = QAction("Normalizar waveform", mw)
        mw.act_normalize_waveform.setCheckable(True)
        mw.act_normalize_waveform.setChecked(True)
        mw.act_normalize_waveform.setToolTip("Normaliza a amplitude da waveform para visualização (ALT+Scroll para zoom vertical)")
        mw.act_normalize_waveform.triggered.connect(mw._toggle_normalize_waveform)
        
        # === CONFIGURAÇÃO DE TECLAS ===
        mw.act_keybinding_config = QAction("Configurar Teclas de Parâmetros...", mw)
        mw.act_keybinding_config.setToolTip("Personalizar teclas Q, W, E, R, T para definir parâmetros de oto.ini")
        mw.act_keybinding_config.triggered.connect(mw._show_keybinding_config)

    def create_menus(self):
        """Cria a estrutura de menus na barra de menu."""
        mw = self.mw
        
        # === ARQUIVO ===
        mw.m_file = mw.menuBar().addMenu("Arquivo")
        mw.m_file.addAction(mw.act_open_voicebank)
        mw.m_file.addAction(mw.act_open_oto)
        mw.m_file.addSeparator()
        mw.m_file.addAction(mw.act_open_project)
        mw.m_file.addAction(mw.act_save_project)
        
        # Submenu de projetos recentes
        mw.m_recent_projects = mw.m_file.addMenu("Projetos Recentes")
        mw._update_recent_projects_menu()
        
        mw.m_file.addSeparator()
        mw.m_file.addAction(mw.act_save)
        mw.m_file.addAction(mw.act_save_as)
        mw.m_file.addSeparator()
        mw.m_file.addAction(mw.act_reveal_voicebank)
        mw.m_file.addAction(mw.act_reload)
        mw.m_file.addSeparator()
        mw.m_file.addAction(mw.act_quit)

        # === EDITAR ===
        mw.m_edit = mw.menuBar().addMenu("Editar")
        mw.m_edit.addAction(mw.act_undo)
        mw.m_edit.addAction(mw.act_redo)
        mw.m_edit.addSeparator()
        mw.m_presets = mw.m_edit.addMenu("Aplicar Preset")
        mw.m_presets.addAction(mw.act_preset_cv)
        mw.m_presets.addAction(mw.act_preset_vcv)
        mw.m_presets.addAction(mw.act_preset_vv)
        mw.m_presets.addAction(mw.act_preset_vc)
        mw.m_presets.addAction(mw.act_preset_minus_v)
        mw.m_edit.addSeparator()
        mw.m_edit.addAction(mw.act_snap)
        mw.m_snap_mode = mw.m_edit.addMenu("Modo de snap")
        mw.m_snap_mode.addAction(mw.act_snap_peaks)
        mw.m_snap_mode.addAction(mw.act_snap_zero_crossing)
        mw.m_snap_mode.addAction(mw.act_snap_none)
        mw.m_edit.addAction(mw.act_toggle_srp)
        mw.m_edit.addAction(mw.act_toggle_srna)
        mw.m_edit.addSeparator()
        mw.m_edit.addAction(mw.act_rename_alias)
        mw.m_edit.addAction(mw.act_duplicate_alias)
        mw.m_edit.addAction(mw.act_delete_alias)
        mw.m_edit.addAction(mw.act_mark_complete)

        # === VISUALIZAR ===
        mw.m_view = mw.menuBar().addMenu("Visualizar")
        mw.m_view.addAction(mw.act_zoom_in)
        mw.m_view.addAction(mw.act_zoom_out)
        mw.m_view.addAction(mw.act_zoom_reset)
        mw.m_view.addSeparator()
        mw.m_view.addAction(mw.act_show_minimap)
        mw.m_view.addAction(mw.act_show_spectrogram)
        mw.m_view.addAction(mw.act_spectrogram_config)
        mw.m_view.addAction(mw.act_persistent_zoom)
        mw.m_view.addAction(mw.act_normalize_waveform)
        mw.m_view.addSeparator()
        mw.m_view.addAction(mw.act_show_preset_config)
        
        # Submenu Temas de Onda
        mw.m_view_wave_theme = mw.m_view.addMenu("Tema de Onda")
        mw.m_view_wave_theme.addAction(mw.act_wave_blue)
        mw.m_view_wave_theme.addAction(mw.act_wave_green)
        mw.m_view_wave_theme.addAction(mw.act_wave_mono)
        mw.m_view_wave_theme.addAction(mw.act_wave_orange)
        mw.m_view_wave_theme.addAction(mw.act_wave_purple)
        mw.m_view_wave_theme.addAction(mw.act_wave_cyan)
        mw.m_view_wave_theme.addAction(mw.act_wave_pink)
        mw.m_view_wave_theme.addAction(mw.act_wave_gold)
        mw.m_view_wave_theme.addAction(mw.act_wave_red)
        mw.m_view_wave_theme.addSeparator()
        mw.m_view_wave_theme.addAction(mw.act_wave_dark_teal)
        mw.m_view_wave_theme.addAction(mw.act_wave_dark_slate)
        mw.m_view_wave_theme.addAction(mw.act_wave_midnight)
        mw.m_view_wave_theme.addAction(mw.act_wave_dark_navy)
        mw.m_view_wave_theme.addAction(mw.act_wave_forest)
        mw.m_view_wave_theme.addAction(mw.act_wave_ocean)
        mw.m_view_wave_theme.addAction(mw.act_wave_sunset)
        mw.m_view_wave_theme.addAction(mw.act_wave_lavender)
        
        mw.m_view.addAction(mw.act_cycle_wave_theme)
        mw.m_view.addSeparator()
        mw.m_view.addAction(mw.act_reset_layout)

        # === REPRODUÇÃO ===
        mw.m_playback = mw.menuBar().addMenu("Reprodução")
        mw.m_playback.addAction(mw.act_play_segment)
        mw.m_playback.addAction(mw.act_play_full)
        mw.m_playback.addSeparator()
        mw.m_playback.addAction(mw.act_synthesis_test)
        mw.m_playback.addAction(mw.act_synthesis_config)

        mw.m_playback.addSeparator()
        mw.m_playback.addAction(mw.act_sector_playback)
        # Dispositivo de áudio movido para Configurações Gerais

        # === CONFIGURAÇÕES ===
        mw.m_settings = mw.menuBar().addMenu("Configurações")
        mw.m_settings.addAction(mw.act_general_settings)
        mw.m_settings.addSeparator()
        mw.m_settings.addAction(mw.act_toggle_auto_save)
        mw.m_settings.addAction(mw.act_keybinding_config)

        # Encoding, Renderização e Idioma foram movidos/removidos ou realocados

        # === PLUGINS ===
        mw.m_plugins = mw.menuBar().addMenu("Plugins")
        
        mw.m_plugins_auto = mw.m_plugins.addMenu("Automação")
        mw.m_plugins_auto.addAction(mw.act_batch_edit)
        
        mw.m_plugins_analysis = mw.m_plugins.addMenu("Análise")
        mw.m_plugins_analysis.addAction(mw.act_plugin_vv_detector)
        mw.m_plugins_analysis.addAction(mw.act_plugin_pitch)
        mw.m_plugins_analysis.addAction(mw.act_plugin_mic_tuner)
        
        mw.m_plugins_manage = mw.m_plugins.addMenu("Gerenciamento")
        mw.m_plugins_manage.addAction(mw.act_plugin_rename)
        mw.m_plugins_manage.addAction(mw.act_plugin_sort)
        mw.m_plugins_manage.addAction(mw.act_plugin_oto_merger)
        
        mw.m_plugins_convert = mw.m_plugins.addMenu("Conversão")
        mw.m_plugins_convert.addAction(mw.act_plugin_romaji)
        
        mw.m_plugins_validate = mw.m_plugins.addMenu("Validação")
        mw.m_plugins_validate.addAction(mw.act_plugin_duplicates)
        mw.m_plugins_validate.addAction(mw.act_plugin_consistency)
        
        mw.m_plugins.addSeparator()
        # mw.m_plugins.addAction(mw.act_manage_plugins) removido

        # === IDIOMA ===
        # Removido (movido para settings)
        # mw.m_language = mw.menuBar().addMenu("Idioma")
        # mw._language_actions = {}
        # self._populate_language_menu()

    def create_toolbar(self):
        """Cria a barra de ferramentas principal."""
        mw = self.mw
        
        tb = QToolBar("Ferramentas", mw)
        tb.setObjectName("MainToolBar")  # Importante para saveState/restoreState
        tb.setMovable(True)
        tb.addAction(mw.act_open_voicebank)
        tb.addAction(mw.act_open_oto)
        tb.addAction(mw.act_reveal_voicebank)
        tb.addAction(mw.act_reload)
        tb.addSeparator()
        tb.addAction(mw.act_save)
        tb.addAction(mw.act_save_as)
        tb.addSeparator()
        tb.addAction(mw.act_play_segment)
        tb.addAction(mw.act_play_full)
        tb.addSeparator()
        tb.addAction(mw.act_zoom_in)
        tb.addAction(mw.act_zoom_out)
        tb.addSeparator()
        tb.addAction(mw.act_zoom_in)
        tb.addAction(mw.act_zoom_out)
        
        # Slider de Zoom
        from PySide6.QtWidgets import QSlider
        slider_zoom = QSlider(Qt.Horizontal)
        slider_zoom.setRange(0, 100)
        slider_zoom.setValue(50)
        slider_zoom.setFixedWidth(120)
        slider_zoom.setToolTip("Zoom Waveform/Espectrograma")
        slider_zoom.valueChanged.connect(mw.on_zoom_slider_changed)
        mw.slider_zoom = slider_zoom
        tb.addWidget(QLabel(" 🔍 "))
        tb.addWidget(slider_zoom)

        tb.addSeparator()
        tb.addAction(mw.act_preset_cv)
        tb.addAction(mw.act_preset_vcv)
        tb.addAction(mw.act_preset_vv)
        tb.addAction(mw.act_preset_vc)
        tb.addAction(mw.act_preset_minus_v)
        tb.addSeparator()
        tb.addAction(mw.act_undo)
        tb.addAction(mw.act_redo)
        mw.addToolBar(tb)

    def _populate_language_menu(self) -> None:
        """Popula o menu de idiomas com os arquivos disponíveis."""
        mw = self.mw
        
        from core.translator import get_translator
        from PySide6.QtGui import QActionGroup
        
        translator = get_translator()
        languages = translator.get_available_languages()
        current_lang = translator.get_current_language()
        
        # Limpa menu existente
        mw.m_language.clear()
        mw._language_actions.clear()
        
        # Cria grupo exclusivo
        lang_group = QActionGroup(mw)
        lang_group.setExclusive(True)
        
        for lang in languages:
            action = mw.m_language.addAction(lang["name"])
            action.setCheckable(True)
            action.setData(lang["code"])
            
            if lang["code"] == current_lang:
                action.setChecked(True)
            
            action.triggered.connect(
                lambda checked, code=lang["code"]: mw._change_language(code)
            )
            
            lang_group.addAction(action)
            mw._language_actions[lang["code"]] = action
        
        # Guarda grupo para evitar garbage collection
        mw._language_group = lang_group
