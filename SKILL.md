# CINEMATIC EXPLAINER STUDIO: MASTER PRODUCTION SKILL & PROMPT
**Channel:** Isy why (@isy019)  
**Standard Framework:** 8–10 Minute Viral Psychological & Scientific Deep Dives  
**Saved Location:** `C:\Users\Indresh HL\.gemini\config\skills\cinematic-explainer-studio\SKILL.md`

---

## 🏛️ System Philosophy & Core Pillars

1. **The 30-Second Somatic Hook:** Never start with abstract science. Start inside an exact, relatable, visceral micro-moment (e.g., *2:14 AM*, staring at the ceiling, stomach dropping, cold pillow).
2. **Contrarian Paradigm Reframes:** Shatter common assumptions immediately (*"It's not a cruel flaw in human design—it's an ancient survival simulation"*).
3. **Dual-Column Production Matrix:** Every syllable of narration is married 1:1 to camera moves, lighting cuts, and specific audio/SFX cues.
4. **Shadow Cut Film Noir Aesthetic:** High-contrast chiaroscuro, 35mm slide projector lighting, midnight indigo palettes, and clean negative space.
5. **The 80/20 Gestalt Legibility Depth Rule:** Subtitles tuck behind characters for trending 3D depth, but never obscure more than 20% of any letterform. Close-ups elevate to foreground priority.
6. **Frame-Accurate Cut Snapping:** Subtitles never bleed or flash prematurely across visual scene cuts.

---

## 📋 Phase 1: Topic Research & Retention Engineering

### 1.1 Topic Selection & Packaging
* **High CTR Tension:** Universal, unspoken human anxieties (*nocturnal cringe, impostor syndrome, procrastination, spotlight effect*).
* **Title Formula:** `Why Your [Body/Brain/Mind] [Surprising Action] at [Specific Uncomfortable Moment]`
* **Channel Signature:** **Isy why** (`@isy019`) — *"Curiosity on Fridays. Psychology on Mondays."*

### 1.2 Retention Cadence
* **Target Runtime:** 8:15 – 8:45 minutes.
* **Target Word Count:** ~1,450 – 1,520 words.
* **Speech Cadence:** Exactly **2.3 to 2.5 words per second** (warm, reflective, thought-provoking).
* **Pattern Interrupts:** Insert an interactive cognitive test at the 60–70% mark (Act 4), such as a real-time 5.0-second countdown with ticking audio.

---

## ✍️ Phase 2: Master Scriptwriting (The 5-Act Arc)

Scripts must follow the **Dual-Column Production Matrix**:

```markdown
| TIMECODE & VISUAL / SFX DIRECTIONS | SPOKEN VOICEOVER NARRATION |
| :--- | :--- |
| **ACT 1: THE CRIME SCENE (0:00 – 1:30)** | |
| [0:00 - 0:08] VISUAL: ... SFX: ... | Spoken line... |
```

### The 5-Act Structural Blueprint:
1. **Act 1: The Crime Scene (0:00 – 1:30):**
   - The exact somatic moment of the dilemma.
   - Visceral physical sensations (heartbeat, blushing cheeks, curling into bed).
   - The 35mm Slide Projector metaphor.
   - The central question: *"Why now?"*
   - The contrarian hook: *"It's running an ancient life-or-death survival simulation."*
2. **Act 2: The Midnight Shift Change (1:30 – 3:30):**
   - Daytime mechanics: Task-Positive Network (TPN) keeps the mind looking outward.
   - Nighttime drop: Sensory input falls to zero.
   - The Default Mode Network (DMN) takes the wheel.
   - Neuroscience reality: *Transient nocturnal hypofrontality* (Prefrontal Cortex powers down; Amygdala stays wide awake).
3. **Act 3: The Social Death Penalty (3:30 – 5:15):**
   - Evolutionary anthropology: 50,000 years ago in nomadic bands (50–150 people).
   - Tribal banishment was a literal death sentence.
   - The 2003 UCLA study: Social exclusion activates the exact same neural pain pathways (dACC) as physical bone fractures.
   - Threat-caching mechanism: Subconscious priority storage.
