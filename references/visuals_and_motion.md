# Phase 3: Visuals, motion and handoffs

## Pacing (fixes the v1 "5-7 s slideshow" problem)
- **New shot every 2-4 s** (average about 3 s). An 8-minute video has about 150-170 shots.
- **Never hold a shot longer than 4.5 s.** Exceptions: an `MG` insert (up to 8 s) or a deliberate dramatic beat marked `HOLD`.
- **Cut on meaning, not on the clock.** A new noun, action or emotion in the narration gets a new shot.
- **Hook (0:00-0:15):** shots every 1.5-2.5 s.

## Slow motion on every still (so it never feels static or rushed)
Each `IMG` shot gets exactly one gentle move, eased in and out (sine in-out):

| Move | Spec over the whole shot | Use for |
|---|---|---|
| `push` | scale 1.00 → 1.06, centred on the subject's face/eyes | emotion, realisation |
| `pull` | scale 1.06 → 1.00 | reveal, context, "zoom out" moments |
| `pan_l` / `pan_r` | 1.08 scale, x drift 2-3% of frame width | scanning a scene, two objects |
| `rise` | 1.06 scale, y drift 2% upward | hope, the fix section |
| `drift` | scale 1.02 → 1.04 + 1% diagonal | calm, reflective lines |

**Transitions:**
- default: 0.35 s crossfade
- new section: 0.6 s dip through a soft blur
- `snap` (hard cut): only on a punchline or reveal, max 1 per 30 s

**Never repeat the same move on 2 shots in a row.**

## Reuse plan (keeps image generation affordable)
One generated image can serve several shots:
- **wide** (full frame, `pull`)
- **mid crop** (about 70% of frame, `push`)
- **detail crop** (about 40%: eyes, hands or prop; `push`)

Crops come from a 4K upscale, so they stay sharp. Target **unique images ≈ 0.6 × shots**, so an 8-minute video needs about 90-100 images. Mark reuse in the shot list as `IMG 014 (crop of 012)`.

## Motion-graphic inserts (`MG`): HyperFrames, free and local
Use an `MG` insert instead of a still whenever the narration contains:
- a **number** (counter or bar)
- a **comparison** (split or bars)
- a **process or loop** (flow arrows)
- a **timeline**
- a **brain region** (SVG brain outline with a glowing region)
- a **study result** (citation card with author, year and one-line finding)
- a **list of steps** (animated checklist)

Plan 6-12 per video. Each one is 3-8 s, 1920×1080, 30 fps, built in the channel palette.

### How to build an MG insert
1. Read the `hyperframes` skill and follow its routing. These are **short, unnarrated, motion-first units under 10 s**, which is the `/motion-graphics` workflow. The voiceover is added later in assembly, not inside the insert.
2. Create one HyperFrames project per episode at `production/<slug>/motion/`, with one composition per insert, named by shot ID (`MG_031.html`).
3. Render each one: `npx hyperframes render` (see `/hyperframes-cli`). Output to `production/<slug>/motion/renders/MG_031.mp4`.
4. **If HyperFrames is unavailable or fails,** use a 4K still for that shot plus a text overlay added in the editor. Never block the video on an insert.

### MG spec format (written in the shot list)
```
MG 031 | 3:12-3:18 (6.0 s) | type: bar_compare
data: "Expected: 21 days" vs "Measured median: 66 days" [F1]
motion: bars grow left→right 0.0-1.8 s, numbers count up, 66 bar glows teal at 2.2 s, hold
style: bg #0B132B, bars #45A29E / #00F0FF, text Inter/Segoe UI Bold white, accent #FFD166
```

### Palette for MG and overlays
- background: deep navy `#0B132B` or seafoam `#45A29E`
- accents: teal `#00F0FF`, gold `#FFD166`, alert red `#EF4444`
- text: white

Use a clean sans-serif font (Inter, Montserrat or Segoe UI Bold). Keep 2 fonts at most.

## Sam: one locked design (used in every IMG prompt)
`Sam, a young man in his early 20s with thick tousled dark brown hair, bold black rectangular glasses, large expressive hazel eyes, warm friendly face, wearing a heather-navy crewneck sweater`

