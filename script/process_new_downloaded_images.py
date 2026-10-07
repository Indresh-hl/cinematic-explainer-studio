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
TEMP_DIR = HABITS_DIR / "_temp_new_batch"
TEMP_CLEAN = TEMP_DIR / "clean"
TEMP_OUT = TEMP_DIR / "upscaled"

TEMP_CLEAN.mkdir(parents=True, exist_ok=True)
TEMP_OUT.mkdir(parents=True, exist_ok=True)

# The new files in Downloads
target_files = [
    "LINE_15-B_20260924020109.jpeg",
    "LINE_16-B_20260924020125.jpeg",
    "LINE_17-B_20260924020141.jpeg",
    "LINE_19-B_20260924020201.jpeg"
]

def step1_copy_raw_and_clean():
    print("=" * 70)
    print("STEP 1: COPYING RAW FILES AND CLEANING GEMINI WATERMARKS")
    print("=" * 70)
    
    remover = gwr.WatermarkRemover()
    alpha = remover.alpha_map_small  # 48x48
    alpha_padded = np.pad(alpha, 6, mode="constant")  # 60x60
    mask_star = (alpha_padded > 0.005).astype(np.uint8) * 255
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    dilated_star = cv2.dilate(mask_star, kernel, iterations=1)

    full_mask = np.zeros((768, 1376), dtype=np.uint8)
    full_mask[641:641+60, 1249:1249+60] = dilated_star

    processed_stems = []

    for fname in target_files:
        src_path = DOWNLOADS_DIR / fname
        if not src_path.exists():
            print(f"[!] Warning: File {src_path} does not exist!")
            continue

        # Extract clean stem, e.g., LINE_15-B
        m = re.match(r"(LINE_\d+-[A-Z]|LINE_\d+)", fname)
        if m:
            clean_stem = m.group(1)
        else:
            clean_stem = re.sub(r'_\d{14}\.(jpeg|jpg|png)$', '', fname, flags=re.IGNORECASE)

        # Copy raw to RAW_DIR
        raw_dest = RAW_DIR / fname
        shutil.copy2(src_path, raw_dest)
        print(f"Copied raw to: {raw_dest.name}")

        # Read binary for robust decoding
        with open(src_path, "rb") as fp:
            buf = np.frombuffer(fp.read(), dtype=np.uint8)
        img = cv2.imdecode(buf, cv2.IMREAD_COLOR)

        h, w = img.shape[:2]
        print(f"Cleaning watermark for {clean_stem} ({w}x{h})...")

        if h == 768 and w == 1376:
            # Reverse alpha blend on 48x48 core
            roi = img[647:647+48, 1255:1255+48]
            blended_roi = remover.remove_watermark_from_region(roi, alpha)
            img_blended = img.copy()
            img_blended[647:647+48, 1255:1255+48] = blended_roi

            # Telea inpainting on 60x60 perimeter
            cleaned = cv2.inpaint(img_blended, full_mask, inpaintRadius=3, flags=cv2.INPAINT_TELEA)
        else:
            cleaned = remover.remove_watermark(img, auto_detect=False)

        # Save to destinations
        success, enc_buf = cv2.imencode('.jpeg', cleaned, [cv2.IMWRITE_JPEG_QUALITY, 100])
        clean_filename = f"{clean_stem}.jpeg"

        for dest_dir in [CLEAN_DIR, PROD_CLEAN_DIR, TEMP_CLEAN]:
            with open(dest_dir / clean_filename, "wb") as out_f:
                out_f.write(enc_buf)

        print(f"  [Cleaned] Saved {clean_filename} (100% Quality JPEG)")
        processed_stems.append(clean_stem)

    return processed_stems

