"""
Adversarial Stress-Testing & Schema Fuzzing Suite for SceneFlow Sync Dataset.

Author: challenger_1 (Role: Dataset & Schema Challenger)
Mission: Empirically stress-test topic_03_sceneflow_sync.json and public/schema.json.
"""

import copy
import json
import math
import random
import re
import unittest
from pathlib import Path

try:
    import jsonschema
except ImportError:
    jsonschema = None

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SCHEMA_PATH = PROJECT_ROOT / "public" / "schema.json"
DATASET_PATH = PROJECT_ROOT / "topic_03_sceneflow_sync.json"
HTML_PATH = PROJECT_ROOT / "sceneflow_review_studio.html"

VALID_CUE_TYPES = [
    "dialogue",
    "action",
    "camera",
    "shot",
    "audio",
    "vfx",
    "transition",
    "environment"
]


class TestAdversarialSchemaFuzzing(unittest.TestCase):
    """Fuzzes and mutates schema instances to verify negative validation and error boundaries."""

    @classmethod
    def setUpClass(cls):
        assert jsonschema is not None, "jsonschema package is required"
        assert SCHEMA_PATH.exists(), f"Schema missing: {SCHEMA_PATH}"
        assert DATASET_PATH.exists(), f"Dataset missing: {DATASET_PATH}"

        with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
            cls.schema = json.load(f)

        with open(DATASET_PATH, "r", encoding="utf-8") as f:
            cls.canonical_dataset = json.load(f)

        cls.validator = jsonschema.Draft7Validator(cls.schema)

    def test_canonical_dataset_validates_without_error(self):
        """The canonical dataset must validate cleanly against the official schema."""
        errors = list(self.validator.iter_errors(self.canonical_dataset))
        self.assertEqual(len(errors), 0, f"Canonical dataset failed validation: {errors}")

    def test_negative_missing_root_cues(self):
        """Root instance lacking 'cues' must be rejected."""
        bad_instances = [
            {},
            {"metadata": {}},
            {"cues_list": []}
        ]
        for inst in bad_instances:
            with self.subTest(inst=inst):
                errors = list(self.validator.iter_errors(inst))
                self.assertGreater(len(errors), 0, f"Expected validation failure for: {inst}")

    def test_negative_invalid_root_cues_type(self):
        """'cues' must be an array, rejecting non-array root types."""
        bad_cues_types = [
            {"cues": "not-an-array"},
            {"cues": 12345},
            {"cues": {"key": "val"}},
            {"cues": None},
            {"cues": True}
        ]
        for inst in bad_cues_types:
            with self.subTest(inst=inst):
                errors = list(self.validator.iter_errors(inst))
                self.assertGreater(len(errors), 0, f"Expected rejection for: {inst}")

    def test_negative_missing_cue_required_fields(self):
        """Omitting any required field (id, type, selectedText, startTime, endTime) must fail."""
        base_cue = {
            "id": "cue_test_001",
            "type": "dialogue",
            "selectedText": "Hello world",
            "startTime": 10.0,
            "endTime": 12.0
        }
        required_fields = ["id", "type", "selectedText", "startTime", "endTime"]

        for req in required_fields:
            mutated_cue = base_cue.copy()
            del mutated_cue[req]
            instance = {"cues": [mutated_cue]}
            with self.subTest(missing_field=req):
                errors = list(self.validator.iter_errors(instance))
                self.assertGreater(len(errors), 0, f"Omission of required field '{req}' was not rejected")

    def test_negative_invalid_cue_types(self):
        """Cue 'type' values outside the 8 canonical tracks must be rejected."""
        invalid_types = [
            "subtitle", "music", "lighting", "sfx", "cut", "b-roll",
            "", "   ", "dialogue ", "DIALOGUE", "Shot", None, 999, False, []
        ]
        base_cue = {
            "id": "cue_test_001",
            "type": "dialogue",
            "selectedText": "Hello world",
            "startTime": 10.0,
            "endTime": 12.0
        }
        for inv_type in invalid_types:
            mutated = base_cue.copy()
            mutated["type"] = inv_type
            instance = {"cues": [mutated]}
            with self.subTest(invalid_type=inv_type):
                errors = list(self.validator.iter_errors(instance))
                self.assertGreater(len(errors), 0, f"Invalid cue type '{inv_type}' was unexpectedly accepted")

    def test_negative_corrupt_timestamps(self):
        """Corrupt timestamp formats (strings, nulls, booleans, objects, arrays) must be rejected."""
        base_cue = {
            "id": "cue_test_001",
            "type": "shot",
            "selectedText": "[SHOT LINE_01-A]",
            "startTime": 0.0,
            "endTime": 3.5
        }
        corrupt_values = [
            "0.0", "3.5", "invalid", "", None, True, False, [0.0], {"val": 3.5}
        ]
        for field in ["startTime", "endTime"]:
            for bad_val in corrupt_values:
                mutated = base_cue.copy()
                mutated[field] = bad_val
                instance = {"cues": [mutated]}
                with self.subTest(field=field, bad_val=bad_val):
                    errors = list(self.validator.iter_errors(instance))
                    self.assertGreater(len(errors), 0, f"Corrupt {field}={bad_val!r} was unexpectedly accepted")

    def test_negative_corrupt_id_and_selected_text(self):
        """Non-string 'id' and 'selectedText' must be rejected."""
        base_cue = {
            "id": "cue_test_001",
            "type": "shot",
            "selectedText": "[SHOT LINE_01-A]",
            "startTime": 0.0,
            "endTime": 3.5
        }
        corrupt_non_strings = [123, None, True, False, ["list"], {"obj": 1}]
        for field in ["id", "selectedText"]:
            for bad_val in corrupt_non_strings:
                mutated = base_cue.copy()
                mutated[field] = bad_val
                instance = {"cues": [mutated]}
                with self.subTest(field=field, bad_val=bad_val):
                    errors = list(self.validator.iter_errors(instance))
                    self.assertGreater(len(errors), 0, f"Corrupt {field}={bad_val!r} was accepted")

    def test_negative_speaker_type_validation(self):
        """Non-string speaker values (integer, boolean, list, dict) must be rejected."""
        base_cue = {
            "id": "cue_dlg_test",
            "type": "dialogue",
            "speaker": "Sam",
            "selectedText": "Test line",
            "startTime": 0.0,
            "endTime": 1.0
        }
        bad_speakers = [123, True, False, ["Sam"], {"name": "Sam"}]
        for bad_speaker in bad_speakers:
            mutated = base_cue.copy()
            mutated["speaker"] = bad_speaker
            instance = {"cues": [mutated]}
            with self.subTest(bad_speaker=bad_speaker):
                errors = list(self.validator.iter_errors(instance))
                self.assertGreater(len(errors), 0, f"Corrupt speaker={bad_speaker!r} was accepted")

    def test_schema_flaw_speaker_nullable_inconsistency(self):
        """Documents the Draft-07 schema issue where speaker: null fails validation despite nullable: true."""
        cue_with_null_speaker = {
            "id": "cue_act_001",
            "type": "action",
            "speaker": None,
            "selectedText": "[ACT LINE_01-A]",
            "startTime": 0.0,
            "endTime": 1.0
        }
        instance = {"cues": [cue_with_null_speaker]}
        errors = list(self.validator.iter_errors(instance))
        # Note: In Draft-07, 'nullable: true' is not honored, so None is rejected as type 'string'
        self.assertGreater(
            len(errors), 0,
            "Expected Draft-07 validator to reject speaker=null because schema lacks type: ['string', 'null']"
        )

    def test_schema_boundary_omission_of_non_negative_constraint(self):
        """Demonstrates that schema.json permits negative timestamps (semantic gap requiring oracle test)."""
        cue_with_negative_time = {
            "id": "cue_test_neg",
            "type": "action",
            "selectedText": "Negative time cue",
            "startTime": -10.0,
            "endTime": -5.0
        }
        instance = {"cues": [cue_with_negative_time]}
        errors = list(self.validator.iter_errors(instance))
        # This confirms public/schema.json lacks 'minimum: 0.0', proving need for empirical dataset oracle
        self.assertEqual(
            len(errors), 0,
            "Schema unexpectedly rejected negative numbers (schema does not declare minimum: 0)"
        )

    def test_adversarial_random_mutation_fuzzing(self):
        """Executes 500 stochastic mutations against valid cues to ensure robust rejection of malformed data."""
        sample_cues = random.sample(self.canonical_dataset["cues"], 50)
        rng = random.Random(42)  # Deterministic seed for reproducible fuzzing

        rejected_count = 0
        total_mutations = 500

        mutation_ops = [
            "delete_required_field",
            "corrupt_type",
            "corrupt_start_time_type",
            "corrupt_end_time_type",
            "corrupt_id_type",
            "corrupt_text_type",
            "set_null_field",
        ]

        for i in range(total_mutations):
            base = copy.deepcopy(rng.choice(sample_cues))
            op = rng.choice(mutation_ops)

            if op == "delete_required_field":
                field = rng.choice(["id", "type", "selectedText", "startTime", "endTime"])
                if field in base:
                    del base[field]
            elif op == "corrupt_type":
                base["type"] = rng.choice(["invalid_" + str(i), 1234, False, "AUDIO"])
            elif op == "corrupt_start_time_type":
                base["startTime"] = rng.choice(["0.0", None, True, [1.0], {"t": 0}])
            elif op == "corrupt_end_time_type":
                base["endTime"] = rng.choice(["5.0", None, False, [5.0], {"t": 5}])
            elif op == "corrupt_id_type":
                base["id"] = rng.choice([123, None, False, ["id"]])
            elif op == "corrupt_text_type":
                base["selectedText"] = rng.choice([456, None, True, []])
            elif op == "set_null_field":
                field = rng.choice(["id", "type", "selectedText", "startTime", "endTime"])
                base[field] = None

            inst = {"cues": [base]}
            errors = list(self.validator.iter_errors(inst))
            if len(errors) > 0:
                rejected_count += 1

        self.assertEqual(
            rejected_count, total_mutations,
            f"Fuzzing detected unhandled invalid cues: {total_mutations - rejected_count} passed unexpectedly"
        )


