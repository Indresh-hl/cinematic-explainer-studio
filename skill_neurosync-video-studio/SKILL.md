---
name: neurosync-video-studio
description: End-to-end production of NeuroSync (@NeuroSyncHQ) long-form YouTube explainers (7-9 min) on neuroscience, psychology, habits, focus and dopamine, made on a zero budget - verified research with real YouTube demand data, plain-English retention scripts, free TTS or own-voice narration, 3D Pixar-style still images of the mascot Sam with slow Ken Burns motion every 2-4 seconds, short HyperFrames motion-graphic inserts for numbers/charts/processes, batch image prompts with copy-paste continuation handoffs, thumbnails, titles and Shorts. Use whenever the user wants to make, research, script, voice, storyboard or generate images for a NeuroSync / Sam / neuroscience explainer video, or pastes the NeuroSync master prompt or a HANDOFF block.
---

# NeuroSync Video Studio (v2)

**Channel:** NeuroSync · **Handle:** `@NeuroSyncHQ` · **Hashtag:** `#NeuroSync`
**Promise:** "Why your brain does what it does, explained simply, with real science."
**Mascot:** Sam (3D Pixar-style, see `references/visuals_and_motion.md`)
**Budget rule:** everything must be free. Paid tools are optional upgrades, never required.

v1 of this skill produced well-made videos that got 5-47 views. The fixes in v2 target what went wrong: unverified research and invented statistics, jargon-heavy scripts, the same template in every episode, an inconsistent and easily-detected AI voice, mixed 2D/3D styles, slow 5-7 s image holds, and packaging done after the video instead of before it.

## The pipeline: 3 phases with stop gates

Run the phases in order. **Stop at each gate and wait for the user.** Never run ahead into the next phase.

```
PHASE 1  RESEARCH + PACKAGING ──► GATE 1: user picks topic, angle, title
PHASE 2  SCRIPT + VOICEOVER   ──► GATE 2: user approves script
PHASE 3  SHOT LIST + IMAGES   ──► batches of 15 prompts, each ending in a HANDOFF block
(after)  MOTION INSERTS · ASSEMBLY · THUMBNAIL · SHORTS
```

Before Phase 1, read `production/EPISODE_REGISTRY.md` in the workspace (create it if missing). It lists published topics and the devices already used, so you don't repeat them.

---

## Phase 1: Research + packaging (read `references/research.md`)

1. **Demand check with real data:** run `python tools/research/yt_demand.py "<seed 1>" "<seed 2>" ...` from the workspace root, using 3-5 seed queries. It is free, needs no API key, and returns autocomplete phrases plus top videos with real view counts. Never write competitor view counts from memory.
2. **Pick the angle:** find what the top videos *don't* cover. Choose a format from the rotation in `references/script.md` that hasn't been used in the last 2 episodes.
3. **Fact sheet:** 4-8 claims, each with author, year, journal or book, and a link or DOI found with web search. Mark each claim *strong / moderate / contested*. **Any number without a source is deleted.**
4. **Packaging first:** 3 title options (≤ 60 characters, curiosity + a clear benefit), 1 thumbnail concept (Sam + 1 glowing prop + ≤ 3 words), and the first 15 seconds of the hook.
5. Output the **Phase 1 report** (template in `references/research.md`), then **STOP: GATE 1.**

## Phase 2: Script + voiceover (read `references/script.md`)

1. Write **1,050-1,300 words** (7-9 minutes at about 145 words per minute) in the chosen format.
2. Write in plain English: a 12-year-old should follow the first 60 seconds. Use at most one technical term per paragraph, and explain it in the same sentence.
3. Tag every factual sentence with its fact-sheet ID, e.g. `[F2]`. Untagged numbers are not allowed.
4. Output the **voiceover script**:
   - numbered lines `L01, L02…` with pause marks
   - estimated duration per line
   - total duration
5. Run the script checklist in `references/script.md` and show the result.
6. **STOP: GATE 2.** After approval, give the voice-generation command (free Edge-TTS settings or own-voice recording notes) from `references/script.md`.

## Phase 3: Shot list + images with handoffs (read `references/visuals_and_motion.md`)

1. **Build the shot list** from the timed script:
   - one shot every **2-4 s** (average about 3 s)
   - every shot matched to the words being spoken at that moment
   - each shot is type `IMG` (still + slow motion) or `MG` (HyperFrames motion graphic)
2. **Reuse to save cost:** one generated image can make 2-3 shots (a wide, a slow push-in, a crop). Aim for about **0.6 unique images per shot**.
3. Plan **6-12 `MG` inserts** for numbers, comparisons, processes, timelines and study results.
4. **Deliver prompts in batches of 15 shots**:
   - full 4-block prompt for each `IMG`
   - full spec for each `MG`
   - each batch ends with the **HANDOFF block** (exact format in `references/visuals_and_motion.md`)
   - when the user types `CONTINUE` or pastes a HANDOFF block, resume from `next_shot`
5. After the last batch: give the assembly plan (motion per shot, transitions), the thumbnail prompt, the title, the description with chapters and sources, tags, and 3 Shorts cut points.

---

## Non-negotiable rules

- **Brand:** say "NeuroSync" at most once, on screen at the end. Never write "Isy why" or "@isy019".
- **Style:** 3D Pixar-style only. One Sam design, defined in `references/visuals_and_motion.md`. No 2D images in a 3D video.
- **No text inside generated images.** All labels, numbers and titles go in the `MG` inserts or as editor overlays.
- **No invented statistics.** Every number traces back to the fact sheet.
- **No repeated devices.** Check the registry. The "2-minute rule", "5-second countdown test" and "6:30 AM / 11:42 PM crime scene" openings are retired until further notice.
- **Never publish production notes.** Prompt styles, voice names and render settings stay out of descriptions.
- **Update the registry** after the video is published: topic, format, devices used, title, and its 48-hour views.

## Workspace layout

```
production/<episode-slug>/
  01_research.md     02_script.md     03_voiceover_lines.txt
  04_shotlist.md     images/          motion/ (HyperFrames projects + rendered mp4)
  audio/             final/
production/EPISODE_REGISTRY.md
tools/research/yt_demand.py
```
