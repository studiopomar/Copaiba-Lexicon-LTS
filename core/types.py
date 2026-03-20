from dataclasses import dataclass

@dataclass
class CellEdit:
    row: int
    col: int
    old: str
    new: str


@dataclass
class RowEdit:
    row: int
    data: list[str]
    is_insert: bool


@dataclass
class ProjectData:
    voicebank_path: str
    oto_path: str
    completed_aliases: list[str]
    custom_presets: dict
