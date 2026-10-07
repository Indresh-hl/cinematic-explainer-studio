import os
import glob
import time
import sys
from PIL import Image
from rembg import remove, new_session

def generate_all_cutouts():
    out_dir = "production/topic_02/cutouts"
    os.makedirs(out_dir, exist_ok=True)
    all_clean = sorted(glob.glob("production/topic_02/images/cleaned/*.jpeg"))
    
    print("=" * 75)
    print("EXTRACTING FOREGROUND ALPHA CUTOUTS VIA REMBG (TOPIC 02)")
    print("=" * 75)
    print(f"Total source images: {len(all_clean)}")
    print("Initializing rembg session (u2net)...")
    sys.stdout.flush()
    session = new_session("u2net")
    
    t0 = time.time()
    generated = 0
    skipped = 0
    
    for idx, src_path in enumerate(all_clean, 1):
        name = os.path.splitext(os.path.basename(src_path))[0]
        out_path = f"{out_dir}/{name}_cutout.png"
        
        if os.path.exists(out_path):
            skipped += 1
            continue
            
        t_img = time.time()
        img = Image.open(src_path).convert("RGBA")
        cutout = remove(img, session=session)
        cutout.save(out_path)
        generated += 1
        
        if generated % 10 == 0 or idx == len(all_clean):
            print(f"  [{idx}/{len(all_clean)}] Extracted {name} ({time.time() - t_img:.2f}s) | Generated: {generated}, Skipped: {skipped}")
            sys.stdout.flush()
        
    print(f"\n[DONE] Generated {generated} new cutouts (skipped {skipped}) in {time.time() - t0:.1f}s!")
    sys.stdout.flush()

if __name__ == "__main__":
    generate_all_cutouts()
