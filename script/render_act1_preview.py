import os
import sys
import json
import time
import subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

def main():
    print("=" * 70)
    print("[+] PREPARING ACT 1 MASTER PREVIEW (0:00 - 1:15)")
    print("=" * 70)

    base_dir = os.path.abspath(".")
    font_path = os.path.join(base_dir, "assets", "fonts", "PlayfairDisplay.ttf")
    word_timestamps_file = os.path.join(base_dir, "assets", "full_timeline_word_timestamps.json")
    audio_full = os.path.join(base_dir, "assets", "final_timeline_audio.aac")
    output_mp4 = os.path.join(base_dir, "assets", "ACT_1_MOTION_PREVIEW.mp4")
    downloads_mp4 = r"C:\Users\Indresh HL\Downloads\ACT_1_MOTION_PREVIEW.mp4"

    # 1. Load Word Timestamps from the master timeline
    with open(word_timestamps_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    # 2. Define Act 1 Shots mapping (0 to 75 seconds)
    # Matched directly from the exact cut timestamps of 0922 (1).mp4
    shots = [
        {"start": 0.00,  "end": 3.00,  "name": "LINE_1-A", "type": "prop",   "pos": (0.50, 0.76)},
        {"start": 3.00,  "end": 5.50,  "name": "LINE_1-B", "type": "bed",    "pos": (0.50, 0.06)},
        {"start": 5.50,  "end": 8.50,  "name": "LINE_2-A", "type": "close",  "pos": (0.58, 0.28)},
        {"start": 8.50,  "end": 12.75, "name": "LINE_2-B", "type": "bed_pr", "pos": (0.50, 0.16)},
        {"start": 12.75, "end": 16.50, "name": "LINE_3-A", "type": "char",   "pos": (0.46, 0.30)},
        {"start": 16.50, "end": 19.25, "name": "LINE_3-B", "type": "prop",   "pos": (0.50, 0.22)},
        {"start": 19.25, "end": 22.25, "name": "LINE_4-A", "type": "char",   "pos": (0.50, 0.24)},
        {"start": 22.25, "end": 26.50, "name": "LINE_5-B", "type": "prop",   "pos": (0.50, 0.20)},
        {"start": 26.50, "end": 36.25, "name": "LINE_6-A", "type": "char",   "pos": (0.58, 0.26)},
        {"start": 36.25, "end": 40.25, "name": "LINE_7-A", "type": "close",  "pos": (0.50, 0.16)},
        {"start": 40.25, "end": 42.50, "name": "LINE_7-B", "type": "char",   "pos": (0.50, 0.18)},
        {"start": 42.50, "end": 46.00, "name": "LINE_7-C", "type": "char",   "pos": (0.50, 0.20)},
        {"start": 46.00, "end": 51.50, "name": "LINE_8-A", "type": "char",   "pos": (0.50, 0.28)},
        {"start": 51.50, "end": 54.75, "name": "LINE_9-A", "type": "char",   "pos": (0.50, 0.22)},
        {"start": 54.75, "end": 57.00, "name": "LINE_9-B", "type": "char",   "pos": (0.50, 0.24)},
        {"start": 57.00, "end": 60.00, "name": "LINE_9-C", "type": "prop",   "pos": (0.50, 0.22)},
        {"start": 60.00, "end": 64.00, "name": "LINE_10-A","type": "char",   "pos": (0.50, 0.26)},
        {"start": 64.00, "end": 67.25, "name": "LINE_10-B","type": "prop",   "pos": (0.50, 0.22)},
        {"start": 67.25, "end": 72.00, "name": "LINE_11-A","type": "char",   "pos": (0.50, 0.26)},
        {"start": 72.00, "end": 75.00, "name": "LINE_12-A","type": "prop",   "pos": (0.50, 0.20)}
    ]

    # 3. Define Phrase Cards with Word-Level timings from transcript
    # Segmented into 2-4 word natural chunks
    phrases = []
    for seg in data["segments"]:
        if seg["start"] >= 75.0:
            break
        words = seg["words"]
        if not words:
            continue
            
        # Chunk words into groups of 2-4
        chunk_size = 3
        if len(words) <= 4:
            phrases.append({
                "start": words[0]["start"],
                "end": words[-1]["end"] + 0.25,
                "words": words
            })
        else:
            # Split into chunks of 2-3 words
            i = 0
            while i < len(words):
                # If remaining is 4, split 2 and 2
                remaining = len(words) - i
                if remaining == 4:
                    take = 2
                elif remaining > 4:
                    take = 3
                else:
                    take = remaining
                chunk = words[i:i+take]
                phrases.append({
                    "start": chunk[0]["start"],
                    "end": chunk[-1]["end"] + (0.25 if i+take >= len(words) else 0.05),
                    "words": chunk
                })
                i += take

    print(f"[*] Total phrases compiled for Act 1: {len(phrases)}")

    # 4. Target Dimensions & Pre-Loading Images
    # Target resolution: 1934x1080 (matching user's video exactly)
    target_w, target_h = 1934, 1080
    fps = 30
    total_duration = 75.0
    total_frames = int(fps * total_duration)

    print(f"[*] Pre-loading 4K assets & cutouts for {len(shots)} shots...")
    cached_shots = {}
    for s in shots:
        name = s["name"]
        if name in cached_shots:
            continue
            
        # Load background from 4K images
        img_4k_path = os.path.join(base_dir, "assets", "images", "4k", f"{name}.jpg")
        if not os.path.exists(img_4k_path):
            img_4k_path = os.path.join(base_dir, "assets", "images", "cleaned", f"{name}.jpeg")
            
        bg_im = Image.open(img_4k_path).convert("RGBA").resize((target_w, target_h), Image.Resampling.LANCZOS)
        
        # Load cutout if character
        cutout_im = None
        cutout_path = os.path.join(base_dir, "assets", "cutouts", f"{name}_cutout.png")
        if os.path.exists(cutout_path):
            cutout_im = Image.open(cutout_path).convert("RGBA").resize((target_w, target_h), Image.Resampling.LANCZOS)
            
        cached_shots[name] = {
            "bg": bg_im,
            "cutout": cutout_im,
            "pos": s["pos"]
        }

    font_size = 105
    font = ImageFont.truetype(font_path, font_size)

    # 5. Setup FFmpeg video encoder pipe
    cmd = [
        "ffmpeg", "-y",
        "-f", "rawvideo",
        "-vcodec", "rawvideo",
        "-s", f"{target_w}x{target_h}",
        "-pix_fmt", "rgba",
        "-r", str(fps),
        "-i", "-",
        "-ss", "0.0",
        "-t", str(total_duration),
        "-i", audio_full,
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-crf", "16",
        "-preset", "fast",
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        output_mp4
    ]

    print(f"[*] Starting FFmpeg encoder for {total_frames} frames ({total_duration}s)...")
    pipe = subprocess.Popen(cmd, stdin=subprocess.PIPE)

    t0_render = time.time()
    last_report = 0

    for frame_idx in range(total_frames):
        t = frame_idx / fps
        
        # Find active shot
        active_shot = None
        for s in shots:
            if s["start"] <= t < s["end"]:
                active_shot = s
                break
        if active_shot is None:
            active_shot = shots[-1]
            
        shot_data = cached_shots[active_shot["name"]]
        base_im = shot_data["bg"]
        cutout_im = shot_data["cutout"]
        pos_x_ratio, pos_y_ratio = shot_data["pos"]
        
        # Find active phrase
        active_phrase = None
        for p in phrases:
            if p["start"] <= t <= p["end"]:
                active_phrase = p
                break
                
        if active_phrase is None:
            # No text in this frame
            if cutout_im:
                frame_out = Image.alpha_composite(base_im, cutout_im)
            else:
                frame_out = base_im
            pipe.stdin.write(frame_out.tobytes())
            continue
            
        # Animate active phrase
        p_start = active_phrase["start"]
        p_end = active_phrase["end"]
        elapsed = t - p_start
        time_left = p_end - t
        
        # Entrance float (first 0.18s)
        if elapsed < 0.18:
            norm_in = elapsed / 0.18
            ease_in = 1.0 - (1.0 - norm_in)**2
            y_float = int((1.0 - ease_in) * 12)
            alpha_mult = ease_in
        else:
            y_float = 0
            alpha_mult = 1.0
            
        # Exit fade (last 0.12s)
        if time_left < 0.12:
            alpha_mult = max(0.0, time_left / 0.12)
            
        words = active_phrase["words"]
        phrase_text = " ".join([w["word"] for w in words])
        
        # Measure phrase width
        dummy = ImageDraw.Draw(base_im)
        full_bbox = dummy.textbbox((0, 0), phrase_text, font=font)
        pw = full_bbox[2] - full_bbox[0]
        ph = full_bbox[3] - full_bbox[1]
        
        # Compute coordinates
        if pos_x_ratio == 0.50:
            tx = (target_w - pw) // 2
        else:
            tx = int(target_w * pos_x_ratio)
            
        ty = int(target_h * pos_y_ratio) + y_float
        
        txt_layer = Image.new("RGBA", (target_w, target_h), (0, 0, 0, 0))
        shadow_layer = Image.new("RGBA", (target_w, target_h), (0, 0, 0, 0))
        tdraw = ImageDraw.Draw(txt_layer)
        sdraw = ImageDraw.Draw(shadow_layer)
        
        cur_x = tx
        space_w = dummy.textbbox((0, 0), " ", font=font)[2] - dummy.textbbox((0, 0), " ", font=font)[0]
        
        for w_data in words:
            word = w_data["word"]
            w_start = w_data["start"]
            w_end = w_data["end"]
            
            is_active = (w_start <= t <= w_end + 0.08)
            
            w_bbox = dummy.textbbox((0, 0), word, font=font)
            ww = w_bbox[2] - w_bbox[0]
            
            if is_active:
                # Active word: Sunglow Gold Pop #FFD166
                color = (255, 209, 102, int(255 * alpha_mult))
                sdraw.text((cur_x + 5, ty + 7), word, font=font, fill=(15, 20, 30, int(110 * alpha_mult)))
                tdraw.text((cur_x, ty), word, font=font, fill=color)
            else:
                # Inactive word: Warm Butter Cream #FFF2A8
                color = (255, 242, 168, int(210 * alpha_mult))
                sdraw.text((cur_x + 4, ty + 6), word, font=font, fill=(15, 20, 30, int(75 * alpha_mult)))
                tdraw.text((cur_x, ty), word, font=font, fill=color)
                
            cur_x += ww + space_w
            
        # Ambient shadow blur
        shadow_blurred = shadow_layer.filter(ImageFilter.GaussianBlur(radius=8))
        
        # 3-Layer Sandwich Compositing
        comp = Image.alpha_composite(base_im, shadow_blurred)
        comp = Image.alpha_composite(comp, txt_layer)
        if cutout_im:
            comp = Image.alpha_composite(comp, cutout_im)
            
        pipe.stdin.write(comp.tobytes())
        
        if frame_idx % 150 == 0:
            print(f"  [Render Progress] Frame {frame_idx}/{total_frames} ({frame_idx/total_frames*100:.1f}%) | Time: {t:.1f}s")

    pipe.stdin.close()
    pipe.wait()
    
    # Copy to Downloads folder
    import shutil
    shutil.copy(output_mp4, downloads_mp4)
    
    print("\n" + "=" * 70)
    print(f"[SUCCESS] Act 1 Master Preview Generated in {time.time() - t0_render:.1f}s!")
    print(f"  Output Workspace: {output_mp4}")
    print(f"  Output Downloads: {downloads_mp4} ({os.path.getsize(downloads_mp4)/(1024*1024):.2f} MB)")
    print("=" * 70)

if __name__ == "__main__":
    main()
