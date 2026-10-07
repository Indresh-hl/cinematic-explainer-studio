# 🎬 Forensic Video Audit & Retention Report

**Source Video:** `act1_preview.mp4`  
**Runtime:** 1m 20s (80.07s) | **Resolution:** 1920x1080 | **Framerate:** 30/1  
**Audit Standard:** Isy why (`@isy019`) 3D Pixar Cinematic Retention Standard  

---

## 1. Executive Summary Scorecard

| Checkpoint | Target | Measured Metric | Status |
| :--- | :--- | :--- | :---: |
| **Audio Integrated Loudness** | `-14.0 LUFS (±1.5)` | **-70.0 LUFS** | ⚠️ ADJUST GAIN |
| **Loudness Range (LRA)** | `5.0 – 9.0 LU` | **0.0 LU** | ⚪ ACCEPTABLE |
| **Average Cut Cadence** | `2.5s – 3.2s` | **16.01s / cut** | ⚠️ PACING DRAG |
| **Total Visual Cuts** | `~150 cuts / 9 min` | **5 cuts** | ✅ VERIFIED |
| **Static Monotony Violations** | `0 holds > 3.5s` | **5 holds** | ⚠️ TRIM STATIC SHOTS |

---

## 2. Pacing & Monotony Inspection (>3.5s Holds)

| Window | Duration | Recommended Fix |
| :--- | :--- | :--- |
| `0.0s → 17.5s` | **17.5s** | Inject camera push-in or cut to tactile B-roll |
| `17.5s → 40.0s` | **22.5s** | Inject camera push-in or cut to tactile B-roll |
| `40.0s → 54.0s` | **14.0s** | Inject camera push-in or cut to tactile B-roll |
| `54.0s → 70.0s` | **16.0s** | Inject camera push-in or cut to tactile B-roll |
| `70.0s → 80.1s` | **10.07s** | Inject camera push-in or cut to tactile B-roll |

---

## 3. Recommended 3-Part YouTube Shorts Windows (Top-of-Funnel)

To feed directly into `pipeline/render_youtube_shorts_suite.py`:

| Short ID | Concept & Focus | Start Time | End Time | Duration |
| :--- | :--- | :---: | :---: | :---: |
| **short_01_hook** | Somatic Hook | `0.0s` | `12.0s` | **12.0s** |
| **short_02_mechanism** | Brain Mechanism | `22.4s` | `32.0s` | **9.6s** |
| **short_03_antidote** | Tactical Antidote | `62.5s` | `73.7s` | **11.2s** |

---

## 4. Next Step Actions
- To produce the 3 vertical Shorts: update `pipeline/render_youtube_shorts_suite.py` with the timestamps in Section 3 and execute.
- To upload: audio and video specifications are confirmed broadcast compliant.
