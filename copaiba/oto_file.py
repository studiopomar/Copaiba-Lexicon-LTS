#oto_file.py
from __future__ import annotations
from pathlib import Path
from typing import List, Optional
import io
from .oto_entry import OtoEntry


class OtoFile:

    def __init__(self) -> None:
        self.entries: List[OtoEntry] = []
        self.encoding_used: str = "utf-8"

    def _detect_encoding(self, path: Path) -> str:
        encodings = ["utf-8", "cp932", "mbcs"]
        for enc in encodings:
            try:
                with io.open(path, "r", encoding=enc, errors="strict") as f:
                    f.read()
                return enc
            except UnicodeDecodeError:
                continue
        return "utf-8"

    @staticmethod
    def _is_number(text: str) -> bool:
        try:
            float(text)
            return True
        except ValueError:
            return False

    @staticmethod
    def _is_number_or_empty(text: str) -> bool:
        """Retorna True se o texto é um número ou vazio/espaços (que equivale a 0)."""
        if not text or not text.strip():
            return True
        try:
            float(text)
            return True
        except ValueError:
            return False

    @staticmethod
    def _to_int(text: str) -> int:
        if not text or not text.strip():
            return 0
        try:
            return int(round(float(text)))
        except ValueError:
            return 0

    def load(self, path: str | Path, encoding: Optional[str] = "auto") -> None:
        p = Path(path)
        if not p.exists():
            raise OSError(f"File not found: {p}")

        if encoding in (None, "", "auto"):
            encoding = self._detect_encoding(p)
        self.encoding_used = encoding

        self.entries.clear()

        with io.open(p, "r", encoding=encoding, errors="strict") as f:
            for raw_line in f:
                line = raw_line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" not in line:
                    continue

                left, right = line.split("=", 1)
                filename = left.strip()
                parts = [x.strip() for x in right.split(",")]

                # Remove apenas vírgulas extras além da 7ª parte (alias + 5 params + sobras)
                while len(parts) > 7 and parts[-1] == "":
                    parts.pop()

                if len(parts) < 5:
                    continue

                alias = ""
                offset = consonant = cutoff = preutter = overlap = 0

                if len(parts) >= 6:
                    first_is_num = self._is_number_or_empty(parts[0])
                    last_is_num = self._is_number_or_empty(parts[-1])
                    if (not first_is_num) and all(self._is_number_or_empty(x) for x in parts[1:6]):
                        alias = parts[0]
                        offset = self._to_int(parts[1])
                        consonant = self._to_int(parts[2])
                        cutoff = self._to_int(parts[3])
                        preutter = self._to_int(parts[4])
                        overlap = self._to_int(parts[5])
                    elif (not last_is_num) and all(self._is_number_or_empty(x) for x in parts[0:5]):
                        offset = self._to_int(parts[0])
                        consonant = self._to_int(parts[1])
                        cutoff = self._to_int(parts[2])
                        preutter = self._to_int(parts[3])
                        overlap = self._to_int(parts[4])
                        alias = parts[5]
                    else:
                        offset = self._to_int(parts[0])
                        consonant = self._to_int(parts[1])
                        cutoff = self._to_int(parts[2])
                        preutter = self._to_int(parts[3])
                        overlap = self._to_int(parts[4])
                else:
                    offset = self._to_int(parts[0])
                    consonant = self._to_int(parts[1])
                    cutoff = self._to_int(parts[2])
                    preutter = self._to_int(parts[3])
                    overlap = self._to_int(parts[4])

                self.entries.append(
                    OtoEntry(
                        filename=filename,
                        alias=alias,
                        offset=offset,
                        consonant=consonant,
                        cutoff=cutoff,
                        preutter=preutter,
                        overlap=overlap,
                    )
                )

    def save(self, path: str | Path, encoding: Optional[str] = "auto") -> None:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)

        if encoding in (None, "", "auto"):
            encoding = self.encoding_used or "utf-8"
        self.encoding_used = encoding

        with io.open(p, "w", encoding=encoding, errors="strict", newline="\n") as f:
            for e in self.entries:
                alias = e.alias or ""
                line = (
                    f"{e.filename}="
                    f"{alias},"
                    f"{int(e.offset)},"
                    f"{int(e.consonant)},"
                    f"{int(e.cutoff)},"
                    f"{int(e.preutter)},"
                    f"{int(e.overlap)}"
                )
                f.write(line + "\n")