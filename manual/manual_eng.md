# Windows and Resources of Copaiba Lexikon

This document describes the main windows, panels, and plugins available in Copaiba Lexikon.

## 🖥️ Main Interface

The main window is divided into three main areas:

### 1. Alias Table (List)
Located at the top (by default), it displays all aliases from the `oto.ini` file.
- **Columns:** Favorite, File (.wav), Alias, Parameters (Offset, Overlap, Preutterance, Consonant, Cutoff).
- **Features:**
    - Quick search filter.
    - Sorting by columns.
    - Direct value editing (double click).
    - Multiple selection for batch editing.

### 2. Waveform Panel
Located at the bottom (by default), it shows the graphical visualization of the audio.
- **Visualization:** Shows the sound wave of the selected file.
- **Visual Editing:** Allows clicking and dragging the colored parameter lines.
    - **Blue:** Offset (start) and Cutoff (end).
    - **Green:** Overlap.
    - **Red:** Preutterance.
    - **Pink:** Consonant (fixed area).
- **Mini-Map:** A smaller bar below the waveform for quick navigation in long files.

### 3. Presets Panel (Side)
Dockable panel that allows configuring and applying parameter presets.
- Allows creating automatic rules for alias types (CV, VCV, etc).

---

## 🛠️ Tools and Dialogs

### General Settings (`Ctrl + ,`)
Global preferences window for the software.
- **General:** Language, interface theme.
- **Paths:** Location of external executables (Resamplers, Wavtool).
- **Backup:** Auto-save configuration.

### Spectrogram Settings
Fine adjustments for the spectrogram visualization on the waveform.
- Contrast, color gamma, and resolution.
- Option to enable/disable hardware acceleration (GPU).

### Key Configuration
Allows remapping shortcut keys used in waveform editing (Default: Q, W, E, R, T).

### Audio Device
Selects the output audio interface (API and Device) for playback.

### Plugin Manager
Shows installed plugins, their versions, and allows enabling/disabling extensions.

---

## 🧩 Integrated Plugins

Copaiba comes with a suite of powerful plugins installed:

### 🌱 Automation

**Grafting - Mass Rename**
- Allows renaming multiple aliases using substitution patterns (Find & Replace), prefixes, and suffixes.
- Supports Regular Expressions (Regex).

**Batch Edit**
- Native tool to apply numerical values of Offset, Overlap, etc., to all selected aliases at once.

### 🔍 Analysis

**Harvest - Pitch Analysis**
- Analyzes the fundamental frequency (F0) of the audio and displays it overlaid on the waveform.
- Useful for checking the tuning of recordings.

**Maturation - VV Detector**
- Specialized in finding the ideal crossfade point between vowels in VCV/VC banks.

**Orchard - Tuner (Mic Tuner)**
- A real-time chromatic tuner using the microphone.
- Useful for the *recounter* (recorder) to verify tuning before recording.

### ⚡ Utilities

**Pollinator - Romaji ↔ Hiragana**
- Automatically converts aliases from Romaji to Hiragana and vice-versa.
- Supports different romanization standards.

**Selection - Sort Aliases**
- Advanced list sorting tools (by suffix, pitch, duration, etc).

### 🛡️ Validation

**Pruner - Duplicate Detector**
- Scans the voicebank for duplicate aliases that may cause conflicts.

**Inspector - Consistency Checker**
- Checks for invalid parameters (e.g., Overlap greater than Preutterance, invalid Cutoff).
