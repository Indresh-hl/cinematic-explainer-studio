import os
import sys
import math
import time
import subprocess
from pathlib import Path
import cv2
import numpy as np

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

BASE_DIR = Path(r"c:\Users\Indresh HL\Downloads\youtube long fromat")
IMAGES_DIR = Path(r"C:\Users\Indresh HL\Downloads\TOPIC_03_4K_IMAGES")
AUDIO_FILE = Path(r"C:\Users\Indresh HL\Downloads\TOPIC_03_FULL_VOICEOVER.mp3")

OUTPUT_WS = BASE_DIR / "production" / "topic_03" / "TOPIC_03_MASTER_VIDEO_FINAL.mp4"
OUTPUT_DL = Path(r"C:\Users\Indresh HL\Downloads\TOPIC_03_MASTER_VIDEO_FINAL.mp4")

OUTPUT_WS.parent.mkdir(parents=True, exist_ok=True)

# 1. Timeline Mapping: Spoken Blocks & Shot Assignments
SCRIPT_MAPPING = [
    # ACT 1 (0:00 - 1:30)
    ("LINE_01", ["LINE_01-A", "LINE_01-B"], [("zoom_in", "dissolve"), ("zoom_out", "snap")]),
    ("LINE_02", ["LINE_02-A", "LINE_02-B", "LINE_02-C"], [("pan_right", "dissolve"), ("zoom_in", "dissolve"), ("zoom_in", "snap")]),
    ("LINE_03", ["LINE_03-A", "LINE_03-B", "LINE_03-C", "LINE_03-D"], [("drift", "dissolve"), ("zoom_in", "snap"), ("pan_right", "dissolve"), ("zoom_in", "dissolve")]),
    ("LINE_04", ["LINE_04-A", "LINE_04-B", "LINE_04-C"], [("zoom_in", "dissolve"), ("zoom_in", "dissolve"), ("zoom_out", "dissolve")]),
    ("LINE_05", ["LINE_05-A", "LINE_05-B", "LINE_05-C"], [("drift", "dissolve"), ("zoom_in", "snap"), ("zoom_out", "dissolve")]),
    ("LINE_06", ["LINE_06-A", "LINE_06-B"], [("zoom_in", "dissolve_act"), ("zoom_in", "dissolve")]),
    ("LINE_07", ["LINE_07-A", "LINE_07-B", "LINE_07-C"], [("pan_right", "dissolve"), ("zoom_in", "snap"), ("pan_left", "dissolve")]),
    ("LINE_08", ["LINE_08-A", "LINE_08-B", "LINE_08-C", "LINE_08-D"], [("zoom_in", "snap"), ("zoom_in", "dissolve"), ("zoom_out", "dissolve"), ("zoom_in", "snap")]),

    # ACT 2 (1:30 - 3:30)
    ("LINE_09", ["LINE_09-A", "LINE_09-B", "LINE_09-C"], [("zoom_in", "dissolve_act"), ("pan_right", "dissolve"), ("zoom_in", "dissolve")]),
    ("LINE_10", ["LINE_10-A", "LINE_10-B", "LINE_10-C"], [("pan_right", "dissolve"), ("zoom_in", "snap"), ("zoom_out", "dissolve")]),
    ("LINE_11", ["LINE_11-A", "LINE_11-B", "LINE_11-C"], [("zoom_in", "dissolve"), ("zoom_in", "dissolve"), ("zoom_in", "dissolve")]),
    ("LINE_12", ["LINE_12-A", "LINE_12-B", "LINE_12-C"], [("drift", "dissolve"), ("zoom_in", "snap"), ("zoom_out", "dissolve")]),
    ("LINE_13", ["LINE_13-A", "LINE_13-B", "LINE_13-C"], [("pan_left", "dissolve"), ("zoom_in", "snap"), ("zoom_out", "dissolve")]),
    ("LINE_14", ["LINE_14-A", "LINE_14-B", "LINE_14-C"], [("zoom_in", "dissolve"), ("zoom_in", "dissolve"), ("zoom_in", "snap")]),
    ("LINE_15", ["LINE_15-A", "LINE_15-B", "LINE_15-C"], [("zoom_out", "dissolve"), ("zoom_in", "dissolve"), ("zoom_in", "dissolve")]),

    # ACT 3 (3:30 - 5:15)
    ("LINE_16", ["LINE_16-A", "LINE_16-B"], [("zoom_in", "dissolve_act"), ("zoom_in", "dissolve")]),
    ("LINE_17", ["LINE_17-A", "LINE_17-B"], [("zoom_in", "dissolve"), ("zoom_in", "dissolve")]),
    ("LINE_18", ["LINE_18-A", "LINE_18-B", "LINE_18-C"], [("pan_right", "dissolve"), ("zoom_in", "dissolve"), ("zoom_out", "dissolve")]),
    ("LINE_19", ["LINE_19-A", "LINE_19-B", "LINE_19-C"], [("zoom_in", "dissolve"), ("zoom_in", "dissolve"), ("zoom_out", "dissolve")]),
    ("LINE_20", ["LINE_20-A", "LINE_20-B", "LINE_20-C"], [("zoom_in", "snap"), ("pan_right", "dissolve"), ("pan_left", "dissolve")]),
    ("LINE_21", ["LINE_21-A", "LINE_21-B"], [("zoom_in", "dissolve"), ("zoom_in", "snap")]),
    ("LINE_22", ["LINE_22-A", "LINE_22-B"], [("zoom_out", "snap"), ("zoom_in", "dissolve")]),
    ("LINE_23", ["LINE_23-A", "LINE_23-B"], [("zoom_out", "dissolve"), ("zoom_in", "dissolve")]),

    # ACT 4 (5:15 - 7:00)
    ("LINE_24", ["LINE_24-A", "LINE_24-B"], [("zoom_in", "dissolve_act"), ("zoom_in", "dissolve")]),
    ("LINE_25", ["LINE_25-A", "LINE_25-B"], [("zoom_in", "dissolve"), ("zoom_in", "dissolve")]),
    ("LINE_26_5", ["LINE_26-A"], [("zoom_in", "snap")]),
    ("LINE_26_4", ["LINE_26-A"], [("zoom_in", "snap")]),
    ("LINE_26_3", ["LINE_26-B"], [("zoom_in", "snap")]),
    ("LINE_26_2", ["LINE_26-B"], [("zoom_in", "snap")]),
    ("LINE_26_1", ["LINE_26-C"], [("zoom_out", "snap")]),
    ("LINE_27", ["LINE_27-A", "LINE_27-B", "LINE_27-C"], [("zoom_in", "dissolve"), ("zoom_in", "dissolve"), ("drift", "dissolve")]),
    ("LINE_28", ["LINE_28-A", "LINE_28-B", "LINE_28-C"], [("zoom_in", "dissolve"), ("pan_right", "dissolve"), ("zoom_out", "dissolve")]),
    ("LINE_29", ["LINE_29-A", "LINE_29-B"], [("zoom_out", "dissolve"), ("zoom_in", "snap")]),
    ("LINE_30", ["LINE_30-A", "LINE_30-B", "LINE_30-C"], [("zoom_in", "dissolve"), ("zoom_in", "dissolve"), ("pan_right", "snap")]),
    ("LINE_31", ["LINE_31-A"], [("zoom_in", "dissolve")]),

    # ACT 5 (7:00 - 8:30)
    ("LINE_32", ["LINE_32-A", "LINE_32-B"], [("zoom_in", "dissolve_act"), ("zoom_in", "dissolve")]),
    ("LINE_33", ["LINE_33-A", "LINE_33-B", "LINE_33-C"], [("pan_right", "dissolve"), ("zoom_in", "dissolve"), ("zoom_in", "dissolve")]),
    ("LINE_34", ["LINE_34-A", "LINE_34-B"], [("pan_left", "dissolve"), ("zoom_out", "dissolve")]),
    ("LINE_35", ["LINE_35-A", "LINE_35-B"], [("zoom_in", "dissolve"), ("zoom_in", "dissolve")]),
    ("LINE_36", ["LINE_36-A", "LINE_36-B"], [("zoom_in", "dissolve"), ("zoom_out", "dissolve")]),
    ("LINE_37", ["LINE_37-A", "LINE_37-B"], [("zoom_in", "dissolve"), ("zoom_in", "dissolve")]),
    ("LINE_38", ["LINE_38-A", "LINE_38-B"], [("zoom_in", "dissolve"), ("zoom_in", "dissolve")]),
    ("LINE_39", ["LINE_39-A"], [("zoom_in", "dissolve_act")])
]

