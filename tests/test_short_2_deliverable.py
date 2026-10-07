"""
Test Suite: Deliverable Verification for Short 2 ("The Stranger in Your Head")
Verifies all 5 tiers of compliance for TOPIC_03_VIRAL_SHORT_2_THE_STRANGER_IN_YOUR_HEAD.mp4:
- Tier 1: Existence & Physical Delivery (> 25MB)
- Tier 2: Stream & Codec Compliance (1080x1920, h264 High yuv420p 30fps, aac stereo 48kHz, faststart)
- Tier 3: Narrative & Duration Boundaries (50.0s <= duration <= 58.0s)
- Tier 4: Subtitle Mobile-Safe Zone (400 < y < 1500) & Dual-Layer Ambient Reframing
- Tier 5: Decoding & Playback Integrity (zero decode errors)
"""

import os
import sys
import unittest
from pathlib import Path
import subprocess

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Ensure subprocess calls within verify_e2e_shorts do not fail on Windows pytest stdin capture
import production.topic_03.shorts.verify_e2e_shorts as verify_module

_orig_run = verify_module.subprocess.run

def _safe_run(*args, **kwargs):
    if "stdin" not in kwargs:
        kwargs["stdin"] = subprocess.DEVNULL
    return _orig_run(*args, **kwargs)

verify_module.subprocess.run = _safe_run

from production.topic_03.shorts.verify_e2e_shorts import (
    SPEC_SHORT_2,
    verify_tier_1_physical_delivery,
    verify_tier_2_stream_codec_compliance,
    verify_tier_3_duration_boundaries,
    verify_tier_4_subtitle_safe_zone_and_reframing,
    verify_tier_5_decoding_and_playback_integrity,
    run_all_tiers_for_deliverable,
    check_mp4_faststart,
    run_ffprobe,
)


class TestShort2Deliverable(unittest.TestCase):
    """E2E Verification for Short 2 Deliverable."""

    @classmethod
    def setUpClass(cls):
        cls.target_path = Path(r"C:\Users\Indresh HL\Downloads\TOPIC_03_VIRAL_SHORT_2_THE_STRANGER_IN_YOUR_HEAD.mp4")
        cls.ass_path = PROJECT_ROOT / "production" / "topic_03" / "shorts" / "short_2_subtitles.ass"

    def test_short2_physical_delivery(self):
        """Tier 1: Short 2 deliverable must exist in Downloads and exceed 25.0 MB."""
        self.assertTrue(self.target_path.exists(), f"Deliverable missing at: {self.target_path}")
        res = verify_tier_1_physical_delivery(self.target_path, SPEC_SHORT_2)
        self.assertTrue(res["passed"], f"Tier 1 Failed: {res['message']}")
        self.assertGreater(res["details"]["actual_bytes"], 25 * 1024 * 1024)

    def test_short2_stream_codec_compliance(self):
        """Tier 2: Codec & stream compliance (1080x1920, h264 High, yuv420p, aac stereo 48k, faststart)."""
        res = verify_tier_2_stream_codec_compliance(self.target_path, SPEC_SHORT_2)
        self.assertTrue(res["passed"], f"Tier 2 Failed: {res['message']}")
        v_details = res["details"]["video"]
        self.assertEqual(v_details["width"], 1080)
        self.assertEqual(v_details["height"], 1920)
        self.assertEqual(v_details["codec"], "h264")
        self.assertEqual(v_details["profile"].lower(), "high")
        self.assertEqual(v_details["pix_fmt"], "yuv420p")
        self.assertAlmostEqual(v_details["fps"], 30.0, delta=0.1)

        a_details = res["details"]["audio"]
        self.assertEqual(a_details["codec"], "aac")
        self.assertEqual(a_details["channels"], 2)
        self.assertEqual(a_details["sample_rate"], 48000)

        # Faststart verification
        faststart_ok, msg = check_mp4_faststart(self.target_path)
        self.assertTrue(faststart_ok, f"Faststart not enabled: {msg}")

    def test_short2_duration_boundaries(self):
        """Tier 3: Duration strictly between 50.0s and 58.0s (Target: ~54.40s)."""
        res = verify_tier_3_duration_boundaries(self.target_path, SPEC_SHORT_2)
        self.assertTrue(res["passed"], f"Tier 3 Failed: {res['message']}")
        dur = res["details"]["actual_duration_seconds"]
        self.assertTrue(50.0 <= dur <= 58.0, f"Duration {dur}s out of range [50.0, 58.0]")
        self.assertAlmostEqual(dur, 54.40, delta=0.5)

    def test_short2_subtitle_safe_zone_and_reframing(self):
        """Tier 4: Subtitles in safe zone (400 < y < 1500) and zero letterbox bars."""
        # 1. ASS companion file check
        self.assertTrue(self.ass_path.exists(), f"ASS subtitle script missing at: {self.ass_path}")

        # 2. Frame-level reframing & subtitle verification
        res = verify_tier_4_subtitle_safe_zone_and_reframing(self.target_path, SPEC_SHORT_2)
        self.assertTrue(res["passed"], f"Tier 4 Failed: {res['message']}")
        self.assertGreater(res["details"]["detected_subtitle_frames"], 0, "No subtitle frames detected")

    def test_short2_decoding_integrity(self):
        """Tier 5: Full ffmpeg null decode pass with 0 errors."""
        res = verify_tier_5_decoding_and_playback_integrity(self.target_path, SPEC_SHORT_2)
        self.assertTrue(res["passed"], f"Tier 5 Failed: {res['message']}")

    def test_short2_all_tiers_comprehensive(self):
        """Combined full 5-tier evaluation."""
        eval_res = run_all_tiers_for_deliverable(self.target_path, SPEC_SHORT_2, skip_tier5=False)
        self.assertTrue(eval_res["overall_passed"], f"Combined verification failed: {eval_res}")


if __name__ == "__main__":
    unittest.main()
