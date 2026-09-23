import torch
import torchvision.transforms.functional as TF
from PIL import Image
import spandrel
import time
import math

def predict_tiled(model, tensor, tile_size=480, tile_pad=16, scale=4):
    batch, channel, height, width = tensor.shape
    output_height = height * scale
    output_width = width * scale
    output = torch.zeros((batch, channel, output_height, output_width), dtype=tensor.dtype, device=tensor.device)
    output_weights = torch.zeros((batch, 1, output_height, output_width), dtype=tensor.dtype, device=tensor.device)

    tiles_x = math.ceil(width / tile_size)
    tiles_y = math.ceil(height / tile_size)

    for y in range(tiles_y):
        for x in range(tiles_x):
            # Tile coordinates with padding
            ofs_x = x * tile_size
            ofs_y = y * tile_size
            
            # Input tile coordinates
            input_start_x = max(ofs_x - tile_pad, 0)
            input_end_x = min(ofs_x + tile_size + tile_pad, width)
            input_start_y = max(ofs_y - tile_pad, 0)
            input_end_y = min(ofs_y + tile_size + tile_pad, height)

            # Slicing
            input_tile = tensor[:, :, input_start_y:input_end_y, input_start_x:input_end_x]

            # Forward pass
            with torch.no_grad():
                output_tile = model(input_tile)

            # Output tile coordinates
            out_start_x = input_start_x * scale
            out_end_x = input_end_x * scale
            out_start_y = input_start_y * scale
            out_end_y = input_end_y * scale

            # Weight mask (linear falloff at edges)
            tile_h = out_end_y - out_start_y
            tile_w = out_end_x - out_start_x
            
            # Simple blending weight
            w_mask = torch.ones((1, 1, tile_h, tile_w), dtype=tensor.dtype, device=tensor.device)
            pad_scale = tile_pad * scale
            if input_start_x > 0:
                ramp = torch.linspace(0, 1, pad_scale, device=tensor.device).view(1, 1, 1, -1)
                w_mask[:, :, :, :pad_scale] *= ramp
            if input_end_x < width:
                ramp = torch.linspace(1, 0, pad_scale, device=tensor.device).view(1, 1, 1, -1)
                w_mask[:, :, :, -pad_scale:] *= ramp
            if input_start_y > 0:
                ramp = torch.linspace(0, 1, pad_scale, device=tensor.device).view(1, 1, -1, 1)
                w_mask[:, :, :pad_scale, :] *= ramp
            if input_end_y < height:
                ramp = torch.linspace(1, 0, pad_scale, device=tensor.device).view(1, 1, -1, 1)
                w_mask[:, :, -pad_scale:, :] *= ramp

            output[:, :, out_start_y:out_end_y, out_start_x:out_end_x] += output_tile * w_mask
            output_weights[:, :, out_start_y:out_end_y, out_start_x:out_end_x] += w_mask

    output = output / torch.clamp(output_weights, min=1e-5)
    return output

# Test
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print("Device:", device)
model_path = "assets/models/RealESRGAN_x4plus_anime_6B.pth"
model = spandrel.ModelLoader().load_from_file(model_path).to(device).eval()

img = Image.open("assets/images/cleaned/LINE_1-A.jpeg").convert("RGB")
tensor = TF.to_tensor(img).unsqueeze(0).to(device)

t0 = time.time()
with torch.no_grad():
    out = predict_tiled(model, tensor, tile_size=480, tile_pad=24, scale=4)
t1 = time.time()

out = out.squeeze(0).clamp(0, 1)
pil_out = TF.to_pil_image(out.cpu())
print(f"Success! Output size: {pil_out.size} in {t1 - t0:.2f} seconds. Peak GPU memory: {torch.cuda.max_memory_allocated() / (1024**2):.1f} MB")
