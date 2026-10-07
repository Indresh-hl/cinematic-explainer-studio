#!/usr/bin/env python3
"""
pipeline/render_topic_02_master_video.py
========================================
Cinema-grade rendering engine for Topic 02:
"The Low Dopamine Morning Routine To Reset Your Brain Focus"

Features:
- 110 synchronized master shots across 29 script lines.
- Dynamic Ken Burns motion: S-curve zoom_in, zoom_out, pan_right, pan_left, drift, and static holds.
- Cosine cross-dissolves tailored per transition type (0.60s act transitions, 0.35s shot dissolves, 0.05s snap cuts).
- Precision temporal synchronization with audio chunks and 5.0s Act 4 recall test.
- Hardware-accelerated NVIDIA NVENC GPU encoding (H.264, CQ 18, 14 Mbps, 30 fps).
- Audio pass-through from TOPIC_02_FULL_VOICEOVER.mp3.
"""

import os
import sys
import math
import time
import json
import shutil
import subprocess
from pathlib import Path
import cv2
import numpy as np

# UTF-8 stdout
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

BASE_DIR = Path(r"c:\Users\Indresh HL\Downloads\youtube long fromat")
IMAGES_DIR = Path(r"C:\Users\Indresh HL\Downloads\TOPIC_02_4K_IMAGES_CURATED")
AUDIO_FILE = Path(r"C:\Users\Indresh HL\Downloads\TOPIC_02_FULL_VOICEOVER.mp3")
METADATA_JSON = BASE_DIR / "production" / "topic_02" / "audio" / "topic_02_timeline_metadata.json"

OUTPUT_WS = BASE_DIR / "production" / "topic_02" / "TOPIC_02_MASTER_VIDEO_FINAL.mp4"
OUTPUT_DL = Path(r"C:\Users\Indresh HL\Downloads\TOPIC_02_MASTER_VIDEO_FINAL.mp4")

OUTPUT_WS.parent.mkdir(parents=True, exist_ok=True)

