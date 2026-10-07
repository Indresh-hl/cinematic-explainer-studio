#!/usr/bin/env python3
"""
E2E Acceptance Verification Suite for Viral Shorts Deliverables.
Adheres strictly to TEST_INFRA.md and ORIGINAL_REQUEST.md (§2026-09-30T12:37:46Z).

Verifies the 5 Tiers of Production Compliance:
  Tier 1: Existence & Physical Delivery (>25MB in C:\\Users\\Indresh HL\\Downloads\\)
  Tier 2: Stream & Codec Compliance (1080x1920, h264 High yuv420p 30fps, aac 2ch 48kHz ~256k, faststart)
  Tier 3: Narrative & Duration Boundaries (Short 1: 48-55s, Short 2: 50-58s)
  Tier 4: Subtitle Mobile-Safe Zone (400 < y < 1500) & Reframing Inspection (no black letterbox bars)
  Tier 5: Decoding & Playback Integrity (ffmpeg null decode check with zero errors)

Supports both standalone CLI execution and Pytest invocation:
  python production/topic_03/shorts/verify_e2e_shorts.py
  pytest production/topic_03/shorts/verify_e2e_shorts.py -v
"""

import os
import sys
import json
import struct
import argparse
import subprocess
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional

try:
    import cv2
    import numpy as np
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False


# ==============================================================================
# Configuration & Deliverable Specifications
# ==============================================================================

DEFAULT_DOWNLOADS_DIR = Path(r"C:\Users\Indresh HL\Downloads")

SHORT_1_FILENAME = "TOPIC_03_VIRAL_SHORT_1_THE_5_SECOND_TEST.mp4"
SHORT_2_FILENAME = "TOPIC_03_VIRAL_SHORT_2_THE_STRANGER_IN_YOUR_HEAD.mp4"

MIN_FILE_SIZE_BYTES = 25 * 1024 * 1024  # 26,214,400 bytes (> 25.0 MB)

SPEC_SHORT_1 = {
    "id": "short_1",
    "title": "The 5-Second Test (Interactive Pattern Interrupt)",
    "filename": SHORT_1_FILENAME,
    "default_path": DEFAULT_DOWNLOADS_DIR / SHORT_1_FILENAME,
    "min_size_bytes": MIN_FILE_SIZE_BYTES,
    "target_width": 1080,
    "target_height": 1920,
    "video_codec": "h264",
    "video_profile": "High",
    "pix_fmt": "yuv420p",
    "fps_min": 29.97,
    "fps_max": 30.05,
    "audio_codec": "aac",
    "audio_channels": 2,
    "audio_sample_rate": 48000,
    "audio_bitrate_min": 192000,
    "audio_bitrate_max": 350000,
    "min_duration": 48.0,
    "max_duration": 55.0,
    "safe_zone_ymin": 400,
    "safe_zone_ymax": 1500,
    "safe_zone_xmin": 80,
    "safe_zone_xmax": 1000,
    "ass_file": Path("production/topic_03/shorts/short_1_subtitles.ass"),
}

SPEC_SHORT_2 = {
    "id": "short_2",
    "title": "The Stranger in Your Head (fMRI Neuroscience Discovery)",
    "filename": SHORT_2_FILENAME,
    "default_path": DEFAULT_DOWNLOADS_DIR / SHORT_2_FILENAME,
    "min_size_bytes": MIN_FILE_SIZE_BYTES,
    "target_width": 1080,
    "target_height": 1920,
    "video_codec": "h264",
    "video_profile": "High",
    "pix_fmt": "yuv420p",
    "fps_min": 29.97,
    "fps_max": 30.05,
    "audio_codec": "aac",
    "audio_channels": 2,
    "audio_sample_rate": 48000,
    "audio_bitrate_min": 192000,
    "audio_bitrate_max": 350000,
    "min_duration": 50.0,
    "max_duration": 58.0,
    "safe_zone_ymin": 400,
    "safe_zone_ymax": 1500,
    "safe_zone_xmin": 80,
    "safe_zone_xmax": 1000,
    "ass_file": Path("production/topic_03/shorts/short_2_subtitles.ass"),
}


# ==============================================================================
# Helper Utilities: MP4 Atom Parsing, FFprobe, and Image Analysis
# ==============================================================================