4. **Act 4: The Spotlight Illusion & Interactive Test (5:15 – 7:00):**
   - The grand cognitive illusion: The Spotlight Effect.
   - Dr. Thomas Gilovich's Cornell Barry Manilow t-shirt experiment (predicted 50% noticed; actual was barely 23%).
   - **Interactive 5-Second Test:** Screen cuts to an obsidian countdown timer (*5... 4... 3... 2... 1... 0*).
   - The punchline: Viewer cannot remember someone else's cringe because they are trapped in their own protagonist drama.
5. **Act 5: The Tactical Reframe & Cure (7:00 – 8:45):**
   - Step 1: Stop fighting the memory (Daniel Wegner's *Ironic Process Theory* / White Bear suppression).
   - Step 2: Close the file (The *Zeigarnik Effect* / Bedside notebook technique).
   - The Philosophical Crest: Cringe is not proof of failure; it is biological proof that your empathy and taste have matured since that day.
   - Projector snaps off. Peaceful sleep. Channel sign-off.

---

## 🎙️ Phase 3: Audio Production & Word-Level Timestamping

### 3.1 Neural TTS Generation
* **Voice Model:** `en-US-ChristopherNeural` (Edge-TTS).
* **Speed Rate:** `-3%` | **Pitch:** `-2Hz`.
* **Acoustic Pauses:** Parse `[PAUSE X.Xs]` tokens in the script and insert synthetic MP3 silence chunks (`lavfi anullsrc=r=24000:cl=mono`).
* **Concatenation:** Assemble via FFmpeg concat demuxer to `assets/full_master_audio.m4a`.

### 3.2 Whisper Millisecond Timestamp Extraction
Run OpenAI Whisper with `word_timestamps=True` on `assets/full_master_audio.m4a` to generate `assets/full_timeline_word_timestamps.json`. Every word stores exact `start` and `end` times down to the millisecond.

---

## 🎨 Phase 4: Visual Art Direction & Prompt Formulas

### 4.1 Visual Archetype: Shadow Cut Film Noir + Forensic Blueprint
* **Character Consistency:** Protagonist **Sam** (20s male, dark disheveled hair, oversized navy t-shirt, expressive posture).
* **Palette Tokens:**
  - Obsidian Void: `#08090C`
  - Midnight Indigo: `#0F172A`
  - 35mm Projector Amber: `#FFB703`
  - Biosensor Cyan: `#06B6D4`
  - Threat Crimson: `#E63946`
  - Growth Gold: `#E0A96D`
* **Shot Pacing:** 116 scene stills cut dynamically (average shot duration: 3.5 to 5.0 seconds).

### 4.2 Midjourney / Flux Prompt Template
```text
cinematic scene, [SUBJECT & ACTION], shadow cut film noir aesthetic, dramatic chiaroscuro lighting, deep midnight indigo (#0F172A) shadows, sharp directional warm amber (#FFB703) beam from a 35mm slide projector, floating dust motes in light beam, rich cinematic atmosphere, subtle anime-editorial line art influence, highly detailed texture, clean negative space on the left third for typography, wide 16:9 shot, masterwork cinematography --ar 16:9 --style raw --v 6.1
```

---

## ⚡ Phase 5: 4K AI Super-Resolution (Real-ESRGAN Vulkan)

Upscale all images to pristine 4K UHD using local GPU Vulkan acceleration:
```bash
tools/realesrgan/realesrgan-ncnn-vulkan.exe -i assets/images/cleaned -o assets/images/4k -n realesrgan-x4plus-anime -s 4 -g 0 -j 2:2:2
```
Post-process in Python: Resize from $5504 \times 3072$ down to standard 4K ($3840 \times 2144$) using Lanczos anti-aliasing and save as 100% quality JPEG (`subsampling=0`).

---

## ✂️ Phase 6: Subject Masking & Alpha Cutout Extraction

Extract pixel-perfect transparent foreground masks for all 116 shots using `rembg`:
```python
from rembg import remove, new_session
session = new_session("u2net")
cutout = remove(image, session=session)
cutout.save("assets/cutouts/{name}_cutout.png")
```
*Note: Caching the `new_session("u2net")` reduces cutout inference to **0.38 seconds per image** on local CPU/GPU.*

---

## 🎬 Phase 7: Master Timeline Synchronization & Scene Cut Detection

Scan the master edited timeline video (`0922 (1).mp4`) using OpenCV sequential difference analysis (`cv2.absdiff`):
- Compare frames every 6 frames against the 116 reference thumbnails.
- Automatically filter blips ($<0.4\text{s}$) and merge contiguous frames.
- Output gapless `assets/all_timeline_shots.json` with exact millisecond start and end boundaries for all 119 cuts.

---

## 🔤 Phase 8: 3D Depth Subtitles & Occlusion-Aware Compositing

### 8.1 Typography & Color Styling
* **Font Family:** *Playfair Display* (Italic / Editorial serif).
* **Case:** Strict lowercase with punctuation (`at night,`, `don't panic.`).
* **Base Color:** Warm Butter Cream `#FFF2A8` (`rgba(255, 242, 168, 220)`).
* **Active Spoken Karaoke Pop:** Sunglow Gold `#FFD166` (`rgba(255, 209, 102, 255)`).
* **Drop Shadow:** Diffused Gaussian ambient shadow (`radius=8`, `rgba(15, 20, 30, 0.35)`).
* **Animation:** Smooth ease-out float-in (+10px $\to$ 0px over 0.16s) with fade-out exit over last 0.10s.

### 8.2 Intelligent Placement Rules
1. **Bed / Lying Down Shots:** Subtitles anchor to the dark bedroom wall at `ty = 65` above Sam's headboard, kissing his hair with **zero subtitles on duvets or blankets**.
2. **Centered Character Shots:** Text shifts to the **open left negative space** (`tx = 120, ty = 230`, max-width: 780px), reading naturally from left to right.
3. **The 80/20 Gestalt Legibility Rule:**
   $$\text{occlusion} = \frac{\sum (\text{cutout\_alpha} > 128 \land \text{text\_mask})}{\sum \text{text\_mask}}$$
   - If $\text{occlusion} \le 20\%$: Composite text **behind the character** (Layer: Background $\to$ Text $\to$ Character Cutout) for 3D depth.
   - If $\text{occlusion} > 20\%$ (e.g. tight close-up): Composite text **in front of the character** (Layer: Background $\to$ Cutout $\to$ Text) to guarantee **100% legibility**.
4. **Adaptive Phrase Width:** Terminology longer than 22 characters automatically downscales from 88px to 68–72px to prevent canvas clipping.

### 8.3 Visual Cut Snapping (Zero Flash / Zero Repetition Rule)
To prevent subtitles from flashing on outgoing shots and repeating on incoming shots:
- **Start Snapping:** If a phrase starts within $0.35\text{s}$ before a visual shot cut, its start is snapped directly to `cut_t`. It enters cleanly on the new shot.
- **End Clamping:** If a phrase padding ends within $0.20\text{s}$ after a visual shot cut, its end is clamped directly to `cut_t`. It never leaves orphan frames on the next shot.

### 8.4 High-Speed NVENC Encoding Engine
```bash
ffmpeg -y -f rawvideo -pix_fmt rgba -s 1934x1080 -r 30 -i - -i assets/full_master_audio.m4a -c:v h264_nvenc -preset p4 -rc vbr -cq 18 -b:v 12M -c:a copy -shortest assets/FINAL_4K_MASTER_VIDEO.mp4
```
*Performance: Pre-compositing text onto shadows and caching sub-phrase bitmaps enables render speeds of **48.5 FPS** (~5 minutes for an 8.5-minute 4K master).*

---

## 🚀 Execution Checklist for Next Video

When given a new topic:
1. `[ ]` **Trend Analysis:** Identify the 30s visceral somatic hook and core contrarian thesis.
2. `[ ]` **Master Script:** Generate the 5-Act Dual-Column Production Matrix (~1,480 words, 2.4 wps).
3. `[ ]` **Voiceover:** Run Edge-TTS `en-US-ChristopherNeural` with pause injection.
4. `[ ]` **Whisper Alignment:** Extract millisecond word timestamps JSON.
5. `[ ]` **Storyboard:** Generate 110–120 scene prompts using the Shadow Cut Film Noir template.
6. `[ ]` **4K AI Upscaling:** Run `realesrgan-ncnn-vulkan.exe` on GPU.
7. `[ ]` **Alpha Cutouts:** Batch extract masks via `rembg`.
8. `[ ]` **Shot Cut Mapping:** Detect scene transitions from timeline video.
9. `[ ]` **Compositing:** Run `render_full_master_video.py` with 80/20 depth rules, visual cut snapping, and NVENC GPU encoding.
