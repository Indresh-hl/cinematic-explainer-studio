import os
import re
import sys
import time
import zipfile
import subprocess
from pathlib import Path
import cv2
import numpy as np
from PIL import Image
import gemini_watermark_remover as gwr

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent
ZIP_SRC = Path(r"c:\Users\Indresh HL\Downloads\habits image.zip")

HABITS_DIR = Path(r"c:\Users\Indresh HL\Downloads\Habits")
RAW_DIR = HABITS_DIR / "raw"
CLEAN_DIR = HABITS_DIR / "cleaned"
RAW_UPSCALED_DIR = HABITS_DIR / "raw_upscaled"
FINAL_4K_DIR = HABITS_DIR / "4k"

PROD_DIR = BASE_DIR / "production" / "topic_02" / "images"
PROD_CLEAN_DIR = PROD_DIR / "cleaned"
PROD_4K_DIR = PROD_DIR / "4k"

CLEAN_ZIP_OUT = Path(r"c:\Users\Indresh HL\Downloads\HABITS_ALL_IMAGES_CLEANED.zip")
FINAL_4K_ZIP_OUT = Path(r"c:\Users\Indresh HL\Downloads\HABITS_ALL_IMAGES_4K.zip")

REALESRGAN_EXE = BASE_DIR / "tools" / "realesrgan" / "realesrgan-ncnn-vulkan.exe"

for p in [RAW_DIR, CLEAN_DIR, RAW_UPSCALED_DIR, FINAL_4K_DIR, PROD_CLEAN_DIR, PROD_4K_DIR]:
    p.mkdir(parents=True, exist_ok=True)

def step1_extract():
    print("=" * 70)
    print("STEP 1: EXTRACTING HABITS IMAGE ARCHIVE")
    print("=" * 70)
    print(f"Reading from: {ZIP_SRC}")
    with zipfile.ZipFile(ZIP_SRC, "r") as z:
        names = z.namelist()
        print(f"Total images in archive: {len(names)}")
        for n in names:
            z.extract(n, RAW_DIR)
    print(f"Extracted {len(names)} raw images to {RAW_DIR}\n")

def step2_clean_watermarks():
    print("=" * 70)
    print("STEP 2: WATERMARK REMOVAL VIA REVERSE ALPHA COLOR BLENDING + TELEA INPAINTING")
    print("=" * 70)
    
    remover = gwr.WatermarkRemover()
    alpha = remover.alpha_map_small  # 48x48
    alpha_padded = np.pad(alpha, 6, mode="constant")  # 60x60
    mask_star = (alpha_padded > 0.005).astype(np.uint8) * 255
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    dilated_star = cv2.dilate(mask_star, kernel, iterations=1)

    full_mask = np.zeros((768, 1376), dtype=np.uint8)
    full_mask[641:641+60, 1249:1249+60] = dilated_star

    raw_files = sorted(list(RAW_DIR.glob("*.jpeg")) + list(RAW_DIR.glob("*.jpg")) + list(RAW_DIR.glob("*.png")))
    print(f"Found {len(raw_files)} raw images to clean.")

    cleaned_records = []
    t0 = time.time()

    for idx, r_path in enumerate(raw_files, 1):
        raw_name = r_path.name
        
        # Clean file name: strip timestamp if present
        # e.g., LINE_45-B_20260923220150.jpeg -> LINE_45-B.jpeg
        m = re.match(r"(LINE_\d+-[A-Z]|LINE_\d+)", raw_name)
        if m:
            clean_name = f"{m.group(1)}.jpeg"
        else:
            base_no_ts = re.sub(r'_\d{14}\.(jpeg|jpg|png)$', '', raw_name, flags=re.IGNORECASE)
            clean_name = f"{base_no_ts}.jpeg"

        img = cv2.imread(str(r_path))
        if img is None:
            print(f"[!] Warning: could not read {r_path}")
            continue

        h, w = img.shape[:2]

        if h == 768 and w == 1376:
            # 1. Reverse alpha color blending on 48x48 core region
            roi = img[647:647+48, 1255:1255+48]
            blended_roi = remover.remove_watermark_from_region(roi, alpha)
            img_blended = img.copy()
            img_blended[647:647+48, 1255:1255+48] = blended_roi

            # 2. Telea inpainting on 60x60 perimeter
            cleaned = cv2.inpaint(img_blended, full_mask, inpaintRadius=3, flags=cv2.INPAINT_TELEA)
        else:
            cleaned = remover.remove_watermark(img, auto_detect=False)

        # Save with maximum 100% JPEG quality
        out_habits = CLEAN_DIR / clean_name
        out_prod = PROD_CLEAN_DIR / clean_name

        cv2.imwrite(str(out_habits), cleaned, [cv2.IMWRITE_JPEG_QUALITY, 100])
        cv2.imwrite(str(out_prod), cleaned, [cv2.IMWRITE_JPEG_QUALITY, 100])

        cleaned_records.append((clean_name, out_habits))
        if idx % 25 == 0 or idx == len(raw_files):
            print(f"  [Cleaned] {idx}/{len(raw_files)} frames processed...")

    print(f"Watermark removal complete in {time.time() - t0:.1f}s!")

    # Package into Clean ZIP
    print(f"Packaging {len(cleaned_records)} cleaned images into {CLEAN_ZIP_OUT}...")
    with zipfile.ZipFile(CLEAN_ZIP_OUT, "w", zipfile.ZIP_DEFLATED) as z:
        for cname, cpath in cleaned_records:
            z.write(cpath, arcname=cname)
    print(f"Cleaned ZIP created: {CLEAN_ZIP_OUT} ({CLEAN_ZIP_OUT.stat().st_size / (1024*1024):.2f} MB)\n")

