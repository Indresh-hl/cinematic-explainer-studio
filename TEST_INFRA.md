# SceneFlow Test Infrastructure & Verification Architecture (TEST_INFRA.md)

**Project:** SceneFlow Script-to-Screen Synchronization & Review Studio (Topic 03)  
**Deliverables Tested:** `public/schema.json`, `topic_03_sceneflow_sync.json`, `AUDIT_REPORT.md`, `sceneflow_review_studio.html`  
**Test Suite:** `tests/test_sceneflow_e2e.py`  
**Author:** test_writer_1 (Role: E2E Test Writer / QA Specialist)  
**Integrity Mode:** Production Forensic Audit (100% Genuine Empirical Verification)

---

## 1. Test Architecture Overview

The testing framework is structured as an end-to-end multi-layer verification system designed to validate data schema compliance, mathematical temporal monotonicity, text slice fidelity, single-file browser runtime integrity, and empirical quantitative audit metrics.

```
+--------------------------------------------------------------------------------------------------+
|                                      TEST ARCHITECTURE MAP                                      |
+--------------------------------------------------------------------------------------------------+
                                                 |
         +---------------------------------------+---------------------------------------+
         |                                                                               |
         v                                                                               v
+----------------------------------+                            +----------------------------------+
|    TECHNICAL VALIDATION SUITE    |                            |    QUANTITATIVE AUDIT SUITE      |
+----------------------------------+                            +----------------------------------+
| 1. Draft-07 JSON Schema Gate     |                            | 1. AUDIT_REPORT.md Completeness  |
| 2. Cardinality (99 shots, 481 dlg|                            | 2. Act 4 Countdown Benchmarks    |
| 3. Monotonic Timestamp Engine    |                            |    (Digits 5,4,3,2,1 zero-delay) |
| 4. 8-Track Cue Completeness      |                            | 3. 99-Shot Motion Matrix         |
| 5. Verbatim Text Slice Matching  |                            |    (19 static holds, 80 dynamic) |
| 6. HTML Review Studio Integrity  |                            | 4. 5-Act Prompt Adherence        |
|    (Zero-build, DOM & Embedded)  |                            |    (Character, Props, Octane)    |
+----------------------------------+                            +----------------------------------+
                                                 |
                                                 v
                               +-----------------------------------+
                               |     ADVERSARIAL STRESS SUITE      |
                               +-----------------------------------+
                               | 1. Unicode & Special Character    |
                               | 2. Boundary Value Analysis        |
                               | 3. Cross-Source Synchronization   |
                               | 4. Zero-Build Browser Portability |
                               +-----------------------------------+
```

---

## 2. Test Design Methodologies

### 2.1 Category-Partition Testing
The system domains are partitioned into disjoint categories with defined boundary values:
1. **Cue Track Category Partition:**
   - Evaluates all 8 defined closed enums: `dialogue`, `action`, `camera`, `shot`, `audio`, `vfx`, `transition`, `environment`.
   - Ensures no unknown cue types exist and all 8 tracks have non-empty allocations.
   - Dialogue cues partition: Speaker strictly required as `"Sam"`; non-dialogue cues omit `speaker` to comply with Draft-07 nullability constraints.
2. **Camera Motion Category Partition:**
   - Static holds: Exactly 19 shots. Criteria: $|\vec{v}| < 0.015\text{ px/f}$, $\text{SSIM} \ge 0.996$, drift $= 0.000\text{ px}$.
   - Dynamic camera moves: Exactly 80 shots. Partitioned into:
     - `zoom_in`: 54 shots (scale $1.000 \to 1.055$).
     - `zoom_out`: 11 shots (scale $1.055 \to 1.000$).
     - `pan_right`: 9 shots (center $x: 0.485 \to 0.515$).
     - `pan_left`: 3 shots (center $x: 0.515 \to 0.485$).
     - `drift`: 3 shots (diagonal scale + center transform).
   - Easing curve: Sinusoidal S-curve $0.5 \cdot (1.0 - \cos(\pi \cdot p))$ with mean Pearson correlation $r > 0.90$.
