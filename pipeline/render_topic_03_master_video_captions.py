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
from PIL import Image, ImageDraw, ImageFont, ImageFilter

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

BASE_DIR = Path(r"c:\Users\Indresh HL\Downloads\youtube long fromat")
IMAGES_DIR = Path(r"C:\Users\Indresh HL\Downloads\TOPIC_03_4K_IMAGES")
AUDIO_FILE = Path(r"C:\Users\Indresh HL\Downloads\TOPIC_03_FULL_VOICEOVER.mp3")
FONT_PATH = BASE_DIR / "assets" / "fonts" / "PlayfairDisplay.ttf"
WORD_TIMESTAMPS_FILE = BASE_DIR / "production" / "topic_03" / "audio" / "full_timeline_word_timestamps.json"

OUTPUT_WS = BASE_DIR / "production" / "topic_03" / "TOPIC_03_MASTER_VIDEO_WITH_CAPTIONS.mp4"
OUTPUT_DL = Path(r"C:\Users\Indresh HL\Downloads\TOPIC_03_MASTER_VIDEO_WITH_CAPTIONS.mp4")

OUTPUT_WS.parent.mkdir(parents=True, exist_ok=True)

# 1. Timeline Mapping: Spoken Blocks & Selective Motion Assignments (All 99 Shots)
SCRIPT_MAPPING = [
    # ACT 1: THE CRIME SCENE (0:00 - 1:30)
    # Line 01: 11:42 PM, project due. Sam at desk -> Clock on wall (STATIC hold)
    ("LINE_01", ["LINE_01-A", "LINE_01-B"], [("zoom_in", "dissolve"), ("static", "snap")]),
    # Line 02: Blank screen -> Macro cursor (STATIC hold) -> Sam's frozen expression
    ("LINE_02", ["LINE_02-A", "LINE_02-B", "LINE_02-C"], [("pan_right", "dissolve"), ("static", "dissolve"), ("zoom_in", "snap")]),
    # Line 03: Fingers hover -> Phone reach -> Doomscroll -> Dopamine hit
    ("LINE_03", ["LINE_03-A", "LINE_03-B", "LINE_03-C", "LINE_03-D"], [("drift", "dissolve"), ("zoom_in", "snap"), ("pan_right", "dissolve"), ("zoom_in", "dissolve")]),
    # Line 04: Clock ticks 1:15 AM -> Pile of work -> Sudden dread
    ("LINE_04", ["LINE_04-A", "LINE_04-B", "LINE_04-C"], [("zoom_in", "dissolve"), ("zoom_in", "dissolve"), ("zoom_out", "dissolve")]),
    # Line 05: Close laptop in shame -> Bed collapse -> Ceiling stare
    ("LINE_05", ["LINE_05-A", "LINE_05-B", "LINE_05-C"], [("drift", "dissolve"), ("zoom_in", "snap"), ("zoom_out", "dissolve")]),
    # Line 06: Presenter Sam reveal -> Somatic mirror
    ("LINE_06", ["LINE_06-A", "LINE_06-B"], [("zoom_in", "dissolve_act"), ("zoom_in", "dissolve")]),
    # Line 07: Blackboard PARADOX (STATIC) -> Lazy diagnosis false -> Involuntary defense
    ("LINE_07", ["LINE_07-A", "LINE_07-B", "LINE_07-C"], [("static", "dissolve"), ("zoom_in", "snap"), ("pan_left", "dissolve")]),
    # Line 08: Cellular lock -> Brain cross-section -> Internal emergency siren
    ("LINE_08", ["LINE_08-A", "LINE_08-B", "LINE_08-C", "LINE_08-D"], [("zoom_in", "snap"), ("zoom_in", "dissolve"), ("zoom_out", "dissolve"), ("zoom_in", "snap")]),

    # ACT 2: THE BIOLOGICAL AMBUSH (1:30 - 3:30)
    # Line 09: Balance scale CEO vs Guard Dog -> Prefrontal cortex CEO -> Amygdala guard dog
    ("LINE_09", ["LINE_09-A", "LINE_09-B", "LINE_09-C"], [("zoom_in", "dissolve_act"), ("pan_right", "dissolve"), ("zoom_in", "dissolve")]),
    # Line 10: Evolutionary split screen -> Saber-toothed tiger ancestor -> Modern threat
    ("LINE_10", ["LINE_10-A", "LINE_10-B", "LINE_10-C"], [("pan_right", "dissolve"), ("zoom_in", "snap"), ("zoom_out", "dissolve")]),
    # Line 11: Paper monster snarling -> Sam flinching -> Floating "EMOTIONAL REGULATION" text (STATIC)
    ("LINE_11", ["LINE_11-A", "LINE_11-B", "LINE_11-C"], [("zoom_in", "dissolve"), ("zoom_in", "dissolve"), ("static", "dissolve")]),
    # Line 12: Tax form/essay beast -> Emotional threat -> 3 Fear index cards (STATIC)
    ("LINE_12", ["LINE_12-A", "LINE_12-B", "LINE_12-C"], [("drift", "dissolve"), ("zoom_in", "snap"), ("static", "dissolve")]),
    # Line 13: Amygdala triggers panic -> Phone soothing shield -> Temporary dopamine calm
    ("LINE_13", ["LINE_13-A", "LINE_13-B", "LINE_13-C"], [("pan_left", "dissolve"), ("zoom_in", "snap"), ("zoom_out", "dissolve")]),
    # Line 14: Dr. Timothy Pychyl quote -> Present Mood Repair -> Immediate relief
    ("LINE_14", ["LINE_14-A", "LINE_14-B", "LINE_14-C"], [("zoom_in", "dissolve"), ("zoom_in", "dissolve"), ("zoom_in", "snap")]),
    # Line 15: Vicious cycle gear -> Guilt spike -> Compounded dread
    ("LINE_15", ["LINE_15-A", "LINE_15-B", "LINE_15-C"], [("zoom_out", "dissolve"), ("zoom_in", "dissolve"), ("zoom_in", "dissolve")]),

    # ACT 3: THE STRANGER IN YOUR HEAD (3:30 - 5:15)
    # Line 16: Translucent 3D Holographic skull -> fMRI scanner beam
    ("LINE_16", ["LINE_16-A", "LINE_16-B"], [("zoom_in", "dissolve_act"), ("zoom_in", "dissolve")]),
    # Line 17: Hal Hershfield fMRI chart (STATIC) -> Neural lighting comparison
    ("LINE_17", ["LINE_17-A", "LINE_17-B"], [("static", "dissolve"), ("zoom_in", "dissolve")]),
    # Line 18: Thinking of yourself -> Thinking of stranger Matt Damon -> Identical neural activation
    ("LINE_18", ["LINE_18-A", "LINE_18-B", "LINE_18-C"], [("pan_right", "dissolve"), ("zoom_in", "dissolve"), ("zoom_out", "dissolve")]),
    # Line 19: Present Sam sitting -> Future Sam silhouette -> Emotional disconnect
    ("LINE_19", ["LINE_19-A", "LINE_19-B", "LINE_19-C"], [("zoom_in", "dissolve"), ("zoom_in", "dissolve"), ("zoom_out", "dissolve")]),
    # Line 20: Future Sam superhero fantasy -> Armchair luxury -> Harsh reality
    ("LINE_20", ["LINE_20-A", "LINE_20-B", "LINE_20-C"], [("zoom_in", "snap"), ("pan_right", "dissolve"), ("pan_left", "dissolve")]),
    # Line 21: Passing heavy dumbbell to Future Sam -> Chained Future Sam collapse
    ("LINE_21", ["LINE_21-A", "LINE_21-B"], [("zoom_in", "dissolve"), ("zoom_in", "snap")]),
    # Line 22: 7:00 AM glowing alarm clock (STATIC) -> Exhausted Sam awakening
    ("LINE_22", ["LINE_22-A", "LINE_22-B"], [("static", "snap"), ("zoom_in", "dissolve")]),
    # Line 23: The tragic realization -> Empathy gap between self and future
    ("LINE_23", ["LINE_23-A", "LINE_23-B"], [("zoom_out", "dissolve"), ("zoom_in", "dissolve")]),

    # ACT 4: THE 5-SECOND TEST & ACTIVATION ENERGY (5:15 - 7:00)
    # Line 24: Countdown apparatus appears in void (STATIC hold)
    ("LINE_24", ["LINE_24-A"], [("static", "dissolve_act")]),
    # Line 25: Countdown bezel primed glowing, instructions given (STATIC hold)
    ("LINE_25", ["LINE_24-B"], [("static", "dissolve")]),
    # Line 26_5: "Five." -> 3D Numeral 5 (STATIC hold, instant SNAP cut)
    ("LINE_26_5", ["LINE_25-A"], [("static", "snap")]),
    # Line 26_4: "Four." -> 3D Numeral 4 (STATIC hold, instant SNAP cut)
    ("LINE_26_4", ["LINE_25-B"], [("static", "snap")]),
    # Line 26_3: "Three." -> 3D Numeral 3 (STATIC hold, instant SNAP cut)
    ("LINE_26_3", ["LINE_26-A"], [("static", "snap")]),
    # Line 26_2: "Two." -> 3D Numeral 2 (STATIC hold, instant SNAP cut)
    ("LINE_26_2", ["LINE_26-B"], [("static", "snap")]),
    # Line 26_1: "One." -> 3D Numeral 1 & Detonation Shockwave (STATIC hold, instant SNAP cut)
    ("LINE_26_1", ["LINE_26-C"], [("static", "snap")]),
    # Line 27: Somatic check -> Solar plexus knot -> Micro-flinch realization
    ("LINE_27", ["LINE_27-A", "LINE_27-B", "LINE_27-C"], [("zoom_in", "dissolve"), ("zoom_in", "dissolve"), ("drift", "dissolve")]),
    # Line 28: Chemistry apparatus -> Molecular reaction -> Activation Energy graph (STATIC hold)
    ("LINE_28", ["LINE_28-A", "LINE_28-B", "LINE_28-C"], [("zoom_in", "dissolve"), ("pan_right", "dissolve"), ("static", "dissolve")]),
    # Line 29: Colossal Granite Boulder -> Straining against boulder
    ("LINE_29", ["LINE_29-A", "LINE_29-B"], [("zoom_out", "dissolve"), ("zoom_in", "snap")]),
    # Line 30: Polished glass marble -> Macro finger flick -> Frictionless rolling marble
    ("LINE_30", ["LINE_30-A", "LINE_30-B", "LINE_30-C"], [("zoom_in", "dissolve"), ("zoom_in", "dissolve"), ("pan_right", "snap")]),
    # Line 31: Sam standing enlightened
    ("LINE_31", ["LINE_31-A"], [("zoom_in", "dissolve")]),

    # ACT 5: THE TACTICAL ANTIDOTE & GRAND FINALE (7:00 - 8:30)
    # Line 32: Protocol 1 Plaque (STATIC) -> Vintage stopwatch in hand (STATIC)
    ("LINE_32", ["LINE_32-A", "LINE_32-B"], [("static", "dissolve_act"), ("static", "dissolve")]),
    # Line 33: Two-minute gateway -> Running shoes -> 1 Sentence written
    ("LINE_33", ["LINE_33-A", "LINE_33-B", "LINE_33-C"], [("pan_right", "dissolve"), ("zoom_in", "dissolve"), ("zoom_in", "dissolve")]),
    # Line 34: Sleeping Guard Dog curled peacefully -> Microscopic threshold
    ("LINE_34", ["LINE_34-A", "LINE_34-B"], [("pan_left", "dissolve"), ("zoom_out", "dissolve")]),
    # Line 35: Kinetic momentum -> Swinging Newton's Cradle
    ("LINE_35", ["LINE_35-A", "LINE_35-B"], [("zoom_in", "dissolve"), ("zoom_in", "dissolve")]),
    # Line 36: Protocol 2 Plaque (STATIC) -> Iron thorn hamster wheel
    ("LINE_36", ["LINE_36-A", "LINE_36-B"], [("static", "dissolve"), ("zoom_out", "dissolve")]),
    # Line 37: Thorn wheel dissolving into soft rose petals -> Self-compassion freedom
    ("LINE_37", ["LINE_37-A", "LINE_37-B"], [("zoom_in", "dissolve"), ("zoom_in", "dissolve")]),
    # Line 38: Serene morning sunrise through window -> Sam profile peaceful smile
    ("LINE_38", ["LINE_38-A", "LINE_38-B"], [("zoom_in", "dissolve"), ("zoom_in", "dissolve")]),
    # Line 39: Final channel outro brand card (STATIC hold)
    ("LINE_39", ["LINE_39-A"], [("static", "dissolve_act")])
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
        speech_file = chunks_dir / f"{idx:02d}_{label}_speech.mp3"
        dur_speech = get_audio_duration(speech_file) if speech_file.exists() else 5.0
        
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

def normalize_words(words):
    normalized = []
    i = 0
    while i < len(words):
        w = words[i]
        text = w["word"]
        if i + 1 < len(words):
            next_w = words[i+1]
            next_text = next_w["word"]
            if text.isdigit() and next_text.startswith('.') and next_text[1:].isdigit():
                merged_word = f"{text}:{next_text[1:]}"
                normalized.append({
                    "word": merged_word,
                    "start": w["start"],
                    "end": next_w["end"]
                })
                i += 2
                continue
            elif text.isdigit() and next_text.startswith(',') and next_text[1:].isdigit():
                merged_word = f"{text}{next_text}"
                normalized.append({
                    "word": merged_word,
                    "start": w["start"],
                    "end": next_w["end"]
                })
                i += 2
                continue
        normalized.append(w)
        i += 1
    return normalized

def build_adaptive_phrases(data, shots=None, max_chars=22):
    phrases = []
    for seg in data["segments"]:
        words = seg.get("words", [])
        if not words:
            continue
        words = normalize_words(words)
        i = 0
        while i < len(words):
            take = 2
            if i + 3 <= len(words):
                three_words = words[i:i+3]
                char_len = sum(len(w["word"]) for w in three_words)
                if char_len <= max_chars and (len(words) - i) != 4:
                    take = 3
            elif (len(words) - i) == 3:
                take = 3
            else:
                take = len(words) - i
                
            chunk = words[i:i+take]
            p_start = chunk[0]["start"]
            p_end = chunk[-1]["end"] + (0.22 if i+take >= len(words) else 0.05)
            
            phrases.append({
                "start": p_start,
                "end": p_end,
                "words": chunk,
                "text": " ".join([w["word"] for w in chunk])
            })
            i += take

    # Snap phrase boundaries to visual cuts
    if shots:
        cut_times = [s["end"] for s in shots[:-1]]
        for p in phrases:
            for cut_t in cut_times:
                if 0 < (cut_t - p["start"]) < 0.35:
                    p["start"] = cut_t
                if 0 < (p["end"] - cut_t) < 0.20:
                    p["end"] = cut_t

    return phrases

def apply_ken_burns(img, progress, motion_type, target_w=1920, target_h=1080):
    img_h, img_w = img.shape[:2]

    # STATIC hold: absolutely zero motion, perfectly crisp image
    if motion_type == "static":
        frame = cv2.resize(img, (target_w, target_h), interpolation=cv2.INTER_AREA)
        return frame

    # Easing curve: smooth S-curve
    ease_p = 0.5 * (1.0 - math.cos(math.pi * progress))

    if motion_type == "zoom_in":
        scale = 1.00 + 0.055 * ease_p
        cx, cy = img_w * 0.5, img_h * 0.5
    elif motion_type == "zoom_out":
        scale = 1.055 - 0.055 * ease_p
        cx, cy = img_w * 0.5, img_h * 0.5
    elif motion_type == "pan_right":
        scale = 1.035
        cx = img_w * (0.485 + 0.03 * ease_p)
        cy = img_h * 0.5
    elif motion_type == "pan_left":
        scale = 1.035
        cx = img_w * (0.515 - 0.03 * ease_p)
        cy = img_h * 0.5
    elif motion_type == "drift":
        scale = 1.01 + 0.035 * ease_p
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
    print("=" * 80)
    print("🎬 RENDERING MASTER VIDEO WITH CORRECTED TIMER, SELECTIVE MOTION & CAPTIONS")
    print("Channel: Isy why (@isy019) | Topic 03: Procrastination Cognitive Science")
    print("Engine: OpenCV + Pillow Karaoke Subtitles + NVIDIA NVENC GPU")
    print("=" * 80)

    timeline_shots, total_audio_dur = compute_timeline()
    print(f"[*] Total compiled shots: {len(timeline_shots)}")
    print(f"[*] Total estimated runtime: {total_audio_dur:.2f}s ({total_audio_dur/60:.2f} mins)")

    # Load Word Timestamps and build adaptive phrases
    print(f"[*] Loading word timestamps from {WORD_TIMESTAMPS_FILE}...")
    with open(WORD_TIMESTAMPS_FILE, "r", encoding="utf-8") as f:
        word_data = json.load(f)
    phrases = build_adaptive_phrases(word_data, timeline_shots)
    print(f"[*] Compiled {len(phrases)} adaptive subtitle phrases!")

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

    # Setup typography
    base_font_size = 78
    base_font = ImageFont.truetype(str(FONT_PATH), base_font_size)
    dummy_img = Image.new("RGBA", (1, 1), (0, 0, 0, 0))
    dummy_draw = ImageDraw.Draw(dummy_img)

    # Subtitle phrase render cache: (p_idx, active_w_idx) -> (RGBA Image, tx, ty)
    subtitle_cache = {}

    def get_subtitle_layer(p_idx, t):
        phrase = phrases[p_idx]
        words = phrase["words"]
        
        # Determine active word
        active_w_idx = 0
        for widx, w in enumerate(words):
            if w["start"] <= t <= w["end"]:
                active_w_idx = widx
                break
            elif t > w["end"]:
                active_w_idx = widx

        cache_key = (p_idx, active_w_idx)
        if cache_key in subtitle_cache:
            return subtitle_cache[cache_key]

        # Measure text with base font
        space_w = dummy_draw.textbbox((0, 0), " ", font=base_font)[2] - dummy_draw.textbbox((0, 0), " ", font=base_font)[0]
        word_widths = []
        for w in words:
            bbox = dummy_draw.textbbox((0, 0), w["word"], font=base_font)
            word_widths.append(bbox[2] - bbox[0])
            
        total_w = sum(word_widths) + space_w * (len(words) - 1)
        font = base_font
        
        # Scale down if unusually wide
        max_allowed_w = 1400
        if total_w > max_allowed_w:
            scaled_size = max(56, int(base_font_size * (max_allowed_w / total_w)))
            font = ImageFont.truetype(str(FONT_PATH), scaled_size)
            space_w = dummy_draw.textbbox((0, 0), " ", font=font)[2] - dummy_draw.textbbox((0, 0), " ", font=font)[0]
            word_widths = []
            for w in words:
                bbox = dummy_draw.textbbox((0, 0), w["word"], font=font)
                word_widths.append(bbox[2] - bbox[0])
            total_w = sum(word_widths) + space_w * (len(words) - 1)

        tx = (target_w - total_w) // 2
        ty = 890  # Lower-third optimal anchor

        # Render subtitle composite
        txt_layer = Image.new("RGBA", (target_w, target_h), (0, 0, 0, 0))
        shadow_layer = Image.new("RGBA", (target_w, target_h), (0, 0, 0, 0))
        tdraw = ImageDraw.Draw(txt_layer)
        sdraw = ImageDraw.Draw(shadow_layer)

        cur_x = tx
        for widx, w in enumerate(words):
            is_active = (widx == active_w_idx)
            text_col = (255, 209, 102, 255) if is_active else (255, 242, 168, 235)
            shadow_col = (10, 15, 20, 180)

            # Draw shadow
            sdraw.text((cur_x, ty + 4), w["word"], font=font, fill=shadow_col)
            # Draw text
            tdraw.text((cur_x, ty), w["word"], font=font, fill=text_col)

            cur_x += word_widths[widx] + space_w

        shadow_layer = shadow_layer.filter(ImageFilter.GaussianBlur(radius=6))
        text_composite = Image.alpha_composite(shadow_layer, txt_layer)
        
        # Convert to BGR numpy array with alpha for fast blending with OpenCV
        comp_np = np.array(text_composite)
        bgr = comp_np[:, :, :3][:, :, ::-1]  # RGB to BGR
        alpha = comp_np[:, :, 3].astype(np.float32) / 255.0

        subtitle_cache[cache_key] = (bgr, alpha)
        return bgr, alpha

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
    total_phrases = len(phrases)
    phrase_idx = 0

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

        # Generate base frame for current shot
        frame_curr = apply_ken_burns(cur_img, progress, cur_shot["motion"], target_w, target_h)

        # Check for transition into next shot
        if active_idx < total_shots - 1:
            trans_type = timeline_shots[active_idx + 1]["transition"]
            if trans_type == "snap":
                trans_dur = 0.0
            elif trans_type == "dissolve_act":
                trans_dur = 0.60
            else:
                trans_dur = 0.30

            time_to_end = cur_shot["end"] - t

            if time_to_end < trans_dur and trans_dur > 0:
                next_shot = timeline_shots[active_idx + 1]
                next_img = loaded_images.get(next_shot["shot_id"])
                next_progress = 0.0
                frame_next = apply_ken_burns(next_img, next_progress, next_shot["motion"], target_w, target_h)

                alpha_dissolve = 0.5 * (1.0 - math.cos(math.pi * (1.0 - time_to_end / trans_dur)))
                frame_final = cv2.addWeighted(frame_curr, 1.0 - alpha_dissolve, frame_next, alpha_dissolve, 0)
            else:
                frame_final = frame_curr
        else:
            frame_final = frame_curr

        # Subtitle overlay
        # Find active subtitle phrase
        while phrase_idx < total_phrases - 1 and t >= phrases[phrase_idx]["end"]:
            phrase_idx += 1

        cur_p = phrases[phrase_idx]
        if cur_p["start"] <= t <= cur_p["end"]:
            sub_bgr, sub_alpha = get_subtitle_layer(phrase_idx, t)
            # Alpha composite onto frame_final
            alpha_3d = sub_alpha[:, :, np.newaxis]
            frame_final = (frame_final * (1.0 - alpha_3d) + sub_bgr * alpha_3d).astype(np.uint8)

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
    print(f"[*] Copying final video to Downloads: {OUTPUT_DL}...")
    shutil.copy2(OUTPUT_WS, OUTPUT_DL)

    file_size_mb = OUTPUT_DL.stat().st_size / (1024 * 1024)
    print("\n" + "=" * 80)
    print("🎉 FULL MASTER CINEMATIC VIDEO (WITH CAPTIONS) READY!")
    print(f"• File Location: {OUTPUT_DL}")
    print(f"• File Size:     {file_size_mb:.2f} MB")
    print(f"• Resolution:    {target_w}x{target_h} (Full HD Widescreen @ 30 fps)")
    print(f"• Video Codec:   H.264 NVENC Studio Master (CQ 18, 14 Mbps)")
    print(f"• Audio Codec:   192 kbps Direct Studio Stream (1:1 Synchronized)")
    print(f"• Total Runtime: {total_audio_dur/60:.2f} Minutes ({total_audio_dur:.2f} Seconds)")
    print("=" * 80)

if __name__ == "__main__":
    main()