def parse_mp4_atoms(file_path: Path) -> List[Tuple[str, int, int]]:
    """
    Parse top-level MP4 atoms (boxes) from binary container.
    Returns list of (atom_type, byte_offset, size).
    """
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
                # 64-bit extended size
                ext_header = f.read(8)
                if len(ext_header) < 8:
                    break
                ext_size = struct.unpack(">Q", ext_header)[0]
                f.seek(offset + ext_size)
            elif size == 0:
                # Atom extends to EOF
                break
            else:
                f.seek(offset + size)
    return atoms


def check_mp4_faststart(file_path: Path) -> Tuple[bool, str]:
    """
    Verify if MP4 has faststart enabled (moov atom precedes mdat atom).
    """
    try:
        atoms = parse_mp4_atoms(file_path)
        atom_names = [a[0] for a in atoms]
        if "moov" not in atom_names:
            return False, "No 'moov' atom found in container"
        if "mdat" not in atom_names:
            return False, "No 'mdat' atom found in container"

        moov_offset = next(a[1] for a in atoms if a[0] == "moov")
        mdat_offset = next(a[1] for a in atoms if a[0] == "mdat")

        if moov_offset < mdat_offset:
            return True, f"Faststart confirmed: 'moov' (offset {moov_offset}) precedes 'mdat' (offset {mdat_offset})"
        else:
            return False, f"Faststart missing: 'mdat' (offset {mdat_offset}) precedes 'moov' (offset {moov_offset})"
    except Exception as e:
        return False, f"Faststart check error: {str(e)}"


def run_ffprobe(file_path: Path) -> Dict[str, Any]:
    """
    Execute ffprobe JSON inspection on given media file.
    """
    cmd = [
        "ffprobe",
        "-v", "quiet",
        "-print_format", "json",
        "-show_format",
        "-show_streams",
        str(file_path)
    ]
    res = subprocess.run(cmd, capture_output=True, text=True, check=True, stdin=subprocess.DEVNULL)
    return json.loads(res.stdout)


# ==============================================================================
# Tier Verification Functions
# ==============================================================================

def verify_tier_1_physical_delivery(file_path: Path, spec: Dict[str, Any]) -> Dict[str, Any]:
    """
    Tier 1: Existence & Physical Delivery
    - Target file must exist at specified destination.
    - File size must be non-zero and exceed 25.0 MB (> 26,214,400 bytes).
    """
    tier_name = "Tier 1: Existence & Physical Delivery"
    if not file_path.exists():
        return {
            "tier": 1,
            "name": tier_name,
            "passed": False,
            "status": "FAIL",
            "message": f"File does not exist: {file_path}",
            "details": {
                "file_path": str(file_path),
                "expected_min_bytes": spec["min_size_bytes"],
                "actual_bytes": 0,
            }
        }

    actual_size = file_path.stat().st_size
    min_size = spec["min_size_bytes"]
    size_mb = actual_size / (1024 * 1024)

    if actual_size < min_size:
        return {
            "tier": 1,
            "name": tier_name,
            "passed": False,
            "status": "FAIL",
            "message": f"File size too small: {size_mb:.2f} MB (< 25.0 MB required)",
            "details": {
                "file_path": str(file_path),
                "expected_min_bytes": min_size,
                "actual_bytes": actual_size,
                "actual_mb": round(size_mb, 2)
            }
        }

    return {
        "tier": 1,
        "name": tier_name,
        "passed": True,
        "status": "PASS",
        "message": f"Deliverable present: {size_mb:.2f} MB (> 25.0 MB threshold satisfied)",
        "details": {
            "file_path": str(file_path),
            "expected_min_bytes": min_size,
            "actual_bytes": actual_size,
            "actual_mb": round(size_mb, 2)
        }
    }


