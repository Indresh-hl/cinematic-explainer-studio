from PIL import Image, ImageDraw, ImageFont, ImageFilter

base_path = "assets/images/4k/LINE_2-A.jpg"
cutout_path = "assets/cutouts/LINE_2-A_cutout.png"
font_path = "assets/fonts/PlayfairDisplay.ttf"

base = Image.open(base_path).convert("RGBA")
cutout = Image.open(cutout_path).convert("RGBA").resize(base.size, Image.Resampling.LANCZOS)
w, h = base.size

txt_layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
shadow_layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
tdraw = ImageDraw.Draw(txt_layer)
sdraw = ImageDraw.Draw(shadow_layer)

font_size = 185
font = ImageFont.truetype(font_path, font_size)

# The phrase that VEED destroyed: "physically exhausted."
# In our smart layout: anchored in the open negative space on the RIGHT side of the frame
# Word 1: "physically"
# Word 2: "exhausted."
phrase_w1 = "physically"
phrase_w2 = "exhausted."

# Measure widths
tw1 = tdraw.textbbox((0, 0), phrase_w1, font=font)[2] - tdraw.textbbox((0, 0), phrase_w1, font=font)[0]
tw2 = tdraw.textbbox((0, 0), phrase_w2, font=font)[2] - tdraw.textbbox((0, 0), phrase_w2, font=font)[0]

# Place in the open upper-right negative space
tx1 = int(w * 0.52) # Just brushing behind the contour of his hair
ty1 = int(h * 0.22)

tx2 = int(w * 0.55)
ty2 = int(h * 0.38)

# Ambient shadow
sdraw.text((tx1 + 10, ty1 + 14), phrase_w1, font=font, fill=(15, 30, 45, 180))
sdraw.text((tx2 + 10, ty2 + 14), phrase_w2, font=font, fill=(15, 30, 45, 180))
shadow_blurred = shadow_layer.filter(ImageFilter.GaussianBlur(radius=16))

# Word 1: Active pop (Sunglow Gold)
tdraw.text((tx1, ty1), phrase_w1, font=font, fill=(255, 209, 102, 255))
# Word 2: Butter Cream
tdraw.text((tx2, ty2), phrase_w2, font=font, fill=(255, 242, 168, 220))

comp = Image.alpha_composite(base, shadow_blurred)
comp = Image.alpha_composite(comp, txt_layer)
final = Image.alpha_composite(comp, cutout)

out_path = "assets/images/LINE_2-A_CORRECTED_4K.jpg"
final.convert("RGB").save(out_path, quality=98)
print(f"Saved {out_path}")
