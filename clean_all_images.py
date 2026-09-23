import os
import re
import zipfile
from pathlib import Path
import cv2
import numpy as np
import gemini_watermark_remover as gwr

ZIP_SRC = r"c:\Users\Indresh HL\Downloads\youtube long fromat\assets\images\download.zip"
CLEAN_DIR_WORKSPACE = Path(r"c:\Users\Indresh HL\Downloads\youtube long fromat\assets\images\cleaned")
CLEAN_DIR_DOWNLOADS = Path(r"C:\Users\Indresh HL\Downloads\TOPIC_01_CLEANED_IMAGES")
CLEAN_ZIP_OUT = Path(r"C:\Users\Indresh HL\Downloads\TOPIC_01_ALL_IMAGES_CLEANED.zip")

CLEAN_DIR_WORKSPACE.mkdir(parents=True, exist_ok=True)
CLEAN_DIR_DOWNLOADS.mkdir(parents=True, exist_ok=True)

def main():
    print(f"Opening archive: {ZIP_SRC}")
    z = zipfile.ZipFile(ZIP_SRC, "r")
    all_names = z.namelist()
    print(f"Total entries in archive: {len(all_names)}")

    # Initialize Watermark Remover
    remover = gwr.WatermarkRemover()
    alpha = remover.alpha_map_small  # 48x48
    alpha_padded = np.pad(alpha, 6, mode="constant")  # 60x60
    mask_star = (alpha_padded > 0.005).astype(np.uint8) * 255
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    dilated_star = cv2.dilate(mask_star, kernel, iterations=1)

    full_mask = np.zeros((768, 1376), dtype=np.uint8)
    full_mask[641:641+60, 1249:1249+60] = dilated_star

    cleaned_records = []
    unwanted_skipped = []

    for idx, raw_name in enumerate(all_names, 1):
        # Filter out unwanted composite storyboard / contact sheets
        if "Storyboard" in raw_name or not raw_name.startswith("LINE_"):
            print(f"[-] SKIPPING UNWANTED IMAGE: {raw_name}")
            unwanted_skipped.append(raw_name)
            continue

        # Extract clean canonical line label (e.g., LINE_1-A, LINE_28-B, LINE_55-B)
        match = re.match(r"(LINE_\d+-[A-Z]|LINE_\d+)", raw_name)
        if match:
            clean_label = match.group(1)
        else:
            clean_label = f"IMAGE_{idx:03d}"

        clean_filename = f"{clean_label}.jpeg"

        # Read image from zip buffer
        raw_bytes = z.read(raw_name)
        img = cv2.imdecode(np.frombuffer(raw_bytes, dtype=np.uint8), cv2.IMREAD_COLOR)
        if img is None:
            print(f"[!] Error decoding {raw_name}")
            continue

        h, w = img.shape[:2]

        # Ensure mask matches image dimensions
        if h == 768 and w == 1376:
            # 1. Reverse alpha color blending on the 48x48 core region
            roi = img[647:647+48, 1255:1255+48]
            blended_roi = remover.remove_watermark_from_region(roi, alpha)
            img_blended = img.copy()
            img_blended[647:647+48, 1255:1255+48] = blended_roi

            # 2. Seamless inpaint with Telea on the dilated perimeter
            cleaned = cv2.inpaint(img_blended, full_mask, inpaintRadius=3, flags=cv2.INPAINT_TELEA)
        else:
            # Generic detection fallback if dimensions differ
            cleaned = remover.remove_watermark(img, auto_detect=False)

        # Save with maximum 100% JPEG quality
        _, encoded = cv2.imencode(".jpeg", cleaned, [cv2.IMWRITE_JPEG_QUALITY, 100])
        
        # Save to workspace cleaned folder
        out_ws = CLEAN_DIR_WORKSPACE / clean_filename
        with open(out_ws, "wb") as f:
            f.write(encoded)

        # Save to user Downloads folder
        out_dl = CLEAN_DIR_DOWNLOADS / clean_filename
        with open(out_dl, "wb") as f:
            f.write(encoded)

        cleaned_records.append((clean_label, clean_filename, out_ws))
        print(f"[{len(cleaned_records)}/116] Cleaned: {raw_name[:30]}... -> {clean_filename}")

    # Build Master Clean ZIP
    print(f"\nPackaging all {len(cleaned_records)} cleaned images into ZIP: {CLEAN_ZIP_OUT}")
    with zipfile.ZipFile(CLEAN_ZIP_OUT, "w", zipfile.ZIP_DEFLATED) as cz:
        for label, fname, path in cleaned_records:
            cz.write(path, arcname=fname)

    print("[SUCCESS] WATERMARK REMOVAL & COLOR BLENDING COMPLETE!")
    print(f"• Total Processed & Cleaned: {len(cleaned_records)} scene images")
    print(f"• Unwanted Images Removed: {len(unwanted_skipped)} ({', '.join(unwanted_skipped)})")
    print(f"• Workspace Directory: {CLEAN_DIR_WORKSPACE}")
    print(f"• Downloads Folder: {CLEAN_DIR_DOWNLOADS}")
    print(f"• Master ZIP Archive: {CLEAN_ZIP_OUT} ({CLEAN_ZIP_OUT.stat().st_size / (1024*1024):.2f} MB)")
    print("="*70)

if __name__ == "__main__":
    main()
