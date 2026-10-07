# Phase 1: Research protocol

The goal is to choose a topic people already search for, find an angle the big videos missed, and collect claims that are actually true. Packaging (title + thumbnail) is decided here, before any script exists, because packaging decides whether anyone clicks.

## Step 1: Seeds
Write 3-5 seed queries the way a viewer would type them. Use plain words, not scientific terms.
Good: `why do i procrastinate`, `why cant i focus`, `how to stop overthinking at night`.
Bad: `prefrontal cortex executive dysfunction`.

## Step 2: Demand check (free tool, real data)
```
python tools/research/yt_demand.py "<seed1>" "<seed2>" "<seed3>" --out production/<slug>/01_demand.md
```
Read the output and decide:
- **Demand:** the median views of the top 10 results are above about 300K, so the topic is proven.
- **Gap:** check the dates and channels. If the top results are 5-10 years old, or all come from huge channels with a different style (TED, Kurzgesagt), there is room for a fresh 3D take.
- **Language:** autocomplete phrases become title words and tags. If people type "procrastinate things i want to do", that exact phrase is a title candidate.
- **Avoid:** topics where every top result is under 50K views (no demand), unless it is a Short test.

## Step 3: Angle
Write one sentence: **"Most videos say ___, but the research actually shows ___."** If you can't fill both blanks with something true and surprising, pick another topic.

## Step 4: Fact sheet (web search required)
Find 4-8 claims. For each one, use web search to confirm it exists and says what you claim.

| ID | Claim (plain English) | Source (author, year, journal/book) | Link/DOI | Strength |
|---|---|---|---|---|
| F1 | Habits took a median of 66 days to become automatic (range 18-254) | Lally et al., 2010, *European Journal of Social Psychology* | doi:10.1002/ejsp.674 | strong |

Rules:
- **Strength:** *strong* means replicated or a large study. *moderate* means a single study or a small sample. *contested* means there are failed replications or the experts disagree. Contested claims must be described as debated in the script.
- Popular-science figures (Huberman, podcasts, books) are fine for ideas, but the claim must trace back to a study.
- **Known traps to avoid or label carefully:**
  - "dopamine detox" as literally lowering dopamine (it doesn't)
  - ego depletion / willpower as a fuel tank (the replications largely failed)
  - "21 days to form a habit" (a myth)
  - "first 90 minutes is peak neuroplasticity" (no evidence)
  - "you only use 10% of your brain"
  - left/right brain personalities
- If a number can't be sourced, delete it. "Most people" is fine. "92% of people" is not, unless it has a source.

## Step 5: Packaging
- **3 titles, each ≤ 60 characters.** Use a curiosity gap plus a clear benefit, and include at least one autocomplete phrase.
  Example: `Why You Procrastinate on Things You WANT to Do`
- **Thumbnail concept:** Sam (waist-up, one strong emotion) + 1 glowing prop + ≤ 3 words. The words must add to the title, not repeat it.
- **Hook draft (first 15 s):** an everyday moment the viewer recognises, then the surprising truth, then a promise of what they'll get by the end.

## Phase 1 report template
```
# Phase 1: <working title>
Demand: median views <n> · freshest top result <age> · gap: <one line>
Angle: Most videos say ___, but the research actually shows ___.
Format: <format from rotation> (last 2 episodes used: <x>, <y>)
Titles: 1) … 2) … 3) …   Recommended: <n> because …
Thumbnail: Sam <emotion> + <prop> + "<≤3 words>"
Hook (15 s): …
Fact sheet: <table>
Devices to avoid (from registry): …
→ GATE 1: reply with the title number (or edits) to start the script.
```