def step3_upscale_vulkan():
    print("=" * 70)
    print("STEP 3: 4K GPU SUPER-RESOLUTION (REAL-ESRGAN VULKAN)")
    print("=" * 70)
    cleaned_files = list(CLEAN_DIR.glob("*.jpeg"))
    total_images = len(cleaned_files)
    print(f"Launching Real-ESRGAN Vulkan (realesrgan-x4plus-anime) on {total_images} images...")

    t0 = time.time()
    cmd = [
        str(REALESRGAN_EXE),
        "-i", str(CLEAN_DIR),
        "-o", str(RAW_UPSCALED_DIR),
        "-n", "realesrgan-x4plus-anime",
        "-s", "4",
        "-f", "png",
        "-g", "0",
        "-j", "2:2:2"
    ]
    
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    last_reported = 0
    while True:
        line = proc.stdout.readline()
        if not line and proc.poll() is not None:
            break
        current_raw_count = len(list(RAW_UPSCALED_DIR.glob("*.png")))
        if current_raw_count > last_reported and current_raw_count % 10 == 0:
            elapsed = time.time() - t0
            pct = (current_raw_count / total_images) * 100
            print(f"  [GPU Upscaling] {current_raw_count}/{total_images} frames ({pct:.1f}%) | Elapsed: {elapsed:.1f}s")
            last_reported = current_raw_count

    proc.wait()
    print(f"Vulkan GPU super-resolution finished in {(time.time() - t0)/60:.1f} minutes!\n")

def step4_lanczos_4k_resample():
    print("=" * 70)
    print("STEP 4: 4K LANCZOS DOWNSAMPLING & ANTI-ALIASING (3840x2144)")
    print("=" * 70)

    raw_upscaled = sorted(list(RAW_UPSCALED_DIR.glob("*.png")))
    total = len(raw_upscaled)
    print(f"Downsampling {total} upscaled PNGs to 4K UHD with Lanczos anti-aliasing...")

    target_w = 3840
    target_h = 2144  # 1376 * (3840/1376) = 2144 (exact pixel-matched 1.7916 ratio)

    t0 = time.time()
    for idx, r_file in enumerate(raw_upscaled, 1):
        clean_stem = r_file.stem
        out_name = f"{clean_stem}.jpg"
        out_habits = FINAL_4K_DIR / out_name
        out_prod = PROD_4K_DIR / out_name

        with Image.open(r_file) as im:
            im_4k = im.resize((target_w, target_h), Image.Resampling.LANCZOS)
            im_4k.save(out_habits, "JPEG", quality=100, subsampling=0)
            im_4k.save(out_prod, "JPEG", quality=100, subsampling=0)

        if idx % 25 == 0 or idx == total:
            print(f"  [Lanczos 4K] Processed {idx}/{total} master 4K UHD frames...")

    print(f"4K Lanczos conversion complete in {time.time() - t0:.1f} seconds!\n")

    # Packaging 4K Archive
    print(f"Packaging {total} 4K images into {FINAL_4K_ZIP_OUT}...")
    with zipfile.ZipFile(FINAL_4K_ZIP_OUT, "w", zipfile.ZIP_DEFLATED) as z:
        for f in sorted(FINAL_4K_DIR.glob("*.jpg")):
            z.write(f, arcname=f.name)
    print(f"Final 4K ZIP created: {FINAL_4K_ZIP_OUT} ({FINAL_4K_ZIP_OUT.stat().st_size / (1024*1024):.2f} MB)\n")

if __name__ == "__main__":
    t_start = time.time()
    step1_extract()
    step2_clean_watermarks()
    step3_upscale_vulkan()
    step4_lanczos_4k_resample()
    print("=" * 70)
    print(f"🎉 ALL PROCESSES COMPLETED SUCCESSFULLY IN {(time.time() - t_start)/60:.1f} MINUTES!")
    print("=" * 70)