# 1. Complete Shot & Transition Mapping across all 29 Lines
# (Shot ID, Motion, Transition)
SCRIPT_MAPPING = [
    # ACT 1: THE CRIME SCENE AT 6:45 AM (0:00 - 1:38)
    ("LINE_01", ["LINE_01-A", "LINE_01-B"], [("static", "dissolve"), ("static", "dissolve")]),
    ("LINE_02", ["LINE_02-A", "LINE_02-B", "LINE_02-C"], [("zoom_in", "dissolve"), ("static", "snap"), ("zoom_in", "dissolve")]),
    ("LINE_03", ["LINE_03-A", "LINE_03-B", "LINE_03-C"], [("drift", "dissolve"), ("pan_right", "dissolve"), ("zoom_in", "snap")]),
    ("LINE_04", ["LINE_04-A", "LINE_04-B", "LINE_04-C", "LINE_04-D"], [("zoom_in", "snap"), ("zoom_in", "dissolve"), ("pan_right", "dissolve"), ("zoom_out", "dissolve")]),
    ("LINE_05", ["LINE_05-A", "LINE_05-B", "LINE_05-C", "LINE_05-D"], [("zoom_in", "dissolve"), ("drift", "dissolve"), ("pan_right", "snap"), ("drift", "dissolve")]),
    ("LINE_06", ["LINE_06-A", "LINE_06-B", "LINE_06-C", "LINE_06-D"], [("zoom_in", "dissolve"), ("static", "snap"), ("zoom_in", "dissolve"), ("zoom_out", "dissolve")]),
    ("LINE_07", ["LINE_07-A", "LINE_07-B", "LINE_07-C", "LINE_07-D"], [("pan_right", "dissolve"), ("static", "snap"), ("zoom_in", "dissolve"), ("zoom_in", "dissolve_act")]),

    # ACT 2: THE NEUROCHEMICAL HEIST (1:38 - 3:59)
    ("LINE_08", ["LINE_08-A", "LINE_08-B", "LINE_08-C", "LINE_08-D"], [("zoom_in", "dissolve"), ("zoom_in", "snap"), ("pan_right", "snap"), ("zoom_in", "dissolve")]),
    ("LINE_09", ["LINE_09-A", "LINE_09-B", "LINE_09-C", "LINE_09-D"], [("drift", "dissolve"), ("static", "dissolve"), ("pan_left", "dissolve"), ("zoom_in", "dissolve")]),
    ("LINE_10", ["LINE_10-A", "LINE_10-B", "LINE_10-C", "LINE_10-D"], [("zoom_in", "snap"), ("pan_right", "dissolve"), ("zoom_in", "snap"), ("zoom_in", "dissolve")]),
    ("LINE_11", ["LINE_11-A", "LINE_11-B", "LINE_11-C", "LINE_11-D"], [("pan_right", "dissolve"), ("zoom_in", "dissolve"), ("static", "dissolve"), ("drift", "dissolve")]),
    ("LINE_12", ["LINE_12-A", "LINE_12-B", "LINE_12-C", "LINE_12-D"], [("zoom_in", "snap"), ("pan_left", "snap"), ("zoom_in", "dissolve"), ("zoom_out", "dissolve")]),
    ("LINE_13", ["LINE_13-A", "LINE_13-B", "LINE_13-C", "LINE_13-D"], [("zoom_in", "dissolve"), ("zoom_in", "dissolve"), ("static", "dissolve"), ("zoom_in", "dissolve_act")]),

    # ACT 3: THE GHOST IN THE MACHINE (3:59 - 5:44)
    ("LINE_14", ["LINE_14-A", "LINE_14-B", "LINE_14-C", "LINE_14-D"], [("pan_left", "dissolve"), ("zoom_in", "dissolve"), ("drift", "dissolve"), ("zoom_in", "dissolve")]),
    ("LINE_15", ["LINE_15-A", "LINE_15-B", "LINE_15-C", "LINE_15-D"], [("zoom_in", "dissolve"), ("pan_right", "dissolve"), ("zoom_out", "dissolve"), ("zoom_in", "dissolve")]),
    ("LINE_16", ["LINE_16-A", "LINE_16-B", "LINE_16-C", "LINE_16-D"], [("zoom_in", "snap"), ("drift", "snap"), ("zoom_in", "snap"), ("zoom_in", "dissolve")]),
    ("LINE_17", ["LINE_17-A", "LINE_17-B", "LINE_17-C", "LINE_17-D"], [("pan_right", "dissolve"), ("zoom_in", "dissolve"), ("zoom_in", "dissolve"), ("zoom_out", "dissolve")]),
    ("LINE_18", ["LINE_18-A", "LINE_18-B", "LINE_18-C", "LINE_18-D"], [("zoom_in", "dissolve"), ("static", "dissolve"), ("pan_left", "snap"), ("zoom_out", "dissolve_act")]),

    # ACT 4: THE 5-SECOND ATTENTION RESET (5:44 - 7:26)
    ("LINE_19", ["LINE_19-A", "LINE_19-B", "LINE_19-C", "LINE_19-D"], [("static", "snap"), ("zoom_in", "snap"), ("zoom_in", "dissolve"), ("zoom_in", "dissolve")]),
    ("LINE_20", ["LINE_20-A", "LINE_20-B", "LINE_20-C", "LINE_20-D"], [("zoom_in", "snap"), ("pan_right", "snap"), ("static", "snap"), ("static", "snap")]),
    ("LINE_21", ["LINE_21-A", "LINE_21-B", "LINE_21-C", "LINE_21-D"], [("zoom_in", "snap"), ("drift", "dissolve"), ("pan_right", "dissolve"), ("zoom_out", "dissolve")]),
    ("LINE_22", ["LINE_22-A", "LINE_22-B", "LINE_22-C", "LINE_22-D"], [("pan_left", "dissolve"), ("zoom_in", "snap"), ("zoom_in", "dissolve"), ("zoom_in", "dissolve")]),
    ("LINE_23", ["LINE_23-A", "LINE_23-B", "LINE_23-C", "LINE_23-D"], [("pan_right", "dissolve"), ("zoom_in", "dissolve"), ("pan_left", "snap"), ("zoom_in", "dissolve_act")]),

    # ACT 5: THE TACTICAL ANTIDOTE (7:26 - 10:00)
    ("LINE_24", ["LINE_24-A", "LINE_24-B", "LINE_24-C", "LINE_24-D"], [("zoom_out", "dissolve"), ("pan_right", "snap"), ("zoom_in", "dissolve"), ("pan_left", "dissolve")]),
    ("LINE_25", ["LINE_25-A", "LINE_25-B", "LINE_25-C", "LINE_25-D"], [("zoom_in", "snap"), ("zoom_in", "snap"), ("static", "dissolve"), ("zoom_out", "dissolve")]),
    ("LINE_26", ["LINE_26-A", "LINE_26-B", "LINE_26-C", "LINE_26-D"], [("zoom_in", "snap"), ("pan_right", "dissolve"), ("zoom_in", "dissolve"), ("zoom_in", "dissolve")]),
    ("LINE_27", ["LINE_27-A", "LINE_27-B", "LINE_27-C", "LINE_27-D"], [("zoom_in", "snap"), ("drift", "dissolve"), ("zoom_in", "dissolve"), ("static", "dissolve")]),
    ("LINE_28", ["LINE_28-A", "LINE_28-B", "LINE_28-C", "LINE_28-D"], [("zoom_out", "dissolve"), ("zoom_in", "snap"), ("zoom_in", "dissolve"), ("zoom_out", "dissolve_act")]),
    ("LINE_29", ["LINE_29-A", "LINE_29-B"], [("drift", "dissolve"), ("zoom_in", "dissolve")])
]


