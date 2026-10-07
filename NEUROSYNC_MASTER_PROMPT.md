# NeuroSync Master Prompt (reuse for every video)

Copy everything inside the box, fill in the 4 blanks, paste into a new chat.

```text
Use the neurosync-video-studio skill (NeuroSync v2) for a new long-form video.

TOPIC: <your topic idea, or write "pick one for me from what people search">
LENGTH: <7-9 minutes>
VOICE: <"my own voice" or "Edge-TTS AndrewMultilingualNeural">
IMAGE TOOL: <Gemini / Bing Image Creator / Leonardo - the free one I will use>

Follow the 3 phases strictly and STOP at each gate:

PHASE 1 - RESEARCH + PACKAGING
- Read production/EPISODE_REGISTRY.md first (avoid repeated topics/devices).
- Run tools/research/yt_demand.py with 3-5 viewer-style seed queries and use the REAL numbers.
- Give me: demand + gap, the "Most videos say ___, but research shows ___" angle, format choice,
  a fact sheet (4-8 claims, each with author/year/journal + link, strength rating; no unsourced numbers),
  3 titles (<=60 chars), thumbnail concept, 15-second hook.
- STOP and wait for me to pick a title.

PHASE 2 - SCRIPT + VOICEOVER
- 1,050-1,300 words, plain English, chosen format, numbered lines L01... with timings and pause marks,
  [F#] tag on every factual line, no spoken channel name.
- Show the script checklist results.
- STOP and wait for my approval, then give me the exact voiceover command/recording notes.

PHASE 3 - SHOT LIST + IMAGES
- One shot every 2-4 seconds matched to the words, slow eased motion on every still,
  crop-reuse to keep unique images ~0.6 x shots.
- Use HyperFrames motion-graphic inserts (MG) for numbers, comparisons, processes, timelines,
  brain regions and study results (6-12 per video); still image + overlay if HyperFrames fails.
- Deliver 15 shots per batch: shot rows + full 4-block prompt for each new image + full spec for each MG.
- End every batch with the HANDOFF block. Wait for me to type CONTINUE.
- After the last batch: assembly plan, thumbnail prompt, final title, description with chapters
  and sources, tags, 3 Shorts cut points, and the registry update.

Save everything under production/<episode-slug>/.
```

---

## Continue in the same chat
```text
CONTINUE
```

## Resume in a new chat (if the chat gets too long)
```text
Use the neurosync-video-studio skill and resume from this handoff. Read the files listed in it first.

<paste the last HANDOFF block here>
```

## Change something mid-way
```text
Before continuing: <what to change, e.g. "make shots 016-030 calmer, fewer close-ups">. Then CONTINUE from the handoff.
```
