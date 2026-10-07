# 🧠 NeuroSync Video Studio (`@NeuroSyncHQ`)

> **Autonomous End-to-End Production Studio for High-Retention, 3D Pixar-Style Long-Format YouTube Explainers (7–9 Minutes).**  
> *Engineered for **NeuroSync** (`@NeuroSyncHQ`) — decoding cognitive neuroscience, habits, focus, dopamine, and human behavior on a **$0 budget**.*

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Resolution 1080p / 4K UHD](https://img.shields.io/badge/resolution-1080p%20%7C%204K%20UHD-gold.svg)]()
[![Hardware NVENC Acceleration](https://img.shields.io/badge/render-NVIDIA%20NVENC-76B900.svg)]()
[![Channel YouTube](https://img.shields.io/badge/YouTube-%40NeuroSyncHQ-red.svg)](https://youtube.com/@neurosynchq)
[![License MIT](https://img.shields.io/badge/license-MIT-green.svg)]()

---

## 🧭 Channel Identity & Creative Promise

* **Channel Name:** NeuroSync
* **YouTube Handle:** [`@NeuroSyncHQ`](https://youtube.com/@neurosynchq)
* **Official Hashtag:** `#NeuroSync`
* **Creative Promise:** *"Why your brain does what it does, explained simply, with real science."*
* **Channel Protagonist / Mascot:** **Sam** — 3D Pixar/Disney-styled character in his early 20s with tousled dark brown hair, black rectangular glasses, expressive hazel eyes, and a signature heather-navy crewneck sweater.
* **Budget Mandate:** **100% Free / Zero Budget.** Every tool in the primary path is free or locally computed; no paid video-generation subscriptions are required.

---

## 🏛️ The 3-Phase Gate Production Pipeline

Every long-form video flows through **three distinct phases with mandatory approval gates** to ensure scientific rigor, high viewer retention, and consistent 3D visual storytelling:

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                              NEUROSYNC PRODUCTION PIPELINE                             │
├────────────────────────────────────────────────────────────────────────────────────────┤
│ PHASE 1: RESEARCH & PACKAGING  ──►  GATE 1: Approve Title, Angle & Fact Sheet          │
│  • tools/research/yt_demand.py scrapes live autocomplete queries & top-10 view counts  │
│  • Verified fact sheet: 4–8 peer-reviewed claims [F1]...[F6] with authors & DOI links   │
│  • Packaging first: 3 clickable titles (≤60 chars) + Mobile 3-Element Thumbnail concept│
├────────────────────────────────────────────────────────────────────────────────────────┤
│ PHASE 2: SCRIPT & VOICEOVER    ──►  GATE 2: Approve Timed Voiceover Script             │
│  • 1,050–1,300 words (7–9 minutes @ 144 WPM) following a rotating storytelling format  │
│  • Plain-English standard (a 12-year-old can follow the first 60 seconds)              │
│  • Numbered lines (L01, L02...) with pause marks (⏸, ⏸⏸) and fact tags [F#]          │
│  • Free Voiceover: Own mic recording OR Edge-TTS (AndrewMultilingualNeural, -2% rate)  │
│  • FFmpeg 5-stage broadcast audio chain (-14 LUFS loudness standard)                  │
├────────────────────────────────────────────────────────────────────────────────────────┤
│ PHASE 3: SHOT LIST & IMAGES    ──►  15-Shot Batches with Continuation HANDOFF Blocks   │
│  • Rapid 2–4s shot cuts matched to spoken syllables (average ~3.0s per visual)        │
│  • Slow eased Ken Burns motion on every still (push, pull, pan, rise, drift)          │
│  • 3-Tier Crop Reuse: 1 image yields Wide + Mid + Macro Detail (~0.6 images per shot)  │
│  • HyperFrames Motion Graphics (MG): 6–12 code-animated inserts for numbers/graphs     │
│  • Continuous production handoffs: batches end with copy-paste HANDOFF blocks          │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 📂 Repository Directory Structure

```
neurosync-video-studio/
├── NEUROSYNC_MASTER_PROMPT.md            # The master prompt to copy-paste for new episodes
├── README.md                             # This studio documentation and setup guide
├── requirements.txt                      # Python dependencies (OpenCV, FFmpeg, Pillow, etc.)
│
├── skill_neurosync-video-studio/         # Active studio skill definition & reference protocols
│   ├── SKILL.md                          # Primary agent skill instructions
│   └── references/
│       ├── research.md                   # Real YouTube demand check & verified fact sheet standard
│       ├── script.md                     # 5-format rotation, retention scripting & audio mastering
│       └── visuals_and_motion.md         # 2–4s shot pacing, Ken Burns motion, MG inserts & handoffs
│
├── tools/                                # Standalone automation and research utilities
│   ├── research/
│   │   └── yt_demand.py                  # Free zero-API YouTube autocomplete & view count scraper
│   ├── branding/
│   │   └── build_neurosync_banner.py     # Channel banner builder & mobile safe-zone compositor
│   └── channel_rebrand/
│       └── rebrand_channel.py            # YouTube API metadata & video updater utility
│
├── production/                           # Active production workspace for episodes
│   ├── EPISODE_REGISTRY.md               # Master registry of published videos & retired devices
│   ├── topic_02/                         # Topic 02 assets, renders & teleprompter scripts
│   └── topic_03/                         # Topic 03 master audio, timestamps & 4K deliverables
│
├── pipeline/                             # Core Python rendering and processing engine
│   ├── export_master_audio.py            # Edge-TTS voice synthesis with acoustic pause injection
│   ├── align_whisper.py                  # Whisper word-level millisecond timestamp alignment
│   ├── extract_cutouts_rembg.py          # U2Net character cutout extractor for 3D depth
│   ├── render_master_video.py            # NVENC hardware compositor with 80/20 depth subtitles
│   └── render_youtube_shorts_suite.py    # Automated 9:16 vertical shorts generator
│
├── assets/                               # Global channel brand assets, fonts, and banners
│   ├── branding/
│   │   ├── YOUTUBE_BANNER_4K_NEUROSYNC.jpg # Official 4K YouTube banner (2560x1440)
│   │   └── NEW_PROFILE_PICTURE_AVATAR.jpg  # Official 3D Sam profile avatar (1024x1024)
│   └── fonts/                            # Studio typography assets (Playfair, Inter, etc.)
│
└── archive/                              # Archived legacy assets and outdated v1 materials
    └── isywhy_v1_legacy/                 # Old 2D style guides, outdated prompts, and scripts
```

---

## 🚀 Step-by-Step Production Guide

### Step 1: Starting a New Episode
1. Open [`NEUROSYNC_MASTER_PROMPT.md`](./NEUROSYNC_MASTER_PROMPT.md).
2. Copy the prompt block, fill in your topic idea (or write `"pick one for me"`), and start the chat.
3. The studio automatically runs [`tools/research/yt_demand.py`](./tools/research/yt_demand.py) to check real search demand:
   ```bash
   python tools/research/yt_demand.py "why cant i focus" "how to stop overthinking"
   ```
4. Review the Phase 1 packaging report (3 titles, thumbnail concept, verified fact sheet `[F1]`–`[F6]`).
5. **Approve Gate 1:** Reply with your chosen title.

### Step 2: Approving the Script & Generating Audio
1. The studio generates a 1,050–1,300 word retention script with numbered lines (`L01`, `L02`...) and acoustic pause marks (`⏸`, `⏸⏸`).
2. **Approve Gate 2:** Give sign-off on the script lines.
3. **Generate Voiceover (Free):**
   * **Option A (Own Voice - Highest Authenticity):** Record with your microphone, then clean via FFmpeg.
   * **Option B (Edge-TTS):**
     ```bash
     edge-tts --voice en-US-AndrewMultilingualNeural --rate=-2% --pitch=+0Hz -f production/<slug>/03_voiceover_lines.txt --write-media production/<slug>/audio/vo_raw.mp3
     ```
4. **Master Broadcast Audio (-14 LUFS):**
   ```bash
   ffmpeg -i vo_raw.mp3 -af "highpass=f=75,equalizer=f=120:t=q:w=1.2:g=2,equalizer=f=3400:t=q:w=1.4:g=1.5,acompressor=threshold=-18dB:ratio=3:attack=5:release=80,loudnorm=I=-14:LRA=7:TP=-1.5" -ar 48000 vo_master.wav
   ```

### Step 3: Generating Visuals in 15-Shot Batches
1. The studio outputs the shot list in **15-shot batches**.
2. Each batch includes:
   * Timed shot rows (2–4 seconds per shot).
   * Exact 4-block 3D Pixar prompts for every new still image.
   * Exact HyperFrames code specs for Motion Graphics (`MG`) inserts.
   * Standardized continuation `HANDOFF` block.
3. Paste the image prompts into free image tools (Google Gemini / Microsoft Designer / Leonardo.ai).
4. Reply `CONTINUE` to receive the next 15 shots until the video is complete.

---

## 🎨 3D Pixar Visual Standard: "Sam"

Every image prompt enforces the locked character design of Sam:
```text
[STYLE] 3D animated feature film still, Pixar-style stylized character, soft global illumination, subsurface skin scattering, shallow depth of field, 16:9.
[SHOT] <wide / medium / close-up / extreme close-up>, <camera angle>.
[SUBJECT] Sam, a young man in his early 20s with thick tousled dark brown hair, bold black rectangular glasses, large expressive hazel eyes, warm friendly face, wearing a heather-navy crewneck sweater, <action + emotion>.
[SET + LIGHT] <simple studio backdrop in palette color>, <key light + rim light>, clean uncluttered background, room for subtitles at bottom third.
NEGATIVE: text, letters, words, numbers, watermark, logo, 2D, flat illustration, anime, photorealistic photo, extra fingers, deformed hands, cluttered background
```

---

## 📊 Motion Graphics (`MG`) with HyperFrames

For data visualizations, brain regions, timelines, and study citations, the studio generates local HyperFrames motion graphics:
* Built with HTML/CSS/GSAP under `production/<slug>/motion/`.
* Free, locally rendered to MP4 via `npx hyperframes render`.
* Seamlessly inserted between 3D character stills.
* If rendering is skipped, a still frame with an editor text overlay is used as a zero-friction fallback.

---

## 📈 Episode Registry & Continuity Control

To avoid audience fatigue and repetitive tropes, all episodes are logged in [`production/EPISODE_REGISTRY.md`](./production/EPISODE_REGISTRY.md):
* **Retired Devices:** Banned repetition of *"It is [exact time] AM/PM"* openings, the 5-second countdown test, and the 2-minute rule.
* **Format Rotation:** Rotates between 5 distinct storytelling structures across episodes.
* **Fact Verification:** Eliminates unverified claims (*"500% dopamine spike"*, *"92% habit failure"* are strictly forbidden).

---

## 📄 License

This studio pipeline and its automation scripts are licensed under the **MIT License**. Created for `@NeuroSyncHQ`.
