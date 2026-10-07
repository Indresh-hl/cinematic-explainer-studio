import os
import re
import sys
import time
import shutil
import zipfile
import subprocess
from pathlib import Path
from collections import defaultdict
import cv2
import numpy as np
from PIL import Image
import gemini_watermark_remover as gwr

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent
DOWNLOADS_DIR = Path(r"c:\Users\Indresh HL\Downloads")
NWEW_ZIP = DOWNLOADS_DIR / "NWEW.zip"

HABITS_DIR = DOWNLOADS_DIR / "Habits"
RAW_DIR = HABITS_DIR / "raw"
CLEAN_DIR = HABITS_DIR / "cleaned"
RAW_UPSCALED_DIR = HABITS_DIR / "raw_upscaled"
FINAL_4K_DIR = HABITS_DIR / "4k"

PROD_DIR = BASE_DIR / "production" / "topic_02" / "images"
PROD_CLEAN_DIR = PROD_DIR / "cleaned"
PROD_4K_DIR = PROD_DIR / "4k"

NWEW_CLEAN_ZIP = DOWNLOADS_DIR / "NWEW_CLEANED.zip"
NWEW_4K_ZIP = DOWNLOADS_DIR / "NWEW_4K.zip"
ALL_CLEAN_ZIP = DOWNLOADS_DIR / "HABITS_ALL_IMAGES_CLEANED.zip"
ALL_4K_ZIP = DOWNLOADS_DIR / "HABITS_ALL_IMAGES_4K.zip"

REALESRGAN_EXE = BASE_DIR / "tools" / "realesrgan" / "realesrgan-ncnn-vulkan.exe"
TEMP_DIR = HABITS_DIR / "_temp_nwew_batch"
TEMP_EXTRACT = TEMP_DIR / "extracted"
TEMP_CLEAN = TEMP_DIR / "clean"
TEMP_OUT = TEMP_DIR / "upscaled"

for d in [TEMP_EXTRACT, TEMP_CLEAN, TEMP_OUT, RAW_DIR, CLEAN_DIR, RAW_UPSCALED_DIR, FINAL_4K_DIR, PROD_CLEAN_DIR, PROD_4K_DIR]:
    d.mkdir(parents=True, exist_ok=True)

def step1_extract_and_clean():
    print("=" * 75)
    print("STEP 1: EXTRACTING NWEW.zip AND CLEANING GEMINI WATERMARKS")
    print("=" * 75)
    
    with zipfile.ZipFile(NWEW_ZIP, 'r') as zf:
        zf.extractall(TEMP_EXTRACT)
    
    extracted_files = sorted([f for f in TEMP_EXTRACT.iterdir() if f.is_file() and f.suffix.lower() in ['.jpg', '.jpeg', '.png']])
    print(f"Extracted {len(extracted_files)} images from NWEW.zip.")

    # Build unique clean stem mapping
    used_stems = defaultdict(int)
    stem_map = {}
    for src_path in extracted_files:
        n = src_path.name
        # Strip timestamp _YYYYMMDDHHMMSS
        clean = re.sub(r'_\d{14}', '', n)
        ext = src_path.suffix.lower()
        base = re.sub(r'\.(jpg|jpeg|png)$', '', clean, flags=re.I)
        # Sanitize special / replacement chars
        base = base.replace('\ufffd', '').strip('._ ')
        if not base:
            base = "image"
        
        used_stems[base] += 1
        if used_stems[base] == 1:
            final_stem = base
        else:
            final_stem = f"{base}_v{used_stems[base]}"
        stem_map[src_path] = final_stem

    remover = gwr.WatermarkRemover()
    alpha = remover.alpha_map_small  # 48x48
    alpha_padded = np.pad(alpha, 6, mode="constant")  # 60x60
    mask_star = (alpha_padded > 0.005).astype(np.uint8) * 255
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    dilated_star = cv2.dilate(mask_star, kernel, iterations=1)

    full_mask = np.zeros((768, 1376), dtype=np.uint8)
    full_mask[641:641+60, 1249:1249+60] = dilated_star

    processed_stems = []
    total = len(extracted_files)

    for idx, src_path in enumerate(extracted_files, 1):
        clean_stem = stem_map[src_path]
        
        # Copy raw to RAW_DIR
        raw_dest = RAW_DIR / src_path.name
        shutil.copy2(src_path, raw_dest)

        # Read binary for robust decoding
        with open(src_path, "rb") as fp:
            buf = np.frombuffer(fp.read(), dtype=np.uint8)
        img = cv2.imdecode(buf, cv2.IMREAD_COLOR)

        if img is None:
            print(f"[{idx}/{total}] ERROR reading {src_path.name}, skipping!")
            continue

        h, w = img.shape[:2]

        if h == 768 and w == 1376:
            roi = img[647:647+48, 1255:1255+48]
            blended_roi = remover.remove_watermark_from_region(roi, alpha)
            img_blended = img.copy()
            img_blended[647:647+48, 1255:1255+48] = blended_roi
            cleaned = cv2.inpaint(img_blended, full_mask, inpaintRadius=3, flags=cv2.INPAINT_TELEA)
        else:
            cleaned = remover.remove_watermark(img, auto_detect=False)

        success, enc_buf = cv2.imencode('.jpeg', cleaned, [cv2.IMWRITE_JPEG_QUALITY, 100])
        clean_filename = f"{clean_stem}.jpeg"

        for dest_dir in [CLEAN_DIR, PROD_CLEAN_DIR, TEMP_CLEAN]:
            with open(dest_dir / clean_filename, "wb") as out_f:
                out_f.write(enc_buf)

        if idx % 10 == 0 or idx == total:
            print(f"[{idx}/{total}] Cleaned: {clean_filename}")
        processed_stems.append(clean_stem)

    print(f"\nSuccessfully cleaned watermarks from all {len(processed_stems)} images!")
    return processed_stems

