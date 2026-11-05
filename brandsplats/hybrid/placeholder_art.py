"""PLACEHOLDER label art for pipeline testing ONLY.

This is NOT official Coca-Cola artwork and says so on its face. Brand-fidelity
results are meaningless until the official dieline/label file is supplied via
`--artwork`. Alpha/mask channel: 1 = printed ink, 0 = bare aluminium.
"""
import numpy as np
from PIL import Image, ImageDraw

def make_placeholder(path_rgb, path_mask, w=4096, h=1536):
    img = Image.new("RGB", (w, h), (200, 16, 30))
    d = ImageDraw.Draw(img)
    d.rectangle([0, int(h * .62), w, int(h * .66)], fill=(245, 245, 245))
    for k in range(4):  # 4 text repeats around the can
        x = k * w // 4 + w // 8
        d.text((x, h // 3), "PLACEHOLDER", fill=(255, 255, 255))
    img.save(path_rgb)
    m = np.full((h, w), 255, np.uint8)
    m[: int(h * .03)] = 0  # bare metal strip at the bottom of the wall
    Image.fromarray(m).save(path_mask)
