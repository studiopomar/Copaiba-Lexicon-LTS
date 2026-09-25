# Complete Shortcuts Reference — Copaiba Lexikon `e-LTS(se)`

Comprehensive list of keyboard shortcuts, mouse actions, and commands for **Copaiba Lexikon**.

---

## File & Project Operations

| Action | Shortcut | Description |
| :--- | :--- | :--- |
| **Open Voicebank...** | `Ctrl + O` | Opens voicebank folder and loads `oto.ini` |
| **Open Project...** | `Ctrl + Shift + O` | Opens a saved project file (`.copaiba`) |
| **Save (oto.ini)** | `Ctrl + S` | Saves changes directly to `oto.ini` |
| **Save Project** | `Ctrl + Shift + P` | Saves current workspace state |
| **Save As...** | `Ctrl + Shift + S` | Saves `oto.ini` with another name or location |
| **Reload All** | `Ctrl + F5` | Reloads configurations and voicebank files from disk |
| **Open Voicebank Folder** | `Ctrl + P` | Opens OS file manager in voicebank directory |
| **General Settings** | `Ctrl + ,` | Opens global preferences window |

---

## Waveform & Marker Positioning

> [!NOTE]
> Letter keys place the respective marker precisely under the current horizontal mouse cursor position on the waveform.

| Key | Marker | Color | Description |
| :---: | :--- | :---: | :--- |
| **`Q`** | **Offset** | Blue | Sets the start of usable audio |
| **`W`** | **Overlap** | Green | Sets the crossfade transition boundary |
| **`E`** | **Preutterance** | Red | Sets the vowel onset / beat alignment point |
| **`R`** | **Consonant** | Pink | Sets the boundary of the un-stretched fixed consonant region |
| **`T`** | **Cutoff** | Blue | Sets the end cutoff point of the audio |

---

## Navigation, Zoom & Pan

| Action | Command | Description |
| :--- | :--- | :--- |
| **Horizontal Zoom** | `Ctrl + Scroll` | Zoom in/out on the time axis |
| **Vertical Zoom** | `Alt + Scroll` | Increase or decrease waveform amplitude scale |
| **Horizontal Pan** | `Shift + Scroll` | Pan view left or right across the audio timeline |
| **Drag Marker** | `Left Click & Drag` | Move parameter lines directly with the mouse |
| **Navigate Aliases** | `Up / Down Arrow` | Select previous or next alias in the list |
| **Scroll Navigation** | `Mouse Scroll` | Mouse wheel over waveform switches current alias |
| **Play Clicked Sector** | `Left Click` | Auditions clicked region of the waveform |
| **Play from Cursor** | `Alt + Click` | Plays segment starting from clicked point |

---

## Playback & Synthesis

| Action | Shortcut | Description |
| :--- | :--- | :--- |
| **Play Segment** | `Space` | Plays configured region between Offset and Cutoff |
| **Play Full Audio** | `Shift + Space` | Plays the complete original `.wav` file |
| **Synthesis Test** | `Ctrl + Shift + Space` | Synthesizes and auditions alias using external resampler |

---

## Quick Parameter Presets

| Shortcut | Preset Applied | Typical Target |
| :--- | :--- | :--- |
| **`Ctrl + 1`** | **CV** | Standard Consonant + Vowel (`ka`, `sa`, `ta`) |
| **`Ctrl + 2`** | **VCV** | Continuous Vowel-Consonant-Vowel (`- ka`, `a ka`) |
| **`Ctrl + 3`** | **VV** | Vowel-to-Vowel crossfade transitions (`a i`, `u e`) |
| **`Ctrl + 4`** | **VC** | Syllable coda / final consonant (`a k`, `o s`) |
| **`Ctrl + 5`** | **-V** | Initial isolated vowel attack (`- a`, `- o`) |

---

## Table & Alias Manipulation

| Action | Shortcut | Description |
| :--- | :--- | :--- |
| **Undo** | `Ctrl + Z` | Reverts the last parameter or text modification |
| **Redo** | `Ctrl + Y` | Reapplies the last undone change |
| **Mark as Done** | `Ctrl + M` | Toggles alias completion status flag |
| **Rename Alias** | `Ctrl + R` | Opens alias rename dialog |
| **Duplicate Alias** | `Ctrl + I` | Duplicates selected row to create alias variations |
| **Delete Alias** | `Ctrl + D` | Deletes selected alias entry |
| **Copy Cells** | `Ctrl + C` | Copies selected table cells to clipboard |
| **Paste Cells** | `Ctrl + V` | Pastes clipboard content into table cells |

---

## Layout & Visual Themes

| Action | Shortcut | Description |
| :--- | :--- | :--- |
| **Cycle Waveform Theme** | `Ctrl + '` | Cycles between high-contrast waveform color palettes |
| **Reset Layout** | `Ctrl + Shift + R` | Restores default positions of all panels and docks |
