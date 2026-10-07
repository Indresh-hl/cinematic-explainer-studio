#!/usr/bin/env python3
"""
Production Pipeline: Render Viral Short #2 ("The Stranger in Your Head")
Topic: 03 - Procrastination & The Future Self (fMRI Neuroscience Discovery)
Narrative Span: LINE_16 through LINE_20 (approx. 222.60s to 277.00s, ~54.40s duration)

Architecture:
- Source Video: production/topic_03/TOPIC_03_MASTER_VIDEO_FINAL.mp4 (clean uncaptioned master cut)
- Source Audio: Master audio mix with 80ms fade-in and 150ms fade-out
- Canvas: 1080x1920 vertical 9:16 canvas with dual-layer blurred ambient extension
- Subtitles: Word-synced ASS karaoke subtitles positioned in mobile safe zone (y ≈ 1330)
- Hardware NVENC GPU Encoding: h264_nvenc, High Profile, yuv420p, 6500 kbps, AAC stereo 256k 48kHz
- Output: C:\\Users\\Indresh HL\\Downloads\\TOPIC_03_VIRAL_SHORT_2_THE_STRANGER_IN_YOUR_HEAD.mp4
"""

import os
import sys
import time
import json
import struct
import argparse
import subprocess
from pathlib import Path
from typing import Dict, Any, Tuple, List

# Ensure UTF-8 stdout on Windows
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

BASE_DIR = Path(r"c:\Users\Indresh HL\Downloads\youtube long fromat")
sys.path.insert(0, str(BASE_DIR))

# Default production paths
DEFAULT_MASTER_VIDEO = BASE_DIR / "production" / "topic_03" / "TOPIC_03_MASTER_VIDEO_FINAL.mp4"
DEFAULT_FALLBACK_VIDEO = BASE_DIR / "production" / "topic_03" / "TOPIC_03_MASTER_VIDEO_WITH_CAPTIONS.mp4"
DEFAULT_WORDS_FILE = BASE_DIR / "production" / "topic_03" / "audio" / "full_timeline_word_timestamps.json"
DEFAULT_FONTS_DIR = BASE_DIR / "assets" / "fonts"
DEFAULT_ASS_FILE = BASE_DIR / "production" / "topic_03" / "shorts" / "short_2_subtitles.ass"
DEFAULT_OUTPUT_MP4 = Path(r"C:\Users\Indresh HL\Downloads\TOPIC_03_VIRAL_SHORT_2_THE_STRANGER_IN_YOUR_HEAD.mp4")

# Short 2 Timing Calibration
SHORT_2_START_SEC = 222.60
SHORT_2_DURATION_SEC = 54.40
SHORT_2_END_SEC = SHORT_2_START_SEC + SHORT_2_DURATION_SEC  # 277.00s

MIN_FILE_SIZE_BYTES = 25 * 1024 * 1024  # 26,214,400 bytes


