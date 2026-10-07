import os
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
TEMP_DIR = HABITS_DIR / "_temp_missing_4"
TEMP_CLEAN = TEMP_DIR / "clean"
TEMP_OUT = TEMP_DIR / "upscaled"

TEMP_CLEAN.mkdir(parents=True, exist_ok=True)
TEMP_OUT.mkdir(parents=True, exist_ok=True)

mapping = {
    'Caveman_scratching_head_at_holog': 'Caveman_scratching_head_at_hologram.jpeg',
    'Character_experiencing_anxiety_i': 'Character_experiencing_anxiety_in_bed.jpeg',
    'Man_scrolling_smartphone_in_armc': 'Man_scrolling_smartphone_in_armchair.jpeg',
    'Presenter_balancing_homeostasis_': 'Presenter_balancing_homeostasis.jpeg'
}

def clean_missing():
    print("=" * 70)
    print("STEP 1: CLEANING WATERMARKS FOR 4 UNICODE-ELLIPSIS IMAGES")
    print("=" * 70)
    
    remover = gwr.WatermarkRemover()
    alpha = remover.alpha_map_small  # 48x48
    alpha_padded = np.pad(alpha, 6, mode="constant")  # 60x60
    mask_star = (alpha_padded > 0.005).astype(np.uint8) * 255
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    dilated_star = cv2.dilate(mask_star, kernel, iterations=1)

    full_mask = np.zeros((768, 1376), dtype=np.uint8)
    full_mask[641:641+60, 1249:1249+60] = dilated_star

    for f in RAW_DIR.glob('*.*'):
        for prefix, clean_name in mapping.items():
            if prefix in f.name:
                with open(f, 'rb') as fp:
                    buf = np.frombuffer(fp.read(), dtype=np.uint8)
                img = cv2.imdecode(buf, cv2.IMREAD_COLOR)
                h, w = img.shape[:2]
                print(f"Processing {clean_name} (Shape: {w}x{h})...")
                
                # Reverse alpha blend + Telea
                roi = img[647:647+48, 1255:1255+48]
                blended_roi = remover.remove_watermark_from_region(roi, alpha)
                img_blended = img.copy()
                img_blended[647:647+48, 1255:1255+48] = blended_roi
                cleaned = cv2.inpaint(img_blended, full_mask, inpaintRadius=3, flags=cv2.INPAINT_TELEA)

                # Save to Habits cleaned, Prod cleaned, and Temp clean
                success, enc_buf = cv2.imencode('.jpeg', cleaned, [cv2.IMWRITE_JPEG_QUALITY, 100])
                for dest in [CLEAN_DIR / clean_name, PROD_CLEAN_DIR / clean_name, TEMP_CLEAN / clean_name]:
                    with open(dest, 'wb') as out_f:
                        out_f.write(enc_buf)
                print(f"Saved: {clean_name}")

def upscale_missing():
    print("=" * 70)
    print("STEP 2: REAL-ESRGAN VULKAN GPU UPSCALING FOR 4 IMAGES")
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
    print(f"Upscaling completed in {time.time() - t0:.1f}s")
    
    # Copy upscaled to raw_upscaled
    for up_f in TEMP_OUT.glob("*.png"):
        dest = RAW_UPSCALED_DIR / up_f.name
        with open(up_f, "rb") as rf, open(dest, "wb") as wf:
            wf.write(rf.read())
        print(f"Copied {up_f.name} to {dest}")

def lanczos_downsample_missing():
    print("=" * 70)
    print("STEP 3: 4K LANCZOS DOWNSAMPLING (3840x2144)")
    print("=" * 70)
    target_w = 3840
    target_h = 2144
    for prefix, clean_name in mapping.items():
        stem = Path(clean_name).stem
        up_png = RAW_UPSCALED_DIR / f"{stem}.png"
        out_jpg_habits = FINAL_4K_DIR / f"{stem}.jpg"
        out_jpg_prod = PROD_4K_DIR / f"{stem}.jpg"
        
        with Image.open(up_png) as im:
            im_4k = im.resize((target_w, target_h), Image.Resampling.LANCZOS)
            im_4k.save(out_jpg_habits, "JPEG", quality=100, subsampling=0)
            im_4k.save(out_jpg_prod, "JPEG", quality=100, subsampling=0)
        print(f"Downsampled 4K: {stem}.jpg ({target_w}x{target_h})")

def repackage_zips():
    print("=" * 70)
    print("STEP 4: REPACKAGING COMPLETE MASTER ZIP ARCHIVES (ALL 132 IMAGES)")
    print("=" * 70)
    
    all_clean = sorted(list(CLEAN_DIR.glob("*.jpeg")) + list(CLEAN_DIR.glob("*.jpg")))
    print(f"Total cleaned files to zip: {len(all_clean)}")
    with zipfile.ZipFile(CLEAN_ZIP_OUT, "w", zipfile.ZIP_DEFLATED) as z:
        for f in all_clean:
            z.write(f, arcname=f.name)
    print(f"Cleaned ZIP updated: {CLEAN_ZIP_OUT} ({CLEAN_ZIP_OUT.stat().st_size / (1024*1024):.2f} MB)")

    all_4k = sorted(list(FINAL_4K_DIR.glob("*.jpg")) + list(FINAL_4K_DIR.glob("*.jpeg")))
    print(f"Total 4K files to zip: {len(all_4k)}")
    with zipfile.ZipFile(FINAL_4K_ZIP_OUT, "w", zipfile.ZIP_DEFLATED) as z:
        for f in all_4k:
            z.write(f, arcname=f.name)
    print(f"4K ZIP updated: {FINAL_4K_ZIP_OUT} ({FINAL_4K_ZIP_OUT.stat().st_size / (1024*1024):.2f} MB)")

if __name__ == "__main__":
    clean_missing()
    upscale_missing()
    lanczos_downsample_missing()
    repackage_zips()
    print("=" * 70)
    print("[SUCCESS] ALL 132 IMAGES FULLY PROCESSED, UPSCALED, DOWNSAMPLED, AND PACKAGED!")
    print("=" * 70)