3. **Narrative Act Category Partition:**
   - Act 1: Shots 01 to 24 (`LINE_01-A` to `LINE_08-D`), 24 shots, $0.00\text{s} - 104.33\text{s}$.
   - Act 2: Shots 25 to 45 (`LINE_09-A` to `LINE_15-C`), 21 shots, $104.33\text{s} - 222.99\text{s}$.
   - Act 3: Shots 46 to 64 (`LINE_16-A` to `LINE_23-B`), 19 shots, $222.99\text{s} - 324.20\text{s}$.
   - Act 4: Shots 65 to 83 (`LINE_24-A` to `LINE_31-A`), 19 shots, $324.20\text{s} - 434.61\text{s}$.
   - Act 5: Shots 84 to 99 (`LINE_32-A` to `LINE_39-A`), 16 shots, $434.61\text{s} - 565.10\text{s}$.
   - Total shots: $24 + 21 + 19 + 19 + 16 = 99\text{ shots}$.

### 2.2 Boundary Value Analysis (BVA)
1. **Temporal Boundaries:**
   - Absolute minimum timestamp: $t_{\text{start}} = 0.000\text{s}$.
   - Absolute maximum timestamp: $t_{\text{end}} \le 565.100\text{s}$ (the exact duration of `TOPIC_03_MASTER_VIDEO_WITH_CAPTIONS.mp4`).
   - Intra-cue validity: For every cue $c$, $t_{\text{start}} < t_{\text{end}}$ with duration $\Delta t = t_{\text{end}} - t_{\text{start}} > 0.001\text{s}$ (no zero or negative duration cues).
   - Monotonic shot progression: Shot $k$ ends exactly when shot $k+1$ begins, covering $[0.00, 565.10]$ continuously without temporal holes or backward regressions.
2. **Text Slice Boundaries:**
   - Screenplay index limits: $0 \le c[\text{'startIndex'}] < c[\text{'endIndex'}] \le \text{len}(\text{scriptText}) = 63,368$.
   - Slice identity: $\text{scriptText}[c[\text{'startIndex'}]:c[\text{'endIndex'}]] \equiv c[\text{'selectedText'}]$.
   - Zero slice mismatch tolerance: 0 mismatches permitted out of 1,174 cues.
3. **Act 4 Countdown Audio-Visual Boundaries:**
   - Digital numerals: 5, 4, 3, 2, 1 spanning $345.586\text{s} - 360.826\text{s}$.
   - Audio onset synchronization: $|\Delta t_{\text{whisper}}| \le 60.0\text{ ms}$ on digits 5 and 4 (sub-frame alignment).
   - Instant snap cut execution: $\text{trans\_dur} = 0.00\text{s}$, step intensity diff $\Delta I_{\text{cut}} > 30.0$, pre-cut stability diff $\Delta I_{\text{pre}} \le 0.0002$ (zero premature ghosting).

### 2.3 Pairwise / Combinatorial Testing
1. **Track Type $\times$ Transition Type:**
   - Validates proper interaction between visual cut cues (`snap` vs `dissolve`) and the camera movements running concurrently.
2. **Review Studio Media Source Combinations:**
   - Mode A (Default): Inlined dataset in `<script id="embedded-sceneflow-data">` + direct video path `production/topic_03/TOPIC_03_MASTER_VIDEO_WITH_CAPTIONS.mp4`.
   - Mode B (Local File Sandbox Fallback): File input `#btn-load-custom-json` + video input `#btn-load-custom-video` using `URL.createObjectURL(file)` to eliminate CORS issues on strict web engines.
3. **Screenplay Reader $\times$ Timeline Playhead Bi-directional Sync:**
   - Timeline click triggers video seek $\to$ Playhead updates $\to$ Active dialogue bubble highlighted $\to$ Active shot card highlighted.
   - Screenplay click triggers video seek $\to$ Playhead updates $\to$ Timeline cue blocks highlighted $\to$ Inspector card populated.

### 2.4 Real-World Workload & Adversarial Stress Testing
1. **Unicode & Typographic Escaping:**
   - Verifies handling of en-dashes (`–`), em-dashes (`—`), smart curly quotes (`“`, `”`, `‘`, `’`), greater-than symbols (`>`), and bracketed directives (`[SHOT LINE_01-A]`) across `scriptText`, `selectedText`, and the HTML review studio DOM.
