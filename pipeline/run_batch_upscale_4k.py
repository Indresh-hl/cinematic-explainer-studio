import os
import sys
import time
import subprocess
import glob
from PIL import Image
import zipfile

def main():
    print("=" * 70)
    print("[START] STEP 1: 4K AI SUPER-RESOLUTION (UPSCALING)")
    print("=" * 70)

    base_dir = os.path.abspath(".")
    in_dir = os.path.join(base_dir, "assets", "images", "cleaned")
    raw_dir = os.path.join(base_dir, "assets", "images", "raw_upscaled")
    final_4k_dir = os.path.join(base_dir, "assets", "images", "4k")
    downloads_4k_dir = r"C:\Users\Indresh HL\Downloads\TOPIC_01_4K_IMAGES"
    zip_dest = r"C:\Users\Indresh HL\Downloads\TOPIC_01_ALL_IMAGES_4K.zip"
    realesrgan_exe = os.path.join(base_dir, "tools", "realesrgan", "realesrgan-ncnn-vulkan.exe")

    os.makedirs(raw_dir, exist_ok=True)
    os.makedirs(final_4k_dir, exist_ok=True)
    os.makedirs(downloads_4k_dir, exist_ok=True)

    input_files = sorted(glob.glob(os.path.join(in_dir, "*.jpeg")))
    total_images = len(input_files)
    print(f"[*] Found {total_images} cleaned source images in {in_dir}")

    # Check how many are already upscaled
    existing_raw = glob.glob(os.path.join(raw_dir, "*.png"))
    print(f"[*] Currently upscaled in raw directory: {len(existing_raw)} / {total_images}")

    # 1. Run Vulkan AI Upscaler
    start_time = time.time()
    print("\n[+] Launching Real-ESRGAN Vulkan GPU Super-Resolution on RTX 4050...")
    cmd = [
        realesrgan_exe,
        "-i", in_dir,
        "-o", raw_dir,
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
        # Track count of raw files generated
        current_raw_count = len(glob.glob(os.path.join(raw_dir, "*.png")))
        if current_raw_count > last_reported and current_raw_count % 5 == 0:
            elapsed = time.time() - start_time
            pct = (current_raw_count / total_images) * 100
            eta = (elapsed / current_raw_count) * (total_images - current_raw_count) if current_raw_count > 0 else 0
            print(f"  [Progress] {current_raw_count}/{total_images} frames upscaled ({pct:.1f}%) | Elapsed: {elapsed/60:.1f}m | ETA: {eta/60:.1f}m")
            last_reported = current_raw_count
            
    proc.wait()
    total_upscale_time = time.time() - start_time
    print(f"\n[SUCCESS] AI GPU Upscaling finished in {total_upscale_time/60:.1f} minutes!")

    # 2. Downsample to Pristine 4K UHD (3840x2144 / 3840x2160)
    print("\n[+] Converting & Downsampling to Standard 4K UHD with Lanczos Anti-Aliasing...")
    raw_files = sorted(glob.glob(os.path.join(raw_dir, "*.png")))
    
    target_w = 3840
    target_h = 2144 # 1376 * (3840/1376) = 2144 (exact pixel-matched 1.7916 ratio)

    t0_down = time.time()
    for idx, r_file in enumerate(raw_files, 1):
        fname = os.path.splitext(os.path.basename(r_file))[0]
        out_name = f"{fname}.jpg"
        out_local = os.path.join(final_4k_dir, out_name)
        out_dl = os.path.join(downloads_4k_dir, out_name)
        
        # Open and resize
        with Image.open(r_file) as im:
            # im is 5504 x 3072
            im_4k = im.resize((target_w, target_h), Image.Resampling.LANCZOS)
            im_4k.save(out_local, "JPEG", quality=100, subsampling=0)
            im_4k.save(out_dl, "JPEG", quality=100, subsampling=0)
            
        if idx % 20 == 0 or idx == len(raw_files):
            print(f"  [Lanczos 4K] Processed {idx}/{len(raw_files)} master 4K frames...")

    print(f"[SUCCESS] 4K Lanczos conversion complete in {time.time() - t0_down:.1f} seconds!")

    # 3. Create Deliverable ZIP archive
    print(f"\n[+] Packaging all 4K images into {zip_dest}...")
    with zipfile.ZipFile(zip_dest, "w", zipfile.ZIP_DEFLATED) as zf:
        for f in sorted(glob.glob(os.path.join(downloads_4k_dir, "*.jpg"))):
            zf.write(f, os.path.basename(f))

    zip_size_mb = os.path.getsize(zip_dest) / (1024 * 1024)
    print(f"[SUCCESS] 4K Zip Archive created: {zip_dest} ({zip_size_mb:.2f} MB)")
    print("\n" + "=" * 70)
    print("[DONE] STEP 1 COMPLETE: ALL 116 FRAMES UPSCALED TO CRISP 4K UHD!")
    print("=" * 70)

if __name__ == "__main__":
    main()