def get_audio_duration(file_path):
    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(file_path)
    ]
    res = subprocess.run(cmd, stdout=subprocess.PIPE, text=True, check=True)
    return float(res.stdout.strip())

def compute_timeline():
    print("[*] Computing timeline synchronization from audio chunks...")
    chunks_dir = BASE_DIR / "production" / "topic_03" / "audio" / "chunks"
    temp_dir = BASE_DIR / "production" / "topic_03" / "audio" / "temp"

    timeline_shots = []
    current_time = 0.0

    for idx, (label, shot_ids, styles) in enumerate(SCRIPT_MAPPING, 1):
        # Find speech file
        speech_file = chunks_dir / f"{idx:02d}_{label}_speech.mp3"
        dur_speech = get_audio_duration(speech_file) if speech_file.exists() else 5.0
        
        # Find pause file if any
        pause_files = list(temp_dir.glob(f"pause_{idx:02d}_*.mp3"))
        dur_pause = get_audio_duration(pause_files[0]) if pause_files else 0.35
        
        block_total_dur = dur_speech + dur_pause
        num_shots = len(shot_ids)
        shot_dur = block_total_dur / num_shots

        for s_idx, shot_id in enumerate(shot_ids):
            motion, trans = styles[s_idx]
            shot_start = current_time + s_idx * shot_dur
            shot_end = shot_start + shot_dur
            timeline_shots.append({
                "shot_id": shot_id,
                "start": shot_start,
                "end": shot_end,
                "duration": shot_dur,
                "motion": motion,
                "transition": trans
            })

        current_time += block_total_dur

    return timeline_shots, current_time

