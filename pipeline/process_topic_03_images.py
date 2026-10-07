import os
import sys
import re
import time
import glob
import zipfile
import subprocess
from pathlib import Path
from collections import defaultdict
import cv2
import numpy as np
from PIL import Image
import gemini_watermark_remover as gwr

# Paths
BASE_DIR = Path(r"c:\Users\Indresh HL\Downloads\youtube long fromat")
ZIP_SRC = Path(r"C:\Users\Indresh HL\Downloads\video 3.zip")

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

for d in [CLEAN_DIR_WS, RAW_DIR_WS, FINAL_4K_DIR_WS, DL_CLEAN_DIR, DL_4K_DIR]:
    d.mkdir(parents=True, exist_ok=True)

def determine_clean_name(raw_name, group_counts):
    # Regex to find shot tag e.g. 01-A, 1-A, 32-B, etc.
    m = re.search(r'(?:LINE_|SHOT_)(\d+-[A-Z])', raw_name)
    if m:
        parts = m.group(1).split('-')
        line_num = int(parts[0])
        shot_letter = parts[1]
        tag = f"LINE_{line_num:02d}-{shot_letter}"
    else:
        tag = "LINE_UNKNOWN"

    count = group_counts[tag]
    group_counts[tag] += 1

    if count == 0:
        clean_name = f"{tag}.jpg"
    else:
        clean_name = f"{tag}_(Variant_{count}).jpg"

    return tag, clean_name

def step1_clean_watermarks():
    print("=" * 70)
    print("[STEP 1/3] GEMINI WATERMARK REMOVAL & ALPHA BLENDING REVERSAL")
    print("=" * 70)

    z = zipfile.ZipFile(ZIP_SRC, "r")
    all_names = sorted(z.namelist())
    print(f"[*] Total entries in archive: {len(all_names)}")

    remover = gwr.WatermarkRemover()
    alpha = remover.alpha_map_small  # 48x48
    alpha_padded = np.pad(alpha, 6, mode="constant")  # 60x60
    mask_star = (alpha_padded > 0.005).astype(np.uint8) * 255
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    dilated_star = cv2.dilate(mask_star, kernel, iterations=1)

    full_mask = np.zeros((768, 1376), dtype=np.uint8)
    full_mask[641:641+60, 1249:1249+60] = dilated_star

    group_counts = defaultdict(int)
    cleaned_records = []

    t0 = time.time()
    for idx, raw_name in enumerate(all_names, 1):
        tag, clean_name = determine_clean_name(raw_name, group_counts)

        raw_bytes = z.read(raw_name)
        img = cv2.imdecode(np.frombuffer(raw_bytes, np.uint8), cv2.IMREAD_COLOR)
        if img is None:
            print(f"[!] Error decoding {raw_name}")
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

        # Save JPEG quality 100
        _, encoded = cv2.imencode(".jpg", cleaned, [cv2.IMWRITE_JPEG_QUALITY, 100])

        ws_path = CLEAN_DIR_WS / clean_name
        dl_path = DL_CLEAN_DIR / clean_name

        with open(ws_path, "wb") as f:
            f.write(encoded)
        with open(dl_path, "wb") as f:
            f.write(encoded)

        cleaned_records.append((clean_name, ws_path))
        if idx % 10 == 0 or idx == len(all_names):
            print(f"  [Watermark Removal] {idx:3d}/{len(all_names)}: {raw_name[:35]}... -> {clean_name}")

    print(f"\n[SUCCESS] All {len(cleaned_records)} images cleaned in {time.time() - t0:.2f}s!")

    # Package cleaned ZIP
    print(f"[*] Packaging Cleaned ZIP: {DL_CLEAN_ZIP}")
    with zipfile.ZipFile(DL_CLEAN_ZIP, "w", zipfile.ZIP_DEFLATED) as cz:
        for fname, path in cleaned_records:
            cz.write(path, arcname=fname)
    print(f"[SUCCESS] Cleaned ZIP created ({DL_CLEAN_ZIP.stat().st_size / (1024*1024):.2f} MB)")
    return cleaned_records