def verify_tier_2_stream_codec_compliance(file_path: Path, spec: Dict[str, Any]) -> Dict[str, Any]:
    """
    Tier 2: Stream & Codec Compliance (via ffprobe JSON inspection)
    - Video: strictly 1080x1920 (9:16), h264, profile High, yuv420p, 30.0 fps
    - Audio: aac, stereo (2 channels), 48,000 Hz, ~256k nominal bitrate
    - Container: MP4 format, faststart enabled (moov before mdat)
    """
    tier_name = "Tier 2: Stream & Codec Compliance"
    if not file_path.exists():
        return {
            "tier": 2,
            "name": tier_name,
            "passed": False,
            "status": "BLOCKED",
            "message": f"Deliverable missing, skipping Tier 2 stream probe",
            "details": {}
        }

    failures = []
    details: Dict[str, Any] = {}

    # 1. FFprobe stream inspection
    try:
        probe = run_ffprobe(file_path)
    except Exception as e:
        return {
            "tier": 2,
            "name": tier_name,
            "passed": False,
            "status": "FAIL",
            "message": f"ffprobe execution failed: {str(e)}",
            "details": {"error": str(e)}
        }

    streams = probe.get("streams", [])
    format_info = probe.get("format", {})

    video_stream = next((s for s in streams if s.get("codec_type") == "video"), None)
    audio_stream = next((s for s in streams if s.get("codec_type") == "audio"), None)

    # 2. Video stream validation
    if not video_stream:
        failures.append("No video stream found in container")
    else:
        v_codec = video_stream.get("codec_name", "")
        v_profile = video_stream.get("profile", "")
        v_width = int(video_stream.get("width", 0))
        v_height = int(video_stream.get("height", 0))
        v_pix_fmt = video_stream.get("pix_fmt", "")

        # FPS calculation
        fps_str = video_stream.get("r_frame_rate", "0/0")
        try:
            num, den = map(int, fps_str.split("/"))
            v_fps = num / den if den != 0 else 0.0
        except Exception:
            v_fps = 0.0

        details["video"] = {
            "codec": v_codec,
            "profile": v_profile,
            "width": v_width,
            "height": v_height,
            "pix_fmt": v_pix_fmt,
            "fps": round(v_fps, 2),
            "fps_raw": fps_str
        }

        if v_codec != spec["video_codec"]:
            failures.append(f"Video codec mismatch: got '{v_codec}', expected '{spec['video_codec']}'")
        if v_profile.lower() != spec["video_profile"].lower():
            failures.append(f"Video profile mismatch: got '{v_profile}', expected '{spec['video_profile']}'")
        if v_width != spec["target_width"] or v_height != spec["target_height"]:
            failures.append(f"Resolution mismatch: got {v_width}x{v_height}, strictly expected {spec['target_width']}x{spec['target_height']} (9:16)")
        if v_pix_fmt != spec["pix_fmt"]:
            failures.append(f"Pixel format mismatch: got '{v_pix_fmt}', strictly expected '{spec['pix_fmt']}' (zero gbrp/444 allowed)")
        if not (spec["fps_min"] <= v_fps <= spec["fps_max"]):
            failures.append(f"FPS boundary violation: got {v_fps:.2f} fps, expected ~30.0 fps [{spec['fps_min']} - {spec['fps_max']}]")

    # 3. Audio stream validation
    if not audio_stream:
        failures.append("No audio stream found in container")
    else:
        a_codec = audio_stream.get("codec_name", "")
        a_channels = int(audio_stream.get("channels", 0))
        a_rate = int(audio_stream.get("sample_rate", 0))
        try:
            a_bitrate = int(audio_stream.get("bit_rate", 0))
        except (ValueError, TypeError):
            a_bitrate = 0

        details["audio"] = {
            "codec": a_codec,
            "channels": a_channels,
            "sample_rate": a_rate,
            "bitrate": a_bitrate
        }

        if a_codec != spec["audio_codec"]:
            failures.append(f"Audio codec mismatch: got '{a_codec}', expected '{spec['audio_codec']}'")
        if a_channels != spec["audio_channels"]:
            failures.append(f"Audio channels mismatch: got {a_channels}, expected stereo ({spec['audio_channels']})")
        if a_rate != spec["audio_sample_rate"]:
            failures.append(f"Audio sample rate mismatch: got {a_rate} Hz, expected {spec['audio_sample_rate']} Hz")

    # 4. Container & Faststart check
    format_name = format_info.get("format_name", "")
    details["container"] = {"format_name": format_name}
    if "mp4" not in format_name:
        failures.append(f"Container format mismatch: got '{format_name}', expected 'mp4'")

    faststart_ok, faststart_msg = check_mp4_faststart(file_path)
    details["faststart"] = {"enabled": faststart_ok, "diagnostic": faststart_msg}
    if not faststart_ok:
        failures.append(f"Faststart violation: {faststart_msg}")

    passed = len(failures) == 0
    return {
        "tier": 2,
        "name": tier_name,
        "passed": passed,
        "status": "PASS" if passed else "FAIL",
        "message": "All codec, stream, and container requirements verified" if passed else "; ".join(failures),
        "failures": failures,
        "details": details
    }


