import os
import re
import sys
import time
import shutil
import zipfile
import subprocess
from pathlib import Path
import cv2
import numpy as np
from PIL import Image
import gemini_watermark_remover as gwr

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent
DOWNLOADS_DIR = Path(r"c:\Users\Indresh HL\Downloads")
SRC_FILE = DOWNLOADS_DIR / "LINE_43-D_20260926203250.jpg"

HABITS_DIR = DOWNLOADS_DIR / "Habits"
RAW_DIR = HABITS_DIR / "raw"
CLEAN_DIR = HABITS_DIR / "cleaned"
RAW_UPSCALED_DIR = HABITS_DIR / "raw_upscaled"
FINAL_4K_DIR = HABITS_DIR / "4k"

PROD_DIR = BASE_DIR / "production" / "topic_02" / "images"
PROD_CLEAN_DIR = PROD_DIR / "cleaned"
PROD_4K_DIR = PROD_DIR / "4k"

ALL_CLEAN_ZIP = DOWNLOADS_DIR / "HABITS_ALL_IMAGES_CLEANED.zip"
ALL_4K_ZIP = DOWNLOADS_DIR / "HABITS_ALL_IMAGES_4K.zip"

REALESRGAN_EXE = BASE_DIR / "tools" / "realesrgan" / "realesrgan-ncnn-vulkan.exe"
TEMP_DIR = HABITS_DIR / "_temp_line_43d"
TEMP_CLEAN = TEMP_DIR / "clean"
TEMP_OUT = TEMP_DIR / "upscaled"

for d in [TEMP_CLEAN, TEMP_OUT, RAW_DIR, CLEAN_DIR, RAW_UPSCALED_DIR, FINAL_4K_DIR, PROD_CLEAN_DIR, PROD_4K_DIR]:
    d.mkdir(parents=True, exist_ok=True)

STEM = "LINE_43-D"

def main():
    t0 = time.time()
    print("=" * 70)
    print(f"PROCESSING {STEM}: WATERMARK REMOVAL + 4K VULKAN UPSCALE")
    print("=" * 70)

    # 1. Copy raw
    raw_dest = RAW_DIR / SRC_FILE.name
    shutil.copy2(SRC_FILE, raw_dest)
    print(f"Copied raw to: {raw_dest.name}")

    # 2. Watermark removal
    with open(SRC_FILE, "rb") as fp:
        buf = np.frombuffer(fp.read(), dtype=np.uint8)
    img = cv2.imdecode(buf, cv2.IMREAD_COLOR)

    remover = gwr.WatermarkRemover()
    alpha = remover.alpha_map_small  # 48x48
    alpha_padded = np.pad(alpha, 6, mode="constant")  # 60x60
    mask_star = (alpha_padded > 0.005).astype(np.uint8) * 255
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    dilated_star = cv2.dilate(mask_star, kernel, iterations=1)

    full_mask = np.zeros((768, 1376), dtype=np.uint8)
    full_mask[641:641+60, 1249:1249+60] = dilated_star

    roi = img[647:647+48, 1255:1255+48]
    blended_roi = remover.remove_watermark_from_region(roi, alpha)
    img_blended = img.copy()
    img_blended[647:647+48, 1255:1255+48] = blended_roi
    cleaned = cv2.inpaint(img_blended, full_mask, inpaintRadius=3, flags=cv2.INPAINT_TELEA)

    success, enc_buf = cv2.imencode('.jpeg', cleaned, [cv2.IMWRITE_JPEG_QUALITY, 100])
    clean_filename = f"{STEM}.jpeg"

    for dest_dir in [CLEAN_DIR, PROD_CLEAN_DIR, TEMP_CLEAN]:
        with open(dest_dir / clean_filename, "wb") as out_f:
            out_f.write(enc_buf)
    print(f"  [Cleaned] Watermark successfully removed -> {clean_filename}")

    # 3. Real-ESRGAN Vulkan GPU 4x upscale
    print("Launching Real-ESRGAN Vulkan GPU super-resolution...")
    t_up = time.time()
    cmd = [
        str(REALESRGAN_EXE),
        "-i", str(TEMP_CLEAN / clean_filename),
        "-o", str(TEMP_OUT / f"{STEM}.png"),
        "-n", "realesrgan-x4plus-anime",
        "-s", "4",
        "-f", "png",
        "-g", "0",
        "-j", "2:2:2"
    ]
    subprocess.run(cmd, check=True)
    print(f"  [Upscaled] 4x Vulkan GPU upscale completed in {time.time() - t_up:.1f}s!")

    up_png = TEMP_OUT / f"{STEM}.png"
    shutil.copy2(up_png, RAW_UPSCALED_DIR / f"{STEM}.png")

    # 4. Lanczos 4K Downsample (3840x2144)
    target_w, target_h = 3840, 2144
    out_name = f"{STEM}.jpg"
    with Image.open(up_png) as im:
        im_4k = im.resize((target_w, target_h), Image.Resampling.LANCZOS)
        im_4k.save(FINAL_4K_DIR / out_name, "JPEG", quality=100, subsampling=0)
        im_4k.save(PROD_4K_DIR / out_name, "JPEG", quality=100, subsampling=0)
    print(f"  [4K Master] {out_name} resampled to {target_w}x{target_h} (Quality 100, Subsampling 0)")

    # 5. Update master deliverable ZIPs
    all_clean = sorted(list(CLEAN_DIR.glob("*.jpeg")) + list(CLEAN_DIR.glob("*.jpg")))
    with zipfile.ZipFile(ALL_CLEAN_ZIP, "w", zipfile.ZIP_DEFLATED) as z:
        for f in all_clean:
            z.write(f, arcname=f.name)
    print(f"  -> Updated {ALL_CLEAN_ZIP.name} ({len(all_clean)} files, {ALL_CLEAN_ZIP.stat().st_size / (1024*1024):.2f} MB)")

    all_4k = sorted(list(FINAL_4K_DIR.glob("*.jpg")) + list(FINAL_4K_DIR.glob("*.jpeg")))
    with zipfile.ZipFile(ALL_4K_ZIP, "w", zipfile.ZIP_DEFLATED) as z:
        for f in all_4k:
            z.write(f, arcname=f.name)
    print(f"  -> Updated {ALL_4K_ZIP.name} ({len(all_4k)} files, {ALL_4K_ZIP.stat().st_size / (1024*1024):.2f} MB)")

    # Cleanup temp
    if TEMP_DIR.exists():
        shutil.rmtree(TEMP_DIR)

    print("=" * 70)
    print(f"LINE_43-D FULLY PROCESSED AND DELIVERED IN {time.time() - t0:.1f} SECONDS!")
    print("=" * 70)

if __name__ == "__main__":
    main()
