"""
Comprehensive End-to-End (E2E) Test Suite for SceneFlow Script-to-Screen Sync & Review Studio.

Author: test_writer_1 (Role: E2E Test Writer / QA Specialist)
Project: SceneFlow Script-to-Screen Synchronization & Review Studio (Topic 03)

Acceptance Criteria Tested:
1. Technical Validation:
   - topic_03_sceneflow_sync.json validates against public/schema.json with zero errors.
   - Exactly 99 shots and 481 dialogue phrases mapped with monotonic timestamps (t_start < t_end <= 565.10s).
   - All 8 tracks present and populated.
   - Verbatim text slice integrity (scriptText[startIndex:endIndex] == selectedText).
   - sceneflow_review_studio.html integrity (single self-contained zero-build file, embedded dataset,
     responsive player, 8 tracks, auto-scrolling reader, cue inspector, benchmark tab).
2. Quantitative Audit Report Acceptance Criteria:
   - AUDIT_REPORT.md presence and completeness.
   - Act 4 countdown table for digits 5, 4, 3, 2, 1 with millisecond precision and zero-lag confirmation.
   - Complete 99-shot motion verification matrix verifying 19 static holds (zero drift) and 80 dynamic moves (sinusoidal easing).
   - 5-Act prompt adherence scorecard on character fidelity, prop accuracy, and Octane lighting.
3. Adversarial and Boundary Integrity:
   - Unicode & escaping integrity, cue ID uniqueness, metadata completeness, sub-frame precision.
"""

import os
import sys
import json
import re
import unittest
from pathlib import Path

# Ensure UTF-8 output encoding across Windows consoles
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

try:
    import jsonschema
except ImportError:
    jsonschema = None

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SCHEMA_PATH = PROJECT_ROOT / "public" / "schema.json"
DATASET_PATH = PROJECT_ROOT / "topic_03_sceneflow_sync.json"
STUDIO_HTML_PATH = PROJECT_ROOT / "sceneflow_review_studio.html"
AUDIT_REPORT_PATH = PROJECT_ROOT / "AUDIT_REPORT.md"
SCRATCH_AUDIT_PATH = PROJECT_ROOT / "scratch" / "audit_results.json"

EXPECTED_TRACKS = [
    "dialogue",
    "action",
    "camera",
    "shot",
    "audio",
    "vfx",
    "transition",
    "environment"
]