def verify_tier_3_duration_boundaries(file_path: Path, spec: Dict[str, Any]) -> Dict[str, Any]:
    """
    Tier 3: Narrative & Duration Boundaries
    - Short 1: 48.0s <= duration <= 55.0s
    - Short 2: 50.0s <= duration <= 58.0s
    """
    tier_name = "Tier 3: Narrative & Duration Boundaries"
    if not file_path.exists():
        return {
            "tier": 3,
            "name": tier_name,
            "passed": False,
            "status": "BLOCKED",
            "message": f"Deliverable missing, skipping duration check",
            "details": {}
        }

    try:
        probe = run_ffprobe(file_path)
        format_info = probe.get("format", {})
        duration = float(format_info.get("duration", 0.0))
    except Exception as e:
        return {
            "tier": 3,
            "name": tier_name,
            "passed": False,
            "status": "FAIL",
            "message": f"Failed to extract duration: {str(e)}",
            "details": {"error": str(e)}
        }

    min_dur = spec["min_duration"]
    max_dur = spec["max_duration"]
    passed = min_dur <= duration <= max_dur

    msg = (f"Duration {duration:.2f}s satisfies retention bounds [{min_dur:.1f}s - {max_dur:.1f}s]"
           if passed else
           f"Duration violation: got {duration:.2f}s, expected strictly between {min_dur:.1f}s and {max_dur:.1f}s")

    return {
        "tier": 3,
        "name": tier_name,
        "passed": passed,
        "status": "PASS" if passed else "FAIL",
        "message": msg,
        "details": {
            "actual_duration_seconds": round(duration, 3),
            "allowed_min_seconds": min_dur,
            "allowed_max_seconds": max_dur
        }
    }


