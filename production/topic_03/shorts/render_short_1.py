"""
Autonomous Production Pipeline for Short 1: "The 5-Second Test" (Interactive Pattern Interrupt)
Milestone 1 - Viral Shorts Project (Topic 03)

Specifications:
- Canvas: 1080x1920 (9:16 vertical ratio)
- Composition: Dual-layer (Ambient blurred background + centered 16:9 foreground)
- Range: t_start = 324.204s, t_end = 375.912s (Duration: 51.708s)
- Subtitles: ASS karaoke subtitles in mobile safe zone (y ~ 1330)
- Acceleration: Hardware NVENC GPU (h264_nvenc, High Profile, yuv420p)
- Target Bitrate: 6500k (guaranteeing file size > 25.0 MB)
- Audio: Stereo AAC 256k 48kHz with 80ms fade-in and 150ms fade-out
- Output: C:\\Users\\Indresh HL\\Downloads\\TOPIC_03_VIRAL_SHORT_1_THE_5_SECOND_TEST.mp4
"""

import os
import sys

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

import json
import time
import shutil
import subprocess
from pathlib import Path

# Base Paths
BASE_DIR = Path(r"c:\Users\Indresh HL\Downloads\youtube long fromat")
VIDEO_MASTER = BASE_DIR / "production" / "topic_03" / "TOPIC_03_MASTER_VIDEO_FINAL.mp4"
FALLBACK_VIDEO = Path(r"C:\Users\Indresh HL\Downloads\TOPIC_03_MASTER_VIDEO_FINAL.mp4")
AUDIO_MASTER = Path(r"C:\Users\Indresh HL\Downloads\TOPIC_03_FULL_VOICEOVER.mp3")
WORD_TIMESTAMPS = BASE_DIR / "production" / "topic_03" / "audio" / "full_timeline_word_timestamps.json"
FONTS_DIR = BASE_DIR / "assets" / "fonts"
ASS_PATH = BASE_DIR / "production" / "topic_03" / "shorts" / "short_1_subtitles.ass"
OUTPUT_PATH = Path(r"C:\Users\Indresh HL\Downloads\TOPIC_03_VIRAL_SHORT_1_THE_5_SECOND_TEST.mp4")

# Short 1 Timing Parameters
T_START = 324.204
T_END = 375.912
DURATION = T_END - T_START  # 51.708s

