from PIL import Image, ImageDraw, ImageFont, ImageFilter

base_path = "assets/images/4k/LINE_1-B.jpg"
cutout_path = "assets/cutouts/LINE_1-B_cutout.png"
font_path = "assets/fonts/PlayfairDisplay.ttf"

base = Image.open(base_path).convert("RGBA")
cutout = Image.open(cutout_path).convert("RGBA").resize(base.size, Image.Resampling.LANCZOS)
w, h = base.size

txt_layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
shadow_layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
tdraw = ImageDraw.Draw(txt_layer)
sdraw = ImageDraw.Draw(shadow_layer)

font_size = 175
font = ImageFont.truetype(font_path, font_size)

phrase = "completely silent."
bbox = tdraw.textbbox((0, 0), phrase, font=font)
tw = bbox[2] - bbox[0]
th = bbox[3] - bbox[1]

tx = (w - tw) // 2
ty = int(h * 0.05) # Pure dark wall above headboard

# Ambient shadow
sdraw.text((tx + 10, ty + 14), phrase, font=font, fill=(10, 15, 25, 180))
shadow_blurred = shadow_layer.filter(ImageFilter.GaussianBlur(radius=16))

# Words
bbox1 = tdraw.textbbox((0, 0), "completely ", font=font)
w1 = bbox1[2] - bbox1[0]
tdraw.text((tx, ty), "completely ", font=font, fill=(255, 209, 102, 255))
tdraw.text((tx + w1, ty), "silent.", font=font, fill=(255, 242, 168, 220))

comp = Image.alpha_composite(base, shadow_blurred)
comp = Image.alpha_composite(comp, txt_layer)
final = Image.alpha_composite(comp, cutout)

out_path = "assets/images/LINE_1-B_CORRECTED_V2.jpg"
final.convert("RGB").save(out_path, quality=98)
print(f"Saved {out_path}")
