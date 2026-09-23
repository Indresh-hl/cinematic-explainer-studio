import torch
import torchvision.transforms.functional as TF
from PIL import Image
import spandrel
import time

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"Using device: {device}")

model_path = "assets/models/RealESRGAN_x4plus_anime_6B.pth"
print("Loading model via spandrel...")
model = spandrel.ModelLoader().load_from_file(model_path).to(device)
model.eval()

img_path = "assets/images/cleaned/LINE_13-A.jpeg"
img = Image.open(img_path).convert("RGB")
print(f"Input image size: {img.size}")

tensor = TF.to_tensor(img).unsqueeze(0).to(device)

start_time = time.time()
with torch.no_grad():
    output_tensor = model(tensor)
elapsed = time.time() - start_time

output_tensor = output_tensor.squeeze(0).clamp(0, 1)
out_img = TF.to_pil_image(output_tensor.cpu())
print(f"Upscaled size: {out_img.size} in {elapsed:.2f} seconds!")

# Resize to standard 4K (3840 x 2160 or keep native aspect ratio)
# 1376x768 has aspect ratio 1.7916:1 (~16:9). 3840x2144 is exact.
out_path = "assets/images/LINE_13-A_4K.jpg"
out_img.save(out_path, quality=95)
print(f"Saved 4K image to {out_path}!")
