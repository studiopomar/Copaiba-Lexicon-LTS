# project_cache.py
from __future__ import annotations


from pathlib import Path
import json
from typing import Dict, Set
import logging

# Configuração básica de logging (opcional, mas recomendado para aplicações maiores)
# logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ProjectCache:
    def __init__(self):
        self._cache_dir = Path.home() / ".copaiba" / "projects"
        self._cache_dir.mkdir(parents=True, exist_ok=True)
        self._current_project: Path | None = None
        self._completed_aliases: Set[str] = set()

    def _get_cache_file(self, oto_path: Path) -> Path:
        safe_name = str(oto_path.resolve()).replace("/", "_").replace("\\", "_").replace(":", "_")
        return self._cache_dir / f"{safe_name}.json"

    def load_project(self, oto_path: Path):
        self._current_project = oto_path
        self._completed_aliases.clear()

        cache_file = self._get_cache_file(oto_path)
        if cache_file.exists():
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self._completed_aliases = set(data.get("completed", []))
            except (OSError, json.JSONDecodeError) as e:
                # Pode-se usar logging.info, warning ou error dependendo do contexto
                print(f"Erro ao carregar cache do projeto {cache_file}: {e}")
                # Opcional: logger.warning(f"Erro ao carregar cache do projeto {cache_file}: {e}")

    def save_project(self):
        if self._current_project is None:
            return

        cache_file = self._get_cache_file(self._current_project)
        try:
            data = {
                "oto_path": str(self._current_project),
                "completed": list(self._completed_aliases),
            }
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except OSError as e:
            print(f"Erro ao salvar cache do projeto {cache_file}: {e}")
            # Opcional: logger.error(f"Erro ao salvar cache do projeto {cache_file}: {e}")

    def mark_completed(self, filename: str, alias: str):
        key = f"{filename}|{alias}"
        self._completed_aliases.add(key)
        self.save_project()

    def unmark_completed(self, filename: str, alias: str):
        key = f"{filename}|{alias}"
        self._completed_aliases.discard(key)
        self.save_project()

    def is_completed(self, filename: str, alias: str) -> bool:
        key = f"{filename}|{alias}"
        return key in self._completed_aliases

    def clear_project(self):
        self._completed_aliases.clear()
        if self._current_project:
            self.save_project()