def step2_upscale_gpu(total_images):
    print("\n" + "=" * 70)
    print("[STEP 2/3] REAL-ESRGAN GPU 4X SUPER-RESOLUTION (NVIDIA RTX 4050)")
    print("=" * 70)

    cmd = [
        str(REALESRGAN_EXE),
        "-i", str(CLEAN_DIR_WS),
        "-o", str(RAW_DIR_WS),
        "-n", "realesrgan-x4plus-anime",
        "-s", "4",
        "-f", "png",
        "-g", "0",
        "-j", "2:2:2"
    ]

    print(f"[*] Launching command: {' '.join(cmd)}")
    start_time = time.time()
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

    last_reported = 0
    while True:
        line = proc.stdout.readline()
        if not line and proc.poll() is not None:
            break
        current_raw_count = len(list(RAW_DIR_WS.glob("*.png")))
        if current_raw_count > last_reported and (current_raw_count % 5 == 0 or current_raw_count == total_images):
            elapsed = time.time() - start_time
            pct = (current_raw_count / total_images) * 100
            eta = (elapsed / current_raw_count) * (total_images - current_raw_count) if current_raw_count > 0 else 0
            print(f"  [Progress] {current_raw_count}/{total_images} frames upscaled ({pct:.1f}%) | Elapsed: {elapsed/60:.1f}m | ETA: {eta/60:.1f}m")
            last_reported = current_raw_count

    proc.wait()
    print(f"\n[SUCCESS] AI GPU 4x Super-Resolution finished in {(time.time() - start_time)/60:.1f} minutes!")

def step3_downsample_4k():
    print("\n" + "=" * 70)
    print("[STEP 3/3] DOWNSAMPLING TO 4K UHD (3840x2144) WITH LANCZOS RESAMPLING")
    print("=" * 70)

    raw_files = sorted(list(RAW_DIR_WS.glob("*.png")))
    total = len(raw_files)
    print(f"[*] Found {total} upscaled 5K PNG frames to convert.")

    target_w = 3840
    target_h = 2144

    t0 = time.time()
    for idx, r_file in enumerate(raw_files, 1):
        fname = r_file.stem
        out_name = f"{fname}.jpg"
        out_local = FINAL_4K_DIR_WS / out_name
        out_dl = DL_4K_DIR / out_name

        with Image.open(r_file) as im:
            im_4k = im.resize((target_w, target_h), Image.Resampling.LANCZOS)
            im_4k.save(out_local, "JPEG", quality=100, subsampling=0)
            im_4k.save(out_dl, "JPEG", quality=100, subsampling=0)

        if idx % 10 == 0 or idx == total:
            print(f"  [Lanczos 4K] {idx:3d}/{total} master 4K frames processed...")

    print(f"\n[SUCCESS] 4K Lanczos downsampling complete in {time.time() - t0:.2f}s!")

    # Package Final 4K ZIP
    print(f"[*] Packaging Final 4K ZIP: {DL_4K_ZIP}")
    with zipfile.ZipFile(DL_4K_ZIP, "w", zipfile.ZIP_DEFLATED) as zf:
        for f in sorted(DL_4K_DIR.glob("*.jpg")):
            zf.write(f, f.name)

    zip_size_mb = DL_4K_ZIP.stat().st_size / (1024 * 1024)
    print(f"[SUCCESS] Final 4K Deliverable ZIP created: {DL_4K_ZIP} ({zip_size_mb:.2f} MB)")

def main():
    cleaned_records = step1_clean_watermarks()
    step2_upscale_gpu(len(cleaned_records))
    step3_downsample_4k()
    print("\n" + "=" * 70)
    print("[COMPLETE] ALL IMAGES CLEANED & UPSCALED TO 4K!")
    print(f"• Cleaned 1080p Directory: {DL_CLEAN_DIR}")
    print(f"• Cleaned 1080p ZIP:       {DL_CLEAN_ZIP}")
    print(f"• 4K Images Directory:     {DL_4K_DIR}")
    print(f"• 4K Deliverable ZIP:      {DL_4K_ZIP}")
    print("=" * 70)

if __name__ == "__main__":
    main()
