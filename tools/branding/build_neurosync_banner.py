"""
NeuroSync 4K YouTube banner (2560x1440).
Starts from the approved reference banner (Sam, brain, dark navy background),
removes the old "ISY WHY" text block, and sets new NeuroSync typography inside
the mobile-safe zone (1546x423 centred).
"""
from pathlib import Path
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(r"c:\Users\Indresh HL\Downloads\youtube long fromat")
REF = Path(r"C:\Users\Indresh HL\Downloads\LOGO\YOUTUBE_CHANNEL_BANNER_2560x1440.png")
OUT = ROOT / "assets" / "branding" / "YOUTUBE_BANNER_4K_NEUROSYNC.jpg"
PREVIEW_DIR = Path(r"C:\Users\Indresh HL\.gemini\antigravity\brain\f2ab72de-3ac6-4b80-952b-4639ab3d1bc9")

W, H = 2560, 1440
SAFE = (507, 509, 2053, 932)  # x0, y0, x1, y1  (1546 x 423)
FONTS = Path(r"C:\Windows\Fonts")
BLACK = str(FONTS / "seguibl.ttf")
BOLD = str(FONTS / "segoeuib.ttf")
ARIAL_BOLD = str(FONTS / "arialbd.ttf")

TEAL = (61, 214, 196)
YELLOW = (255, 210, 63)
WHITE = (255, 255, 255)
SOFT = (214, 224, 234)

TEXT_X = 550
TEXT_MAX_X = 1450  # keep clear of the brain glow


# ---------------------------------------------------------------- 1. remove old text
img = cv2.imread(str(REF), cv2.IMREAD_COLOR)
assert img.shape[:2] == (H, W), img.shape
x0, y0, x1, y1 = 520, 525, 1420, 870
roi = img[y0:y1, x0:x1]
gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
mask_roi = (gray > 38).astype(np.uint8) * 255
mask_roi = cv2.dilate(mask_roi, np.ones((11, 11), np.uint8))
mask = np.zeros((H, W), np.uint8)
mask[y0:y1, x0:x1] = mask_roi
clean = cv2.inpaint(img, mask, 12, cv2.INPAINT_TELEA)
# smooth the patched area slightly so no ghost outlines remain
blur = cv2.GaussianBlur(clean, (0, 0), 6)
soft_mask = cv2.GaussianBlur(cv2.dilate(mask, np.ones((15, 15), np.uint8)).astype(np.float32) / 255, (0, 0), 8)[..., None]
clean = (clean * (1 - soft_mask) + blur * soft_mask).astype(np.uint8)
base = Image.fromarray(cv2.cvtColor(clean, cv2.COLOR_BGR2RGB)).convert("RGBA")


# ---------------------------------------------------------------- helpers
def fit_font(path, text, size, max_w):
    while size > 10:
        f = ImageFont.truetype(path, size)
        if f.getlength(text) <= max_w:
            return f
        size -= 2
    return ImageFont.truetype(path, size)


def text_layer():
    return Image.new("RGBA", (W, H), (0, 0, 0, 0))


