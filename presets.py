# presets.py

from dataclasses import dataclass, asdict
from pathlib import Path
import json
import logging

# Configuração básica de logging (opcional, mas recomendado para aplicações maiores)
# logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class Preset:
    name: str
    overlap: int
    preutter: int
    consonant: int
    cutoff: int

DEFAULT_PRESETS = {
    "cv": Preset("Preset CV", 50, 100, 200, -380),
    "vcv": Preset("Preset VCV", 120, 300, 430, -580),
    "vv": Preset("Preset VV", 120, 300, 430, -580),
    "vc": Preset("Preset VC", 90, 150, 150, -200),
    "minus_v": Preset("Preset -V", 0, 100, 200, -400),
}

PRESETS = {k: Preset(v.name, v.overlap, v.preutter, v.consonant, v.cutoff)
           for k, v in DEFAULT_PRESETS.items()}

def get_presets_file() -> Path:
    config_dir = Path.home() / ".copaiba"
    config_dir.mkdir(exist_ok=True)
    return config_dir / "presets.json"

def load_presets():
    global PRESETS
    presets_file = get_presets_file()
    if presets_file.exists():
        try:
            with open(presets_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            for key, values in data.items():
                if key in PRESETS:
                    PRESETS[key] = Preset(**values)
        except (OSError, json.JSONDecodeError) as e:
            # Pode-se usar logging.info, warning ou error dependendo do contexto
            print(f"Erro ao carregar presets do arquivo {presets_file}: {e}")
            # Opcional: logger.warning(f"Erro ao carregar presets do arquivo {presets_file}: {e}")

def save_presets():
    presets_file = get_presets_file()
    try:
        data = {k: asdict(v) for k, v in PRESETS.items()}
        with open(presets_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except OSError as e:
        print(f"Erro ao salvar presets no arquivo {presets_file}: {e}")
        # Opcional: logger.error(f"Erro ao salvar presets no arquivo {presets_file}: {e}")

def reset_preset(key: str):
    if key in DEFAULT_PRESETS:
        PRESETS[key] = Preset(
            DEFAULT_PRESETS[key].name,
            DEFAULT_PRESETS[key].overlap,
            DEFAULT_PRESETS[key].preutter,
            DEFAULT_PRESETS[key].consonant,
            DEFAULT_PRESETS[key].cutoff,
        )
        save_presets()

def update_preset(key: str, overlap: int, preutter: int, consonant: int, cutoff: int):
    if key in PRESETS:
        PRESETS[key] = Preset(PRESETS[key].name, overlap, preutter, consonant, cutoff)
        save_presets()

load_presets()