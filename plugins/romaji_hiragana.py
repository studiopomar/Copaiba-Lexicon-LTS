# plugins/romaji_hiragana.py
"""
Plugin: Conversor Romaji ↔ Hiragana
Converte aliases entre Romaji e Hiragana/Katakana.
"""

from typing import Optional, List, Tuple

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QRadioButton, QButtonGroup, QGroupBox, QCheckBox,
    QTableWidget, QTableWidgetItem, QAbstractItemView, QMessageBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor

from .base_plugin import BasePlugin, PluginResult, PluginCategory


# Tabelas de conversão
ROMAJI_TO_HIRAGANA = {
    # Vogais
    'a': 'あ', 'i': 'い', 'u': 'う', 'e': 'え', 'o': 'お',
    # K
    'ka': 'か', 'ki': 'き', 'ku': 'く', 'ke': 'け', 'ko': 'こ',
    'kya': 'きゃ', 'kyu': 'きゅ', 'kyo': 'きょ',
    # G
    'ga': 'が', 'gi': 'ぎ', 'gu': 'ぐ', 'ge': 'げ', 'go': 'ご',
    'gya': 'ぎゃ', 'gyu': 'ぎゅ', 'gyo': 'ぎょ',
    # V
    'va': 'ヴァ', 'vi': 'ヴィ', 'vu': 'ヴ', 've': 'ヴェ', 'vo': 'ヴォ',
    # S
    'sa': 'さ', 'si': 'し', 'shi': 'し', 'su': 'す', 'se': 'せ', 'so': 'そ',
    'sha': 'しゃ', 'shu': 'しゅ', 'sho': 'しょ',
    'sya': 'しゃ', 'syu': 'しゅ', 'syo': 'しょ',
    # Z
    'za': 'ざ', 'zi': 'ずぃ', 'ji': 'じ', 'zu': 'ず', 'ze': 'ぜ', 'zo': 'ぞ',
    'ja': 'じゃ', 'ju': 'じゅ', 'jo': 'じょ',
    'jya': 'じゃ', 'jyu': 'じゅ', 'jyo': 'じょ',
    'zya': 'ずゃ', 'zyu': 'ずゅ', 'zyo': 'ずょ',
    # T
    'ta': 'た', 'ti': 'てぃ', 'chi': 'ち', 'tu': 'とぅ', 'tsu': 'つ', 'te': 'て', 'to': 'と',
    'cha': 'ちゃ', 'chu': 'ちゅ', 'cho': 'ちょ',
    'tya': 'てゃ', 'tyu': 'てゅ', 'tyo': 'てょ',  # te + small ya/yu/yo
    # D
    'da': 'だ', 'di': 'でぃ', 'du': 'どぅ', 'de': 'で', 'do': 'ど',
    'dya': 'でゃ', 'dyu': 'でゅ', 'dyo': 'でょ',  # de + small ya/yu/yo
    # N
    'na': 'な', 'ni': 'に', 'nu': 'ぬ', 'ne': 'ね', 'no': 'の',
    'nya': 'にゃ', 'nyu': 'にゅ', 'nyo': 'にょ',
    'n': 'ん', 'nn': 'ん',
    # H
    'ha': 'は', 'hi': 'ひ', 'hu': 'ほぅ', 'fu': 'ふ', 'he': 'へ', 'ho': 'ほ', 
    'hya': 'ひゃ', 'hyu': 'ひゅ', 'hyo': 'ひょ',
    # B
    'ba': 'ば', 'bi': 'び', 'bu': 'ぶ', 'be': 'べ', 'bo': 'ぼ',
    'bya': 'びゃ', 'byu': 'びゅ', 'byo': 'びょ',
    # P
    'pa': 'ぱ', 'pi': 'ぴ', 'pu': 'ぷ', 'pe': 'ぺ', 'po': 'ぽ',
    'pya': 'ぴゃ', 'pyu': 'ぴゅ', 'pyo': 'ぴょ',
    # M
    'ma': 'み', 'mi': 'み', 'mu': 'む', 'me': 'め', 'mo': 'も',
    'mya': 'みゃ', 'myu': 'みゅ', 'myo': 'みょ',
    # Y
    'ya': 'や', 'yu': 'ゆ', 'yo': 'よ',
    # R
    'ra': 'ら', 'ri': 'り', 'ru': 'る', 're': 'れ', 'ro': 'ろ',
    'rya': 'りゃ', 'ryu': 'りゅ', 'ryo': 'りょ',
    # W
    'wa': 'わ', 'wi': 'ゐ', 'we': 'うぇ', 'wo': 'を',
    # Pequenos
    'xa': 'ぁ', 'xi': 'ぃ', 'xu': 'ぅ', 'xe': 'ぇ', 'xo': 'ぉ',
    'xya': 'ゃ', 'xyu': 'ゅ', 'xyo': 'ょ',
    'xtu': 'っ', 'xtsu': 'っ', 'ltu': 'っ', 'ltsu': 'っ',
    # Sokuon (っ) - consoante dupla
    'kk': 'っk', 'ss': 'っs', 'tt': 'っt', 'pp': 'っp',
    'cc': 'っc', 'ff': 'っf', 'hh': 'っh', 'mm': 'っm',
    # Vogais longas
    'aa': 'ああ', 'ii': 'いい', 'uu': 'うう', 'ee': 'ええ', 'oo': 'おお',
    # Correção ma
    'ma': 'ま',
}

