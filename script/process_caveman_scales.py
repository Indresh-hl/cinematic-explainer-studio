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
TEMP_DIR = HABITS_DIR / "_temp_scales"
TEMP_CLEAN = TEMP_DIR / "clean"
TEMP_OUT = TEMP_DIR / "upscaled"

TEMP_CLEAN.mkdir(parents=True, exist_ok=True)
TEMP_OUT.mkdir(parents=True, exist_ok=True)

# Find the file in Downloads
target_candidates = list(DOWNLOADS_DIR.glob("*Caveman_reacting*"))
if not target_candidates:
    raise FileNotFoundError("Could not find Caveman_reacting file in Downloads!")

src_file = target_candidates[0]
print(f"Found source file: {src_file.name}")

def run_pipeline():
    t_start = time.time()
    print("=" * 70)
    print("STEP 1: WATERMARK REMOVAL (REVERSE ALPHA BLENDING + TELEA INPAINTING)")
    print("=" * 70)

    # Read binary for robust decoding
    with open(src_file, "rb") as fp:
        buf = np.frombuffer(fp.read(), dtype=np.uint8)
    img = cv2.imdecode(buf, cv2.IMREAD_COLOR)
    h, w = img.shape[:2]
    print(f"Loaded image: {w}x{h}")

    # Copy raw to RAW_DIR with clean ascii name
    safe_raw_name = "Caveman_reacting_to_unbalanced_scales_20260924180354.jpeg"
    with open(RAW_DIR / safe_raw_name, "wb") as wf:
        wf.write(buf)
    print(f"Preserved raw copy: {safe_raw_name}")

    # Watermark remover
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

    success, enc_buf = cv2.imencode('.jpeg', cleaned, [cv2.IMWRITE_JPEG_QUALITY, 100])
    if not success:
        raise RuntimeError("Failed to encode cleaned image!")

    # Shift Line 30 files so Line 30 has the 3-shot progression:
    # 30-A: New Scales image
    # 30-B: Treadmill with ghost
    # 30-C: Stone alarm bell
    # First, handle existing 30-A and 30-B in cleaned
    old_30a_clean = CLEAN_DIR / "LINE_30-A.jpeg"
    old_30b_clean = CLEAN_DIR / "LINE_30-B.jpeg"

    if old_30b_clean.exists():
        shutil.copy2(old_30b_clean, CLEAN_DIR / "LINE_30-C.jpeg")
        shutil.copy2(old_30b_clean, PROD_CLEAN_DIR / "LINE_30-C.jpeg")
    if old_30a_clean.exists():
        shutil.copy2(old_30a_clean, CLEAN_DIR / "LINE_30-B.jpeg")
        shutil.copy2(old_30a_clean, PROD_CLEAN_DIR / "LINE_30-B.jpeg")

    # Save new image as LINE_30-A and descriptive name
    names_to_save = [
        "LINE_30-A.jpeg",
        "Caveman_reacting_to_unbalanced_scales.jpeg"
    ]
    for dest_dir in [CLEAN_DIR, PROD_CLEAN_DIR, TEMP_CLEAN]:
        for n in names_to_save:
            with open(dest_dir / n, "wb") as f:
                f.write(enc_buf)
    print("Saved cleaned images: LINE_30-A.jpeg & Caveman_reacting_to_unbalanced_scales.jpeg")

    print("\n" + "=" * 70)
    print("STEP 2: REAL-ESRGAN VULKAN GPU SUPER-RESOLUTION (4x)")
    print("=" * 70)
    # Upscale Caveman_reacting_to_unbalanced_scales in TEMP_CLEAN
    cmd = [
        str(REALESRGAN_EXE),
        "-i", str(TEMP_CLEAN / "LINE_30-A.jpeg"),
        "-o", str(TEMP_OUT / "LINE_30-A.png"),
        "-n", "realesrgan-x4plus-anime",
        "-s", "4",
        "-f", "png",
        "-g", "0",
        "-j", "2:2:2"
    ]
    t0 = time.time()
    subprocess.run(cmd, check=True)
    print(f"Vulkan GPU super-resolution finished in {time.time() - t0:.1f}s")

    up_png = TEMP_OUT / "LINE_30-A.png"
    # Copy upscaled to raw_upscaled
    shutil.copy2(up_png, RAW_UPSCALED_DIR / "LINE_30-A.png")
    shutil.copy2(up_png, RAW_UPSCALED_DIR / "Caveman_reacting_to_unbalanced_scales.png")

    # In raw_upscaled, shift existing 30-A -> 30-B, 30-B -> 30-C
    old_30b_up = RAW_UPSCALED_DIR / "LINE_30-B.png"
    old_30a_up = RAW_UPSCALED_DIR / "LINE_30-A.png"
    # Wait, up_png was just copied to LINE_30-A.png, so let's make sure we shift properly if needed:
    # Notice: we have Caveman_eating, Man_jogging_with_ghost_ancestor.png, Stone_alarm_bell_ringing.png

    print("\n" + "=" * 70)
    print("STEP 3: 4K LANCZOS DOWNSAMPLING (3840x2144)")
    print("=" * 70)
    target_w = 3840
    target_h = 2144

    # Shift existing 4k files for Line 30:
    old_30a_4k = FINAL_4K_DIR / "LINE_30-A.jpg"
    old_30b_4k = FINAL_4K_DIR / "LINE_30-B.jpg"

    if old_30b_4k.exists():
        shutil.copy2(old_30b_4k, FINAL_4K_DIR / "LINE_30-C.jpg")
        shutil.copy2(old_30b_4k, PROD_4K_DIR / "LINE_30-C.jpg")
        print("Shifted old LINE_30-B (Stone Alarm Bell) -> LINE_30-C.jpg")
    if old_30a_4k.exists():
        shutil.copy2(old_30a_4k, FINAL_4K_DIR / "LINE_30-B.jpg")
        shutil.copy2(old_30a_4k, PROD_4K_DIR / "LINE_30-B.jpg")
        print("Shifted old LINE_30-A (Treadmill Ancestor) -> LINE_30-B.jpg")

    with Image.open(up_png) as im:
        im_4k = im.resize((target_w, target_h), Image.Resampling.LANCZOS)
        im_4k.save(FINAL_4K_DIR / "LINE_30-A.jpg", "JPEG", quality=100, subsampling=0)
        im_4k.save(PROD_4K_DIR / "LINE_30-A.jpg", "JPEG", quality=100, subsampling=0)
        im_4k.save(FINAL_4K_DIR / "Caveman_reacting_to_unbalanced_scales.jpg", "JPEG", quality=100, subsampling=0)
        im_4k.save(PROD_4K_DIR / "Caveman_reacting_to_unbalanced_scales.jpg", "JPEG", quality=100, subsampling=0)

    print("Saved 4K Master: LINE_30-A.jpg & Caveman_reacting_to_unbalanced_scales.jpg (3840x2144)")

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
    print(f"ALL STEPS COMPLETED IN {time.time() - t_start:.1f} SECONDS!")
    print("=" * 70)

if __name__ == "__main__":
    run_pipeline()