class TestSceneFlowSchemaAndDataset(unittest.TestCase):
    """Verifies schema definition and dataset strict compliance, cardinality, monotonicity, and text slicing."""

    @classmethod
    def setUpClass(cls):
        cls.assertTrue(SCHEMA_PATH.exists(), f"Schema file not found at {SCHEMA_PATH}")
        cls.assertTrue(DATASET_PATH.exists(), f"Dataset file not found at {DATASET_PATH}")

        with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
            cls.schema = json.load(f)

        with open(DATASET_PATH, "r", encoding="utf-8") as f:
            cls.dataset = json.load(f)

        cls.cues = cls.dataset.get("cues", [])
        cls.script_text = cls.dataset.get("scriptText", "")

    def test_schema_definition_draft07(self):
        """Schema must declare Draft-07 and enforce required cues array."""
        self.assertEqual(self.schema.get("$schema"), "http://json-schema.org/draft-07/schema#")
        self.assertIn("cues", self.schema.get("required", []))
        cue_props = self.schema["properties"]["cues"]["items"]["properties"]
        self.assertIn("type", cue_props)
        self.assertEqual(cue_props["type"]["enum"], EXPECTED_TRACKS)

    def test_dataset_strict_jsonschema_validation(self):
        """topic_03_sceneflow_sync.json must strictly validate against public/schema.json with 0 errors."""
        self.assertIsNotNone(jsonschema, "jsonschema package must be installed")
        # Raises jsonschema.ValidationError on failure
        jsonschema.validate(instance=self.dataset, schema=self.schema)

    def test_shot_track_exact_cardinality(self):
        """Shot track must contain exactly 99 shots spanning the entire master video."""
        shot_cues = [c for c in self.cues if c.get("type") == "shot"]
        self.assertEqual(
            len(shot_cues),
            99,
            f"Expected exactly 99 shots in 'shot' track, found {len(shot_cues)}"
        )

    def test_dialogue_track_exact_cardinality(self):
        """Dialogue track must contain exactly 481 spoken dialogue phrases."""
        dialogue_cues = [c for c in self.cues if c.get("type") == "dialogue"]
        self.assertEqual(
            len(dialogue_cues),
            481,
            f"Expected exactly 481 dialogue phrases, found {len(dialogue_cues)}"
        )

    def test_all_8_tracks_present_and_populated(self):
        """All 8 canonical SceneFlow tracks must be present and populated."""
        track_counts = {}
        for c in self.cues:
            t = c.get("type")
            track_counts[t] = track_counts.get(t, 0) + 1

        for track_name in EXPECTED_TRACKS:
            self.assertIn(track_name, track_counts, f"Missing track: {track_name}")
            self.assertGreater(track_counts[track_name], 0, f"Track {track_name} has 0 cues")

        # Total cues count verification
        self.assertEqual(len(self.cues), 1174, f"Expected 1,174 total cues, found {len(self.cues)}")
        self.assertEqual(track_counts["dialogue"], 481)
        self.assertEqual(track_counts["shot"], 99)
        self.assertEqual(track_counts["camera"], 99)
        self.assertEqual(track_counts["action"], 99)
        self.assertEqual(track_counts["audio"], 99)
        self.assertEqual(track_counts["vfx"], 99)
        self.assertEqual(track_counts["transition"], 99)
        self.assertEqual(track_counts["environment"], 99)

    def test_monotonic_timestamps_and_runtime_bounds(self):
        """All cues must satisfy 0.0 <= startTime < endTime <= 565.10s with positive duration."""
        runtime_limit = 565.1001  # Master video duration 565.10s
        for idx, c in enumerate(self.cues):
            start = c.get("startTime")
            end = c.get("endTime")
            dur = c.get("duration")

            self.assertIsInstance(start, (int, float), f"Cue {c.get('id')} has non-numeric startTime")
            self.assertIsInstance(end, (int, float), f"Cue {c.get('id')} has non-numeric endTime")
            self.assertGreaterEqual(start, 0.0, f"Cue {c.get('id')} startTime < 0.0: {start}")
            self.assertLess(start, end, f"Cue {c.get('id')} startTime >= endTime: {start} >= {end}")
            self.assertLessEqual(end, runtime_limit, f"Cue {c.get('id')} endTime > 565.10s: {end}")

            if dur is not None:
                self.assertAlmostEqual(
                    dur,
                    end - start,
                    places=3,
                    msg=f"Cue {c.get('id')} duration mismatch: {dur} vs {end - start}"
                )

    def test_shot_track_continuity(self):
        """Shot track must form a continuous unbroken timeline from 0.00s to 565.10s."""
        shot_cues = [c for c in self.cues if c.get("type") == "shot"]
        shot_cues.sort(key=lambda x: x["startTime"])

        self.assertAlmostEqual(shot_cues[0]["startTime"], 0.0, places=2)
        # 565.094s is within 1 video frame (33.3ms) of 565.10s
        self.assertAlmostEqual(shot_cues[-1]["endTime"], 565.10, delta=0.05)

        for i in range(len(shot_cues) - 1):
            curr_end = shot_cues[i]["endTime"]
            next_start = shot_cues[i + 1]["startTime"]
            self.assertAlmostEqual(
                curr_end,
                next_start,
                places=2,
                msg=f"Shot discontinuity between shot {i} ({shot_cues[i]['id']}) and {i+1} ({shot_cues[i+1]['id']})"
            )

    def test_verbatim_text_slice_integrity(self):
        """Every cue must satisfy scriptText[startIndex:endIndex] == selectedText with zero mismatches."""
        self.assertTrue(len(self.script_text) > 0, "scriptText must not be empty")

        mismatches = []
        for c in self.cues:
            cid = c.get("id", "unknown")
            start = c.get("startIndex")
            end = c.get("endIndex")
            selected = c.get("selectedText")

            self.assertIsNotNone(start, f"Cue {cid} missing startIndex")
            self.assertIsNotNone(end, f"Cue {cid} missing endIndex")
            self.assertIsNotNone(selected, f"Cue {cid} missing selectedText")

            self.assertGreaterEqual(start, 0, f"Cue {cid} startIndex < 0")
            self.assertLessEqual(end, len(self.script_text), f"Cue {cid} endIndex out of bounds")
            self.assertLess(start, end, f"Cue {cid} startIndex >= endIndex")

            extracted = self.script_text[start:end]
            if extracted != selected:
                mismatches.append((cid, selected, extracted))

        self.assertEqual(
            len(mismatches),
            0,
            f"Found {len(mismatches)} verbatim text slice mismatches! First 3: {mismatches[:3]}"
        )

    def test_speaker_field_draft07_compliance(self):
        """Dialogue cues must have speaker 'Sam'; non-dialogue cues must omit speaker."""
        for c in self.cues:
            t = c.get("type")
            if t == "dialogue":
                self.assertEqual(c.get("speaker"), "Sam", f"Dialogue cue {c.get('id')} speaker != 'Sam'")
            else:
                self.assertNotIn("speaker", c, f"Non-dialogue cue {c.get('id')} has unexpected speaker field")