def drop_shadow(layer, offset=(0, 10), blur=18, alpha=170):
    a = layer.split()[3].point(lambda v: v * alpha // 255)
    sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sh.putalpha(a)
    sh = sh.filter(ImageFilter.GaussianBlur(blur))
    out = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    out.alpha_composite(sh, offset)
    return out


# ---------------------------------------------------------------- 2. category chip
chip_text = "NEUROSCIENCE  \u2022  PSYCHOLOGY  \u2022  HABITS"
chip_font = ImageFont.truetype(BOLD, 27)
cw = chip_font.getlength(chip_text)
chip_y = 528
chip = text_layer()
d = ImageDraw.Draw(chip)
d.rounded_rectangle((TEXT_X - 14, chip_y, TEXT_X + 52 + cw, chip_y + 44), radius=22,
                    fill=(61, 214, 196, 28), outline=TEAL + (255,), width=2)
d.ellipse((TEXT_X + 6, chip_y + 16, TEXT_X + 18, chip_y + 28), fill=TEAL + (255,))
d.text((TEXT_X + 32, chip_y + 22), chip_text, font=chip_font, fill=TEAL + (255,), anchor="lm")
base.alpha_composite(chip)


# ---------------------------------------------------------------- 3. title "NEUROSYNC" with 3D extrusion
title_font = fit_font(BLACK, "NEUROSYNC", 172, TEXT_MAX_X - TEXT_X)
title_y = 712  # baseline
neuro_w = title_font.getlength("NEURO")

face = text_layer()
fd = ImageDraw.Draw(face)
fd.text((TEXT_X - 6, title_y), "NEURO", font=title_font, fill=WHITE + (255,), anchor="ls")

# gradient fill for "SYNC"
sync_mask = Image.new("L", (W, H), 0)
ImageDraw.Draw(sync_mask).text((TEXT_X - 6 + neuro_w, title_y), "SYNC", font=title_font, fill=255, anchor="ls")
bbox = sync_mask.getbbox()
grad = Image.new("RGBA", (W, H), (0, 0, 0, 0))
gx0, gy0, gx1, gy1 = bbox
g = np.zeros((gy1 - gy0, gx1 - gx0, 4), np.uint8)
t = np.linspace(0, 1, gy1 - gy0)[:, None]
top, bot = np.array([110, 245, 228]), np.array([24, 160, 200])
g[..., :3] = (top * (1 - t) + bot * t)[:, None, :].astype(np.uint8).repeat(gx1 - gx0, 1).reshape(gy1 - gy0, gx1 - gx0, 3)
g[..., 3] = 255
grad.paste(Image.fromarray(g, "RGBA"), (gx0, gy0))
grad.putalpha(Image.fromarray(np.minimum(np.array(grad.split()[3]), np.array(sync_mask))))
face.alpha_composite(grad)

# extrusion: stacked darker copies down-right
alpha = face.split()[3]
extrude = text_layer()
depth = 9
for i in range(depth, 0, -1):
    shade = int(18 + 30 * (1 - i / depth))
    lay = Image.new("RGBA", (W, H), (shade, shade + 22, shade + 34, 0))
    lay.putalpha(alpha)
    extrude.alpha_composite(lay, (i, i))
base.alpha_composite(drop_shadow(face, offset=(10, 18), blur=22, alpha=200))
base.alpha_composite(extrude)
base.alpha_composite(face)

# ---------------------------------------------------------------- 4. tagline + schedule line
tag_text = "REWIRE YOUR BRAIN  \u2022  MASTER YOUR HABITS"
tag_font = fit_font(BLACK, tag_text, 44, TEXT_MAX_X - TEXT_X)
tag = text_layer()
ImageDraw.Draw(tag).text((TEXT_X, 778), tag_text, font=tag_font, fill=YELLOW + (255,), anchor="lm")
base.alpha_composite(drop_shadow(tag, offset=(0, 4), blur=6, alpha=200))
base.alpha_composite(tag)

sub_text = "3D ANIMATED SCIENCE EXPLAINERS  \u2022  NEW VIDEOS EVERY MONDAY & FRIDAY"
sub_font = fit_font(ARIAL_BOLD, sub_text, 27, TEXT_MAX_X - TEXT_X)
sub = text_layer()
ImageDraw.Draw(sub).text((TEXT_X + 2, 836), sub_text, font=sub_font, fill=SOFT + (255,), anchor="lm")
base.alpha_composite(sub)

# ---------------------------------------------------------------- 5. export + checks
final = base.convert("RGB")
OUT.parent.mkdir(parents=True, exist_ok=True)
final.save(OUT, "JPEG", quality=95, subsampling=0, optimize=True)
size_mb = OUT.stat().st_size / 1024 / 1024
print(f"Saved {OUT}  {final.size}  {size_mb:.2f} MB")
assert size_mb < 6

# content bounds check vs safe zone (text only)
diff = np.abs(np.asarray(final, np.int16) - cv2.cvtColor(clean, cv2.COLOR_BGR2RGB).astype(np.int16)).sum(2) > 40
ys, xs = np.where(diff)
print("text bounds:", xs.min(), ys.min(), xs.max(), ys.max(), "safe:", SAFE)
assert xs.min() >= SAFE[0] and ys.min() >= SAFE[1] and xs.max() <= SAFE[2] and ys.max() <= SAFE[3]

final.save(PREVIEW_DIR / "neurosync_banner_4k.jpg", "JPEG", quality=92)
final.crop(SAFE).save(PREVIEW_DIR / "neurosync_banner_mobile.jpg", "JPEG", quality=92)
# desktop view: YouTube shows full width x ~ 423px tall centre strip (2560x423)
final.crop((0, SAFE[1], W, SAFE[3])).save(PREVIEW_DIR / "neurosync_banner_desktop.jpg", "JPEG", quality=92)