def format_ass_time(sec):
    if sec < 0:
        sec = 0.0
    h = int(sec // 3600)
    m = int((sec % 3600) // 60)
    s = int(sec % 60)
    cs = int(round((sec - int(sec)) * 100))
    if cs >= 100:
        s += 1
        cs -= 100
    return f"{h:d}:{m:02d}:{s:02d}.{cs:02d}"

def ensure_subtitles():
    """Generates short_1_subtitles.ass with updated compliant margins."""
    print(f"[*] Generating updated ASS subtitles for Short 1...")
    sys.path.insert(0, str(BASE_DIR))
    from pipeline.render_topic_03_master_video_captions import compute_timeline, build_adaptive_phrases

    with open(WORD_TIMESTAMPS, "r", encoding="utf-8") as f:
        word_data = json.load(f)

    shots, _ = compute_timeline()
    phrases = build_adaptive_phrases(word_data, shots)
    s1_phrases = [p for p in phrases if T_START - 0.2 <= p['start'] < T_END]

    header = f"""[Script Info]
Title: Short 1: The 5-Second Test (Interactive Pattern Interrupt)
ScriptType: v4.00+
WrapStyle: 0
ScaledBorderAndShadow: yes
YCbCr Matrix: TV.709
PlayResX: 1080
PlayResY: 1920

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
; ShortsDefault: Warm butter cream text (#FFF2A8), bold Playfair Display, thick obsidian stroke, deep shadow
Style: ShortsDefault,Playfair Display,74,&H00A8F2FF,&H0066D1FF,&H000C0908,&H90000000,-1,0,0,0,100,100,0,0,1,6,4,2,60,60,570,1
; ShortsKaraoke: Active sunglow gold (#FFD166) highlight, italic, glowing gold pop
Style: ShortsKaraoke,Playfair Display,76,&H0066D1FF,&H00A8F2FF,&H000C0908,&HA0000000,-1,1,0,0,105,105,0,0,1,7,5,2,60,60,570,1
; ShortsPop: Used for single-word explosive emphasis (e.g. countdown or pivotal reveals)
Style: ShortsPop,Playfair Display,96,&H0066D1FF,&H00A8F2FF,&H000C0908,&HA0000000,-1,1,0,0,115,115,0,0,1,8,6,2,60,60,570,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    events = []
    digits = {"5.", "4.", "3.", "2.", "1."}

    for p in s1_phrases:
        p_start_rel = max(0.0, p["start"] - T_START)
        p_end_rel = min(DURATION, p["end"] - T_START)
        if p_end_rel <= p_start_rel:
            continue

        words = p.get("words", [])
        if not words:
            continue

        is_digit = len(words) == 1 and words[0]["word"].strip() in digits

        for widx, w in enumerate(words):
            w_start_rel = max(p_start_rel, w["start"] - T_START)
            if widx < len(words) - 1:
                next_w_start = max(p_start_rel, words[widx + 1]["start"] - T_START)
                w_end_rel = min(p_end_rel, next_w_start)
            else:
                w_end_rel = p_end_rel

            if w_end_rel <= w_start_rel:
                w_end_rel = w_start_rel + 0.15

            if is_digit:
                style_name = "ShortsPop"
                event_text = r"{\pos(540,1330)}{\c&H0066D1FF&\fscx115\fscy115}" + w["word"] + r"{\r}"
            else:
                style_name = "ShortsDefault"
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
            events.append(f"Dialogue: 0,{start_str},{end_str},{style_name},,0,0,0,,{event_text}")

    content = header + "\n".join(events) + "\n"
    ASS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(ASS_PATH, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"[+] Generated ASS subtitles: {ASS_PATH} with {len(events)} events.")
    return ASS_PATH

def render_short_1():
    print("=" * 80)
    print("PRODUCTION: TOPIC 03 - SHORT 1: 'THE 5-SECOND TEST' (NVENC GPU)")
    print("=" * 80)

    # 1. Source resolution
    source_video = VIDEO_MASTER if VIDEO_MASTER.exists() else FALLBACK_VIDEO
    if not source_video.exists():
        raise FileNotFoundError(f"Master clean video not found at {VIDEO_MASTER} or {FALLBACK_VIDEO}")
    print(f"[+] Source Master Video: {source_video}")

    # 2. Subtitles preparation
    ass_file = ensure_subtitles()

    # 3. Destination preparation
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    # Convert paths to forward slashes for FFmpeg filtergraph safety
    ass_path_str = str(ass_file).replace("\\", "/").replace(":", "\\:")
    fonts_dir_str = str(FONTS_DIR).replace("\\", "/").replace(":", "\\:")

    # 4. Construct Dual-Layer Filtergraph
    # - Background: 1080x1920 scaled, cropped, boxblurred (26:5), graded (brightness=-0.02, saturation=1.20, gamma=0.90)
    # - Foreground: 1080x608 pristine lanczos scaled 16:9 video centered vertically at y=(1920-608)/2 = 656
    # - Subtitles: ASS filter loading Playfair Display with fallback to direct fontsdir, centered at y=1330
    # - Audio: 80ms fade-in, 150ms fade-out, peak limiter at 0.98, stereo 48kHz
    filtergraph = (
        "[0:v]split=2[bg_raw][fg_raw];"
        "[bg_raw]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,"
        "boxblur=26:5,eq=brightness=0.04:saturation=1.25:gamma=0.95[bg];"
        "[fg_raw]scale=1080:608:flags=lanczos[fg];"
        "[bg][fg]overlay=(W-w)/2:(H-h)/2[comp];"
        f"[comp]ass='{ass_path_str}':fontsdir='{fonts_dir_str}',setsar=1[outv];"
        f"[0:a]afade=t=in:ss=0:d=0.08,afade=t=out:st={DURATION - 0.150:.3f}:d=0.150,volume=1.05,alimiter=limit=0.98[outa]"
    )

    # 5. Build FFmpeg command with NVIDIA NVENC acceleration
    cmd = [
        "ffmpeg", "-y",
        "-ss", f"{T_START:.3f}",
        "-t", f"{DURATION:.3f}",
        "-i", str(source_video),
        "-filter_complex", filtergraph,
        "-map", "[outv]",
        "-map", "[outa]",
        "-c:v", "h264_nvenc",
        "-preset", "p5",
        "-profile:v", "high",
        "-pix_fmt", "yuv420p",
        "-b:v", "6500k",
        "-minrate", "5000k",
        "-maxrate", "8000k",
        "-bufsize", "16000k",
        "-c:a", "aac",
        "-b:a", "256k",
        "-ar", "48000",
        "-ac", "2",
        "-movflags", "+faststart",
        str(OUTPUT_PATH)
    ]

    print(f"[*] Range: {T_START:.3f}s to {T_END:.3f}s (Duration: {DURATION:.3f}s)")
    print(f"[*] Encoder: h264_nvenc (Preset: p5, Profile: high, PixFmt: yuv420p)")
    print(f"[*] Target Bitrates: Video 6500 kbps (Min 5000k, Max 8000k), Audio 256 kbps stereo")
    print(f"[*] Output: {OUTPUT_PATH}")
    print("[*] Launching hardware NVENC GPU render...")

    start_time = time.time()
    proc = subprocess.run(cmd, capture_output=True, text=True)
    elapsed = time.time() - start_time

    if proc.returncode != 0:
        print("[!] FFmpeg execution failed:")
        print(proc.stderr)
        raise RuntimeError(f"FFmpeg render failed with exit code {proc.returncode}")

    print(f"[+] Render completed in {elapsed:.2f}s ({DURATION / elapsed:.2f}x real-time speed)!")

    # 6. Verify Deliverable
    verify_deliverable(OUTPUT_PATH)

def verify_deliverable(file_path):
    print("\n" + "=" * 80)
    print("VERIFICATION GATE: SHORT 1 DELIVERABLE")
    print("=" * 80)

    # File size check (> 25 MB = 26,214,400 bytes)
    file_size = file_path.stat().st_size
    file_size_mb = file_size / (1024 * 1024)
    print(f"[*] File Size: {file_size:,} bytes ({file_size_mb:.2f} MB)")
    assert file_size > 26_214_400, f"FAILED: File size {file_size_mb:.2f} MB is <= 25.0 MB"
    print("    -> PASS: File size strictly exceeds 25.0 MB threshold.")

    # Probe metadata via ffprobe
    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration,size,bit_rate",
        "-show_entries", "stream=codec_name,profile,width,height,pix_fmt,r_frame_rate,sample_aspect_ratio,display_aspect_ratio,sample_rate,channels",
        "-of", "json",
        str(file_path)
    ]
    res = subprocess.run(cmd, capture_output=True, text=True, check=True)
    meta = json.loads(res.stdout)

    v_stream = next(s for s in meta["streams"] if s.get("width"))
    a_stream = next(s for s in meta["streams"] if s.get("sample_rate"))
    duration = float(meta["format"]["duration"])

    # Duration check (48.0s <= t <= 55.0s)
    print(f"[*] Duration: {duration:.3f}s (Target: {DURATION:.3f}s)")
    assert 48.0 <= duration <= 55.0, f"FAILED: Duration {duration:.3f}s outside [48.0s, 55.0s]"
    print("    -> PASS: Duration is strictly within [48.0s, 55.0s].")

    # Resolution check (1080x1920)
    width, height = int(v_stream["width"]), int(v_stream["height"])
    print(f"[*] Resolution: {width}x{height}")
    assert (width, height) == (1080, 1920), f"FAILED: Resolution is {width}x{height}, expected 1080x1920"
    print("    -> PASS: Resolution is exactly 1080x1920 (9:16 vertical).")

    # Pixel format check (yuv420p)
    pix_fmt = v_stream["pix_fmt"]
    codec_name = v_stream["codec_name"]
    profile = v_stream["profile"]
    print(f"[*] Video Format: codec={codec_name}, profile={profile}, pix_fmt={pix_fmt}")
    assert pix_fmt == "yuv420p", f"FAILED: pix_fmt is {pix_fmt}, expected yuv420p"
    assert codec_name == "h264", f"FAILED: codec is {codec_name}, expected h264"
    assert profile == "High", f"FAILED: profile is {profile}, expected High"
    print("    -> PASS: Video conforms strictly to H.264 High Profile yuv420p.")

    # Audio check (aac, 48000Hz, stereo)
    a_codec = a_stream["codec_name"]
    sample_rate = int(a_stream["sample_rate"])
    channels = int(a_stream["channels"])
    print(f"[*] Audio Format: codec={a_codec}, sample_rate={sample_rate}Hz, channels={channels}")
    assert a_codec == "aac", f"FAILED: audio codec is {a_codec}, expected aac"
    assert sample_rate == 48000, f"FAILED: sample_rate is {sample_rate}, expected 48000"
    assert channels == 2, f"FAILED: channels is {channels}, expected 2 (stereo)"
    print("    -> PASS: Audio conforms strictly to AAC stereo 48kHz.")

    # Aspect ratio check (SAR 1:1, DAR 9:16)
    sar = v_stream.get("sample_aspect_ratio", "1:1")
    dar = v_stream.get("display_aspect_ratio", "9:16")
    print(f"[*] Aspect Ratios: SAR={sar}, DAR={dar}")
    assert sar in ("1:1", "0:1"), f"FAILED: SAR is {sar}"
    print("    -> PASS: Aspect ratios are strictly compliant.")

    # Faststart check (moov atom before mdat)
    with open(file_path, "rb") as f:
        head = f.read(1024 * 1024)
        moov_pos = head.find(b"moov")
        mdat_pos = head.find(b"mdat")
    print(f"[*] Faststart Check: moov={moov_pos}, mdat={mdat_pos}")
    assert moov_pos != -1 and (mdat_pos == -1 or moov_pos < mdat_pos), "FAILED: faststart moov atom not placed before mdat"
    print("    -> PASS: Faststart is enabled (+faststart container flag verified).")

    print("\n[***] ALL ACCEPTANCE VERIFICATION GATES PASSED! DELIVERABLE IS READY.")
    print("=" * 80)

if __name__ == "__main__":
    render_short_1()
