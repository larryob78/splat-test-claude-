"""Per-pixel control channels for a finishing (diffusion) pass: everything the finisher must be conditioned on or protected by."""
import numpy as np, cv2
from PIL import Image
import mitsuba as mi
from brandsplats.hybrid.scene import build_scene, render, Rig

def _sample_atlas(path, uv, gray=False):
    a = np.array(Image.open(path).convert("L" if gray else "RGB")).astype(np.float32)
    H, W = a.shape[:2]; mx = (uv[..., 0] % 1.0) * (W - 1); my = (1.0 - uv[..., 1]) * (H - 1)   # v=0 is the bottom of the atlas
    return cv2.remap(a, mx.astype(np.float32), my.astype(np.float32), cv2.INTER_LINEAR)

def render_channels(rig: Rig, obj, art, mask, brand_mask=None, spp=64, seed=0):
    """-> dict: rgb (linear HDR), can (bool silhouette), depth (m), normal, albedo (0-1), ink (0-1), brand (0-1, protect mask).
    Geometry/uv come from a cheap 4-spp pass; edge pixels (antialiased) are excluded from `can`, so masks are slightly conservative."""
    rgb = render(rig, obj, art, mask, spp=spp, seed=seed)
    sc = build_scene(rig, obj, art, mask, aov=True); ids = [s.id() for s in sc.shapes()]
    out = np.array(mi.render(sc, spp=4, seed=seed)); can = np.abs(out[..., 3] - (ids.index("can") + 1)) < 1e-4
    can = cv2.erode(can.astype(np.uint8), np.ones((3, 3), np.uint8)).astype(bool)
    uv = out[..., 4:6]
    ch = dict(rgb=rgb, can=can, depth=out[..., 6], normal=out[..., 7:10], uv=uv,
              albedo=_sample_atlas(art, uv) / 255., ink=_sample_atlas(mask, uv, True) / 255. * can)
    ch["albedo"] *= can[..., None]
    ch["brand"] = (_sample_atlas(brand_mask, uv, True) / 255. * can) if brand_mask else ch["ink"].copy()
    return ch
