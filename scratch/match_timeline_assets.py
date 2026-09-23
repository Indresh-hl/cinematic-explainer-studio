import cv2
import glob
import os
import numpy as np

sampled = sorted(glob.glob("assets/sampled_frame_*s.jpg"), key=lambda x: int(os.path.basename(x).split('_')[2].replace('s.jpg','')))
cleaned = sorted(glob.glob("assets/images/cleaned/*.jpeg"))

# Pre-load cleaned images as small thumbnails
clean_thumbs = {}
for c in cleaned:
    name = os.path.splitext(os.path.basename(c))[0]
    im = cv2.imread(c)
    clean_thumbs[name] = cv2.resize(im, (160, 90))

print("Matching sampled frames to cleaned assets:")
for s in sampled:
    t_str = os.path.basename(s).split('_')[2].replace('.jpg','')
    sim = cv2.imread(s)
    small_s = cv2.resize(sim, (160, 90))
    
    best_name = None
    best_diff = float("inf")
    for name, thumb in clean_thumbs.items():
        diff = np.mean(cv2.absdiff(small_s, thumb))
        if diff < best_diff:
            best_diff = diff
            best_name = name
            
    print(f"  At {t_str:>3}: Best match = {best_name} (diff: {best_diff:.1f})")
