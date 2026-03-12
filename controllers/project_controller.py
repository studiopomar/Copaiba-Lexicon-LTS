# controllers/project_controller.py
"""
Controller de gerenciamento de projetos e arquivos.
Extraído de main.py para melhorar modularidade.
"""

from __future__ import annotations
import json
import subprocess
import platform
from pathlib import Path
from datetime import datetime
from dataclasses import asdict
from typing import TYPE_CHECKING, Optional, Set, List

from PySide6.QtWidgets import QFileDialog, QMessageBox
from PySide6.QtCore import Qt

from copaiba import OtoFile, OtoEntry

if TYPE_CHECKING:
    from main import MainWindow


class ProjectController:
    """
    Gerencia operações de projeto, voicebank e arquivos oto.ini.
    Recebe referência ao MainWindow para acessar widgets e estado.
    """

    def __init__(self, main_window: 'MainWindow'):
        self.mw = main_window

    # ============================================================
    # Voicebank
    # ============================================================

    def open_voicebank_folder(self) -> None:
        """Abre um diálogo para selecionar pasta de voicebank."""
        mw = self.mw
        
        # Usa último diretório se disponível
        last_dir = mw.settings.value("last_voicebank_dir", "")
        folder = QFileDialog.getExistingDirectory(
            mw, "Selecionar pasta do voicebank", last_dir
        )
        if not folder:
            return
        folder_path = Path(folder)

        # Salva diretório para próxima vez
        mw.settings.setValue("last_voicebank_dir", str(folder_path.parent))

        # Encontra todos os arquivos oto.ini recursivamente
        oto_files = list(folder_path.rglob("oto.ini"))
        
        if len(oto_files) > 0:
            mw._voicebank_dir = folder_path
            
            for oto_path in oto_files:
                self.load_oto(oto_path)
                
            # Atualiza Discord RPC (sum of all entries is not easy here, so just send folder name)
            self._update_discord_rpc(folder_path.name, sum(len(s.oto.entries) for s in mw.sessions if s.oto))
        else:
            # Verificar se existem arquivos .wav na RAIZ apenas
            wav_files = sorted(folder_path.glob("*.wav"))
            if wav_files:
                reply = QMessageBox.question(
                    mw, "Criar oto.ini",
                    f"Nenhum oto.ini encontrado nesta pasta.\n\n"
                    f"Foram encontrados {len(wav_files)} arquivos .wav na raiz.\n\n"
                    f"Deseja criar um oto.ini com entradas padrão para cada arquivo?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                if reply == QMessageBox.StandardButton.Yes:
                    self.create_default_oto(folder_path, wav_files)
            else:
                QMessageBox.warning(
                    mw, "Erro",
                    "Nenhum oto.ini ou arquivo .wav encontrado nesta pasta."
                )

    def create_default_oto(self, folder_path: Path, wav_files: list) -> None:
        """Cria um oto.ini com entradas padrão para cada arquivo .wav."""
        mw = self.mw
        oto_path = folder_path / "oto.ini"

        try:
            lines = []
            for wav_file in wav_files:
                filename = wav_file.name
                alias = wav_file.stem
                line = f"{filename}={alias},0,0,0,0,0"
                lines.append(line)

            oto_path.write_text("\n".join(lines), encoding="utf-8")
            mw.statusBar().showMessage(f"oto.ini criado com {len(wav_files)} entradas", 3000)

            mw._voicebank_dir = folder_path
            self.load_oto(oto_path)
            self._update_discord_rpc(folder_path.name, len(wav_files))

        except Exception as e:
            QMessageBox.critical(mw, "Erro", f"Não foi possível criar oto.ini:\n{e}")

    def reveal_voicebank(self) -> None:
        """Abre a pasta do voicebank no explorador de arquivos."""
        mw = self.mw
        if mw._voicebank_dir and mw._voicebank_dir.exists():
            if platform.system() == "Windows":
                subprocess.run(["explorer", str(mw._voicebank_dir)])
            elif platform.system() == "Darwin":
                subprocess.run(["open", str(mw._voicebank_dir)])
            else:
                subprocess.run(["xdg-open", str(mw._voicebank_dir)])

    # ============================================================
    # oto.ini File
    # ============================================================

    def open_oto(self) -> None:
        """Abre diálogo para carregar arquivo oto.ini."""
        mw = self.mw
        path, _ = QFileDialog.getOpenFileName(
            mw, "Abrir oto.ini", "", "Arquivos oto.ini (oto.ini);;All Files (*)"
        )
        if path:
            self.load_oto(Path(path))

    def load_oto(self, path: Path) -> None:
        """Carrega arquivo oto.ini em uma nova aba ou na atual se estiver vazia."""
        mw = self.mw
        try:
            # Pega o nome da pasta pai para a aba (ex: "Canário", "Canário_Append", etc)
            dir_name = path.parent.name
            
            # Check if current session is empty (not dirty, no file loaded)
            if mw.current_session and not mw.current_session.dirty and not mw.current_session.current_path:
                session = mw.current_session
                mw.tab_widget.setTabText(mw.current_session_index, dir_name)
            else:
                session = mw._add_new_session(dir_name)
                
            session.oto.load(str(path), encoding=mw._encoding)
            session.current_path = path
            session.voicebank_dir = path.parent
            session.dirty = False
            session.undo_stack.clear()
            session.redo_stack.clear()

            # The session might not be the active one temporarily, but _add_new_session makes it active
            if mw.current_session == session:
                mw._load_oto_to_table()
                mw._update_title()
                mw._update_progress()
                mw.statusBar().showMessage(f"Carregado: {path.name}", 3000)

                # Atualiza Discord Rich Presence
                self._update_discord_rpc(str(session.voicebank_dir), len(session.oto.entries))

                # Auto-carregar o primeiro áudio
                if mw.table.rowCount() > 0:
                    mw.table.setFocus()
                    mw.table.setCurrentCell(0, mw.COL_ALIAS)
                    mw._load_waveform_for_current_row()
            
            # If notes exist, try to load them
            notes_path = path.parent / "notas.copaiba.json"
            session.notes_data = {}
            if notes_path.exists():
                try:
                    with open(notes_path, 'r', encoding='utf-8') as f:
                        session.notes_data = json.load(f)
                except Exception as e:
                    print(f"Erro ao carregar notas: {e}")
            if mw.current_session == session:
                mw._restore_notes_to_table()

        except Exception as e:
            QMessageBox.critical(mw, "Erro ao carregar", str(e))

    def save_oto(self) -> None:
        """Salva o arquivo oto.ini."""
        mw = self.mw
        if mw._current_path is None:
            self.save_oto_as()
            return
        try:
            mw._sync_table_to_oto()
            mw._oto.save(str(mw._current_path), encoding=mw._encoding)
            mw._dirty = False
            mw._last_saved_time = datetime.now()
            mw._update_title()
            mw.statusBar().showMessage("Salvo com sucesso!", 3000)
            mw._last_save_label.setText(f"Salvo: {mw._last_saved_time.strftime('%H:%M:%S')}")

        except Exception as e:
            QMessageBox.critical(mw, "Erro ao salvar", str(e))

    def save_oto_as(self) -> None:
        """Salva oto.ini com novo nome."""
        mw = self.mw
        path, _ = QFileDialog.getSaveFileName(
            mw, "Salvar oto.ini como", "", "Arquivos oto.ini (*.ini);;All Files (*)"
        )
        if path:
            mw._current_path = Path(path)
            self.save_oto()

    def reload_oto(self) -> None:
        """Recarrega o arquivo oto.ini do disco."""
        mw = self.mw
        if mw._current_path and mw._current_path.exists():
            if mw._dirty:
                reply = QMessageBox.question(
                    mw, "Recarregar",
                    "Existem alterações não salvas. Deseja recarregar mesmo assim?",
                    QMessageBox.Yes | QMessageBox.No
                )
                if reply != QMessageBox.Yes:
                    return
            self.load_oto(mw._current_path)

    # ============================================================
    # Project Files (.copaiba)
    # ============================================================

    def get_projects_folder(self) -> Path:
        """Retorna pasta padrão de projetos em Documentos."""
        docs = Path.home() / "Documents" / "Copaiba Projetos de Voz"
        docs.mkdir(parents=True, exist_ok=True)
        return docs

    def open_project(self) -> None:
        """Abre um projeto .copaiba."""
        mw = self.mw
        path, _ = QFileDialog.getOpenFileName(
            mw, "Abrir projeto", "", "Copaiba Project (*.copaiba);;All Files (*)"
        )
        if not path:
            return
        self._load_project_file(Path(path))

    def _load_project_file(self, path: Path) -> None:
        """Carrega dados de um arquivo de projeto."""
        mw = self.mw
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)

            from main import ProjectData
            project = ProjectData(**data)
            oto_path = Path(project.oto_path)

            if oto_path.exists():
                self.load_oto(oto_path)
                mw._voicebank_dir = Path(project.voicebank_path)
                mw._completed_aliases = set(project.completed_aliases)
                mw.preset_config.set_all_presets(project.custom_presets)
                mw._project_file = path
                mw._load_oto_to_table()
                mw._update_progress()
                mw.statusBar().showMessage(f"Projeto carregado: {path.name}", 3000)

                self.add_to_recent_projects(path)
            else:
                QMessageBox.warning(mw, "Erro", f"O arquivo oto.ini não foi encontrado:\n{oto_path}")

        except Exception as e:
            QMessageBox.critical(mw, "Erro ao carregar projeto", str(e))

    def save_project(self) -> None:
        """Salva o projeto atual."""
        mw = self.mw
        if mw._current_path is None:
            QMessageBox.warning(mw, "Erro", "Nenhum oto.ini carregado.")
            return

        if mw._project_file is None:
            default_folder = self.get_projects_folder()
            default_name = mw._voicebank_dir.name if mw._voicebank_dir else "projeto"

            path, _ = QFileDialog.getSaveFileName(
                mw, "Salvar projeto",
                str(default_folder / f"{default_name}.copaiba"),
                "Copaiba Project (*.copaiba)"
            )
            if not path:
                return
            mw._project_file = Path(path)

        try:
            from main import ProjectData
            project = ProjectData(
                voicebank_path=str(mw._voicebank_dir or ""),
                oto_path=str(mw._current_path),
                completed_aliases=list(mw._completed_aliases),
                custom_presets=mw.preset_config.get_all_presets(),
            )
            with open(mw._project_file, "w", encoding="utf-8") as f:
                json.dump(asdict(project), f, indent=2, ensure_ascii=False)

            mw.statusBar().showMessage(f"Projeto salvo: {mw._project_file.name}", 3000)
            mw._last_saved_time = datetime.now()
            mw._last_save_label.setText(f"Salvo: {mw._last_saved_time.strftime('%H:%M:%S')}")

            self.add_to_recent_projects(mw._project_file)

        except Exception as e:
            QMessageBox.critical(mw, "Erro ao salvar projeto", str(e))

    # ============================================================
    # Recent Projects
    # ============================================================

    def add_to_recent_projects(self, project_path: Path) -> None:
        """Adiciona projeto à lista de recentes."""
        mw = self.mw
        recent = mw.settings.value("recent_projects", [], type=list)
        path_str = str(project_path)

        if path_str in recent:
            recent.remove(path_str)
        recent.insert(0, path_str)
        recent = recent[:10]

        mw.settings.setValue("recent_projects", recent)
        self.update_recent_projects_menu()

    def update_recent_projects_menu(self) -> None:
        """Atualiza o menu de projetos recentes."""
        mw = self.mw
        if not hasattr(mw, 'm_recent_projects'):
            return

        mw.m_recent_projects.clear()
        recent = mw.settings.value("recent_projects", [], type=list)

        if not recent:
            action = mw.m_recent_projects.addAction("(Nenhum projeto recente)")
            action.setEnabled(False)
            return

        for path_str in recent:
            path = Path(path_str)
            if path.exists():
                action = mw.m_recent_projects.addAction(path.name)
                action.setData(path_str)
                action.triggered.connect(lambda checked, p=path_str: self.open_recent_project(p))

        mw.m_recent_projects.addSeparator()
        clear_action = mw.m_recent_projects.addAction("Limpar lista")
        clear_action.triggered.connect(self.clear_recent_projects)

    def open_recent_project(self, path_str: str) -> None:
        """Abre um projeto recente."""
        path = Path(path_str)
        if not path.exists():
            QMessageBox.warning(self.mw, "Erro", f"Projeto não encontrado:\n{path}")
            recent = self.mw.settings.value("recent_projects", [], type=list)
            if path_str in recent:
                recent.remove(path_str)
                self.mw.settings.setValue("recent_projects", recent)
                self.update_recent_projects_menu()
            return

        self._load_project_file(path)

    def clear_recent_projects(self) -> None:
        """Limpa a lista de projetos recentes."""
        self.mw.settings.setValue("recent_projects", [])
        self.update_recent_projects_menu()

    # ============================================================
    # Helpers
    # ============================================================

    def _update_discord_rpc(self, voicebank_name: str, entry_count: int) -> None:
        """Atualiza Discord Rich Presence se disponível."""
        try:
            from discord_rpc import get_discord_rpc
            rpc = get_discord_rpc()
            rpc.set_voicebank(voicebank_name, entry_count)
        except:
            pass
