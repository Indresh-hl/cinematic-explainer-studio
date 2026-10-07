import os
import sys
import json
import time
import shutil
import subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

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

    # Snap phrase boundaries to visual cuts to prevent premature subtitle flashing and duplicate appearances
    if shots:
        cut_times = [s["end"] for s in shots[:-1]]
        for p in phrases:
            for cut_t in cut_times:
                # If a phrase starts within 0.35s before a cut, snap its start to the cut so it starts cleanly on the new shot
                if 0 < (cut_t - p["start"]) < 0.35:
                    p["start"] = cut_t
                # If a phrase ends within 0.20s after a cut, clamp its end to the cut so it doesn't leave orphan frames on the new shot
                if 0 < (p["end"] - cut_t) < 0.20:
                    p["end"] = cut_t

    return phrases

def main():
    print("=" * 75)
    print("[+] STARTING FULL TOPIC 02 MASTER 4K VIDEO RENDER WITH 3D DEPTH CAPTIONS")
    print("=" * 75)
    sys.stdout.flush()

    base_dir = os.path.abspath(".")
    font_path = os.path.join(base_dir, "assets", "fonts", "PlayfairDisplay.ttf")
    word_timestamps_file = os.path.join(base_dir, "production", "topic_02", "audio", "full_timeline_word_timestamps.json")
    shots_file = os.path.join(base_dir, "production", "topic_02", "all_timeline_shots.json")
    audio_full = os.path.join(base_dir, "production", "topic_02", "audio", "final_timeline_audio.m4a")
    
    os.makedirs(os.path.join(base_dir, "production", "topic_02", "renders"), exist_ok=True)
    output_mp4 = os.path.join(base_dir, "production", "topic_02", "renders", "FINAL_4K_MASTER_VIDEO_TOPIC_02.mp4")
    downloads_mp4 = r"C:\Users\Indresh HL\Downloads\FINAL_4K_MASTER_VIDEO_TOPIC_02.mp4"
    ready_mp4 = r"C:\Users\Indresh HL\Downloads\READY IT UPLOAD\FINAL_4K_MASTER_VIDEO_TOPIC_02.mp4"

    # 1. Load shots & phrases
    with open(shots_file, "r") as f:
        shots = json.load(f)
    with open(word_timestamps_file, "r", encoding="utf-8") as f:
        word_data = json.load(f)

    phrases = build_adaptive_phrases(word_data, shots)
    print(f"[*] Total timeline shots: {len(shots)}")
    print(f"[*] Total phrases compiled: {len(phrases)}")

    target_w, target_h = 1934, 1080
    fps = 30
    total_duration = shots[-1]["end"]
    total_frames = int(round(fps * total_duration))
    print(f"[*] Canvas: {target_w}x{target_h} @ {fps} fps | Duration: {total_duration:.2f}s ({total_frames} frames)")
    sys.stdout.flush()

    # 2. Known shot classifications
    bed_shots = {
        "LINE_01-A", "LINE_01-B", "LINE_02-A", "LINE_04-A", "LINE_04-B",
        "LINE_35-A", "LINE_35-A_2", "LINE_35-B", "LINE_35-B_2",
        "LINE_50-A", "LINE_50-B",
        "Character_experiencing_anxiety_in_bed", "Man_pulling_duvet_to_nose"
    }

    # 3. Pre-load assets
    print("[*] Pre-loading 4K backgrounds and alpha cutouts...")
    sys.stdout.flush()
    cached_shots = {}
    
    for s in shots:
        name = s["name"]
        if name in cached_shots:
            continue
            
        # Priority order for background
        bg_paths = [
            os.path.join(base_dir, "production", "topic_02", "images", "4k", f"{name}.jpg"),
            os.path.join(r"C:\Users\Indresh HL\Downloads\Habits\4k", f"{name}.jpg"),
            os.path.join(base_dir, "production", "topic_02", "images", "cleaned", f"{name}.jpeg"),
            os.path.join(r"C:\Users\Indresh HL\Downloads\Habits\cleaned", f"{name}.jpeg")
        ]
        
        bg_path = None
        for p in bg_paths:
            if os.path.exists(p):
                bg_path = p
                break
                
        if not bg_path:
            print(f"[!] Warning: Image for {name} not found, checking alternatives...")
            continue
            
        bg_im = Image.open(bg_path).convert("RGBA").resize((target_w, target_h), Image.Resampling.LANCZOS)
        
        cutout_path = os.path.join(base_dir, "production", "topic_02", "cutouts", f"{name}_cutout.png")
        cutout_im = None
        alpha_arr = None
        base_with_cutout = bg_im
        if os.path.exists(cutout_path):
            cutout_im = Image.open(cutout_path).convert("RGBA").resize((target_w, target_h), Image.Resampling.LANCZOS)
            alpha_arr = np.array(cutout_im.split()[-1])
            base_with_cutout = Image.alpha_composite(bg_im, cutout_im)
            
        cached_shots[name] = {
            "bg": bg_im,
            "cutout": cutout_im,
            "base_with_cutout": base_with_cutout,
            "alpha": alpha_arr,
            "is_bed": (name in bed_shots)
        }

    print(f"[*] Pre-loaded {len(cached_shots)} unique shots successfully.")
    sys.stdout.flush()

    # 4. Setup FFmpeg NVENC encoder
    cmd = [
        "ffmpeg", "-y",
        "-f", "rawvideo",
        "-vcodec", "rawvideo",
        "-s", f"{target_w}x{target_h}",
        "-pix_fmt", "rgba",
        "-r", str(fps),
        "-i", "-",
        "-i", audio_full,
        "-c:v", "h264_nvenc",
        "-pix_fmt", "yuv420p",
        "-preset", "p4",
        "-rc", "vbr",
        "-cq", "18",
        "-b:v", "12M",
        "-c:a", "copy",
        "-shortest",
        output_mp4
    ]

    print("[*] Launching hardware NVENC encoder...")
    sys.stdout.flush()
    pipe = subprocess.Popen(cmd, stdin=subprocess.PIPE)

    # 5. Phrase & Subtitle Placement Optimizer Cache
    phrase_render_cache = {}
    base_font_size = 88
    base_font = ImageFont.truetype(font_path, base_font_size)
    dummy_img = Image.new("RGBA", (100, 100))
    dummy_draw = ImageDraw.Draw(dummy_img)

    def get_phrase_rendering(p_idx, phrase, shot_info):
        is_bed = shot_info["is_bed"]
        alpha = shot_info["alpha"]
        words = phrase["words"]
        full_text = phrase["text"]

        bbox = dummy_draw.textbbox((0, 0), full_text, font=base_font)
        pw = bbox[2] - bbox[0]
        ph = bbox[3] - bbox[1]

        max_allowed_w = 780
        if is_bed:
            max_allowed_w = 1400

        font = base_font
        if pw > max_allowed_w:
            scaled_size = max(68, int(base_font_size * (max_allowed_w / pw)))
            font = ImageFont.truetype(font_path, scaled_size)
            bbox = dummy_draw.textbbox((0, 0), full_text, font=font)
            pw = bbox[2] - bbox[0]
            ph = bbox[3] - bbox[1]

        render_in_front = False
        if is_bed:
            tx = (target_w - pw) // 2
            ty = 65
        elif alpha is None:
            tx = (target_w - pw) // 2
            ty = 180
        else:
            cand_left = (120, 230)
            cand_right = (target_w - pw - 120, 230)
            cand_top = ((target_w - pw) // 2, 75)

            def eval_occ(cx, cy):
                clamped_x = max(0, min(target_w - pw, cx))
                clamped_y = max(0, min(target_h - ph, cy))
                sub_a = alpha[clamped_y : clamped_y + ph, clamped_x : clamped_x + pw]
                return (sub_a > 128).mean(), clamped_x, clamped_y

            occ_l, xl, yl = eval_occ(*cand_left)
            occ_r, xr, yr = eval_occ(*cand_right)
            occ_t, xt, yt = eval_occ(*cand_top)

            candidates = [
                (occ_l, 0, xl, yl),
                (occ_r, 1, xr, yr),
                (occ_t, 2, xt, yt),
            ]
            valid = [c for c in candidates if c[0] <= 0.20]
            if valid:
                valid.sort(key=lambda c: (round(c[0], 2), c[1]))
                best = valid[0]
                tx, ty = best[2], best[3]
            else:
                # Occlusion > 20% on all background positions -> 100% legibility rule in front
                tx, ty = cand_top[0], cand_top[1]
                render_in_front = True

        return {
            "tx": tx,
            "ty": ty,
            "pw": pw,
            "ph": ph,
            "font": font,
            "render_in_front": render_in_front
        }

    # 6. Render Loop
    print(f"[*] Rendering {total_frames} frames ({total_duration:.2f}s)...")
    sys.stdout.flush()
    t0_render = time.time()
    active_shot_idx = 0
    active_phrase_idx = 0

    for frame_idx in range(total_frames):
        t = frame_idx / fps

        # Advance active shot
        while active_shot_idx < len(shots) - 1 and t >= shots[active_shot_idx]["end"]:
            active_shot_idx += 1
        current_shot = shots[active_shot_idx]
        shot_data = cached_shots[current_shot["name"]]
        base_im = shot_data["bg"]
        cutout_im = shot_data["cutout"]
        base_with_cutout = shot_data["base_with_cutout"]

        # Advance active phrase
        while active_phrase_idx < len(phrases) - 1 and t > phrases[active_phrase_idx]["end"]:
            active_phrase_idx += 1
            
        cur_p = phrases[active_phrase_idx]
        is_phrase_active = (cur_p["start"] <= t <= cur_p["end"])

        if not is_phrase_active:
            pipe.stdin.write(base_with_cutout.tobytes())
            continue

        layout = get_phrase_rendering(active_phrase_idx, cur_p, shot_data)
        tx = layout["tx"]
        ty = layout["ty"]
        pfont = layout["font"]
        render_in_front = layout["render_in_front"]

        # Animation timing
        p_start = cur_p["start"]
        p_end = cur_p["end"]
        elapsed = t - p_start
        time_left = p_end - t

        # Float entrance (+10px -> 0px) over first 0.16s
        if elapsed < 0.16:
            norm_in = elapsed / 0.16
            ease_in = 1.0 - (1.0 - norm_in)**2
            y_float = int((1.0 - ease_in) * 10)
            alpha_mult = ease_in
        else:
            y_float = 0
            alpha_mult = 1.0

        # Exit fade over last 0.10s
        if time_left < 0.10:
            alpha_mult = max(0.0, time_left / 0.10)

        # Identify active word index
        active_w_idx = -1
        for widx, w_data in enumerate(cur_p["words"]):
            if w_data["start"] <= t <= w_data["end"] + 0.08:
                active_w_idx = widx
                break

        # Check sub-phrase render cache
        cache_key = (active_phrase_idx, active_w_idx, current_shot["name"])
        if cache_key not in phrase_render_cache:
            txt_layer = Image.new("RGBA", (target_w, target_h), (0, 0, 0, 0))
            shadow_layer = Image.new("RGBA", (target_w, target_h), (0, 0, 0, 0))
            tdraw = ImageDraw.Draw(txt_layer)
            sdraw = ImageDraw.Draw(shadow_layer)

            cur_x = tx
            space_w = dummy_draw.textbbox((0, 0), " ", font=pfont)[2] - dummy_draw.textbbox((0, 0), " ", font=pfont)[0]

            for widx, w_data in enumerate(cur_p["words"]):
                w_str = w_data["word"]
                is_active = (widx == active_w_idx)
                w_bbox = dummy_draw.textbbox((0, 0), w_str, font=pfont)
                w_w = w_bbox[2] - w_bbox[0]

                # Colors: Warm Butter Cream for passive, Sunglow Gold for active
                text_col = (255, 209, 102, 255) if is_active else (255, 242, 168, 220)
                shadow_col = (15, 20, 30, 160)

                # Draw shadow
                sdraw.text((cur_x, ty + 4), w_str, font=pfont, fill=shadow_col)
                # Draw text
                tdraw.text((cur_x, ty), w_str, font=pfont, fill=text_col)

                cur_x += w_w + space_w

            # Diffuse the shadow
            shadow_layer = shadow_layer.filter(ImageFilter.GaussianBlur(radius=8))
            combined_text = Image.alpha_composite(shadow_layer, txt_layer)
            phrase_render_cache[cache_key] = combined_text

        cached_text_shadow = phrase_render_cache[cache_key]

        # Apply float entrance / fade opacity if animating
        if y_float != 0 or alpha_mult < 0.98:
            trans_layer = Image.new("RGBA", (target_w, target_h), (0, 0, 0, 0))
            trans_layer.paste(cached_text_shadow, (0, y_float))
            if alpha_mult < 0.98:
                r, g, b, a = trans_layer.split()
                a = a.point(lambda p: int(p * alpha_mult))
                trans_layer.putalpha(a)
            use_layer = trans_layer
        else:
            use_layer = cached_text_shadow

        # Layer Compositing: 80/20 Depth Rule
        if cutout_im and not render_in_front:
            # 3D Depth Sandwich: BG -> TextWithShadow -> Cutout
            comp = Image.alpha_composite(base_im, use_layer)
            comp = Image.alpha_composite(comp, cutout_im)
        else:
            # In Front: BaseWithCutout -> TextWithShadow
            comp = Image.alpha_composite(base_with_cutout, use_layer)

        pipe.stdin.write(comp.tobytes())

        if frame_idx % 600 == 0 or frame_idx == total_frames - 1:
            fps_current = frame_idx / max(0.01, time.time() - t0_render)
            pct = frame_idx / total_frames * 100
            eta = (total_frames - frame_idx) / max(1.0, fps_current)
            print(f"  [Render] Frame {frame_idx:5d}/{total_frames} ({pct:5.1f}%) | Time: {t:5.1f}s | Speed: {fps_current:5.1f} fps | ETA: {eta:.0f}s")
            sys.stdout.flush()

    pipe.stdin.close()
    pipe.wait()

    render_time = time.time() - t0_render
    print("\n" + "=" * 75)
    print(f"[SUCCESS] Master Video Rendered in {render_time:.1f}s ({render_time/60:.2f} mins)!")
    print(f"  Average Encoding Speed: {total_frames / render_time:.1f} fps")
    
    # Copy to Downloads destinations
    print(f"[*] Copying to {downloads_mp4}...")
    shutil.copy(output_mp4, downloads_mp4)
    print(f"[*] Copying to {ready_mp4}...")
    shutil.copy(output_mp4, ready_mp4)
    
    file_size_mb = os.path.getsize(output_mp4) / (1024 * 1024)
    print(f"  Final File Size: {file_size_mb:.2f} MB")
    print(f"  Downloads Output: {downloads_mp4}")
    print(f"  Ready Upload Output: {ready_mp4}")
    print("=" * 75)

if __name__ == "__main__":
    main()
