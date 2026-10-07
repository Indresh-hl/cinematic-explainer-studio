# Phase 2: Script + voiceover

## What was wrong in v1 (don't repeat)
| v1 problem | v2 rule |
|---|---|
| Same 5-act template, same "crime scene at 6:45 AM" opening and 5-second test in every video | Rotate formats (below). Check the registry for retired devices |
| Jargon wall ("protect your tonic dopamine baseline, clear residual adenosine") | Plain English. One term per paragraph, explained in the same sentence |
| Invented numbers ("500% spike", "92% of habits die", "60% bandwidth depleted") | Every number is tagged `[F#]` from the fact sheet |
| Purple prose ("neurochemical heist", "biologically repulsive", "dopamine tsunami") | Concrete, calm, confident. One vivid image per idea, not three |
| Spoken channel name "I'm Isy why" baked into audio | Never say the channel name in the voiceover. The end card shows it |
| 9:30-10:00 runtime with slow middle | 7-9 min. Cut anything that doesn't move the viewer forward |

## Format rotation (pick one that wasn't used in the last 2 episodes)
1. **The Myth-Buster:** state the popular belief, show why it's wrong, give the real model, then the practical fix.
2. **The Investigation:** start with a strange everyday mystery, follow 3 clues (studies), reveal the answer, then what to do.
3. **The Story of a Study:** tell one landmark experiment like a story (the people, what they expected, the twist), then what it means for you.
4. **The Countdown:** "5 things your brain does when…", from smallest to most surprising, each with one fact and one tip.
5. **Day-in-the-Life:** follow Sam through one day. Each time-stamped moment explains one brain mechanism.

## Universal structure (sits under any format)
| Part | Time | Job |
|---|---|---|
| Hook | 0:00-0:15 | A moment the viewer recognises, a surprising truth, and a promise ("by the end you'll know…") |
| Setup | 0:15-1:00 | Why this matters, plus an **open loop** (a question answered later) |
| Body | 1:00-6:30 | 3-4 sections. Each ends with a mini-payoff and a new open loop |
| Re-hook | ~50-60% | A pattern break: a direct question to the viewer, a surprising reversal, or a quick self-test. **Different device every episode** |
| Fix | 6:30-8:00 | 2-3 specific actions with "when X happens, do Y" phrasing |
| Close | last 20 s | A one-line takeaway, then point to one specific related video. No brand name spoken |

## Writing rules
- Sentences average 10-15 words. Read every line out loud. If you'd run out of breath, split it.
- Use "you" and the present tense. Show Sam doing it so the visuals have something to show.
- Explain each mechanism with **one** concrete metaphor, and reuse it so viewers learn it.
- Every 45-60 s, give the viewer a reason to stay: a question, a reveal, or "but here's the strange part".
- For a contested finding, say so: "researchers still argue about this, but…". This builds trust.
- Sources go in the description, not read aloud. Say "a 2010 study at University College London", not a full citation.

## Script output format
```
L01 [0:00-0:06] (hook)    It's 1 AM. You're exhausted. And you're still scrolling.  ⏸
L02 [0:06-0:12]           You know you should sleep. So why can't you put the phone down?
...
L24 [3:10-3:17] [F2]      In 2010, researchers at UCL tracked 96 people building a new habit.
```
- `⏸` marks a short pause (about 0.4 s). `⏸⏸` marks a long beat (about 0.8 s).
- Estimate time at about 2.4 words per second.
- Then show the totals: word count, estimated runtime, number of `[F#]` tags, and the format used.

## Script checklist (show it, all must pass)
- [ ] Hook names a concrete moment in ≤ 2 sentences, and the promise appears by 0:15
- [ ] No jargon in the first 60 s
- [ ] Every number has an `[F#]` tag; contested claims are labelled
- [ ] At least 3 open loops, each closed later
- [ ] The re-hook device is not in the registry's "used" list
- [ ] The fix section has specific "when X, do Y" actions
- [ ] No spoken brand name; no "Isy why"
- [ ] 1,050-1,300 words

## Voiceover (free)
**Option A: your own voice (best for trust, free).** Use a phone or USB mic in a quiet room with soft furnishings around you. Record each line 2 times, then remove noise in Audacity (free) or with the FFmpeg chain below.

**Option B: Edge-TTS (free).** Pick ONE voice and keep it forever.
```
edge-tts --voice en-US-AndrewMultilingualNeural --rate=-2% --pitch=+0Hz -f production/<slug>/03_voiceover_lines.txt --write-media production/<slug>/audio/vo_raw.mp3
```
- Generate line by line (the existing `pipeline/generate_topic_0X_voiceover.py` pattern). Insert silence for `⏸` (400 ms) and `⏸⏸` (800 ms).
- Don't use extreme pitch shifts. They make the voice more obviously synthetic.

**Mastering (both options):**
```
ffmpeg -i vo_raw.mp3 -af "highpass=f=75,equalizer=f=120:t=q:w=1.2:g=2,equalizer=f=3400:t=q:w=1.4:g=1.5,acompressor=threshold=-18dB:ratio=3:attack=5:release=80,loudnorm=I=-14:LRA=7:TP=-1.5" -ar 48000 vo_master.wav
```
**Timestamps:** run Whisper with `word_timestamps=True` (the existing `pipeline/align_whisper.py`) to produce `audio/word_timestamps.json`. Phase 3 uses the real timings when they exist. Otherwise it uses the estimates.

**Music (free):** use the YouTube Audio Library. Keep music at -28 to -32 LUFS under the voice, and duck it during the hook.