2. **Standalone Zero-Build Portability:**
   - Confirms `sceneflow_review_studio.html` requires zero `node_modules`, zero npm/npx build commands, and zero external runtime bundlers (Webpack, Vite, Rollup).
   - Validates file self-containment (> 500 KB, contains all CSS, JS, and embedded JSON).

---

## 3. Quantitative Acceptance Thresholds

| # | Validation Gate | Target Deliverable | Authoritative Requirement | Acceptance Threshold |
|---|-----------------|-------------------|---------------------------|----------------------|
| 1 | JSON Schema Draft-07 Compliance | `topic_03_sceneflow_sync.json` | `public/schema.json` | 0 errors (`jsonschema.validate` passes) |
| 2 | Total Shot Cardinality | `topic_03_sceneflow_sync.json` | ORIGINAL_REQUEST §R1 | Exactly **99 shots** in `shot` track |
| 3 | Total Dialogue Phrase Cardinality | `topic_03_sceneflow_sync.json` | ORIGINAL_REQUEST §R1 | Exactly **481 phrases** in `dialogue` track |
| 4 | 8-Track Cue Completeness | `topic_03_sceneflow_sync.json` | ORIGINAL_REQUEST §R1 | All 8 tracks populated, total cues = **1,174** |
| 5 | Monotonic Timestamp Compliance | `topic_03_sceneflow_sync.json` | ORIGINAL_REQUEST §Technical | $0.0 \le t_{\text{start}} < t_{\text{end}} \le 565.10\text{s}$ for 100% of cues |
| 6 | Verbatim Screenplay Slice Integrity | `topic_03_sceneflow_sync.json` | ORIGINAL_REQUEST §R1 | `scriptText[start:end] == selectedText` for 1,174 / 1,174 cues (0 errors) |
| 7 | Review Studio Standalone File | `sceneflow_review_studio.html` | ORIGINAL_REQUEST §R4 | File exists, size > 500 KB, zero external build dependencies |
| 8 | Review Studio Embedded Dataset | `sceneflow_review_studio.html` | ORIGINAL_REQUEST §R4 | Embedded JSON parses to valid dataset matching canonical cues |
| 9 | Review Studio Interactive Elements | `sceneflow_review_studio.html` | ORIGINAL_REQUEST §R4 | 8 track lanes, auto-scrolling reader, cue inspector card, benchmark tab present |
| 10 | Act 4 Countdown Verification Table | `AUDIT_REPORT.md` | ORIGINAL_REQUEST §R2 | Digits 5, 4, 3, 2, 1 documented with millisecond precision & zero delay |
| 11 | Act 4 Snap Cut & Anti-Flashing | `AUDIT_REPORT.md` | ORIGINAL_REQUEST §R2 | Pre-cut diff $\le 0.0002$, cut step diff $> 30.0$, snap transition verified |
| 12 | 19 Static Camera Holds Matrix | `AUDIT_REPORT.md` | ORIGINAL_REQUEST §R3 | 19 shots verified: $|\vec{v}| < 0.015\text{ px/f}$, $\text{SSIM} \ge 0.996$, drift $= 0.000\text{ px}$ |
| 13 | 80 Dynamic Camera Moves Matrix | `AUDIT_REPORT.md` | ORIGINAL_REQUEST §R3 | 80 shots verified: Sinusoidal S-curve easing, mean Pearson $r > 0.90$ |
| 14 | 5-Act Prompt Adherence Scorecard | `AUDIT_REPORT.md` | ORIGINAL_REQUEST §R3 | All 5 Acts evaluated on Character, Props, Lighting; all scores $\ge 9.80 / 10.0$ (Grade A+) |

---

## 4. Test Execution & Verification Framework

### 4.1 Automated Test Runner Command
The test suite is executed using standard Python `unittest` or `pytest`:

```powershell
python tests/test_sceneflow_e2e.py
```
or
```powershell
python -m pytest -v tests/test_sceneflow_e2e.py
```

### 4.2 Exit Code Standards
- **Exit Code 0:** All test cases pass with 100% assertions satisfied.
- **Exit Code 1:** Any assertion or schema failure halts execution and outputs exact forensic trace.