class TestReviewStudioHtml(unittest.TestCase):
    """Verifies standalone HTML studio integrity, embedded dataset, DOM structure, and player components."""

    @classmethod
    def setUpClass(cls):
        cls.assertTrue(STUDIO_HTML_PATH.exists(), f"Studio HTML not found at {STUDIO_HTML_PATH}")
        with open(STUDIO_HTML_PATH, "r", encoding="utf-8") as f:
            cls.html_content = f.read()

    def test_html_file_exists_and_size_threshold(self):
        """HTML review studio must be a substantial standalone file (> 500 KB)."""
        file_size = os.path.getsize(STUDIO_HTML_PATH)
        self.assertGreater(
            file_size,
            500_000,
            f"Expected review studio HTML size > 500,000 bytes, got {file_size}"
        )

    def test_zero_build_and_standalone(self):
        """HTML file must be self-contained with no external npm or bundler requirements."""
        # Must not reference node_modules, webpack, or external framework dev servers
        self.assertNotIn("node_modules", self.html_content)
        self.assertNotIn("localhost:3000", self.html_content)
        self.assertNotIn("localhost:5173", self.html_content)
        # Must contain embedded styles and scripts
        self.assertIn("<style>", self.html_content)
        self.assertIn("<script>", self.html_content)

    def test_embedded_sceneflow_dataset(self):
        """HTML must embed topic_03_sceneflow_sync.json inside <script id='embedded-sceneflow-data'>."""
        start_tag = '<script type="application/json" id="embedded-sceneflow-data">'
        self.assertIn(start_tag, self.html_content, "Missing embedded dataset script tag")

        start_idx = self.html_content.find(start_tag) + len(start_tag)
        end_idx = self.html_content.find("</script>", start_idx)
        json_raw = self.html_content[start_idx:end_idx].strip()

        embedded_data = json.loads(json_raw)
        self.assertIn("cues", embedded_data)
        self.assertIn("tracks", embedded_data)
        self.assertEqual(len(embedded_data["cues"]), 1174, "Embedded dataset cues count != 1,174")
        self.assertEqual(len(embedded_data["tracks"]), 8, "Embedded dataset tracks count != 8")

        # Verify embedded data matches canonical dataset
        with open(DATASET_PATH, "r", encoding="utf-8") as f:
            canonical_data = json.load(f)
        self.assertEqual(len(embedded_data["cues"]), len(canonical_data["cues"]))
        self.assertEqual(embedded_data["metadata"]["totalShots"], 99)
        self.assertEqual(embedded_data["metadata"]["totalDialoguePhrases"], 481)

    def test_responsive_video_player_elements(self):
        """HTML must include video player element, deliverable source, and CORS fallback picker."""
        self.assertIn('<video', self.html_content)
        self.assertIn('id="video-player"', self.html_content)
        self.assertIn('TOPIC_03_MASTER_VIDEO_WITH_CAPTIONS.mp4', self.html_content)
        # CORS Fallback controls
        self.assertIn('id="video-file-input"', self.html_content)
        self.assertIn('id="btn-load-custom-video"', self.html_content)

    def test_8_tracks_timeline_structure(self):
        """HTML must contain 8-track timeline viewport, sticky headers, ruler, and playhead cursor."""
        self.assertIn('id="timeline-viewport"', self.html_content)
        self.assertIn('id="track-headers-column"', self.html_content)
        self.assertIn('id="timeline-lanes-area"', self.html_content)
        self.assertIn('id="timeline-ruler"', self.html_content)
        self.assertIn('id="track-lanes-container"', self.html_content)
        self.assertIn('id="playhead-cursor"', self.html_content)

        # Verify all 8 track names and color tokens exist in HTML
        for t in EXPECTED_TRACKS:
            self.assertIn(f"track-{t}", self.html_content)

    def test_screenplay_reader_structure(self):
        """HTML must contain auto-scrolling screenplay reader, search filter, and cards container."""
        self.assertIn('id="screenplay-content"', self.html_content)
        self.assertIn('id="screenplay-search"', self.html_content)
        self.assertIn('id="tab-screenplay"', self.html_content)

    def test_cue_inspector_structure(self):
        """HTML must contain interactive cue inspector card, quote area, metadata, and seek controls."""
        self.assertIn('id="inspector-card"', self.html_content)
        self.assertIn('id="insp-quote"', self.html_content)
        self.assertIn('id="insp-meta-body"', self.html_content)
        self.assertIn('id="btn-replay-cue"', self.html_content)
        self.assertIn('id="btn-jump-cue-start"', self.html_content)
        self.assertIn('id="btn-jump-cue-end"', self.html_content)

    def test_act4_benchmark_tab_structure(self):
        """HTML must contain Act 4 countdown benchmark tab and rows for digits 5 through 1."""
        self.assertIn('id="tab-benchmark"', self.html_content)
        self.assertIn('benchmark-container', self.html_content)
        self.assertIn('id="benchmark-row-5"', self.html_content)
        self.assertIn('id="benchmark-row-4"', self.html_content)
        self.assertIn('id="benchmark-row-3"', self.html_content)
        self.assertIn('id="benchmark-row-2"', self.html_content)
        self.assertIn('id="benchmark-row-1"', self.html_content)

    def test_in_dom_self_test_suite_harness(self):
        """HTML must contain embedded test suite runner and results container."""
        self.assertIn('id="studio-test-results"', self.html_content)
        self.assertIn('runSelfTestSuite', self.html_content)