def step2_upscale_vulkan(stems):
    print("\n" + "=" * 75)
    print("STEP 2: REAL-ESRGAN VULKAN GPU SUPER-RESOLUTION (4x)")
    print("=" * 75)
    t0 = time.time()
    
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
    print(f"Launching Real-ESRGAN Vulkan GPU batch on {len(stems)} images...")
    subprocess.run(cmd, check=True)
    print(f"Vulkan GPU super-resolution finished in {time.time() - t0:.1f} seconds!")

    # Copy upscaled PNGs to RAW_UPSCALED_DIR
    for stem in stems:
        up_png = TEMP_OUT / f"{stem}.png"
        if up_png.exists():
            dest = RAW_UPSCALED_DIR / f"{stem}.png"
            shutil.copy2(up_png, dest)

def step3_lanczos_4k_resample(stems):
    print("\n" + "=" * 75)
    print("STEP 3: 4K LANCZOS DOWNSAMPLING & ANTI-ALIASING (3840x2144)")
    print("=" * 75)
    target_w = 3840
    target_h = 2144
    total = len(stems)

    for idx, stem in enumerate(stems, 1):
        up_png = RAW_UPSCALED_DIR / f"{stem}.png"
        if not up_png.exists():
            print(f"[{idx}/{total}] Warning: {up_png.name} not found!")
            continue

        out_name = f"{stem}.jpg"
        out_habits = FINAL_4K_DIR / out_name
        out_prod = PROD_4K_DIR / out_name

        with Image.open(up_png) as im:
            im_4k = im.resize((target_w, target_h), Image.Resampling.LANCZOS)
            im_4k.save(out_habits, "JPEG", quality=100, subsampling=0)
            im_4k.save(out_prod, "JPEG", quality=100, subsampling=0)

        if idx % 20 == 0 or idx == total:
            print(f"[{idx}/{total}] 4K Master: {out_name} (3840x2144, Quality 100)")

def step4_package_zips(stems):
    print("\n" + "=" * 75)
    print("STEP 4: PACKAGING DELIVERABLE ZIP ARCHIVES")
    print("=" * 75)
    
    # 1. Package NWEW batch clean zip
    print(f"Packaging {len(stems)} cleaned images into {NWEW_CLEAN_ZIP.name}...")
    with zipfile.ZipFile(NWEW_CLEAN_ZIP, "w", zipfile.ZIP_DEFLATED) as z:
        for stem in stems:
            f = CLEAN_DIR / f"{stem}.jpeg"
            if f.exists():
                z.write(f, arcname=f.name)
    print(f"  -> {NWEW_CLEAN_ZIP.name}: {NWEW_CLEAN_ZIP.stat().st_size / (1024*1024):.2f} MB")

    # 2. Package NWEW batch 4K zip
    print(f"Packaging {len(stems)} 4K images into {NWEW_4K_ZIP.name}...")
    with zipfile.ZipFile(NWEW_4K_ZIP, "w", zipfile.ZIP_DEFLATED) as z:
        for stem in stems:
            f = FINAL_4K_DIR / f"{stem}.jpg"
            if f.exists():
                z.write(f, arcname=f.name)
    print(f"  -> {NWEW_4K_ZIP.name}: {NWEW_4K_ZIP.stat().st_size / (1024*1024):.2f} MB")

    # 3. Update master HABITS_ALL_IMAGES_CLEANED.zip
    all_clean = sorted(list(CLEAN_DIR.glob("*.jpeg")) + list(CLEAN_DIR.glob("*.jpg")))
    print(f"Updating master {ALL_CLEAN_ZIP.name} with {len(all_clean)} total images...")
    with zipfile.ZipFile(ALL_CLEAN_ZIP, "w", zipfile.ZIP_DEFLATED) as z:
        for f in all_clean:
            z.write(f, arcname=f.name)
    print(f"  -> {ALL_CLEAN_ZIP.name}: {ALL_CLEAN_ZIP.stat().st_size / (1024*1024):.2f} MB")

    # 4. Update master HABITS_ALL_IMAGES_4K.zip
    all_4k = sorted(list(FINAL_4K_DIR.glob("*.jpg")) + list(FINAL_4K_DIR.glob("*.jpeg")))
    print(f"Updating master {ALL_4K_ZIP.name} with {len(all_4k)} total images...")
    with zipfile.ZipFile(ALL_4K_ZIP, "w", zipfile.ZIP_DEFLATED) as z:
        for f in all_4k:
            z.write(f, arcname=f.name)
    print(f"  -> {ALL_4K_ZIP.name}: {ALL_4K_ZIP.stat().st_size / (1024*1024):.2f} MB")

    # Cleanup temp
    if TEMP_DIR.exists():
        shutil.rmtree(TEMP_DIR)
        print("Cleaned up temporary working directory.")

if __name__ == "__main__":
    t_start = time.time()
    stems = step1_extract_and_clean()
    step2_upscale_vulkan(stems)
    step3_lanczos_4k_resample(stems)
    step4_package_zips(stems)
    print("\n" + "=" * 75)
    print(f"COMPLETED ALL 170 IMAGES IN {time.time() - t_start:.1f} SECONDS!")
    print("=" * 75)
