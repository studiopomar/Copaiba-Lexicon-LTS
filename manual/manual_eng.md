# User Manual — Copaiba Lexikon `e-LTS(se)`

Welcome to **Copaiba Lexikon**, a high-precision integrated development environment (IDE) designed for configuring, editing, and calibrating `oto.ini` files for [UTAU](https://utau.wiki/) and [OpenUtau](https://github.com/stakira/OpenUtau).

This manual provides comprehensive guidance for both novice voicebank creators and veteran otoers looking to achieve consistent, robust, and rapid voicebank configurations.

---

## Table of Contents
1. [Core Concepts of `oto.ini`](#1-core-concepts-of-otoini)
2. [User Interface Overview](#2-user-interface-overview)
3. [Step-by-Step Otoing Workflow](#3-step-by-step-otoing-workflow)
4. [Hardware-Accelerated Spectrogram (GPU)](#4-hardware-accelerated-spectrogram-gpu)
5. [Auditory Validation: Real-Time Synthesis Testing](#5-auditory-validation-real-time-synthesis-testing)
6. [The Pomar Tools Plugin Suite](#6-the-pomar-tools-plugin-suite)
7. [Project Management, Encodings & Backups](#7-project-management-encodings--backups)
8. [Frequently Asked Questions & Troubleshooting](#8-frequently-asked-questions--troubleshooting)

---

## 1. Core Concepts of `oto.ini`

Each entry in an `oto.ini` file instructs the vocal synthesizer on how to slice, crossfade, and time-stretch recorded `.wav` audio. The standard structure is:

```text
filename.wav=alias,offset,consonant,cutoff,preutterance,overlap
```

### The 5 Time-Alignment Parameters

```text
|--- (Offset) --->|================== [Usable Audio Region] ==================| <--- (Cutoff) ---|
                  |--- [Overlap] --->|
                  |---------- [Preutterance] ---------->|
                  |----------------- [Consonant (Fixed)] ----------------->|
```

1. **Offset (Start / Blue):** Starting point in milliseconds where the audio begins being processed. Discards initial silence and background noise.
2. **Overlap (Crossfade / Green):** Point where the preceding note crossfades into the current note.
3. **Preutterance (Attack / Red):** The moment where the vowel or core consonant hits the musical beat.
4. **Consonant / Fixed (Fixed Region / Pink):** Section that is **never** stretched or compressed by the resampler, preserving natural consonant attacks.
5. **Cutoff (End / Blue):** Defines the end boundary of usable audio. Negative values specify the distance from the end of the `.wav` file.

---

## 2. User Interface Overview

Copaiba Lexikon is organized into ergonomic modular components:

- **Alias Table (Top):** Searchable, sortable list of all phonemes and parameters. Supports in-place cell editing, status tracking, and multi-row selection.
- **Waveform & Spectrogram Canvas (Center):** High-density audio waveform renderer with draggable colored markers and optional $F_0$ pitch overlay.
- **Panoramic Mini-Map (Bottom of Waveform):** Interactive overview of the entire audio file for rapid navigation in long recordings.
- **Presets Dock Panel (Side):** Quick application of standard time-parameter presets (CV, VCV, VV, VC, -V) via `Ctrl+1` through `Ctrl+5`.

---

## 3. Step-by-Step Otoing Workflow

1. **Open Voicebank:** Press `Ctrl + O` and select your voicebank directory. Copaiba automatically detects and parses `oto.ini`.
2. **Navigate Phonemes:** Use the keyboard arrow keys or mouse scroll over the waveform to switch between aliases.
3. **Set Parameters with Quick Keys:**
   - Hover mouse over consonant start and press **`Q`** (Offset).
   - Hover mouse over crossfade point and press **`W`** (Overlap).
   - Hover mouse over stable vowel onset and press **`E`** (Preutterance).
   - Hover mouse over end of consonant body and press **`R`** (Consonant / Fixed).
   - Hover mouse where vowel tail terminates and press **`T`** (Cutoff).
4. **Auditory Validation:**
   - Press `Space` to play the configured segment.
   - Press `Ctrl + Shift + Space` for instant external resampler synthesis.
5. **Mark as Done:** Press `Ctrl + M` to toggle completion status.
6. **Save:** Press `Ctrl + S` to write changes to `oto.ini`.

---

## 4. Hardware-Accelerated Spectrogram (GPU)

Copaiba Lexikon features a real-time spectrogram renderer powered by **PyOpenGL** with hardware acceleration support for **CUDA** (NVIDIA) and **OpenCL** (AMD / Intel / Apple Silicon).

- Open **Tools > Spectrogram Settings**.
- Adjust **Contrast**, **Gamma**, **Frequency Gain**, and **FFT Window Size** (128 to 4096 samples).
- Select high-contrast color maps (Magma, Viridis, Inferno, Greyscale).

---

## 5. Auditory Validation: Real-Time Synthesis Testing

Eliminating the need to switch back and forth between external editors, Copaiba features a built-in immediate synthesis loop:

- Press **`Ctrl + Shift + Space`**.
- The alias is rendered through your chosen resampler (`TIPS`, `moresampler`, `resampler.exe`) and auditioned immediately.
- Configure your preferred resampler executable in **General Settings (`Ctrl + ,`)**.

---

## 6. The Pomar Tools Plugin Suite

Integrated directly under the [plugins/](file:///Users/victor/copaiba-lexicon-lts/plugins) menu:

- **Harvest (*Pitch Analyzer*):** Fundamental frequency ($F_0$) curve extraction overlaid on the waveform.
- **Pomar Tuner (*Mic Tuner*):** Real-time chromatic tuner via microphone for source recording QA.
- **Maturation (*VV Detector*):** Automated harmonic crossfade point detection for VCV voicebanks.
- **Grafting (*Mass Rename*):** Batch renaming with Regular Expressions (Regex), prefixes, and suffixes.
- **Pollinator (*Romaji ↔ Hiragana*):** Bidirectional phonetic script conversion.
- **Pruner (*Duplicate Detector*):** Voicebank sanitation and duplicate alias collision resolution.
- **Inspector (*Consistency Checker*):** Mathematical validator catching timing anomalies (Overlap > Preutter, invalid Cutoff).
- **Metadata Generators:** One-click generation of structured `README.md` and OpenUtau `character.yaml`.

---

## 7. Project Management, Encodings & Backups

- **Character Encodings:** Full support for **UTF-8** (OpenUtau), **Shift-JIS / cp932** (Classic Japanese UTAU), and **ANSI**.
- **Automated Backups:** Configurable background auto-save to prevent data loss.
- **Discord Rich Presence:** Live status broadcast of your current voicebank and alias session.