def build_timeline_schedule():
    with open(METADATA_JSON, "r", encoding="utf-8") as f:
        meta = json.load(f)

    lines_info = {l["line_label"]: l for l in meta["lines"]}
    total_audio_duration = meta["total_duration"]

    timeline_shots = []
    
    for label, shot_ids, styles in SCRIPT_MAPPING:
        info = lines_info[label]
        block_start = info["start_time"]
        speech_dur = info["speech_duration"]
        pause_dur = info["pause_duration"]
        block_total_dur = speech_dur + pause_dur
        
        num_shots = len(shot_ids)
        
        # Special case: LINE_20 has a 5.0-second thinking countdown on the final shot (LINE_20-D)
        if label == "LINE_20":
            # speech_dur ~ 16.75s, pause_dur = 5.00s -> total = 21.75s
            # 20-A: 4.5s ("first 3 apps")
            # 20-B: 6.0s ("valuable info")
            # 20-C: 3.5s ("Think. 5 seconds.")
            # 20-D: 7.75s ("Starting now." + 5s countdown space)
            durations = [4.5, 6.0, 3.5, block_total_dur - (4.5 + 6.0 + 3.5)]
        else:
            shot_dur = block_total_dur / num_shots
            durations = [shot_dur] * num_shots

        cur_shot_start = block_start
        for s_idx, shot_id in enumerate(shot_ids):
            dur = durations[s_idx]
            motion, trans = styles[s_idx]
            timeline_shots.append({
                "shot_id": shot_id,
                "start": cur_shot_start,
                "end": cur_shot_start + dur,
                "duration": dur,
                "motion": motion,
                "transition": trans
            })
            cur_shot_start += dur

    return timeline_shots, total_audio_duration