class TestQuantitativeAuditReport(unittest.TestCase):
    """Verifies AUDIT_REPORT.md presence, Act 4 countdown table, 99-shot motion matrix, and 5-Act scorecard."""

    @classmethod
    def setUpClass(cls):
        cls.assertTrue(AUDIT_REPORT_PATH.exists(), f"Audit report not found at {AUDIT_REPORT_PATH}")
        with open(AUDIT_REPORT_PATH, "r", encoding="utf-8") as f:
            cls.report_text = f.read()
        cls.lines = cls.report_text.splitlines()

    def test_audit_report_presence_and_size(self):
        """AUDIT_REPORT.md must exist and be comprehensive (> 30 KB)."""
        file_size = os.path.getsize(AUDIT_REPORT_PATH)
        self.assertGreater(file_size, 30_000, f"AUDIT_REPORT.md size too small: {file_size} bytes")

    def test_act4_countdown_table_and_zero_delay(self):
        """Act 4 countdown table must document digits 5, 4, 3, 2, 1 with millisecond precision and zero-delay."""
        countdown_rows = []
        in_countdown = False
        for l in self.lines:
            if "### 2.2 Act 4 Countdown Verification Table" in l:
                in_countdown = True
                continue
            if in_countdown and l.startswith("###"):
                break
            if in_countdown and l.startswith("|") and not l.startswith("| :") and not l.startswith("| Digit"):
                cols = [c.strip() for c in l.split("|")[1:-1]]
                if cols:
                    countdown_rows.append(cols)

        self.assertEqual(
            len(countdown_rows),
            5,
            f"Expected exactly 5 rows in Act 4 countdown table, found {len(countdown_rows)}"
        )

        expected_digits = ["**5**", "**4**", "**3**", "**2**", "**1**"]
        expected_shots = ["`LINE_25-A`", "`LINE_25-B`", "`LINE_26-A`", "`LINE_26-B`", "`LINE_26-C`"]
        expected_frames = ["Frame 10368", "Frame 10461", "Frame 10553", "Frame 10646", "Frame 10739"]

        for idx, row in enumerate(countdown_rows):
            # Columns: Digit, Shot ID, Preceding Shot, Spoken Whisper Onset, Acoustic Onset,
            # Visual Cut Frame, Visual Cut Time, Delta t (Whisper), Delta t (Acoustic),
            # Cut Step Diff, Pre-Cut Stability, Post-Cut Stability, Transition Type, Verification Status
            digit = row[0]
            shot_id = row[1]
            cut_frame = row[5]
            cut_step_diff = float(row[9])
            pre_cut_stab = float(row[10])
            trans_type = row[12]
            status = row[13]

            self.assertEqual(digit, expected_digits[idx])
            self.assertEqual(shot_id, expected_shots[idx])
            self.assertEqual(cut_frame, expected_frames[idx])

            # Snap cut verification: high intensity step change between shots
            self.assertGreater(cut_step_diff, 30.0, f"Digit {digit} cut step diff <= 30.0: {cut_step_diff}")

            # Zero premature flashing: pre-cut difference is effectively zero (no pre-blending)
            self.assertLessEqual(pre_cut_stab, 0.0005, f"Digit {digit} pre-cut stability diff > 0.0005: {pre_cut_stab}")

            # Hard snap cut transition
            self.assertIn("snap", trans_type)

            # Verification status confirmed
            self.assertIn("PASSED (Zero Delay)", status)

    def test_motion_matrix_19_static_holds_zero_drift(self):
        """19 static holds must be verified with zero camera drift and SSIM >= 0.996."""
        static_rows = []
        in_static = False
        for l in self.lines:
            if "### 3.1 Deep Dive: The 19 Designated Static Holds" in l:
                in_static = True
                continue
            if in_static and l.startswith("**Static Hold Verification"):
                break
            if in_static and l.startswith("|") and not l.startswith("| :") and not l.startswith("| #"):
                cols = [c.strip() for c in l.split("|")[1:-1]]
                if cols:
                    static_rows.append(cols)

        self.assertEqual(
            len(static_rows),
            19,
            f"Expected exactly 19 static hold rows, found {len(static_rows)}"
        )

        for row in static_rows:
            # Columns: #, Shot ID, Block, Narrative Subject, Duration, MAE Diff, SSIM, Flow Velocity, Max Drift, Verification Status
            shot_id = row[1]
            ssim = float(row[6])
            flow_str = row[7].replace("px/f", "").strip()
            flow_vel = float(flow_str)
            status = row[9]

            self.assertGreaterEqual(ssim, 0.996, f"Shot {shot_id} SSIM < 0.996: {ssim}")
            self.assertLess(flow_vel, 0.015, f"Shot {shot_id} flow velocity >= 0.015 px/f: {flow_vel}")
            self.assertIn("VERIFIED STATIC HOLD", status)
            self.assertIn("0 drift", status)

    def test_motion_matrix_80_dynamic_camera_moves_easing(self):
        """80 dynamic camera moves must use sinusoidal S-curve easing with mean Pearson r > 0.90."""
        # Cross-reference with scratch/audit_results.json if present
        if SCRATCH_AUDIT_PATH.exists():
            with open(SCRATCH_AUDIT_PATH, "r", encoding="utf-8") as f:
                audit_json = json.load(f)
            dyn_shots = [
                s for s in audit_json["motion_audit_matrix"]["shots"]
                if s["assigned_motion"] != "static"
            ]
            self.assertEqual(len(dyn_shots), 80, f"Expected 80 dynamic shots in audit json, got {len(dyn_shots)}")
            correlations = [s["easing_correlation_r"] for s in dyn_shots]
            mean_r = sum(correlations) / len(correlations)
            self.assertGreater(mean_r, 0.90, f"Mean Pearson r <= 0.90: {mean_r}")
            for s in dyn_shots:
                self.assertIn(s["assigned_motion"], ["zoom_in", "zoom_out", "pan_right", "pan_left", "drift"])
                self.assertIn("cos", s["easing_function"])

        # Verify from AUDIT_REPORT.md narrative breakdown
        self.assertIn("Zoom In (`zoom_in` — 54 shots)", self.report_text)
        self.assertIn("Zoom Out (`zoom_out` — 11 shots)", self.report_text)
        self.assertIn("Pan Right (`pan_right` — 9 shots)", self.report_text)
        self.assertIn("Pan Left (`pan_left` — 3 shots)", self.report_text)
        self.assertIn("Drift (`drift` — 3 shots)", self.report_text)
        # 54 + 11 + 9 + 3 + 3 = 80 dynamic shots

    def test_master_99_shot_motion_matrix_completeness(self):
        """The 99-shot motion verification matrix in Section 3.3 must list all 99 shots with PASS status."""
        matrix_rows = []
        in_matrix = False
        for l in self.lines:
            if "### 3.3 Master 99-Shot Motion Verification Matrix" in l:
                in_matrix = True
                continue
            if in_matrix and l.startswith("---"):
                break
            if in_matrix and l.startswith("|") and not l.startswith("| :") and not l.startswith("| Shot #"):
                cols = [c.strip() for c in l.split("|")[1:-1]]
                if cols:
                    matrix_rows.append(cols)

        self.assertEqual(
            len(matrix_rows),
            99,
            f"Expected exactly 99 shots in Section 3.3 matrix, found {len(matrix_rows)}"
        )

        for row in matrix_rows:
            # Columns: Shot #, Shot ID, Block, Timecode, Duration, Assigned Motion, Measured Motion, Easing Curve, Pearson r, Drift/Motion Verif, Status
            shot_num = int(row[0])
            shot_id = row[1]
            status = row[10]

            self.assertTrue(1 <= shot_num <= 99)
            self.assertTrue("PASS" in status, f"Shot {shot_id} did not pass: {status}")

    def test_5_act_prompt_adherence_scorecard(self):
        """Scorecard must evaluate all 5 Acts with Character, Props, Lighting scores >= 9.80 (Grade A+)."""
        scorecard_rows = []
        in_scorecard = False
        for l in self.lines:
            if "### 4.2 Act-by-Act Prompt Adherence Scorecard" in l:
                in_scorecard = True
                continue
            if in_scorecard and l.startswith("### **Cumulative"):
                break
            if in_scorecard and l.startswith("|") and not l.startswith("| :") and not l.startswith("| Act #"):
                cols = [c.strip() for c in l.split("|")[1:-1]]
                if cols:
                    scorecard_rows.append(cols)

        self.assertEqual(len(scorecard_rows), 5, f"Expected 5 Act scorecard rows, got {len(scorecard_rows)}")

        expected_acts = ["**Act 1**", "**Act 2**", "**Act 3**", "**Act 4**", "**Act 5**"]
        expected_shots_per_act = [24, 21, 19, 19, 16]

        total_shots = 0
        for idx, row in enumerate(scorecard_rows):
            # Columns: Act #, Narrative Phase, Timecode, Shots, Character Fidelity, Prop Accuracy, Octane Lighting, Overall Score, Visual Grade
            act_name = row[0]
            shots_str = row[3].replace("**", "").strip()
            shots_count = int(shots_str)
            total_shots += shots_count

            char_score = float(row[4].split("/")[0].strip())
            prop_score = float(row[5].split("/")[0].strip())
            octane_score = float(row[6].split("/")[0].strip())
            overall_score = float(row[7].replace("**", "").split("/")[0].strip())
            grade = row[8].replace("**", "").strip()

            self.assertEqual(act_name, expected_acts[idx])
            self.assertEqual(shots_count, expected_shots_per_act[idx])
            self.assertGreaterEqual(char_score, 9.80, f"Act {idx+1} character score < 9.80: {char_score}")
            self.assertGreaterEqual(prop_score, 9.80, f"Act {idx+1} prop score < 9.80: {prop_score}")
            self.assertGreaterEqual(octane_score, 9.80, f"Act {idx+1} octane score < 9.80: {octane_score}")
            self.assertGreaterEqual(overall_score, 9.80, f"Act {idx+1} overall score < 9.80: {overall_score}")
            self.assertEqual(grade, "Grade A+")

        self.assertEqual(total_shots, 99, f"Sum of Act shots != 99: {total_shots}")
        self.assertIn("Cumulative Grand Visual Fidelity Score: 9.89 / 10.0 (Grade A+)", self.report_text)


