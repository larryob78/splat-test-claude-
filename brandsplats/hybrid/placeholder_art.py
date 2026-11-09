"""PLACEHOLDER label art for pipeline testing ONLY (no licensed Coca-Cola artwork available).

Atlas = full can height x label-canvas width at `px` px/mm. The 182x139 mm label canvas sits
at the vertically centred band; everything outside is bare aluminium (mask 0).
Flat brand-red fill (#F40009) with safe-area / overlap guides so wrap + seam can be inspected.
Swap in official artwork with the same canvas geometry via make_atlas_from_canvas().
"""
import numpy as np
from PIL import Image, ImageDraw, ImageFont
BRAND_RED = (0xF4, 0x00, 0x09)

def make_atlas_from_canvas(canvas: Image.Image, spec, px=10):
    W, H = int(spec.label_w_mm * px), int(spec.height_mm * px)
    ch = int(spec.label_h_mm * px); canvas = canvas.convert("RGB").resize((W, ch))
    top = int(round((H - (spec.label_y0_mm + spec.label_h_mm) * px)))  # image row 0 = can top
    art = Image.new("RGB", (W, H), (128, 128, 128)); art.paste(canvas, (0, top))
    m = np.zeros((H, W), np.uint8); m[top:top + ch] = 255
    return art, Image.fromarray(m)

def make_placeholder(path_rgb, path_mask, spec, px=10):
    W, ch = int(spec.label_w_mm * px), int(spec.label_h_mm * px)
    c = Image.new("RGB", (W, ch), BRAND_RED); d = ImageDraw.Draw(c)
    sw, sh = spec.label_safe_w_mm * px, spec.label_safe_h_mm * px
    d.rectangle([(W - sw) / 2, (ch - sh) / 2, (W + sw) / 2, (ch + sh) / 2], outline=(255, 255, 255), width=4)
    d.rectangle([W - spec.label_overlap_mm * px, 0, W, ch], fill=(255, 220, 0))  # seam/overlap strip
    f = ImageFont.load_default(size=120)
    d.text((W // 2, ch // 2), "PLACEHOLDER - NOT OFFICIAL ARTWORK", fill=(255, 255, 255), font=f, anchor="mm")
    art, mask = make_atlas_from_canvas(c, spec, px); art.save(path_rgb); mask.save(path_mask)


def make_brand_mask(path_mask, spec, px=10, grow_px=8):
    """Atlas mask (255 = brand-critical: lettering/logo that a finishing model must never alter). For the placeholder this is
    the text; for real artwork supply a logo/lettering mask with the same atlas geometry instead."""
    import cv2
    W, ch, H = int(spec.label_w_mm * px), int(spec.label_h_mm * px), int(spec.height_mm * px)
    c = Image.new("L", (W, ch), 0); d = ImageDraw.Draw(c)
    d.text((W // 2, ch // 2), "PLACEHOLDER - NOT OFFICIAL ARTWORK", fill=255, font=ImageFont.load_default(size=120), anchor="mm")
    top = int(round(H - (spec.label_y0_mm + spec.label_h_mm) * px)); m = np.zeros((H, W), np.uint8); m[top:top + ch] = np.array(c)
    m = cv2.dilate(m, np.ones((grow_px, grow_px), np.uint8)); Image.fromarray(m).save(path_mask)
