"""
Adversarial Stress Test Suite: Viral Shorts Deliverables Verification
Milestone 2 - Empirical Challenger Evaluation
Adheres strictly to ORIGINAL_REQUEST.md (§2026-09-30T12:37:46Z), PROJECT.md, and TEST_INFRA.md.

Empirical verification of:
1. C:\\Users\\Indresh HL\\Downloads\\TOPIC_03_VIRAL_SHORT_1_THE_5_SECOND_TEST.mp4
2. C:\\Users\\Indresh HL\\Downloads\\TOPIC_03_VIRAL_SHORT_2_THE_STRANGER_IN_YOUR_HEAD.mp4

Verification Dimensions:
- Physical Delivery & Container Faststart
- Codec, Profile, Pixel Format (yuv420p), and Streams
- Constant Frame Rate (CFR 30.0 fps) & Timestamp Jitter Analysis
- EBU R128 Loudness (-24 to -14 LUFS) & True Peak Headroom (<= 0 dBFS)
- Visual Frame Sampling: Ambient Blur Fill vs Black Letterbox Bars
- Subtitle Mobile-Safe Zone Compliance (400 < y < 1500, 80 < x < 1000)
- End-to-End Acceptance Gate Status
"""

import json
import os
import re
import struct
import subprocess
import sys
import unittest
from pathlib import Path
import numpy as np

try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DOWNLOADS_DIR = Path(r"C:\Users\Indresh HL\Downloads")

SHORT_1_PATH = DOWNLOADS_DIR / "TOPIC_03_VIRAL_SHORT_1_THE_5_SECOND_TEST.mp4"
SHORT_2_PATH = DOWNLOADS_DIR / "TOPIC_03_VIRAL_SHORT_2_THE_STRANGER_IN_YOUR_HEAD.mp4"
SHORT_1_ASS = PROJECT_ROOT / "production" / "topic_03" / "shorts" / "short_1_subtitles.ass"
SHORT_2_ASS = PROJECT_ROOT / "production" / "topic_03" / "shorts" / "short_2_subtitles.ass"


def parse_atoms(file_path: Path):
    atoms = []
    if not file_path.exists():
        return atoms
    file_size = file_path.stat().st_size
    with open(file_path, "rb") as f:
        while f.tell() < file_size:
            header = f.read(8)
            if len(header) < 8:
                break
            size, fourcc = struct.unpack(">I4s", header)
            atom_type = fourcc.decode("latin1", errors="replace")
            offset = f.tell() - 8
            atoms.append((atom_type, offset, size))
            if size == 1:
                ext_header = f.read(8)
                if len(ext_header) < 8:
                    break
                ext_size = struct.unpack(">Q", ext_header)[0]
                f.seek(offset + ext_size)
            elif size == 0:
                break
            else:
                f.seek(offset + size)
    return atoms


def get_ffprobe_data(file_path: Path):
    cmd = [
        "ffprobe", "-v", "quiet",
        "-print_format", "json",
        "-show_format",
        "-show_streams",
        str(file_path)
    ]
    res = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return json.loads(res.stdout)