def format_ass_time(sec: float) -> str:
    """Format seconds into ASS timecode H:MM:SS.cs."""
    if sec < 0:
        sec = 0.0
    h = int(sec // 3600)
    m = int((sec % 3600) // 60)
    s = int(sec % 60)
    cs = int(round((sec - int(sec)) * 100))
    if cs >= 100:
        cs = 99
    return f"{h:d}:{m:02d}:{s:02d}.{cs:02d}"


def generate_short_2_subtitles(
    ass_path: Path,
    words_file: Path,
    offset_time: float = SHORT_2_START_SEC,
    duration: float = SHORT_2_DURATION_SEC
) -> Path:
    """
    Generate mobile-safe karaoke ASS subtitles for Short 2.
    Anchors text at y ≈ 1330 with Playfair Display, butter cream base,
    and sunglow gold active word pop highlight.
    """
    from pipeline.render_topic_03_master_video_captions import compute_timeline, build_adaptive_phrases

    print(f"[*] Parsing word timestamps from {words_file}...")
    with open(words_file, "r", encoding="utf-8") as f:
        word_data = json.load(f)

    shots, _ = compute_timeline()
    phrases = build_adaptive_phrases(word_data, shots)

    end_time = offset_time + duration
    s2_phrases = [p for p in phrases if p["start"] < end_time and p["end"] > offset_time]

    header = """[Script Info]
Title: Short 2: The Stranger in Your Head (fMRI Neuroscience Discovery)
ScriptType: v4.00+
WrapStyle: 0
ScaledBorderAndShadow: yes
YCbCr Matrix: TV.709
PlayResX: 1080
PlayResY: 1920

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
; ShortsDefault: Warm butter cream text (#FFF2A8), bold Playfair Display, thick obsidian stroke (#08090C), deep shadow
Style: ShortsDefault,Playfair Display,74,&H00A8F2FF,&H0066D1FF,&H000C0908,&H90000000,-1,0,0,0,100,100,0,0,1,6,4,2,570,570,570,1
; ShortsKaraoke: Active sunglow gold (#FFD166) highlight, italic, glowing gold pop
Style: ShortsKaraoke,Playfair Display,76,&H0066D1FF,&H00A8F2FF,&H000C0908,&HA0000000,-1,1,0,0,105,105,0,0,1,7,5,2,570,570,570,1
; ShortsPop: Used for single-word explosive emphasis (e.g. countdown or pivotal reveals)
Style: ShortsPop,Playfair Display,92,&H0000EBFF,&H00FFFFFF,&H00000000,&HB0000000,-1,1,0,0,110,110,0,0,1,8,6,2,570,570,570,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    events = []
    for p in s2_phrases:
        p_start_rel = max(0.0, p["start"] - offset_time)
        p_end_rel = min(duration, p["end"] - offset_time)
        if p_end_rel <= p_start_rel or p_start_rel >= duration - 0.2:
            continue

        words = p.get("words", [])
        if not words:
            continue

        for widx, w in enumerate(words):
            w_start_rel = max(p_start_rel, w["start"] - offset_time)
            if w_start_rel >= duration:
                continue

            if widx < len(words) - 1:
                next_w_start = max(p_start_rel, words[widx + 1]["start"] - offset_time)
                w_end_rel = min(p_end_rel, next_w_start)
            else:
                w_end_rel = p_end_rel

            if w_end_rel <= w_start_rel:
                w_end_rel = min(duration, w_start_rel + 0.15)

            if w_end_rel <= w_start_rel:
                continue

            line_parts = []
            for j, other_w in enumerate(words):
                w_txt = other_w["word"]
                if j == widx:
                    line_parts.append(r"{\c&H0066D1FF&\fscx108\fscy108}" + w_txt + r"{\r}")
                else:
                    line_parts.append(r"{\c&H00A8F2FF&}" + w_txt)

            event_text = r"{\pos(540,1330)}" + " ".join(line_parts)
            start_str = format_ass_time(w_start_rel)
            end_str = format_ass_time(w_end_rel)
            events.append(f"Dialogue: 0,{start_str},{end_str},ShortsDefault,,0,0,0,,{event_text}")

    ass_path.parent.mkdir(parents=True, exist_ok=True)
    with open(ass_path, "w", encoding="utf-8") as f:
        f.write(header + "\n".join(events) + "\n")

    print(f"[+] Subtitles generated at {ass_path} ({len(events)} word-events).")
    return ass_path


def parse_mp4_faststart(file_path: Path) -> Tuple[bool, str]:
    """Inspect MP4 atom order to confirm faststart (moov precedes mdat)."""
    atoms = []
    if not file_path.exists():
        return False, "File does not exist"

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

    atom_names = [a[0] for a in atoms]
    if "moov" not in atom_names:
        return False, "Missing 'moov' atom"
    if "mdat" not in atom_names:
        return False, "Missing 'mdat' atom"

    moov_pos = next(a[1] for a in atoms if a[0] == "moov")
    mdat_pos = next(a[1] for a in atoms if a[0] == "mdat")

    if moov_pos < mdat_pos:
        return True, f"moov ({moov_pos}) precedes mdat ({mdat_pos})"
    else:
        return False, f"mdat ({mdat_pos}) precedes moov ({moov_pos})"


def verify_rendered_deliverable(output_path: Path) -> Dict[str, Any]:
    """Run comprehensive ffprobe verification on the rendered MP4 deliverable."""
    print("\n" + "=" * 80)
    print("DELIVERABLE VERIFICATION REPORT")
    print("=" * 80)

    if not output_path.exists():
        raise FileNotFoundError(f"Rendered output missing: {output_path}")

    file_size_bytes = output_path.stat().st_size
    file_size_mb = file_size_bytes / (1024 * 1024)
    print(f"File Size: {file_size_mb:.2f} MB ({file_size_bytes:,} bytes)")
    assert file_size_bytes > MIN_FILE_SIZE_BYTES, f"File size too small: {file_size_mb:.2f} MB (Required > 25.0 MB)"

    cmd = [
        "ffprobe", "-v", "quiet",
        "-print_format", "json",
        "-show_format",
        "-show_streams",
        str(output_path)
    ]
    res = subprocess.run(cmd, capture_output=True, text=True, check=True)
    probe = json.loads(res.stdout)

    v_stream = next((s for s in probe["streams"] if s["codec_type"] == "video"), None)
    a_stream = next((s for s in probe["streams"] if s["codec_type"] == "audio"), None)
    fmt = probe["format"]

    assert v_stream is not None, "Video stream missing"
    assert a_stream is not None, "Audio stream missing"

    # 1. Video validation
    w = int(v_stream["width"])
    h = int(v_stream["height"])
    pix_fmt = v_stream["pix_fmt"]
    v_codec = v_stream["codec_name"]
    v_profile = v_stream.get("profile", "")
    fps_parts = v_stream["r_frame_rate"].split("/")
    fps = float(fps_parts[0]) / float(fps_parts[1]) if len(fps_parts) == 2 else 0.0

    print(f"Video: {v_codec} ({v_profile}), {w}x{h}, {pix_fmt}, {fps:.2f} fps")
    assert w == 1080 and h == 1920, f"Resolution violation: got {w}x{h}, expected 1080x1920"
    assert v_codec == "h264", f"Video codec mismatch: got {v_codec}, expected h264"
    assert v_profile.lower() == "high", f"Profile mismatch: got {v_profile}, expected High"
    assert pix_fmt == "yuv420p", f"Pixel format mismatch: got {pix_fmt}, expected yuv420p"
    assert 29.97 <= fps <= 30.05, f"FPS mismatch: got {fps:.2f}, expected 30.0"

    # 2. Audio validation
    a_codec = a_stream["codec_name"]
    channels = int(a_stream["channels"])
    sample_rate = int(a_stream["sample_rate"])
    print(f"Audio: {a_codec}, {channels} channels (stereo), {sample_rate} Hz")
    assert a_codec == "aac", f"Audio codec mismatch: got {a_codec}, expected aac"
    assert channels == 2, f"Audio channels mismatch: got {channels}, expected 2 (stereo)"
    assert sample_rate == 48000, f"Sample rate mismatch: got {sample_rate}, expected 48000"

    # 3. Duration validation
    duration = float(fmt.get("duration", 0.0))
    print(f"Duration: {duration:.2f}s (Allowed: 50.0s - 58.0s)")
    assert 50.0 <= duration <= 58.0, f"Duration violation: {duration:.2f}s outside [50.0, 58.0]"

    # 4. Faststart validation
    faststart_ok, faststart_msg = parse_mp4_faststart(output_path)
    print(f"Faststart: {'PASSED' if faststart_ok else 'FAILED'} ({faststart_msg})")
    assert faststart_ok, f"Faststart violation: {faststart_msg}"

    print("-" * 80)
    print("ALL ACCEPTANCE GATES PASSED! Short 2 is 100% compliant.")
    print("=" * 80 + "\n")

    return {
        "file_size_mb": round(file_size_mb, 2),
        "duration_sec": round(duration, 2),
        "resolution": f"{w}x{h}",
        "video_codec": v_codec,
        "pix_fmt": pix_fmt,
        "audio_codec": a_codec,
        "faststart": faststart_ok
    }


def render_short_2(
    input_video: Path = DEFAULT_MASTER_VIDEO,
    output_mp4: Path = DEFAULT_OUTPUT_MP4,
    ass_subtitles: Path = DEFAULT_ASS_FILE,
    fonts_dir: Path = DEFAULT_FONTS_DIR,
    words_file: Path = DEFAULT_WORDS_FILE,
    start_sec: float = SHORT_2_START_SEC,
    duration_sec: float = SHORT_2_DURATION_SEC,
    target_bitrate: str = "6500k",
    min_bitrate: str = "5000k",
    max_bitrate: str = "8000k",
    bufsize: str = "16000k",
    preset: str = "p5"
) -> Path:
    """
    Execute hardware NVENC GPU rendering of Short 2 into 1080x1920 9:16 deliverable.
    """
    t0 = time.time()
    print("=" * 80)
    print("RENDERING SHORT 2: THE STRANGER IN YOUR HEAD (fMRI Discovery)")
    print(f"Narrative Span: LINE_16 to LINE_20 | {start_sec:.2f}s to {start_sec + duration_sec:.2f}s ({duration_sec:.2f}s)")
    print(f"Hardware: NVIDIA GeForce RTX GPU (h264_nvenc, preset {preset})")
    print(f"Source Video: {input_video}")
    print(f"Destination: {output_mp4}")
    print("=" * 80)

    if not input_video.exists():
        if DEFAULT_FALLBACK_VIDEO.exists():
            print(f"[!] Warning: {input_video} not found, falling back to {DEFAULT_FALLBACK_VIDEO}")
            input_video = DEFAULT_FALLBACK_VIDEO
        else:
            raise FileNotFoundError(f"Input video not found: {input_video}")

    # Generate ASS subtitles if missing or requested
    if not ass_subtitles.exists():
        generate_short_2_subtitles(ass_subtitles, words_file, offset_time=start_sec, duration=duration_sec)
    else:
        print(f"[*] Using existing ASS subtitles: {ass_subtitles}")

    output_mp4.parent.mkdir(parents=True, exist_ok=True)

    # Windows path formatting for FFmpeg filtergraph
    ass_filter_path = str(ass_subtitles).replace("\\", "/")
    if ":" in ass_filter_path and not ass_filter_path.startswith("/"):
        ass_filter_path = ass_filter_path[0] + "\\:" + ass_filter_path[2:]

    fonts_filter_dir = str(fonts_dir).replace("\\", "/")
    if ":" in fonts_filter_dir and not fonts_filter_dir.startswith("/"):
        fonts_filter_dir = fonts_filter_dir[0] + "\\:" + fonts_filter_dir[2:]

    fade_out_start = round(duration_sec - 0.15, 3)

    filter_complex = (
        "[0:v]split=2[bg_raw][fg_raw];"
        "[bg_raw]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=26:5,eq=brightness=-0.02:saturation=1.20:gamma=0.90[bg];"
        "[fg_raw]scale=1080:608:flags=lanczos[fg];"
        "[bg][fg]overlay=(W-w)/2:(H-h)/2[comp];"
        f"[comp]ass='{ass_filter_path}':fontsdir='{fonts_filter_dir}',setsar=1[outv];"
        f"[0:a]afade=t=in:ss=0:d=0.08,afade=t=out:st={fade_out_start}:d=0.15,alimiter=limit=0.98[outa]"
    )

    cmd = [
        "ffmpeg", "-y",
        "-ss", f"{start_sec:.3f}",
        "-t", f"{duration_sec:.3f}",
        "-i", str(input_video),
        "-filter_complex", filter_complex,
        "-map", "[outv]",
        "-map", "[outa]",
        "-c:v", "h264_nvenc",
        "-preset", preset,
        "-profile:v", "high",
        "-pix_fmt", "yuv420p",
        "-b:v", target_bitrate,
        "-minrate", min_bitrate,
        "-maxrate", max_bitrate,
        "-bufsize", bufsize,
        "-c:a", "aac",
        "-b:a", "256k",
        "-ar", "48000",
        "-ac", "2",
        "-movflags", "+faststart",
        str(output_mp4)
    ]

    print("[*] Launching FFmpeg NVENC acceleration pipeline...")
    print(f"Command: {' '.join(cmd)}\n")
    proc = subprocess.run(cmd, capture_output=True, text=True)

    if proc.returncode != 0:
        print(f"[!] FFmpeg render failed with exit code {proc.returncode}:")
        print(proc.stderr)
        raise RuntimeError(f"FFmpeg render failed: {proc.stderr[-800:]}")

    elapsed = time.time() - t0
    print(f"\n[+] Render successfully finished in {elapsed:.1f}s ({duration_sec / elapsed:.2f}x real-time speed)!")

    # Verify deliverable meets all acceptance criteria
    verify_rendered_deliverable(output_mp4)
    return output_mp4


def main():
    parser = argparse.ArgumentParser(description="Render Short 2: The Stranger in Your Head (1080x1920 NVENC)")
    parser.add_argument("--input", type=str, default=str(DEFAULT_MASTER_VIDEO), help="Input clean master cut MP4")
    parser.add_argument("--output", type=str, default=str(DEFAULT_OUTPUT_MP4), help="Destination deliverable MP4 path")
    parser.add_argument("--start", type=float, default=SHORT_2_START_SEC, help="Start time in seconds")
    parser.add_argument("--duration", type=float, default=SHORT_2_DURATION_SEC, help="Duration in seconds")
    parser.add_argument("--regenerate-ass", action="store_true", help="Force regenerate ASS subtitles")
    parser.add_argument("--preset", type=str, default="p5", help="NVENC preset (p1 to p7)")
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)
    ass_path = DEFAULT_ASS_FILE

    if args.regenerate_ass or not ass_path.exists():
        generate_short_2_subtitles(ass_path, DEFAULT_WORDS_FILE, offset_time=args.start, duration=args.duration)

    render_short_2(
        input_video=input_path,
        output_mp4=output_path,
        ass_subtitles=ass_path,
        start_sec=args.start,
        duration_sec=args.duration,
        preset=args.preset
    )


if __name__ == "__main__":
    main()
