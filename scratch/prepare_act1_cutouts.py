import os
from PIL import Image
from rembg import remove

os.makedirs("assets/cutouts", exist_ok=True)

act1_shots = [
    "LINE_1-B", "LINE_2-A", "LINE_2-B", "LINE_3-A", "LINE_3-B",
    "LINE_4-A", "LINE_5-B", "LINE_6-A", "LINE_7-A", "LINE_7-B",
    "LINE_7-C", "LINE_8-A", "LINE_9-A", "LINE_9-B", "LINE_10-A",
    "LINE_10-B", "LINE_11-A", "LINE_12-A"
]

print(f"Generating cutouts for {len(act1_shots)} Act 1 shots on GPU...")

for idx, name in enumerate(act1_shots, 1):
    out_path = f"assets/cutouts/{name}_cutout.png"
    if os.path.exists(out_path):
        print(f"  [{idx}/{len(act1_shots)}] {name} already exists. Skipping.")
        continue
        
    src_path = f"assets/images/cleaned/{name}.jpeg"
    if not os.path.exists(src_path):
        print(f"  [!] Missing source {src_path}")
        continue
        
    print(f"  [{idx}/{len(act1_shots)}] Extracting {name}...")
    img = Image.open(src_path).convert("RGBA")
    cutout = remove(img)
    cutout.save(out_path)

print("[SUCCESS] All Act 1 cutouts ready!")
