from PIL import Image, ImageDraw, ImageFont, ImageFilter
import os

base_path = "assets/images/4k/LINE_1-B.jpg"
cutout_path = "assets/cutouts/LINE_1-B_cutout.png"
font_path = "assets/fonts/PlayfairDisplay.ttf"

base = Image.open(base_path).convert("RGBA")
cutout = Image.open(cutout_path).convert("RGBA")

# Resize cutout to match 4K base
cutout = cutout.resize(base.size, Image.Resampling.LANCZOS)
w, h = base.size

# Text Layer
txt_layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
shadow_layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
tdraw = ImageDraw.Draw(txt_layer)
sdraw = ImageDraw.Draw(shadow_layer)

font_size = 220 # Scaled for 4K
font = ImageFont.truetype(font_path, font_size)

# The phrase that VEED botched: "completely silent."
# In our smart layout: anchored in the upper dark negative space above the bed
phrase = "completely silent."
bbox = tdraw.textbbox((0, 0), phrase, font=font)
tw = bbox[2] - bbox[0]
th = bbox[3] - bbox[1]

tx = (w - tw) // 2
ty = int(h * 0.17) # In the dark space above the bed, touching hair tip

# Ambient shadow
sdraw.text((tx + 12, ty + 16), phrase, font=font, fill=(15, 20, 30, 160))
shadow_blurred = shadow_layer.filter(ImageFilter.GaussianBlur(radius=20))

# Active word pop on "completely" (Sunglow Gold), "silent." in Butter Cream
# Word 1: "completely "
bbox1 = tdraw.textbbox((0, 0), "completely ", font=font)
w1 = bbox1[2] - bbox1[0]
tdraw.text((tx, ty), "completely ", font=font, fill=(255, 209, 102, 255)) # Active Sunglow Gold #FFD166
# Word 2: "silent."
tdraw.text((tx + w1, ty), "silent.", font=font, fill=(255, 242, 168, 220)) # Butter Cream #FFF2A8

# 3-Layer Sandwich Compositing: Base 4K -> Shadow -> Text -> Sam Cutout
comp = Image.alpha_composite(base, shadow_blurred)
comp = Image.alpha_composite(comp, txt_layer)
final = Image.alpha_composite(comp, cutout)

out_path = "assets/images/LINE_1-B_CORRECTED_4K.jpg"
final.convert("RGB").save(out_path, quality=98)
print(f"SUCCESS! Saved corrected 4K frame at: {out_path}")
