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

HABITS_DIR = DOWNLOADS_DIR / "Habits"
RAW_DIR = HABITS_DIR / "raw"
CLEAN_DIR = HABITS_DIR / "cleaned"
RAW_UPSCALED_DIR = HABITS_DIR / "raw_upscaled"
FINAL_4K_DIR = HABITS_DIR / "4k"

PROD_DIR = BASE_DIR / "production" / "topic_02" / "images"
PROD_CLEAN_DIR = PROD_DIR / "cleaned"
PROD_4K_DIR = PROD_DIR / "4k"

CLEAN_ZIP_OUT = DOWNLOADS_DIR / "HABITS_ALL_IMAGES_CLEANED.zip"
FINAL_4K_ZIP_OUT = DOWNLOADS_DIR / "HABITS_ALL_IMAGES_4K.zip"

REALESRGAN_EXE = BASE_DIR / "tools" / "realesrgan" / "realesrgan-ncnn-vulkan.exe"
TEMP_DIR = HABITS_DIR / "_temp_19a"
TEMP_CLEAN = TEMP_DIR / "clean"
TEMP_OUT = TEMP_DIR / "upscaled"

TEMP_CLEAN.mkdir(parents=True, exist_ok=True)
TEMP_OUT.mkdir(parents=True, exist_ok=True)

target_file = "LINE_19-A_20260924085752.jpeg"
clean_stem = "LINE_19-A"

def process_19a():
    t_start = time.time()
    print("=" * 70)
    print("STEP 1: COPY RAW AND CLEAN GEMINI WATERMARK FOR LINE_19-A")
    print("=" * 70)

    src_path = DOWNLOADS_DIR / target_file
    if not src_path.exists():
        raise FileNotFoundError(f"File {src_path} not found!")

    # Copy raw to RAW_DIR
    raw_dest = RAW_DIR / target_file
    shutil.copy2(src_path, raw_dest)
    print(f"Copied raw to: {raw_dest.name}")

    # Read binary for robust decoding
    with open(src_path, "rb") as fp:
        buf = np.frombuffer(fp.read(), dtype=np.uint8)
    img = cv2.imdecode(buf, cv2.IMREAD_COLOR)
    h, w = img.shape[:2]
    print(f"Loaded image: {w}x{h}")

    # Watermark removal
    remover = gwr.WatermarkRemover()
    alpha = remover.alpha_map_small  # 48x48
    alpha_padded = np.pad(alpha, 6, mode="constant")  # 60x60
    mask_star = (alpha_padded > 0.005).astype(np.uint8) * 255
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    dilated_star = cv2.dilate(mask_star, kernel, iterations=1)

    full_mask = np.zeros((768, 1376), dtype=np.uint8)
    full_mask[641:641+60, 1249:1249+60] = dilated_star

    # Reverse alpha blend on 48x48 core
    roi = img[647:647+48, 1255:1255+48]
    blended_roi = remover.remove_watermark_from_region(roi, alpha)
    img_blended = img.copy()
    img_blended[647:647+48, 1255:1255+48] = blended_roi

    # Telea inpainting on 60x60 perimeter
    cleaned = cv2.inpaint(img_blended, full_mask, inpaintRadius=3, flags=cv2.INPAINT_TELEA)

    # Save to clean destinations
    success, enc_buf = cv2.imencode('.jpeg', cleaned, [cv2.IMWRITE_JPEG_QUALITY, 100])
    clean_filename = f"{clean_stem}.jpeg"

    for dest_dir in [CLEAN_DIR, PROD_CLEAN_DIR, TEMP_CLEAN]:
        with open(dest_dir / clean_filename, "wb") as out_f:
            out_f.write(enc_buf)
    print(f"Saved cleaned: {clean_filename} (100% Quality JPEG)")

    print("\n" + "=" * 70)
    print("STEP 2: REAL-ESRGAN VULKAN GPU SUPER-RESOLUTION (4x)")
    print("=" * 70)
    cmd = [
        str(REALESRGAN_EXE),
        "-i", str(TEMP_CLEAN),
        "-o", str(TEMP_OUT),
        "-n", "realesrgan-x4plus-anime",
        "-s", "4",
        "-f", "png",
        "-g", "0",
        "-j", "2:2:2"
    ]
    t0 = time.time()
    subprocess.run(cmd, check=True)
    print(f"Vulkan GPU super-resolution finished in {time.time() - t0:.1f} seconds!")

    up_png = TEMP_OUT / f"{clean_stem}.png"
    dest_up = RAW_UPSCALED_DIR / f"{clean_stem}.png"
    shutil.copy2(up_png, dest_up)
    print(f"Saved 5504x3072 upscaled PNG: {dest_up.name}")

    print("\n" + "=" * 70)
    print("STEP 3: 4K LANCZOS DOWNSAMPLING (3840x2144)")
    print("=" * 70)
    target_w = 3840
    target_h = 2144
    out_name = f"{clean_stem}.jpg"
    out_habits = FINAL_4K_DIR / out_name
    out_prod = PROD_4K_DIR / out_name

    with Image.open(dest_up) as im:
        im_4k = im.resize((target_w, target_h), Image.Resampling.LANCZOS)
        im_4k.save(out_habits, "JPEG", quality=100, subsampling=0)
        im_4k.save(out_prod, "JPEG", quality=100, subsampling=0)
    print(f"Saved 4K Master: {out_name} (3840x2144, Quality 100, Subsampling 0)")

    print("\n" + "=" * 70)
    print("STEP 4: REPACKAGING MASTER DELIVERABLE ZIPS")
    print("=" * 70)
    all_clean = sorted(list(CLEAN_DIR.glob("*.jpeg")) + list(CLEAN_DIR.glob("*.jpg")))
    with zipfile.ZipFile(CLEAN_ZIP_OUT, "w", zipfile.ZIP_DEFLATED) as z:
        for f in all_clean:
            z.write(f, arcname=f.name)
    clean_size_mb = CLEAN_ZIP_OUT.stat().st_size / (1024 * 1024)
    print(f"Updated {CLEAN_ZIP_OUT.name}: {len(all_clean)} files ({clean_size_mb:.2f} MB)")

    all_4k = sorted(list(FINAL_4K_DIR.glob("*.jpg")) + list(FINAL_4K_DIR.glob("*.jpeg")))
    with zipfile.ZipFile(FINAL_4K_ZIP_OUT, "w", zipfile.ZIP_DEFLATED) as z:
        for f in all_4k:
            z.write(f, arcname=f.name)
    k4_size_mb = FINAL_4K_ZIP_OUT.stat().st_size / (1024 * 1024)
    print(f"Updated {FINAL_4K_ZIP_OUT.name}: {len(all_4k)} files ({k4_size_mb:.2f} MB)")

    # Cleanup temp
    if TEMP_DIR.exists():
        shutil.rmtree(TEMP_DIR)
        print("Cleaned up temporary working directory.")

    print("\n" + "=" * 70)
    print(f"LINE_19-A FULLY PROCESSED, UPSCALED, AND DELIVERED IN {time.time() - t_start:.1f} SECONDS!")
    print("=" * 70)

if __name__ == "__main__":
    process_19a()