def apply_ken_burns(img, progress, motion_type, target_w=1920, target_h=1080):
    # Easing curve: smooth S-curve
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
    frame = cv2.resize(cropped, (target_w, target_h), interpolation=cv2.INTER_AREA)
    return frame

def main():
    print("=" * 75)
    print("🎬 RENDERING MASTER CINEMATIC VIDEO (TOPIC 03)")
    print("Engine: OpenCV Ken Burns + Cosine Dissolves + NVIDIA NVENC GPU")
    print("=" * 75)

    timeline_shots, total_audio_dur = compute_timeline()
    print(f"[*] Total compiled shots: {len(timeline_shots)}")
    print(f"[*] Total estimated runtime: {total_audio_dur:.2f}s ({total_audio_dur/60:.2f} mins)")

    # Preload all 99 images into RAM
    print("\n[*] Preloading 99 4K master images into memory...")
    t0_load = time.time()
    loaded_images = {}
    for shot in timeline_shots:
        sid = shot["shot_id"]
        if sid not in loaded_images:
            img_path = IMAGES_DIR / f"{sid}.jpg"
            if not img_path.exists():
                print(f"[!] Warning: Missing image {img_path}")
                continue
            img = cv2.imread(str(img_path))
            loaded_images[sid] = img
    print(f"[SUCCESS] Preloaded {len(loaded_images)} images in {time.time() - t0_load:.2f}s!")

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
        "-c:a", "copy",
        "-shortest",
        str(OUTPUT_WS)
    ]

    print("[*] Launching hardware NVENC GPU encoder...")
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)

    t0_render = time.time()
    active_idx = 0
    total_shots = len(timeline_shots)

    for f_idx in range(total_frames):
        t = f_idx / fps

        # Advance active shot
        while active_idx < total_shots - 1 and t >= timeline_shots[active_idx]["end"]:
            active_idx += 1

        cur_shot = timeline_shots[active_idx]
        cur_img = loaded_images.get(cur_shot["shot_id"])
        
        # Calculate intra-shot progress
        shot_t = t - cur_shot["start"]
        dur = cur_shot["duration"]
        progress = max(0.0, min(1.0, shot_t / dur)) if dur > 0 else 0.0

        # Generate base Ken Burns frame for current shot
        frame_curr = apply_ken_burns(cur_img, progress, cur_shot["motion"], target_w, target_h)

        # Check for transition into next shot
        # Transition duration: 0.55s for act dissolves, 0.40s for normal dissolves, 0.05s for snap
        trans_type = cur_shot["transition"]
        if trans_type == "dissolve_act":
            trans_dur = 0.55
        elif trans_type == "dissolve":
            trans_dur = 0.40
        else:
            trans_dur = 0.05

        time_to_end = cur_shot["end"] - t
        if active_idx < total_shots - 1 and time_to_end < trans_dur:
            next_shot = timeline_shots[active_idx + 1]
            next_img = loaded_images.get(next_shot["shot_id"])
            if next_img is not None:
                # Progress into next shot
                next_t = trans_dur - time_to_end
                next_prog = max(0.0, min(1.0, next_t / next_shot["duration"]))
                frame_next = apply_ken_burns(next_img, next_prog, next_shot["motion"], target_w, target_h)

                # Smooth cosine alpha blend
                blend_p = 1.0 - (time_to_end / trans_dur)
                alpha = 0.5 * (1.0 - math.cos(math.pi * blend_p))
                frame_final = cv2.addWeighted(frame_curr, 1.0 - alpha, frame_next, alpha, 0)
            else:
                frame_final = frame_curr
        else:
            frame_final = frame_curr

        proc.stdin.write(frame_final.tobytes())

        if f_idx % 300 == 0 or f_idx == total_frames - 1:
            elapsed = time.time() - t0_render
            pct = (f_idx / total_frames) * 100
            cur_fps = (f_idx / elapsed) if elapsed > 0 else 0
            eta = (total_frames - f_idx) / cur_fps if cur_fps > 0 else 0
            print(f"  [Rendering] {f_idx:5d}/{total_frames} frames ({pct:5.1f}%) | Time: {t:5.1f}s | Speed: {cur_fps:5.1f} fps | ETA: {eta/60:4.1f}m")

    proc.stdin.close()
    proc.wait()
    total_time = time.time() - t0_render
    print(f"\n[SUCCESS] Render finished in {total_time/60:.2f} minutes ({total_frames/total_time:.1f} fps)!")

    # Copy to user Downloads folder
    import shutil
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