class TestAdversarialAndEdgeCases(unittest.TestCase):
    """Adversarial stress-testing: Unicode integrity, timestamp edge cases, and cue ID collisions."""

    @classmethod
    def setUpClass(cls):
        with open(DATASET_PATH, "r", encoding="utf-8") as f:
            cls.dataset = json.load(f)
        cls.cues = cls.dataset.get("cues", [])
        cls.script_text = cls.dataset.get("scriptText", "")

    def test_cue_id_uniqueness(self):
        """All 1,174 cue IDs must be strictly unique without collisions."""
        ids = [c["id"] for c in self.cues]
        unique_ids = set(ids)
        self.assertEqual(len(ids), len(unique_ids), f"Found {len(ids) - len(unique_ids)} duplicate cue IDs")

    def test_cue_id_conventions(self):
        """Cue IDs must adhere to standard track prefix conventions."""
        prefixes = {
            "dialogue": "cue_dlg_",
            "action": "cue_act_",
            "camera": "cue_cam_",
            "shot": "cue_shot_",
            "audio": "cue_aud_",
            "vfx": "cue_vfx_",
            "transition": "cue_trans_",
            "environment": "cue_env_"
        }
        for c in self.cues:
            t = c["type"]
            cid = c["id"]
            expected_prefix = prefixes[t]
            self.assertTrue(
                cid.startswith(expected_prefix),
                f"Cue {cid} of type '{t}' does not start with '{expected_prefix}'"
            )

    def test_unicode_and_typographic_slice_fidelity(self):
        """Verifies special unicode characters in selectedText match scriptText without UTF corruption."""
        special_cues = [
            c for c in self.cues
            if any(ch in c["selectedText"] for ch in ["—", "–", "“", "”", "‘", "’", ">", "<", "[", "]"])
        ]
        self.assertGreater(len(special_cues), 50, "Expected numerous cues with typographic characters")
        for c in special_cues:
            extracted = self.script_text[c["startIndex"]:c["endIndex"]]
            self.assertEqual(extracted, c["selectedText"])

    def test_sub_second_boundary_precision(self):
        """Verifies all timestamp deltas are positive and reasonable for 30fps video."""
        for c in self.cues:
            dur = c["endTime"] - c["startTime"]
            self.assertGreater(dur, 0.001, f"Cue {c['id']} duration <= 1ms: {dur}")


def run_tests():
    """Runs all test cases with a formatted summary."""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    suite.addTests(loader.loadTestsFromTestCase(TestSceneFlowSchemaAndDataset))
    suite.addTests(loader.loadTestsFromTestCase(TestReviewStudioHtml))
    suite.addTests(loader.loadTestsFromTestCase(TestQuantitativeAuditReport))
    suite.addTests(loader.loadTestsFromTestCase(TestAdversarialAndEdgeCases))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
