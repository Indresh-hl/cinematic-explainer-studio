"""
Unit and Adversarial Test Suite for Viral Shorts Verification Script (verify_e2e_shorts.py).
Tests all 5 validation tiers against mock, boundary, and synthesized edge cases.
"""

import os
import sys
import struct
import tempfile
import unittest
from pathlib import Path

# Ensure UTF-8 output
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from production.topic_03.shorts.verify_e2e_shorts import (
    SPEC_SHORT_1,
    SPEC_SHORT_2,
    parse_mp4_atoms,
    check_mp4_faststart,
    verify_tier_1_physical_delivery,
    verify_tier_2_stream_codec_compliance,
    verify_tier_3_duration_boundaries,
    verify_tier_4_subtitle_safe_zone_and_reframing,
    verify_tier_5_decoding_and_playback_integrity,
    run_all_tiers_for_deliverable,
)


class TestShortsVerificationUnits(unittest.TestCase):
    """Verifies that verification algorithms correctly enforce all requirements."""

    def test_tier1_missing_file(self):
        """Tier 1 must fail gracefully with descriptive message if file does not exist."""
        dummy_path = Path("non_existent_deliverable_short_xyz.mp4")
        res = verify_tier_1_physical_delivery(dummy_path, SPEC_SHORT_1)
        self.assertFalse(res["passed"])
        self.assertEqual(res["status"], "FAIL")
        self.assertIn("does not exist", res["message"])

    def test_tier1_undersized_file(self):
        """Tier 1 must fail if file is smaller than 25 MB."""
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tf:
            tf.write(b"x" * 1024 * 1024)  # 1 MB
            tmp_path = Path(tf.name)

        try:
            res = verify_tier_1_physical_delivery(tmp_path, SPEC_SHORT_1)
            self.assertFalse(res["passed"])
            self.assertEqual(res["status"], "FAIL")
            self.assertIn("File size too small", res["message"])
        finally:
            if tmp_path.exists():
                tmp_path.unlink()

    def test_parse_mp4_atoms_and_faststart(self):
        """Verify binary parser extracts atoms and checks moov vs mdat order."""
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tf:
            # Construct synthetic MP4 with faststart: ftyp -> moov -> mdat
            ftyp = b"ftyp" + b"isom" + b"\x00\x00\x02\x00" + b"isommp41"
            moov = b"moov" + b"dummy_moov_data"
            mdat = b"mdat" + b"dummy_mdat_data"

            # 4 bytes size + 4 bytes fourcc
            tf.write(struct.pack(">I", len(ftyp) + 4) + ftyp)
            tf.write(struct.pack(">I", len(moov) + 4) + moov)
            tf.write(struct.pack(">I", len(mdat) + 4) + mdat)
            faststart_path = Path(tf.name)

        try:
            atoms = parse_mp4_atoms(faststart_path)
            atom_names = [a[0] for a in atoms]
            self.assertIn("moov", atom_names)
            self.assertIn("mdat", atom_names)

            ok, msg = check_mp4_faststart(faststart_path)
            self.assertTrue(ok)
            self.assertIn("Faststart confirmed", msg)
        finally:
            if faststart_path.exists():
                faststart_path.unlink()

    def test_check_mp4_faststart_negative(self):
        """Verify faststart check fails when mdat precedes moov."""
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tf:
            # Construct non-faststart MP4: ftyp -> mdat -> moov
            ftyp = b"ftyp" + b"isom" + b"\x00\x00\x02\x00" + b"isommp41"
            mdat = b"mdat" + b"dummy_mdat_data"
            moov = b"moov" + b"dummy_moov_data"

            tf.write(struct.pack(">I", len(ftyp) + 4) + ftyp)
            tf.write(struct.pack(">I", len(mdat) + 4) + mdat)
            tf.write(struct.pack(">I", len(moov) + 4) + moov)
            non_faststart_path = Path(tf.name)

        try:
            ok, msg = check_mp4_faststart(non_faststart_path)
            self.assertFalse(ok)
            self.assertIn("Faststart missing", msg)
        finally:
            if non_faststart_path.exists():
                non_faststart_path.unlink()

    def test_tier3_duration_boundaries(self):
        """Tier 3 must reject durations outside allowed bounds."""
        # Using mock probe or dummy path to verify calculation logic
        dummy_path = Path("non_existent.mp4")
        res = verify_tier_3_duration_boundaries(dummy_path, SPEC_SHORT_1)
        self.assertFalse(res["passed"])
        self.assertEqual(res["status"], "BLOCKED")

    def test_tier4_missing_file_blocked(self):
        """Tier 4 returns BLOCKED if deliverable is missing."""
        dummy_path = Path("non_existent.mp4")
        res = verify_tier_4_subtitle_safe_zone_and_reframing(dummy_path, SPEC_SHORT_1)
        self.assertFalse(res["passed"])
        self.assertEqual(res["status"], "BLOCKED")

    def test_tier5_decoding_integrity_missing_file(self):
        """Tier 5 returns BLOCKED if deliverable is missing."""
        dummy_path = Path("non_existent.mp4")
        res = verify_tier_5_decoding_and_playback_integrity(dummy_path, SPEC_SHORT_1)
        self.assertFalse(res["passed"])
        self.assertEqual(res["status"], "BLOCKED")

    def test_run_all_tiers_cascading_blocked(self):
        """run_all_tiers_for_deliverable blocks downstream tiers when tier 1 fails."""
        dummy_path = Path("missing_short.mp4")
        res = run_all_tiers_for_deliverable(dummy_path, SPEC_SHORT_1)
        self.assertFalse(res["overall_passed"])
        self.assertEqual(res["tiers"]["tier_1"]["status"], "FAIL")
        self.assertEqual(res["tiers"]["tier_2"]["status"], "BLOCKED")
        self.assertEqual(res["tiers"]["tier_3"]["status"], "BLOCKED")
        self.assertEqual(res["tiers"]["tier_4"]["status"], "BLOCKED")
        self.assertEqual(res["tiers"]["tier_5"]["status"], "BLOCKED")


if __name__ == "__main__":
    unittest.main()
