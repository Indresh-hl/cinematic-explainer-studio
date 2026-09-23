import os
import subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

# Setup paths
base_img_path = "assets/images/cleaned/LINE_13-A.jpeg"
cutout_img_path = "assets/cutouts/LINE_13-A_cutout.png"
font_path = "assets/fonts/PlayfairDisplay.ttf"
audio_path = "assets/audio_test_line13.mp3"
output_video = "assets/LINE_13_VEED_MOTION_PREVIEW.mp4"

print("Loading base and cutout images...")
base_img = Image.open(base_img_path).convert("RGBA")
cutout_img = Image.open(cutout_img_path).convert("RGBA")

width, height = base_img.size
fps = 30
duration = 3.6  # First 3.6 seconds covers 'to understand why' -> 'the cringe strikes' -> 'at night,'
total_frames = int(fps * duration)

# Phrases with word-level timings
phrases = [
    {
        "start": 0.0,
        "end": 1.20,
        "words": [
            {"word": "to", "start": 0.0, "end": 0.48},
            {"word": "understand", "start": 0.48, "end": 0.96},
            {"word": "why", "start": 0.96, "end": 1.20}
        ]
    },
    {
        "start": 1.22,
        "end": 2.00,
        "words": [
            {"word": "the", "start": 1.22, "end": 1.42},
            {"word": "cringe", "start": 1.42, "end": 1.68},
            {"word": "strikes", "start": 1.68, "end": 2.00}
        ]
    },
    {
        "start": 2.02,
        "end": 3.60,
        "words": [
            {"word": "at", "start": 2.02, "end": 2.26},
            {"word": "night,", "start": 2.26, "end": 2.55}
        ]
    }
]

# FFmpeg subprocess to pipe raw frames
ffmpeg_cmd = [
    "ffmpeg", "-y",
    "-f", "rawvideo",
    "-vcodec", "rawvideo",
    "-s", f"{width}x{height}",
    "-pix_fmt", "rgba",
    "-r", str(fps),
    "-i", "-",
    "-i", audio_path,
    "-c:v", "libx264",
    "-pix_fmt", "yuv420p",
    "-crf", "17",
    "-preset", "fast",
    "-c:a", "aac",
    "-b:a", "192k",
    "-t", str(duration),
    "-shortest",
    output_video
]

print("Starting FFmpeg encoder...")
pipe = subprocess.Popen(ffmpeg_cmd, stdin=subprocess.PIPE)

font_size = 145
base_font = ImageFont.truetype(font_path, font_size)

print(f"Rendering {total_frames} frames with VEED-style behind-character motion...")

for frame_idx in range(total_frames):
    t = frame_idx / fps
    
    # Find active phrase
    active_phrase = None
    for p in phrases:
        if p["start"] <= t <= p["end"]:
            active_phrase = p
            break
            
    if active_phrase is None:
        # Just render base + cutout (or empty frame)
        comp = Image.alpha_composite(base_img, cutout_img)
        pipe.stdin.write(comp.tobytes())
        continue
        
    p_start = active_phrase["start"]
    p_end = active_phrase["end"]
    p_dur = p_end - p_start
    elapsed_in_p = t - p_start
    
    # 1. Entrance animation (first 0.20s): float up 16px and fade in
    float_duration = 0.20
    if elapsed_in_p < float_duration:
        norm_in = elapsed_in_p / float_duration
        ease_in = 1.0 - (1.0 - norm_in)**2  # Quad ease-out
        y_offset = int((1.0 - ease_in) * 16)
        alpha_mult = ease_in
    else:
        y_offset = 0
        alpha_mult = 1.0
        
    # 2. Exit animation (last 0.15s): fade out
    time_left = p_end - t
    if time_left < 0.15:
        alpha_mult = max(0.0, time_left / 0.15)
        
    # Text positioning
    words_list = active_phrase["words"]
    full_text = " ".join([w["word"] for w in words_list])
    
    # Measure full phrase width
    dummy_draw = ImageDraw.Draw(base_img)
    full_bbox = dummy_draw.textbbox((0, 0), full_text, font=base_font)
    total_w = full_bbox[2] - full_bbox[0]
    
    # Center horizontally, place at 32% vertically
    start_x = (width - total_w) // 2
    base_y = int(height * 0.32) + y_offset
    
    # Create text & shadow layers
    txt_layer = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    shadow_layer = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    tdraw = ImageDraw.Draw(txt_layer)
    sdraw = ImageDraw.Draw(shadow_layer)
    
    cur_x = start_x
    space_w = dummy_draw.textbbox((0, 0), " ", font=base_font)[2] - dummy_draw.textbbox((0, 0), " ", font=base_font)[0]
    
    for w_info in words_list:
        word = w_info["word"]
        w_start = w_info["start"]
        w_end = w_info["end"]
        
        # Is word active right now?
        is_active = (w_start <= t <= w_end + 0.1)
        has_passed = (t > w_end + 0.1)
        
        w_bbox = dummy_draw.textbbox((0, 0), word, font=base_font)
        word_w = w_bbox[2] - w_bbox[0]
        
        if is_active:
            # Active word: pop to bright warm gold with subtle scale
            word_color = (255, 230, 90, int(255 * alpha_mult))
            # Draw shadow
            sdraw.text((cur_x + 6, base_y + 10), word, font=base_font, fill=(50, 35, 15, int(90 * alpha_mult)))
            tdraw.text((cur_x, base_y), word, font=base_font, fill=word_color)
        else:
            # Inactive word: soft pastel butter cream
            word_color = (255, 243, 170, int(210 * alpha_mult))
            sdraw.text((cur_x + 5, base_y + 8), word, font=base_font, fill=(50, 35, 15, int(60 * alpha_mult)))
            tdraw.text((cur_x, base_y), word, font=base_font, fill=word_color)
            
        cur_x += word_w + space_w
        
    # Blur the shadow layer for soft ambient wall shadow
    shadow_blurred = shadow_layer.filter(ImageFilter.GaussianBlur(radius=10))
    
    # Sandwich compositing: Base -> Shadow -> Text -> Sam Cutout
    comp = Image.alpha_composite(base_img, shadow_blurred)
    comp = Image.alpha_composite(comp, txt_layer)
    final_frame = Image.alpha_composite(comp, cutout_img)
    
    pipe.stdin.write(final_frame.tobytes())

pipe.stdin.close()
pipe.wait()
print(f"DONE! Successfully generated: {output_video} ({os.path.getsize(output_video)} bytes)")