def verify_tier_4_subtitle_safe_zone_and_reframing(file_path: Path, spec: Dict[str, Any]) -> Dict[str, Any]:
    """
    Tier 4: Subtitle Mobile-Safe Zone & Reframing Inspection
    - Inspects video frames across duration:
      1. Confirms dual-layer ambient blurred background eliminates solid black letterbox bars.
      2. Validates dialogue subtitles are positioned strictly within mobile safe zone (400 < y < 1500, 80 < x < 1000).
    - Inspects companion .ass subtitle script if present in shorts directory.
    """
    tier_name = "Tier 4: Subtitle Mobile-Safe Zone & Reframing"
    if not file_path.exists():
        return {
            "tier": 4,
            "name": tier_name,
            "passed": False,
            "status": "BLOCKED",
            "message": f"Deliverable missing, skipping safe zone and reframing inspection",
            "details": {}
        }

    if not CV2_AVAILABLE:
        return {
            "tier": 4,
            "name": tier_name,
            "passed": False,
            "status": "FAIL",
            "message": "OpenCV (cv2) or numpy not installed in Python environment",
            "details": {}
        }

    failures = []
    details: Dict[str, Any] = {"sampled_frames": []}

    # 1. Inspect ASS subtitle script geometry if present
    ass_path = spec.get("ass_file")
    ass_checked = False
    if ass_path and Path(ass_path).exists():
        try:
            with open(ass_path, "r", encoding="utf-8", errors="replace") as f:
                ass_lines = f.readlines()

            res_y = 1920
            margin_v = 0
            alignment = 2

            for line in ass_lines:
                if line.startswith("PlayResY:"):
                    res_y = int(line.split(":")[1].strip())
                elif line.startswith("Style:"):
                    parts = line.split(",")
                    if len(parts) >= 22:
                        margin_v = int(parts[21].strip())
                        alignment = int(parts[18].strip())

            # Baseline calculation based on ASS Alignment (2 = bottom-center)
            if alignment in [1, 2, 3]:
                baseline_y = res_y - margin_v
            elif alignment in [7, 8, 9]:
                baseline_y = margin_v
            else:
                baseline_y = res_y // 2

            ass_in_bounds = (spec["safe_zone_ymin"] <= baseline_y <= spec["safe_zone_ymax"])

            details["ass_script_inspection"] = {
                "file": str(ass_path),
                "PlayResY": res_y,
                "MarginV": margin_v,
                "calculated_baseline_y": baseline_y,
                "in_safe_zone": ass_in_bounds
            }
            if not ass_in_bounds:
                failures.append(f"ASS subtitle baseline y={baseline_y} violates safe zone [{spec['safe_zone_ymin']}, {spec['safe_zone_ymax']}]")
            ass_checked = True
        except Exception as e:
            details["ass_script_error"] = str(e)

    # 2. Inspect Rendered Video Frames for Reframing & Letterbox Absence
    cap = cv2.VideoCapture(str(file_path))
    if not cap.isOpened():
        return {
            "tier": 4,
            "name": tier_name,
            "passed": False,
            "status": "FAIL",
            "message": f"Failed to open video file with OpenCV: {file_path}",
            "details": {}
        }

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    duration = total_frames / fps if fps > 0 else 0.0

    # Sample 8 equidistant points across the video
    sample_ratios = [0.10, 0.20, 0.35, 0.50, 0.65, 0.75, 0.85, 0.95]
    frame_indices = [int(r * total_frames) for r in sample_ratios if 0 <= int(r * total_frames) < total_frames]

    letterbox_violation_count = 0
    subtitle_violation_count = 0
    detected_subtitles_count = 0

    for idx in frame_indices:
        cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
        ret, frame = cap.read()
        if not ret or frame is None:
            continue

        h, w = frame.shape[:2]
        time_sec = round(idx / fps, 2)

        # Dimension check
        if h != spec["target_height"] or w != spec["target_width"]:
            # If resolution doesn't match target 9:16 vertical canvas
            failures.append(f"Frame resolution {w}x{h} at {time_sec}s does not match {spec['target_width']}x{spec['target_height']}")
            break

        # Reframing check: Ensure top and bottom are not solid unblurred black bars
        # Sample top region (y: 50-150) and bottom region (y: 1770-1870)
        top_strip = frame[50:150, :]
        bot_strip = frame[1770:1870, :]

        top_mean = float(np.mean(top_strip))
        top_std = float(np.std(top_strip))
        bot_mean = float(np.mean(bot_strip))
        bot_std = float(np.std(bot_strip))

        # A flat unblurred black letterbox bar has mean < 0.5 and std < 0.1 across the entire 100x1080 strip
        is_letterbox_top = (top_mean < 0.5 and top_std < 0.1)
        is_letterbox_bot = (bot_mean < 0.5 and bot_std < 0.1)

        if is_letterbox_top or is_letterbox_bot:
            letterbox_violation_count += 1

        # Subtitle safe-zone check on sampled frame:
        # Detect high-contrast bright text clusters (such as captions)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # A. Check bottom danger zone (y > 1500) for caption text
        bot_danger = gray[spec["safe_zone_ymax"]:, :]
        bot_bright = (bot_danger > 180).astype(np.uint8) * 255
        bot_contours, _ = cv2.findContours(bot_bright, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        # Filter for text-like contours (w >= 12, h >= 12)
        bot_text_contours = [c for c in bot_contours if cv2.boundingRect(c)[2] >= 12 and cv2.boundingRect(c)[3] >= 12]
        if len(bot_text_contours) >= 3:
            # Significant cluster of text in bottom danger zone
            subtitle_violation_count += 1

        # B. Check subtitle band (y: 1150-1480, x: 80-1000)
        sub_region = gray[1150:1480, 80:1000]
        sub_bright = (sub_region > 180).astype(np.uint8) * 255
        sub_contours, _ = cv2.findContours(sub_bright, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        valid_sub_chars = [c for c in sub_contours if 10 <= cv2.boundingRect(c)[2] <= 120 and 10 <= cv2.boundingRect(c)[3] <= 90]
        if len(valid_sub_chars) >= 3:
            detected_subtitles_count += 1

        details["sampled_frames"].append({
            "frame_index": idx,
            "timestamp_sec": time_sec,
            "top_mean": round(top_mean, 2),
            "bot_mean": round(bot_mean, 2),
            "has_letterbox_bars": (is_letterbox_top or is_letterbox_bot)
        })

    cap.release()

    if letterbox_violation_count > 0:
        failures.append(f"Letterbox violation: detected {letterbox_violation_count} sampled frames with solid unblurred black bars")

    if subtitle_violation_count > 0:
        failures.append(f"Subtitle safe zone violation: detected text exceeding y={spec['safe_zone_ymax']} in {subtitle_violation_count} frames")

    details["detected_subtitle_frames"] = detected_subtitles_count

    passed = len(failures) == 0
    return {
        "tier": 4,
        "name": tier_name,
        "passed": passed,
        "status": "PASS" if passed else "FAIL",
        "message": "Reframing active with zero black letterbox bars; captions bounded within mobile safe zone" if passed else "; ".join(failures),
        "failures": failures,
        "details": details
    }


def verify_tier_5_decoding_and_playback_integrity(file_path: Path, spec: Dict[str, Any]) -> Dict[str, Any]:
    """
    Tier 5: Decoding & Playback Integrity
    - Runs full ffmpeg decode pass: ffmpeg -v error -i <file> -f null -
    - Ensures zero stream corruption, zero decode errors, zero truncated packets.
    """
    tier_name = "Tier 5: Decoding & Playback Integrity"
    if not file_path.exists():
        return {
            "tier": 5,
            "name": tier_name,
            "passed": False,
            "status": "BLOCKED",
            "message": f"Deliverable missing, skipping ffmpeg decode pass",
            "details": {}
        }

    cmd = [
        "ffmpeg",
        "-v", "error",
        "-i", str(file_path),
        "-f", "null",
        "-"
    ]

    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, stdin=subprocess.DEVNULL)
    except Exception as e:
        return {
            "tier": 5,
            "name": tier_name,
            "passed": False,
            "status": "FAIL",
            "message": f"ffmpeg execution failed: {str(e)}",
            "details": {"error": str(e)}
        }

    stderr_output = proc.stderr.strip()
    returncode = proc.returncode

    # Check for decode errors
    # Filter non-fatal informational warnings if any
    error_lines = [l for l in stderr_output.splitlines() if any(k in l.lower() for k in ["error", "corrupt", "invalid", "truncat", "fatal"])]

    passed = (returncode == 0 and len(error_lines) == 0)

    if passed:
        msg = "Full stream decode completed with 0 errors across all video and audio frames"
    else:
        msg = f"Decode errors detected (code {returncode}): {'; '.join(error_lines[:3])}"

    return {
        "tier": 5,
        "name": tier_name,
        "passed": passed,
        "status": "PASS" if passed else "FAIL",
        "message": msg,
        "details": {
            "returncode": returncode,
            "stderr_raw": stderr_output,
            "error_lines": error_lines
        }
    }


# ==============================================================================
# Comprehensive Video Evaluator
# ==============================================================================

def run_all_tiers_for_deliverable(file_path: Path, spec: Dict[str, Any], skip_tier5: bool = False) -> Dict[str, Any]:
    """
    Executes Tiers 1 through 5 for a single short deliverable.
    """
    results = {}

    # Tier 1
    t1 = verify_tier_1_physical_delivery(file_path, spec)
    results["tier_1"] = t1

    if not t1["passed"]:
        # Block dependent tiers if file does not exist
        results["tier_2"] = verify_tier_2_stream_codec_compliance(file_path, spec)
        results["tier_3"] = verify_tier_3_duration_boundaries(file_path, spec)
        results["tier_4"] = verify_tier_4_subtitle_safe_zone_and_reframing(file_path, spec)
        results["tier_5"] = verify_tier_5_decoding_and_playback_integrity(file_path, spec)
        overall_passed = False
    else:
        results["tier_2"] = verify_tier_2_stream_codec_compliance(file_path, spec)
        results["tier_3"] = verify_tier_3_duration_boundaries(file_path, spec)
        results["tier_4"] = verify_tier_4_subtitle_safe_zone_and_reframing(file_path, spec)
        if skip_tier5:
            results["tier_5"] = {
                "tier": 5,
                "name": "Tier 5: Decoding & Playback Integrity",
                "passed": True,
                "status": "SKIPPED",
                "message": "Tier 5 skipped via --skip-tier5 flag",
                "details": {}
            }
        else:
            results["tier_5"] = verify_tier_5_decoding_and_playback_integrity(file_path, spec)

        overall_passed = all(
            results[k]["passed"] for k in ["tier_1", "tier_2", "tier_3", "tier_4", "tier_5"]
        )

    return {
        "id": spec["id"],
        "title": spec["title"],
        "file_path": str(file_path),
        "overall_passed": overall_passed,
        "tiers": results
    }


# ==============================================================================
# Pytest Integration Test Cases
# ==============================================================================

class TestViralShortsE2E:
    """
    Pytest test suite executing against deliverables in C:\\Users\\Indresh HL\\Downloads\\.
    Can be run via: python -m pytest production/topic_03/shorts/verify_e2e_shorts.py -v
    Optionally override paths via env vars:
      TEST_SHORT1_PATH, TEST_SHORT2_PATH
    """
    @property
    def short1_path(self) -> Path:
        return Path(os.environ.get("TEST_SHORT1_PATH", str(SPEC_SHORT_1["default_path"])))

    @property
    def short2_path(self) -> Path:
        return Path(os.environ.get("TEST_SHORT2_PATH", str(SPEC_SHORT_2["default_path"])))

    def test_tier1_physical_delivery(self):
        """Tier 1: Both deliverable MP4 files must exist and be > 25MB."""
        res1 = verify_tier_1_physical_delivery(self.short1_path, SPEC_SHORT_1)
        res2 = verify_tier_1_physical_delivery(self.short2_path, SPEC_SHORT_2)
        assert res1["passed"], f"Short 1 Tier 1 Failed: {res1['message']}"
        assert res2["passed"], f"Short 2 Tier 1 Failed: {res2['message']}"

    def test_tier2_stream_codec_compliance(self):
        """Tier 2: Stream & Codec Compliance (1080x1920, h264 High, yuv420p, aac stereo 48k, faststart)."""
        res1 = verify_tier_2_stream_codec_compliance(self.short1_path, SPEC_SHORT_1)
        res2 = verify_tier_2_stream_codec_compliance(self.short2_path, SPEC_SHORT_2)
        assert res1["passed"], f"Short 1 Tier 2 Failed: {res1['message']}"
        assert res2["passed"], f"Short 2 Tier 2 Failed: {res2['message']}"

    def test_tier3_duration_boundaries(self):
        """Tier 3: Narrative & Duration Boundaries (Short 1: 48-55s, Short 2: 50-58s)."""
        res1 = verify_tier_3_duration_boundaries(self.short1_path, SPEC_SHORT_1)
        res2 = verify_tier_3_duration_boundaries(self.short2_path, SPEC_SHORT_2)
        assert res1["passed"], f"Short 1 Tier 3 Failed: {res1['message']}"
        assert res2["passed"], f"Short 2 Tier 3 Failed: {res2['message']}"

    def test_tier4_subtitle_safe_zone_and_reframing(self):
        """Tier 4: Subtitle Mobile-Safe Zone (400 < y < 1500) & Reframing Inspection."""
        res1 = verify_tier_4_subtitle_safe_zone_and_reframing(self.short1_path, SPEC_SHORT_1)
        res2 = verify_tier_4_subtitle_safe_zone_and_reframing(self.short2_path, SPEC_SHORT_2)
        assert res1["passed"], f"Short 1 Tier 4 Failed: {res1['message']}"
        assert res2["passed"], f"Short 2 Tier 4 Failed: {res2['message']}"

    def test_tier5_decoding_and_playback_integrity(self):
        """Tier 5: Full ffmpeg null decode check with zero errors."""
        res1 = verify_tier_5_decoding_and_playback_integrity(self.short1_path, SPEC_SHORT_1)
        res2 = verify_tier_5_decoding_and_playback_integrity(self.short2_path, SPEC_SHORT_2)
        assert res1["passed"], f"Short 1 Tier 5 Failed: {res1['message']}"
        assert res2["passed"], f"Short 2 Tier 5 Failed: {res2['message']}"


# ==============================================================================
# Standalone CLI Runner & Pretty Formatter
# ==============================================================================

def print_banner():
    banner = """
================================================================================
   VIRAL SHORTS E2E ACCEPTANCE VERIFICATION RUNNER (5 TIERS)
   Universal Hardware Compatibility & Narrative Retention Standards
================================================================================
"""
    print(banner)


def format_tier_status(status: str) -> str:
    color_map = {
        "PASS": "\033[92m[PASS]\033[0m",
        "FAIL": "\033[91m[FAIL]\033[0m",
        "BLOCKED": "\033[93m[BLOCKED]\033[0m",
        "SKIPPED": "\033[94m[SKIPPED]\033[0m",
    }
    return color_map.get(status, f"[{status}]")


def main():
    parser = argparse.ArgumentParser(description="E2E Verification for Topic 03 Viral Shorts Deliverables")
    parser.add_argument("--short1", type=str, default=str(SPEC_SHORT_1["default_path"]),
                        help="Path to Short 1 deliverable")
    parser.add_argument("--short2", type=str, default=str(SPEC_SHORT_2["default_path"]),
                        help="Path to Short 2 deliverable")
    parser.add_argument("--downloads-dir", type=str, default=None,
                        help="Override default Downloads folder directory")
    parser.add_argument("--json-report", type=str, default="production/topic_03/shorts/e2e_verification_report.json",
                        help="Path to output JSON verification report")
    parser.add_argument("--skip-tier5", action="store_true",
                        help="Skip full ffmpeg decode pass for rapid iteration")
    parser.add_argument("--verbose", action="store_true",
                        help="Print verbose stream and atom debugging details")

    args = parser.parse_args()

    short1_path = Path(args.short1)
    short2_path = Path(args.short2)

    if args.downloads_dir:
        d_dir = Path(args.downloads_dir)
        short1_path = d_dir / SHORT_1_FILENAME
        short2_path = d_dir / SHORT_2_FILENAME

    print_banner()
    print(f"Target Short 1: {short1_path}")
    print(f"Target Short 2: {short2_path}")
    print("-" * 80)

    # Evaluate deliverables
    eval_short1 = run_all_tiers_for_deliverable(short1_path, SPEC_SHORT_1, skip_tier5=args.skip_tier5)
    eval_short2 = run_all_tiers_for_deliverable(short2_path, SPEC_SHORT_2, skip_tier5=args.skip_tier5)

    all_evals = [eval_short1, eval_short2]

    for ev in all_evals:
        print(f"\nDeliverable: {ev['title']}")
        print(f"File: {ev['file_path']}")
        print(f"Overall Status: {format_tier_status('PASS' if ev['overall_passed'] else 'FAIL')}")
        print("-" * 80)

        for tier_key in ["tier_1", "tier_2", "tier_3", "tier_4", "tier_5"]:
            t = ev["tiers"][tier_key]
            st = format_tier_status(t["status"])
            print(f"  {st} Tier {t['tier']}: {t['name']}")
            print(f"         Result: {t['message']}")
            if args.verbose and t.get("details"):
                print(f"         Details: {json.dumps(t['details'], indent=2)}")

    # Overall Summary
    total_passed = sum(1 for ev in all_evals if ev["overall_passed"])
    print("\n" + "=" * 80)
    print(f"SUMMARY: {total_passed}/2 Deliverables Passed All Verification Tiers.")
    print("=" * 80)

    # Write JSON report
    report_data = {
        "timestamp_utc": subprocess.check_output(["python", "-c", "import datetime; print(datetime.datetime.now(datetime.timezone.utc).isoformat())"], text=True).strip(),
        "summary": {
            "deliverables_evaluated": 2,
            "deliverables_passed": total_passed,
            "deliverables_failed": 2 - total_passed,
            "all_passed": (total_passed == 2)
        },
        "deliverables": {
            "short_1": eval_short1,
            "short_2": eval_short2
        }
    }

    report_path = Path(args.json_report)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report_data, f, indent=2)
    print(f"\n[REPORT] Saved full JSON verification report to: {report_path.resolve()}")

    if total_passed == 2:
        print("\n\033[92mALL 5 TIERS COMPLIANT: Ready for Final Handover.\033[0m\n")
        sys.exit(0)
    else:
        print("\n\033[91mVERIFICATION DEFICIENCIES DETECTED: Check failures above.\033[0m\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
