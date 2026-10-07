import os
import sys
import re
import time
import glob
import zipfile
import subprocess
from pathlib import Path
import cv2
import numpy as np
from PIL import Image
import gemini_watermark_remover as gwr

# Paths
BASE_DIR = Path(r"c:\Users\Indresh HL\Downloads\youtube long fromat")
ZIP_SRC = Path(r"C:\Users\Indresh HL\Downloads\15-16.zip")

WS_TOPIC_03 = BASE_DIR / "production" / "topic_03" / "images"
CLEAN_DIR_WS = WS_TOPIC_03 / "cleaned"
RAW_DIR_WS = WS_TOPIC_03 / "raw_upscaled"
FINAL_4K_DIR_WS = WS_TOPIC_03 / "4k"

DL_DIR = Path(r"C:\Users\Indresh HL\Downloads")
DL_CLEAN_DIR = DL_DIR / "TOPIC_03_CLEANED_IMAGES"
DL_4K_DIR = DL_DIR / "TOPIC_03_4K_IMAGES"
DL_CLEAN_ZIP = DL_DIR / "TOPIC_03_ALL_IMAGES_CLEANED.zip"
DL_4K_ZIP = DL_DIR / "TOPIC_03_ALL_IMAGES_4K.zip"

REALESRGAN_EXE = BASE_DIR / "tools" / "realesrgan" / "realesrgan-ncnn-vulkan.exe"

TEMP_CLEAN_DIR = BASE_DIR / "production" / "topic_03" / "images" / "temp_missing_cleaned"
TEMP_RAW_DIR = BASE_DIR / "production" / "topic_03" / "images" / "temp_missing_raw"

for d in [TEMP_CLEAN_DIR, TEMP_RAW_DIR, CLEAN_DIR_WS, RAW_DIR_WS, FINAL_4K_DIR_WS, DL_CLEAN_DIR, DL_4K_DIR]:
    d.mkdir(parents=True, exist_ok=True)

def determine_name(raw_name):
    m = re.search(r'(?:LINE_|SHOT_)(\d+-[A-Z])', raw_name)
    if m:
        parts = m.group(1).split('-')
        return f"LINE_{int(parts[0]):02d}-{parts[1]}.jpg"
    return f"{raw_name}.jpg"

