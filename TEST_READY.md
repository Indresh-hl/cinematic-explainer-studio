# TEST READY: Viral Shorts E2E Acceptance Verification Suite

**Project**: Topic 03 Viral Shorts Extraction & NVENC Production  
**Author**: E2E Test Suite Writer (`test_writer_e2e`)  
**Specification**: `ORIGINAL_REQUEST.md` (§2026-09-30T12:37:46Z) & `orchestrator_2/TEST_INFRA.md`  
**Date**: 2026-09-30  

---

## 1. Executive Summary

The automated, opaque-box End-to-End (E2E) verification test suite for the two viral Shorts deliverables has been developed and verified. The test runner rigorously enforces all 5 acceptance tiers specified in `TEST_INFRA.md`, ensuring universal mobile compatibility, hardware NVENC compliance, narrative duration bounds, mobile-safe subtitle placement, and full stream playback integrity.

---

## 2. Test Execution Commands

### Primary Standalone Verification Runner
To evaluate the rendered deliverables in `C:\Users\Indresh HL\Downloads\`:
```bash
python production/topic_03/shorts/verify_e2e_shorts.py
```

### Verbose Mode with Detailed Frame & Stream Metrics
```bash
python production/topic_03/shorts/verify_e2e_shorts.py --verbose
```

### Fast Mode (Skips Full FFmpeg Decode Pass)
```bash
python production/topic_03/shorts/verify_e2e_shorts.py --skip-tier5
```

### Custom Path or Staging Deliverables Override
```bash
python production/topic_03/shorts/verify_e2e_shorts.py --short1 "path/to/short1.mp4" --short2 "path/to/short2.mp4"
```

### Pytest Execution Mode
```bash
python -m pytest production/topic_03/shorts/verify_e2e_shorts.py -v
```

### Verification Suite Unit & Adversarial Tests
```bash
python -m pytest tests/test_shorts_verification_unit.py -v
```

---

## 3. Tier Coverage & Validation Architecture

| Tier | Name | Target Specification | Enforcement Mechanism | Failure Condition |
| :--- | :--- | :--- | :--- | :--- |
| **Tier 1** | **Existence & Physical Delivery** | `TOPIC_03_VIRAL_SHORT_1_THE_5_SECOND_TEST.mp4`<br>`TOPIC_03_VIRAL_SHORT_2_THE_STRANGER_IN_YOUR_HEAD.mp4`<br>Location: `C:\Users\Indresh HL\Downloads\`<br>Size: `> 25.0 MB` (`> 26,214,400 bytes`) | `Path.exists()` & `stat().st_size` check | File missing or file size $\le 25.0$ MB |
| **Tier 2** | **Stream & Codec Compliance** | **Video**: Strictly `1080x1920` (9:16 vertical canvas), `h264`, profile `High`, pixel format strictly `yuv420p` (zero `gbrp` or 4:4:4), frame rate `30.0 fps`<br>**Audio**: `aac` stereo (`2 channels`), sample rate `48,000 Hz`, nominal bitrate `~256 kbps`<br>**Container**: MP4 with `faststart` atom ordering (`moov` before `mdat`) | `ffprobe -show_format -show_streams -print_format json`<br>+ Custom binary MP4 atom parser (`parse_mp4_atoms`) | Resolution $\ne 1080\times 1920$, codec $\ne$ h264, profile $\ne$ High, `pix_fmt` $\ne$ yuv420p, channels $\ne$ 2, sample rate $\ne$ 48kHz, or `mdat` precedes `moov` |
| **Tier 3** | **Narrative & Duration Boundaries** | **Short 1**: `48.0s <= duration <= 55.0s` (Act 4 Countdown challenge)<br>**Short 2**: `50.0s <= duration <= 58.0s` (Act 3 fMRI revelation) | `ffprobe` format & stream duration evaluation | Duration $< 48.0$s or $> 55.0$s (Short 1); Duration $< 50.0$s or $> 58.0$s (Short 2) |
| **Tier 4** | **Subtitle Mobile-Safe Zone & Reframing** | 1. **Reframing**: Dual-layer ambient blurred background eliminates solid black letterbox bars.<br>2. **Safe Zone**: Dialogue karaoke subtitles bounded strictly within mobile safe zone ($400 < y < 1500$, $80 < x < 1000$).<br>3. **ASS Geometry**: Baseline verified at $y \approx 1330$ ($1200 \le y \le 1450$). | `cv2.VideoCapture` equidistant frame sampling (top/bottom luminance variance analysis)<br>+ Connected component text contour detection<br>+ ASS script `MarginV` & `Alignment` parsing | Solid black letterbox bars detected (mean $< 0.5$, std $< 0.1$), or caption text exceeding safe boundaries ($y > 1500$ or $y < 400$) |
| **Tier 5** | **Decoding & Playback Integrity** | Full file decode to null muxer ensuring zero corrupt packets, invalid timestamps, or truncation | `ffmpeg -v error -i <file> -f null -`<br>Stderr inspection for corruption keywords | Non-zero exit code or stderr decode errors (`error`, `corrupt`, `invalid`, `truncat`, `fatal`) |

---

## 4. Current Test Verification Status

1. **Missing Deliverables Gate (Pre-Render State)**:
   - When run against target deliverable paths before rendering, the suite gracefully reports `[FAIL]` on Tier 1 and blocks dependent Tiers 2–5 with `[BLOCKED]` status.
   - Generates machine-readable diagnostic JSON: `production/topic_03/shorts/e2e_verification_report.json`.
   - Exits with return code `1`.
2. **Verification Suite Unit Tests**:
   - `tests/test_shorts_verification_unit.py` contains 8 unit and adversarial test cases verifying MP4 atom parsing, faststart detection, negative faststart handling, undersized file rejection, and cascading tier blocking.
   - Result: `8/8 PASSED` (100% pass rate in 0.12s).
3. **Execution Gate**:
   - The test script is fully operational and ready to serve as the quality acceptance gate as soon as the rendering pipeline produces the final deliverables.