# Correção do 'ma'
ROMAJI_TO_HIRAGANA['ma'] = 'ま'

# Criar tabela reversa
HIRAGANA_TO_ROMAJI = {}
for romaji, hiragana in ROMAJI_TO_HIRAGANA.items():
    if hiragana not in HIRAGANA_TO_ROMAJI:
        # Preferir versões Hepburn
        if romaji in ['shi', 'chi', 'tsu', 'fu', 'ji', 'sha', 'shu', 'sho', 'cha', 'chu', 'cho', 'ja', 'ju', 'jo']:
            HIRAGANA_TO_ROMAJI[hiragana] = romaji
        elif hiragana not in HIRAGANA_TO_ROMAJI:
            HIRAGANA_TO_ROMAJI[hiragana] = romaji

# Katakana (deslocamento de 96 do hiragana)
HIRAGANA_START = ord('ぁ')
KATAKANA_START = ord('ァ')


def hiragana_to_katakana(text: str) -> str:
    """Converte hiragana para katakana"""
    result = []
    for char in text:
        code = ord(char)
        if HIRAGANA_START <= code <= HIRAGANA_START + 86:
            result.append(chr(code - HIRAGANA_START + KATAKANA_START))
        else:
            result.append(char)
    return ''.join(result)


def katakana_to_hiragana(text: str) -> str:
    """Converte katakana para hiragana"""
    result = []
    for char in text:
        code = ord(char)
        if KATAKANA_START <= code <= KATAKANA_START + 86:
            result.append(chr(code - KATAKANA_START + HIRAGANA_START))
        else:
            result.append(char)
    return ''.join(result)


def romaji_to_hiragana(text: str) -> str:
    """Converte romaji para hiragana"""
    text = text.lower()
    result = []
    i = 0
    
    while i < len(text):
        # Tentar match mais longo primeiro
        matched = False
        for length in [4, 3, 2, 1]:
            if i + length <= len(text):
                substr = text[i:i + length]
                if substr in ROMAJI_TO_HIRAGANA:
                    converted = ROMAJI_TO_HIRAGANA[substr]
                    # Lidar com sokuon parcial (ex: 'っk' -> precisa continuar)
                    if len(converted) > 1 and converted[0] == 'っ' and converted[1].isalpha():
                        result.append('っ')
                        # Não avançar o caractere extra
                        i += length - 1
                    else:
                        result.append(converted)
                        i += length
                    matched = True
                    break
        
        if not matched:
            # Manter caractere original
            result.append(text[i])
            i += 1
    
    return ''.join(result)