def main():
    print("=" * 70)
    print("[PROCESSING MISSING ACT 2 IMAGES (LINES 14-A to 15-C)]")
    print("=" * 70)

    z = zipfile.ZipFile(ZIP_SRC, "r")
    names = sorted(z.namelist())
    print(f"[*] Found {len(names)} images in {ZIP_SRC}")

    remover = gwr.WatermarkRemover()
    alpha = remover.alpha_map_small
    alpha_padded = np.pad(alpha, 6, mode="constant")
    mask_star = (alpha_padded > 0.005).astype(np.uint8) * 255
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    dilated_star = cv2.dilate(mask_star, kernel, iterations=1)

    full_mask = np.zeros((768, 1376), dtype=np.uint8)
    full_mask[641:641+60, 1249:1249+60] = dilated_star

    processed_names = []

    # 1. Clean watermarks
    print("\n[STEP 1] Cleaning Watermarks...")
    for n in names:
        clean_name = determine_name(n)
        raw_bytes = z.read(n)
        img = cv2.imdecode(np.frombuffer(raw_bytes, np.uint8), cv2.IMREAD_COLOR)
        if img is None:
            print(f"[!] Error decoding {n}")
            continue

        roi = img[647:647+48, 1255:1255+48]
        blended_roi = remover.remove_watermark_from_region(roi, alpha)
        img_blended = img.copy()
        img_blended[647:647+48, 1255:1255+48] = blended_roi
        cleaned = cv2.inpaint(img_blended, full_mask, inpaintRadius=3, flags=cv2.INPAINT_TELEA)

        _, encoded = cv2.imencode(".jpg", cleaned, [cv2.IMWRITE_JPEG_QUALITY, 100])

        # Write to temp clean folder, ws folder, and dl folder
        for target_dir in [TEMP_CLEAN_DIR, CLEAN_DIR_WS, DL_CLEAN_DIR]:
            with open(target_dir / clean_name, "wb") as f:
                f.write(encoded)

        processed_names.append(clean_name)
        print(f"  [Cleaned] {n[:35]}... -> {clean_name}")

    # 2. Real-ESRGAN GPU Upscale
    print("\n[STEP 2] Upscaling 4x on NVIDIA RTX 4050 GPU...")
    cmd = [
        str(REALESRGAN_EXE),
        "-i", str(TEMP_CLEAN_DIR),
        "-o", str(TEMP_RAW_DIR),
        "-n", "realesrgan-x4plus-anime",
        "-s", "4",
        "-f", "png",
        "-g", "0",
        "-j", "2:2:2"
    ]
    t0 = time.time()
    subprocess.run(cmd, check=True)
    print(f"[SUCCESS] Upscaled in {time.time() - t0:.2f}s!")

    # 3. Downsample to 4K Lanczos
    print("\n[STEP 3] Downsampling to 4K UHD (3840x2144)...")
    target_w, target_h = 3840, 2144
    for cname in processed_names:
        stem = Path(cname).stem
        raw_png = TEMP_RAW_DIR / f"{stem}.png"
        if not raw_png.exists():
            print(f"[!] Warning: {raw_png} not found")
            continue

        with Image.open(raw_png) as im:
            im_4k = im.resize((target_w, target_h), Image.Resampling.LANCZOS)
            # Save to WS and DL 4K directories
            im_4k.save(FINAL_4K_DIR_WS / cname, "JPEG", quality=100, subsampling=0)
            im_4k.save(DL_4K_DIR / cname, "JPEG", quality=100, subsampling=0)
            # Also keep raw png in WS raw dir
            im.save(RAW_DIR_WS / f"{stem}.png")

        print(f"  [Lanczos 4K] Saved 4K: {cname}")

    # Clean up temp directories
    for f in TEMP_CLEAN_DIR.glob("*"):
        f.unlink()
    TEMP_CLEAN_DIR.rmdir()
    for f in TEMP_RAW_DIR.glob("*"):
        f.unlink()
    TEMP_RAW_DIR.rmdir()

    # 4. Repack master zip files
    print("\n[STEP 4] Repacking Master ZIP Archives...")
    print(f"[*] Repacking {DL_CLEAN_ZIP}...")
    with zipfile.ZipFile(DL_CLEAN_ZIP, "w", zipfile.ZIP_DEFLATED) as cz:
        for f in sorted(DL_CLEAN_DIR.glob("*.jpg")):
            cz.write(f, f.name)
    print(f"[SUCCESS] Repacked Cleaned ZIP: {DL_CLEAN_ZIP.stat().st_size / (1024*1024):.2f} MB")

    print(f"[*] Repacking {DL_4K_ZIP}...")
    with zipfile.ZipFile(DL_4K_ZIP, "w", zipfile.ZIP_DEFLATED) as zf:
        for f in sorted(DL_4K_DIR.glob("*.jpg")):
            zf.write(f, f.name)
    print(f"[SUCCESS] Repacked 4K ZIP: {DL_4K_ZIP.stat().st_size / (1024*1024):.2f} MB")

    total_4k_files = len(list(DL_4K_DIR.glob("*.jpg")))
    print("\n" + "=" * 70)
    print(f"[COMPLETE] ALL {total_4k_files} IMAGES NOW 100% COMPLETE IN 4K UHD!")
    print(f"• Total 4K Images:      {total_4k_files} frames")
    print(f"• 4K Output Folder:     {DL_4K_DIR}")
    print(f"• Master 4K ZIP Archive:{DL_4K_ZIP}")
    print("=" * 70)

if __name__ == "__main__":
    main()
