import os
from PIL import Image
from rembg import remove

os.makedirs("assets/cutouts", exist_ok=True)
src_img = "assets/images/cleaned/LINE_13-A.jpeg"
cutout_path = "assets/cutouts/LINE_13-A_cutout.png"

print(f"Loading {src_img}...")
img = Image.open(src_img).convert("RGBA")
print("Generating clean cutout with rembg...")
cutout = remove(img)
cutout.save(cutout_path, "PNG")
print(f"Cutout saved successfully: {cutout_path} ({os.path.getsize(cutout_path)} bytes)")