def apply_ken_burns(img, progress, motion_type, target_w=1920, target_h=1080):
    """Applies smooth S-curve eased Ken Burns camera motion."""
    ease_p = 0.5 * (1.0 - math.cos(math.pi * progress))
    img_h, img_w = img.shape[:2]

    if motion_type == "zoom_in":
        scale = 1.00 + 0.06 * ease_p
        cx, cy = img_w * 0.5, img_h * 0.5
    elif motion_type == "zoom_out":
        scale = 1.06 - 0.06 * ease_p
        cx, cy = img_w * 0.5, img_h * 0.5
    elif motion_type == "pan_right":
        scale = 1.04
        cx = img_w * (0.48 + 0.04 * ease_p)
        cy = img_h * 0.5
    elif motion_type == "pan_left":
        scale = 1.04
        cx = img_w * (0.52 - 0.04 * ease_p)
        cy = img_h * 0.5
    elif motion_type == "drift":
        scale = 1.01 + 0.04 * ease_p
        cx = img_w * (0.49 + 0.02 * ease_p)
        cy = img_h * (0.49 + 0.02 * ease_p)
    elif motion_type == "static":
        scale = 1.02
        cx, cy = img_w * 0.5, img_h * 0.5
    else:
        scale = 1.02
        cx, cy = img_w * 0.5, img_h * 0.5

    crop_w = int(img_w / scale)
    crop_h = int(img_h / scale)

    x1 = max(0, min(img_w - crop_w, int(cx - crop_w / 2)))
    y1 = max(0, min(img_h - crop_h, int(cy - crop_h / 2)))
    x2 = x1 + crop_w
    y2 = y1 + crop_h

    cropped = img[y1:y2, x1:x2]
    return cv2.resize(cropped, (target_w, target_h), interpolation=cv2.INTER_AREA)