class TestDatasetEmpiricalOracles(unittest.TestCase):
    """Rigorous empirical oracle verification on topic_03_sceneflow_sync.json."""

    @classmethod
    def setUpClass(cls):
        with open(DATASET_PATH, "r", encoding="utf-8") as f:
            cls.dataset = json.load(f)
        cls.cues = cls.dataset.get("cues", [])
        cls.script_text = cls.dataset.get("scriptText", "")
        cls.metadata = cls.dataset.get("metadata", {})

    def test_cue_id_uniqueness_and_canonical_prefixes(self):
        """All cue IDs must be strictly unique and adhere to track prefix conventions."""
        ids = [c["id"] for c in self.cues]
        self.assertEqual(len(ids), len(set(ids)), f"Duplicate cue IDs found: {len(ids) - len(set(ids))}")
        self.assertEqual(len(ids), len(set(i.lower() for i in ids)), "Case-insensitive ID collision detected")

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
            cid = c["id"]
            ctype = c["type"]
            self.assertTrue(cid.startswith(prefixes[ctype]), f"Cue {cid} prefix mismatch for track {ctype}")
            self.assertEqual(cid, cid.strip(), f"Cue {cid} has trailing/leading whitespace")

    def test_zero_length_and_inverted_timestamps(self):
        """Every cue must satisfy strictly positive duration and monotonic timestamps."""
        for c in self.cues:
            cid = c["id"]
            start = c["startTime"]
            end = c["endTime"]
            self.assertGreaterEqual(start, 0.0, f"Negative startTime in cue {cid}: {start}")
            self.assertGreater(end, start, f"Inverted or zero-length cue {cid}: start={start}, end={end}")
            duration = end - start
            self.assertGreaterEqual(duration, 0.001, f"Micro-duration cue {cid} < 1ms: {duration}")
            if "duration" in c:
                self.assertAlmostEqual(c["duration"], duration, places=3, msg=f"Duration mismatch in {cid}")

    def test_runtime_boundaries(self):
        """All cues must fit within the master video runtime (565.10s + 0.05s tolerance)."""
        runtime_limit = 565.10 + 0.05
        for c in self.cues:
            self.assertLessEqual(c["endTime"], runtime_limit, f"Cue {c['id']} exceeds runtime: {c['endTime']}")

    def test_shot_track_continuity_and_no_gaps(self):
        """The 99 shots must form a continuous sequence with zero gaps and zero overlaps."""
        shots = [c for c in self.cues if c["type"] == "shot"]
        self.assertEqual(len(shots), 99, f"Expected 99 shots, found {len(shots)}")
        shots.sort(key=lambda x: x["startTime"])

        self.assertAlmostEqual(shots[0]["startTime"], 0.0, places=3)
        self.assertAlmostEqual(shots[-1]["endTime"], 565.10, delta=0.05)

        for i in range(len(shots) - 1):
            s1 = shots[i]
            s2 = shots[i + 1]
            diff = abs(s1["endTime"] - s2["startTime"])
            self.assertLessEqual(
                diff, 0.001,
                f"Discontinuity between shot {s1['id']} ({s1['endTime']}s) and {s2['id']} ({s2['startTime']}s): {diff}s"
            )

    def test_script_text_verbatim_slice_integrity(self):
        """Every cue slice must match scriptText byte-for-byte with zero offset deviations."""
        self.assertGreater(len(self.script_text), 0, "scriptText is empty")

        mismatches = []
        for c in self.cues:
            cid = c["id"]
            st = c.get("startIndex")
            et = c.get("endIndex")
            sel = c.get("selectedText")

            self.assertIsNotNone(st, f"Cue {cid} missing startIndex")
            self.assertIsNotNone(et, f"Cue {cid} missing endIndex")
            self.assertIsNotNone(sel, f"Cue {cid} missing selectedText")

            self.assertGreaterEqual(st, 0, f"Cue {cid} negative startIndex")
            self.assertLessEqual(et, len(self.script_text), f"Cue {cid} endIndex exceeds script length")
            self.assertLess(st, et, f"Cue {cid} startIndex >= endIndex")

            extracted = self.script_text[st:et]
            if extracted != sel:
                mismatches.append((cid, sel, extracted))

        self.assertEqual(len(mismatches), 0, f"Found {len(mismatches)} slice mismatches: {mismatches[:3]}")

    def test_monotonicity_per_track(self):
        """For all 8 tracks, cues must appear in non-decreasing order of startTime."""
        by_track = {t: [] for t in VALID_CUE_TYPES}
        for c in self.cues:
            by_track[c["type"]].append(c)

        for t, track_cues in by_track.items():
            for i in range(len(track_cues) - 1):
                c1 = track_cues[i]
                c2 = track_cues[i + 1]
                self.assertLessEqual(
                    c1["startTime"], c2["startTime"],
                    f"Out of order start times in track {t}: cue {c1['id']} ({c1['startTime']}s) > cue {c2['id']} ({c2['startTime']}s)"
                )

    def test_array_level_global_ordering(self):
        """Global cues array must be ordered chronologically by startTime."""
        for i in range(len(self.cues) - 1):
            c1 = self.cues[i]
            c2 = self.cues[i + 1]
            self.assertLessEqual(
                c1["startTime"], c2["startTime"] + 0.001,
                f"Global array inversion: cue {c1['id']} ({c1['startTime']}s) > cue {c2['id']} ({c2['startTime']}s)"
            )

    def test_exact_track_cardinalities(self):
        """Verify exact cue counts match the master specification."""
        self.assertEqual(len(self.cues), 1174)
        counts = {t: sum(1 for c in self.cues if c["type"] == t) for t in VALID_CUE_TYPES}
        self.assertEqual(counts["dialogue"], 481)
        self.assertEqual(counts["shot"], 99)
        self.assertEqual(counts["camera"], 99)
        self.assertEqual(counts["action"], 99)
        self.assertEqual(counts["audio"], 99)
        self.assertEqual(counts["vfx"], 99)
        self.assertEqual(counts["transition"], 99)
        self.assertEqual(counts["environment"], 99)

    def test_static_holds_and_dynamic_moves_breakdown(self):
        """Verify exactly 19 static holds and 80 dynamic moves are cataloged in camera metadata."""
        cam_cues = [c for c in self.cues if c["type"] == "camera"]
        self.assertEqual(len(cam_cues), 99)

        static_cues = [c for c in cam_cues if "Static Hold" in c["selectedText"] or c.get("metadata", {}).get("motion") == "static"]
        dynamic_cues = [c for c in cam_cues if c not in static_cues]

        self.assertEqual(len(static_cues), 19, f"Expected 19 static holds, found {len(static_cues)}")
        self.assertEqual(len(dynamic_cues), 80, f"Expected 80 dynamic moves, found {len(dynamic_cues)}")

    def test_act4_countdown_sequence_temporal_mapping(self):
        """Verify Act 4 countdown cues (5, 4, 3, 2, 1) map to shots LINE_25-A to LINE_26-C."""
        countdown_shots = ["LINE_25-A", "LINE_25-B", "LINE_26-A", "LINE_26-B", "LINE_26-C"]
        shot_cues = [c for c in self.cues if c["type"] == "shot" and c.get("metadata", {}).get("shotId") in countdown_shots]
        self.assertEqual(len(shot_cues), 5, f"Expected 5 countdown shot cues, got {len(shot_cues)}")

        # Verify time boundaries 324.20s - 360.83s range (approx 345s - 360s for countdown digits)
        first_shot = shot_cues[0]
        last_shot = shot_cues[-1]
        self.assertGreaterEqual(first_shot["startTime"], 340.0)
        self.assertLessEqual(last_shot["endTime"], 361.0)

        # Verify hard snap cuts on all countdown shots
        trans_cues = [
            c for c in self.cues
            if c["type"] == "transition" and any(sid in c.get("metadata", {}).get("shotId", "") for sid in countdown_shots)
        ]
        self.assertEqual(len(trans_cues), 5)
        for tc in trans_cues:
            self.assertIn("SNAP", tc["selectedText"])

    def test_html_embedded_dataset_parity(self):
        """Verify topic_03_sceneflow_sync.json is faithfully mirrored inside sceneflow_review_studio.html."""
        self.assertTrue(HTML_PATH.exists(), f"HTML missing: {HTML_PATH}")
        content = HTML_PATH.read_text(encoding="utf-8")
        marker = '<script type="application/json" id="embedded-sceneflow-data">'
        self.assertIn(marker, content)
        s_idx = content.find(marker) + len(marker)
        e_idx = content.find("</script>", s_idx)
        embedded_json = json.loads(content[s_idx:e_idx].strip())

        self.assertEqual(len(embedded_json["cues"]), len(self.cues))
        self.assertEqual(embedded_json["metadata"]["totalCues"], 1174)
        self.assertEqual(embedded_json["metadata"]["totalShots"], 99)
        self.assertEqual(embedded_json["metadata"]["totalDialoguePhrases"], 481)
        self.assertEqual(len(embedded_json["tracks"]), 8)


def run_adversarial_suite():
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    suite.addTests(loader.loadTestsFromTestCase(TestAdversarialSchemaFuzzing))
    suite.addTests(loader.loadTestsFromTestCase(TestDatasetEmpiricalOracles))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return result.wasSuccessful()


if __name__ == "__main__":
    import sys
    success = run_adversarial_suite()
    sys.exit(0 if success else 1)