def hiragana_to_romaji(text: str) -> str:
    """Converte hiragana para romaji"""
    # Primeiro converter katakana para hiragana
    text = katakana_to_hiragana(text)
    
    result = []
    i = 0
    
    while i < len(text):
        # Tentar match de 2 caracteres primeiro (para combinações)
        if i + 1 < len(text):
            pair = text[i:i + 2]
            if pair in HIRAGANA_TO_ROMAJI:
                result.append(HIRAGANA_TO_ROMAJI[pair])
                i += 2
                continue
        
        # Tentar caractere único
        char = text[i]
        if char in HIRAGANA_TO_ROMAJI:
            # Lidar com sokuon
            if char == 'っ' and i + 1 < len(text):
                next_char = text[i + 1]
                if next_char in HIRAGANA_TO_ROMAJI:
                    next_romaji = HIRAGANA_TO_ROMAJI[next_char]
                    if next_romaji and next_romaji[0].isalpha():
                        result.append(next_romaji[0])  # Duplicar primeira consoante
                        i += 1
                        continue
            
            result.append(HIRAGANA_TO_ROMAJI[char])
        else:
            result.append(char)
        
        i += 1
    
    return ''.join(result)


class RomajiHiraganaDialog(QDialog):
    """Diálogo do Conversor Romaji ↔ Hiragana"""
    
    def __init__(self, plugin: 'RomajiHiraganaPlugin', parent=None):
        super().__init__(parent)
        self.plugin = plugin
        self.preview_data: List[Tuple[int, str, str]] = []
        self._setup_ui()
    
    def _setup_ui(self):
        self.setWindowTitle("Conversor Romaji ↔ Hiragana")
        self.setMinimumSize(550, 450)
        
        layout = QVBoxLayout(self)
        
        # Escopo
        scope_group = QGroupBox("Aplicar a")
        scope_layout = QHBoxLayout(scope_group)
        
        self.radio_selected = QRadioButton("Aliases selecionados")
        self.radio_all = QRadioButton("Todos os aliases")
        self.radio_selected.setChecked(True)
        
        scope_layout.addWidget(self.radio_selected)
        scope_layout.addWidget(self.radio_all)
        scope_layout.addStretch()
        layout.addWidget(scope_group)
        
        # Modo de conversão
        mode_group = QGroupBox("Modo de Conversão")
        mode_layout = QVBoxLayout(mode_group)
        
        self.mode_group = QButtonGroup(self)
        
        self.radio_to_hiragana = QRadioButton("Romaji → Hiragana (ka → か)")
        self.radio_to_hiragana.setChecked(True)
        
        self.radio_to_katakana = QRadioButton("Romaji → Katakana (ka → カ)")
        
        self.radio_to_romaji = QRadioButton("Hiragana/Katakana → Romaji (か → ka)")
        
        self.radio_hira_to_kata = QRadioButton("Hiragana → Katakana (か → カ)")
        
        self.radio_kata_to_hira = QRadioButton("Katakana → Hiragana (カ → か)")
        
        for i, radio in enumerate([
            self.radio_to_hiragana, self.radio_to_katakana, self.radio_to_romaji,
            self.radio_hira_to_kata, self.radio_kata_to_hira
        ]):
            self.mode_group.addButton(radio, i)
            mode_layout.addWidget(radio)
            radio.toggled.connect(self._update_preview)
        
        layout.addWidget(mode_group)
        
        # Preview
        preview_group = QGroupBox("Preview")
        preview_layout = QVBoxLayout(preview_group)
        
        self.preview_table = QTableWidget()
        self.preview_table.setColumnCount(3)
        self.preview_table.setHorizontalHeaderLabels(["Linha", "Original", "Convertido"])
        self.preview_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        preview_layout.addWidget(self.preview_table)
        
        self.preview_count = QLabel("")
        preview_layout.addWidget(self.preview_count)
        
        layout.addWidget(preview_group)
        
        # Botões
        buttons_layout = QHBoxLayout()
        
        btn_apply = QPushButton("🇯🇵 Aplicar Conversão")
        btn_apply.clicked.connect(self._apply)
        
        btn_close = QPushButton("Fechar")
        btn_close.clicked.connect(self.close)
        
        buttons_layout.addWidget(btn_apply)
        buttons_layout.addStretch()
        buttons_layout.addWidget(btn_close)
        layout.addLayout(buttons_layout)
        
        # Atualizar preview
        self._update_preview()
    
    def _get_target_rows(self) -> List[int]:
        if self.radio_selected.isChecked():
            rows = self.plugin.get_selected_rows()
            if not rows:
                return self.plugin.get_all_rows()
            return rows
        return self.plugin.get_all_rows()
    
    def _convert(self, text: str) -> str:
        """Converte texto baseado no modo selecionado"""
        mode = self.mode_group.checkedId()
        
        if mode == 0:  # Romaji → Hiragana
            return romaji_to_hiragana(text)
        elif mode == 1:  # Romaji → Katakana
            return hiragana_to_katakana(romaji_to_hiragana(text))
        elif mode == 2:  # Hiragana/Katakana → Romaji
            return hiragana_to_romaji(text)
        elif mode == 3:  # Hiragana → Katakana
            return hiragana_to_katakana(text)
        elif mode == 4:  # Katakana → Hiragana
            return katakana_to_hiragana(text)
        
        return text
    
    def _update_preview(self):
        """Atualiza o preview"""
        rows = self._get_target_rows()
        self.preview_data = []
        
        for row in rows:
            data = self.plugin.get_alias_data(row)
            old = data["alias"]
            new = self._convert(old)
            
            if new != old:
                self.preview_data.append((row, old, new))
        
        # Atualizar tabela
        self.preview_table.setRowCount(len(self.preview_data))
        for i, (row, old, new) in enumerate(self.preview_data):
            self.preview_table.setItem(i, 0, QTableWidgetItem(str(row + 1)))
            self.preview_table.setItem(i, 1, QTableWidgetItem(old))
            
            new_item = QTableWidgetItem(new)
            new_item.setBackground(QColor(200, 255, 200))
            self.preview_table.setItem(i, 2, new_item)
        
        self.preview_table.resizeColumnsToContents()
        self.preview_count.setText(f"📝 {len(self.preview_data)} alias(es) serão convertidos")
    
    def _apply(self):
        """Aplica a conversão"""
        if not self.preview_data:
            QMessageBox.information(self, "Info", "Nenhuma conversão a aplicar.")
            return
        
        reply = QMessageBox.question(
            self, "Confirmar Conversão",
            f"Deseja converter {len(self.preview_data)} alias(es)?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        for row, old, new in self.preview_data:
            self.plugin.set_alias_data(row, "alias", new)
        
        self.plugin.mark_dirty()
        self.plugin.show_message(f"Convertidos {len(self.preview_data)} alias(es)")
        
        self._update_preview()


class RomajiHiraganaPlugin(BasePlugin):
    """Plugin para conversão entre Romaji e Hiragana/Katakana"""
    
    NAME = "Polinizador - Conversor Romaji ↔ Hiragana"
    DESCRIPTION = "Converte aliases entre Romaji e Hiragana/Katakana"
    CATEGORY = PluginCategory.CONVERSION
    VERSION = "1.0.0"
    
    def get_dialog(self) -> Optional[QDialog]:
        return RomajiHiraganaDialog(self, self.main_window)
    
    def execute(self, **kwargs) -> PluginResult:
        return PluginResult(
            success=True,
            message="Use o diálogo para converter aliases"
        )