He wears the same outfit all episode unless the script calls for pyjamas (bed scenes). That exception gets a continuity note.

## 4-block IMG prompt
```
[STYLE] 3D animated feature film still, Pixar-style stylized character, soft global illumination, subsurface skin scattering, shallow depth of field, 16:9.
[SHOT] <wide / medium / close-up / extreme close-up / over-the-shoulder>, <camera angle>.
[SUBJECT] Sam <locked description> <action + emotion, one clear verb>. <prop/metaphor if any>.
[SET + LIGHT] <simple stylized set or plain studio backdrop in palette colour>, <key light + rim light colour>, clean uncluttered background, room for subtitle at bottom third.
NEGATIVE: text, letters, words, numbers, watermark, logo, 2D, flat illustration, anime, photorealistic photo, extra fingers, deformed hands, cluttered background, different hairstyle, missing glasses
```
**Rules:**
- Never put words, numbers or clock digits in the prompt. Generators misspell them. Add them as `MG` inserts or overlays instead.
- Leave the bottom 20% calm, because subtitles go there.
- **Free generators** (pick one and keep it all episode for consistency):
  - Google Gemini / AI Studio image generation (free daily quota)
  - Microsoft Designer / Bing Image Creator (free)
  - Leonardo.ai (free daily credits)
- For Sam consistency, attach the reference `assets/branding/NEW_PROFILE_PICTURE_AVATAR.jpg` (or a previous Sam render) as an image reference whenever the generator allows it.

## Shot list format
```
| ID | Time | Dur | Line | Type | Visual / spec | Move | Trans |
| 001 | 0:00.0-0:02.2 | 2.2 | L01 | IMG | Sam lying in bed, phone glow on face (new) | push | — |
| 002 | 0:02.2-0:04.6 | 2.4 | L01 | IMG | crop of 001: eyes + glasses reflection | push | 0.35 xf |
| 031 | 3:12.0-3:18.0 | 6.0 | L24 | MG  | bar_compare 21 vs 66 days [F1] | — | 0.35 xf |
```

## Batch delivery + HANDOFF block
Deliver **15 shots per batch**:
- the shot-list rows for that batch
- the full prompt for every *new* `IMG`
- the full spec for every `MG`

End every batch with this block, exactly:

```
═══════════════ HANDOFF ═══════════════
episode: <slug>
title: <approved title>
batch: <n> of <total>
shots_done: 001-015    next_shot: 016    total_shots: <n>
timeline_done_to: 0:44.8 / <runtime>
next_lines: L07-L12
continuity: Sam=navy sweater · current set=bedroom (sky blue #6BA4B8) · props in play=phone, alarm clock
unique_images_so_far: 9    mg_inserts_so_far: 1
files: production/<slug>/02_script.md · 04_shotlist.md
resume: type CONTINUE, or paste this block in a new chat with "Use cinematic-explainer-studio and resume from this handoff".
═══════════════════════════════════════
```

**On `CONTINUE` or a pasted HANDOFF:**
1. Re-read `02_script.md` and `04_shotlist.md` if they exist.
2. Keep the continuity values.
3. Start exactly at `next_shot`.

Also append each batch to `production/<slug>/04_shotlist.md`, so a new chat can resume from the files.

## After the last batch
1. **Assembly plan:** the existing renderer pattern (`pipeline/render_topic_0X_master_video*.py`), with these changes:
   - read the shot list
   - apply the moves and transitions above
   - insert `MG_###.mp4` clips at their times
   - add subtitles in the bottom 20%
   - add a 6-8 s end screen
2. **Thumbnail prompt:** Sam waist-up with a strong emotion, plus 1 glowing prop on the right. Keep the left 45% clear for ≤ 3 words, added in the editor in white/`#FFD166` with a heavy shadow. Check that it reads at 168×94 px.
3. **Description:**
   - 2-line hook
   - chapters
   - sources list (the fact sheet)
   - 3-5 hashtags ending with `#NeuroSync`
   - no production notes
4. **Tags:** autocomplete phrases from `01_demand.md` + `NeuroSync`.
5. **3 Shorts cut points** (25-50 s each). Each must stand alone and end with "full video on the channel".
6. **Registry update text** for `production/EPISODE_REGISTRY.md`.