class TestChallengerShortsAdversarial(unittest.TestCase):
    """Adversarial stress-testing suite for Viral Shorts deliverables."""

    def test_01_deliverable_files_exist_and_sized(self):
        """Verify both files exist in Downloads and strictly exceed 25.0 MB (26,214,400 bytes)."""
        for path, name in [(SHORT_1_PATH, "Short 1"), (SHORT_2_PATH, "Short 2")]:
            self.assertTrue(path.exists(), f"Deliverable missing: {path}")
            size = path.stat().st_size
            self.assertGreater(
                size, 26_214_400,
                f"{name} file size {size / (1024*1024):.2f} MB is below required 25.0 MB threshold"
            )

    def test_02_faststart_moov_atom_order(self):
        """Verify moov atom precedes mdat atom for faststart streaming compatibility."""
        for path, name in [(SHORT_1_PATH, "Short 1"), (SHORT_2_PATH, "Short 2")]:
            atoms = parse_atoms(path)
            atom_names = [a[0] for a in atoms]
            self.assertIn("moov", atom_names, f"{name} missing 'moov' atom")
            self.assertIn("mdat", atom_names, f"{name} missing 'mdat' atom")
            moov_idx = atom_names.index("moov")
            mdat_idx = atom_names.index("mdat")
            self.assertLess(
                moov_idx, mdat_idx,
                f"{name} failed faststart: 'mdat' (index {mdat_idx}) appears before 'moov' (index {moov_idx})"
            )

    def test_03_stream_codecs_and_pixel_format(self):
        """Verify 1080x1920 canvas, yuv420p, h264 High Profile, AAC stereo 48kHz, and NVENC encoder."""
        for path, name in [(SHORT_1_PATH, "Short 1"), (SHORT_2_PATH, "Short 2")]:
            probe = get_ffprobe_data(path)
            streams = probe.get("streams", [])
            v_stream = next((s for s in streams if s["codec_type"] == "video"), None)
            a_stream = next((s for s in streams if s["codec_type"] == "audio"), None)

            self.assertIsNotNone(v_stream, f"{name} missing video stream")
            self.assertIsNotNone(a_stream, f"{name} missing audio stream")

            # Video stream checks
            self.assertEqual(v_stream["codec_name"], "h264")
            self.assertEqual(v_stream["profile"].lower(), "high")
            self.assertEqual(v_stream["pix_fmt"], "yuv420p")
            self.assertEqual(v_stream["width"], 1080)
            self.assertEqual(v_stream["height"], 1920)

            # Check hardware encoder tag
            encoder_tag = v_stream.get("tags", {}).get("encoder", "")
            self.assertIn("h264_nvenc", encoder_tag.lower(), f"{name} not encoded with h264_nvenc: {encoder_tag}")

            # Audio stream checks
            self.assertEqual(a_stream["codec_name"], "aac")
            self.assertEqual(a_stream["channels"], 2)
            self.assertEqual(a_stream["sample_rate"], "48000")

    def test_04_duration_retention_boundaries(self):
        """Verify Short 1 duration in [48.0s, 55.0s] and Short 2 in [50.0s, 58.0s]."""
        p1 = get_ffprobe_data(SHORT_1_PATH)
        dur1 = float(p1["format"]["duration"])
        self.assertTrue(
            48.0 <= dur1 <= 55.0,
            f"Short 1 duration {dur1:.2f}s outside bounds [48.0, 55.0]"
        )

        p2 = get_ffprobe_data(SHORT_2_PATH)
        dur2 = float(p2["format"]["duration"])
        self.assertTrue(
            50.0 <= dur2 <= 58.0,
            f"Short 2 duration {dur2:.2f}s outside bounds [50.0, 58.0]"
        )

    def test_05_cfr_constancy_and_zero_timestamp_jitter(self):
        """Adversarially probe video packet timestamps to verify constant 30.0 fps and zero jitter."""
        for path, name in [(SHORT_1_PATH, "Short 1"), (SHORT_2_PATH, "Short 2")]:
            cmd = [
                "ffprobe", "-v", "error",
                "-select_streams", "v:0",
                "-show_entries", "packet=pts_time",
                "-of", "json",
                str(path)
            ]
            res = subprocess.run(cmd, capture_output=True, text=True, check=True)
            packets = json.loads(res.stdout).get("packets", [])
            pts = sorted([float(p["pts_time"]) for p in packets if "pts_time" in p])
            deltas = np.diff(pts)

            # Theoretical delta at 30 fps is 1/30 = 0.0333333...
            expected_delta = 1.0 / 30.0
            mean_delta = float(np.mean(deltas))
            std_delta = float(np.std(deltas))
            max_jitter = float(np.max(np.abs(deltas - expected_delta)))

            self.assertAlmostEqual(mean_delta, expected_delta, places=4, msg=f"{name} mean delta {mean_delta} != {expected_delta}")
            self.assertLess(std_delta, 1e-4, f"{name} high timestamp jitter std: {std_delta}s")
            self.assertLess(max_jitter, 1e-3, f"{name} maximum packet jitter {max_jitter}s exceeds 1ms tolerance")

    def test_06_audio_ebur128_loudness_and_true_peak(self):
        """Verify audio loudness satisfies broadcast standards with no true-peak clipping."""
        for path, name, exp_lufs_min, exp_lufs_max in [
            (SHORT_1_PATH, "Short 1", -24.0, -14.0),
            (SHORT_2_PATH, "Short 2", -24.0, -14.0)
        ]:
            cmd = [
                "ffmpeg", "-i", str(path),
                "-af", "ebur128=peak=true",
                "-f", "null", "-"
            ]
            res = subprocess.run(cmd, capture_output=True, text=True)
            stderr = res.stderr

            # Extract Integrated loudness
            i_match = re.search(r"Integrated loudness:\s+I:\s+([-\d\.]+)\s+LUFS", stderr)
            self.assertIsNotNone(i_match, f"Failed to extract Integrated loudness for {name}")
            int_lufs = float(i_match.group(1))

            # Extract True Peak
            tpk_match = re.search(r"True peak:\s+Peak:\s+([-\d\.]+)\s+dBFS", stderr)
            self.assertIsNotNone(tpk_match, f"Failed to extract True peak for {name}")
            true_peak = float(tpk_match.group(1))

            # Extract Loudness Range
            lra_match = re.search(r"Loudness range:\s+LRA:\s+([-\d\.]+)\s+LU", stderr)
            self.assertIsNotNone(lra_match, f"Failed to extract LRA for {name}")
            lra = float(lra_match.group(1))

            self.assertTrue(
                exp_lufs_min <= int_lufs <= exp_lufs_max,
                f"{name} Integrated loudness {int_lufs} LUFS out of range [{exp_lufs_min}, {exp_lufs_max}]"
            )
            self.assertLessEqual(
                true_peak, 0.0,
                f"{name} True peak {true_peak} dBFS exceeds 0.0 dBFS ceiling (clipping/distortion detected!)"
            )
            self.assertGreater(
                lra, 1.0,
                f"{name} LRA {lra} LU is suspiciously low (potential audio flattening)"
            )

    def test_07_short2_visual_frame_sampling_and_ambient_blur(self):
        """Stress-test Short 2 across timeline for black/frozen frames and verify ambient blur fill."""
        if not CV2_AVAILABLE:
            self.skipTest("OpenCV not available")

        cap = cv2.VideoCapture(str(SHORT_2_PATH))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.assertGreater(total_frames, 1500)

        # Sample 15 equidistant frames
        indices = np.linspace(15, total_frames - 15, 15, dtype=int)
        prev_frame = None

        for idx in indices:
            cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
            ret, frame = cap.read()
            self.assertTrue(ret, f"Failed to read frame {idx}")

            # 1. No completely black frames
            mean_lum = float(frame.mean())
            self.assertGreater(mean_lum, 15.0, f"Frame {idx} in Short 2 is excessively dark: mean={mean_lum}")

            # 2. No frozen frames
            if prev_frame is not None:
                diff = float(np.mean(np.abs(frame.astype(float) - prev_frame.astype(float))))
                self.assertGreater(diff, 5.0, f"Frame {idx} appears frozen compared to previous sample: diff={diff}")
            prev_frame = frame.copy()

            # 3. Ambient blur fill in top strip (y=50..150) and bottom strip (y=1770..1870)
            top_strip = frame[50:150, :]
            bot_strip = frame[1770:1870, :]
            top_mean, top_std = float(top_strip.mean()), float(top_strip.std())
            bot_mean, bot_std = float(bot_strip.mean()), float(bot_strip.std())

            # Verify neither strip is a flat unblurred black letterbox bar
            self.assertFalse(
                top_mean < 0.5 and top_std < 0.1,
                f"Short 2 frame {idx} has black letterbox bar at top: mean={top_mean}, std={top_std}"
            )
            self.assertFalse(
                bot_mean < 0.5 and bot_std < 0.1,
                f"Short 2 frame {idx} has black letterbox bar at bottom: mean={bot_mean}, std={bot_std}"
            )

        cap.release()

    def test_08_short1_ambient_blur_adversarial_vulnerability(self):
        """
        Adversarial test revealing the Short 1 ambient background crushing defect.
        Due to 'eq=brightness=-0.20' in render_short_1.py, frames in the obsidian void
        have their bottom ambient fill crushed to solid black (mean < 0.5, std < 0.1),
        triggering letterbox failure in verify_e2e_shorts.py.
        """
        if not CV2_AVAILABLE:
            self.skipTest("OpenCV not available")

        cap = cv2.VideoCapture(str(SHORT_1_PATH))
        # Frame 310 (t=10.33s), Frame 543 (t=18.1s), Frame 1474 (t=49.13s)
        crushed_frames = []
        for idx in [310, 543, 1474]:
            cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
            ret, frame = cap.read()
            if ret:
                bot_strip = frame[1770:1870, :]
                bot_mean = float(bot_strip.mean())
                bot_std = float(bot_strip.std())
                if bot_mean < 0.5 and bot_std < 0.1:
                    crushed_frames.append((idx, bot_mean, bot_std))
        cap.release()

        # Verify remediation: zero frames have crushed solid black bars
        self.assertEqual(
            len(crushed_frames), 0,
            f"Expected 0 crushed frames after remediation, found: {crushed_frames}"
        )

    def test_09_subtitle_safe_zone_geometry(self):
        """Verify subtitle positioning in ASS scripts and rendered deliverables."""
        # 1. Verify companion ASS script coordinates
        for ass_path, name in [(SHORT_1_ASS, "Short 1"), (SHORT_2_ASS, "Short 2")]:
            self.assertTrue(ass_path.exists(), f"ASS script missing: {ass_path}")
            text = ass_path.read_text(encoding="utf-8")
            positions = re.findall(r"\\pos\((\d+),(\d+)\)", text)
            self.assertGreater(len(positions), 0, f"{name} ASS script has no \\pos tags")
            for x_str, y_str in positions:
                x, y = int(x_str), int(y_str)
                self.assertTrue(
                    400 <= y <= 1500,
                    f"{name} subtitle y={y} outside mobile safe zone [400, 1500]"
                )
                self.assertTrue(
                    80 <= x <= 1000,
                    f"{name} subtitle x={x} outside horizontal margin bounds [80, 1000]"
                )

        # 2. Identify the ASS parsing index flaw in verify_e2e_shorts.py for Short 1
        text_s1 = SHORT_1_ASS.read_text(encoding="utf-8")
        for line in text_s1.splitlines():
            if line.startswith("Style: ShortsDefault"):
                parts = line.split(",")
                # parts[19] is MarginL (60), parts[21] is MarginV (570)
                margin_l = int(parts[19].strip())
                margin_v = int(parts[21].strip())
                self.assertEqual(margin_l, 60)
                self.assertEqual(margin_v, 570)
                # verify_e2e_shorts.py incorrectly used parts[19] leading to 1920 - 60 = 1860


if __name__ == "__main__":
    unittest.main()