def step2_upscale_vulkan(stems):
    print("\n" + "=" * 70)
    print("STEP 2: REAL-ESRGAN VULKAN GPU SUPER-RESOLUTION (4x)")
    print("=" * 70)
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
    print(f"Launching Real-ESRGAN Vulkan GPU on {len(stems)} images...")
    subprocess.run(cmd, check=True)
    print(f"Vulkan GPU super-resolution finished in {time.time() - t0:.1f} seconds!")

    # Copy upscaled PNGs to RAW_UPSCALED_DIR
    for stem in stems:
        up_png = TEMP_OUT / f"{stem}.png"
        if up_png.exists():
            dest = RAW_UPSCALED_DIR / f"{stem}.png"
            shutil.copy2(up_png, dest)
            print(f"  [Upscaled] 5504x3072 PNG -> {dest.name}")

def step3_lanczos_4k_resample(stems):
    print("\n" + "=" * 70)
    print("STEP 3: 4K LANCZOS DOWNSAMPLING & ANTI-ALIASING (3840x2144)")
    print("=" * 70)
    target_w = 3840
    target_h = 2144

    for stem in stems:
        up_png = RAW_UPSCALED_DIR / f"{stem}.png"
        if not up_png.exists():
            print(f"[!] Warning: {up_png} not found!")
            continue

        out_name = f"{stem}.jpg"
        out_habits = FINAL_4K_DIR / out_name
        out_prod = PROD_4K_DIR / out_name

        with Image.open(up_png) as im:
            im_4k = im.resize((target_w, target_h), Image.Resampling.LANCZOS)
            im_4k.save(out_habits, "JPEG", quality=100, subsampling=0)
            im_4k.save(out_prod, "JPEG", quality=100, subsampling=0)

        print(f"  [4K Master] {out_name} saved at {target_w}x{target_h} (Quality 100, Subsampling 0)")

def step4_repackage_zips():
    print("\n" + "=" * 70)
    print("STEP 4: REPACKAGING COMPLETE MASTER DELIVERABLE ZIPS")
    print("=" * 70)
    
    # Repack Cleaned ZIP
    all_clean = sorted(list(CLEAN_DIR.glob("*.jpeg")) + list(CLEAN_DIR.glob("*.jpg")))
    print(f"Packaging {len(all_clean)} cleaned images into {CLEAN_ZIP_OUT.name}...")
    with zipfile.ZipFile(CLEAN_ZIP_OUT, "w", zipfile.ZIP_DEFLATED) as z:
        for f in all_clean:
            z.write(f, arcname=f.name)
    clean_size_mb = CLEAN_ZIP_OUT.stat().st_size / (1024 * 1024)
    print(f"  -> {CLEAN_ZIP_OUT.name}: {len(all_clean)} files ({clean_size_mb:.2f} MB)")

    # Repack 4K ZIP
    all_4k = sorted(list(FINAL_4K_DIR.glob("*.jpg")) + list(FINAL_4K_DIR.glob("*.jpeg")))
    print(f"Packaging {len(all_4k)} 4K images into {FINAL_4K_ZIP_OUT.name}...")
    with zipfile.ZipFile(FINAL_4K_ZIP_OUT, "w", zipfile.ZIP_DEFLATED) as z:
        for f in all_4k:
            z.write(f, arcname=f.name)
    k4_size_mb = FINAL_4K_ZIP_OUT.stat().st_size / (1024 * 1024)
    print(f"  -> {FINAL_4K_ZIP_OUT.name}: {len(all_4k)} files ({k4_size_mb:.2f} MB)")

    # Cleanup temp
    if TEMP_DIR.exists():
        shutil.rmtree(TEMP_DIR)
        print("Cleaned up temporary working directory.")

if __name__ == "__main__":
    t_start = time.time()
    stems = step1_copy_raw_and_clean()
    step2_upscale_vulkan(stems)
    step3_lanczos_4k_resample(stems)
    step4_repackage_zips()
    print("\n" + "=" * 70)
    print(f"ALL NEW IMAGES PROCESSED, UPSCALED, AND DELIVERED IN {time.time() - t_start:.1f} SECONDS!")
    print("=" * 70)