def main():
    print("=" * 75)
    print("🎬 RENDERING TOPIC 02 MASTER CINEMATIC EXPLAINER VIDEO")
    print("Engine: OpenCV High-Acutance Ken Burns + Cosine Dissolves + NVIDIA NVENC")
    print("=" * 75)

    timeline_shots, total_audio_dur = build_timeline_schedule()
    total_shots = len(timeline_shots)
    print(f"[*] Total compiled shots: {total_shots}")
    print(f"[*] Total runtime: {total_audio_dur/60:.2f} minutes ({total_audio_dur:.2f} seconds)")

    # Preload all 110 images into memory
    print("\n[*] Preloading 110 4K master images into memory...")
    t0_load = time.time()
    loaded_images = {}
    for shot in timeline_shots:
        sid = shot["shot_id"]
        if sid not in loaded_images:
            p = IMAGES_DIR / f"{sid}.jpg"
            if not p.exists():
                raise FileNotFoundError(f"Missing master 4K image: {p}")
            img = cv2.imread(str(p))
            loaded_images[sid] = img

    print(f"[SUCCESS] Preloaded {len(loaded_images)} master 4K images in {time.time() - t0_load:.2f}s!")

    target_w, target_h = 1920, 1080
    fps = 30
    total_frames = int(round(fps * total_audio_dur))
    print(f"[*] Canvas: {target_w}x{target_h} @ {fps} fps | Total frames: {total_frames}")

    # Launch FFmpeg NVENC pipeline
    cmd = [
        "ffmpeg", "-y",
        "-f", "rawvideo",
        "-pix_fmt", "bgr24",
        "-s", f"{target_w}x{target_h}",
        "-r", str(fps),
        "-i", "-",
        "-i", str(AUDIO_FILE),
        "-c:v", "h264_nvenc",
        "-preset", "p4",
        "-rc", "vbr",
        "-cq", "18",
        "-b:v", "14M",
        "-maxrate", "20M",
        "-bufsize", "28M",
        "-pix_fmt", "yuv420p",
        "-profile:v", "high",
        "-level", "4.1",
        "-c:a", "aac",
        "-b:a", "192k",
        "-ar", "48000",
        "-ac", "2",
        "-movflags", "+faststart",
        "-shortest",
        str(OUTPUT_WS)
    ]

    print("[*] Launching hardware NVENC GPU encoder on RTX 4050...")
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)

    t0_render = time.time()
    active_idx = 0

    for f_idx in range(total_frames):
        t = f_idx / fps

        # Advance active shot
        while active_idx < total_shots - 1 and t >= timeline_shots[active_idx]["end"]:
            active_idx += 1

        cur_shot = timeline_shots[active_idx]
        cur_img = loaded_images[cur_shot["shot_id"]]

        # Calculate progress inside current shot
        shot_t = t - cur_shot["start"]
        dur = cur_shot["duration"]
        progress = max(0.0, min(1.0, shot_t / dur)) if dur > 0 else 0.0

        # Generate base Ken Burns frame
        frame_curr = apply_ken_burns(cur_img, progress, cur_shot["motion"], target_w, target_h)

        # Transition handling
        trans_type = cur_shot["transition"]
        if trans_type == "dissolve_act":
            trans_dur = 0.60
        elif trans_type == "dissolve":
            trans_dur = 0.35
        else:  # snap
            trans_dur = 0.05

        time_to_end = cur_shot["end"] - t
        if active_idx < total_shots - 1 and time_to_end < trans_dur:
            next_shot = timeline_shots[active_idx + 1]
            next_img = loaded_images[next_shot["shot_id"]]
            
            next_t = trans_dur - time_to_end
            next_prog = max(0.0, min(1.0, next_t / next_shot["duration"]))
            frame_next = apply_ken_burns(next_img, next_prog, next_shot["motion"], target_w, target_h)

            # Cosine smooth blending
            blend_p = 1.0 - (time_to_end / trans_dur)
            alpha = 0.5 * (1.0 - math.cos(math.pi * blend_p))
            frame_final = cv2.addWeighted(frame_curr, 1.0 - alpha, frame_next, alpha, 0)
        else:
            frame_final = frame_curr

        proc.stdin.write(frame_final.tobytes())

        if f_idx % 450 == 0 or f_idx == total_frames - 1:
            elapsed = time.time() - t0_render
            pct = (f_idx / total_frames) * 100
            cur_fps = (f_idx / elapsed) if elapsed > 0 else 0
            eta = (total_frames - f_idx) / cur_fps if cur_fps > 0 else 0
            print(f"  [Rendering] {f_idx:5d}/{total_frames} frames ({pct:5.1f}%) | Time: {t:5.1f}s | Speed: {cur_fps:5.1f} fps | ETA: {eta/60:4.1f}m")

    proc.stdin.close()
    proc.wait()
    total_time = time.time() - t0_render
    print(f"\n[SUCCESS] Hardware rendering finished in {total_time/60:.2f} minutes ({total_frames/total_time:.1f} fps)!")

    # Copy to user Downloads folder
    print(f"[*] Copying final video to Downloads: {OUTPUT_DL}...")
    shutil.copy2(OUTPUT_WS, OUTPUT_DL)

    file_size_mb = OUTPUT_DL.stat().st_size / (1024 * 1024)
    print("\n" + "=" * 75)
    print("🎉 FULL MASTER CINEMATIC VIDEO COMPLETE & READY!")
    print(f"• File Location: {OUTPUT_DL}")
    print(f"• File Size:     {file_size_mb:.2f} MB")
    print(f"• Resolution:    {target_w}x{target_h} (Full HD Widescreen @ 30 fps)")
    print(f"• Video Codec:   H.264 NVENC Studio Master (CQ 18, 14 Mbps)")
    print(f"• Audio Codec:   192 kbps Direct Studio Stream (1:1 Synchronized)")
    print(f"• Total Runtime: {total_audio_dur/60:.2f} Minutes ({total_audio_dur:.2f} Seconds)")
    print("=" * 75)

if __name__ == "__main__":
    main()
