from PIL import Image
from rembg import remove
import os

os.makedirs("assets/cutouts", exist_ok=True)

for name in ["LINE_1-B", "LINE_2-A"]:
    out_path = f"assets/cutouts/{name}_cutout.png"
    if not os.path.exists(out_path):
        src_path = f"assets/images/cleaned/{name}.jpeg"
        print(f"Generating cutout for {src_path}...")
        img = Image.open(src_path).convert("RGBA")
        cutout = remove(img)
        cutout.save(out_path)
        print(f"Saved {out_path}!")
    else:
        print(f"Cutout {out_path} already exists.")
