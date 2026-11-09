"""Tests of the BRAND GATES using synthetic stand-ins for a diffusion finisher (noise/grade = acceptable; hue shift / warp / blur =
unacceptable). They validate the checker and the protect-and-composite step, NOT any real diffusion model."""
import numpy as np, cv2, pytest
from brandsplats.hybrid.can_mesh import CanSpec, build_can_mesh, write_obj
from brandsplats.hybrid.placeholder_art import make_placeholder, make_brand_mask
from brandsplats.hybrid.scene import Rig, Light, srgb
from brandsplats.finish.channels import render_channels
from brandsplats.finish.gates import run_gates, composite_protect

@pytest.fixture(scope="module")
def world(tmp_path_factory):
    d = str(tmp_path_factory.mktemp("w")); sp = CanSpec(); V, N, UV, F = build_can_mesh(sp); write_obj(f"{d}/can.obj", V, N, UV, F)
    make_placeholder(f"{d}/art.png", f"{d}/m.png", sp); make_brand_mask(f"{d}/b.png", sp)
    rig = Rig(width=810, height=1440, fov=11, cam_distance=.65, cam_elevation_deg=0, cam_azimuth_deg=180, lights=[Light(position=(-.3, .2, -.5), size=.3)],
              env_kind="constant", env_scale=.3, floor=False)
    ch = render_channels(rig, f"{d}/can.obj", f"{d}/art.png", f"{d}/m.png", f"{d}/b.png", spp=48)
    return ch, srgb(ch["rgb"])

def mild(base, seed=0):      # what an acceptable finisher might do: grain + slight grade + tiny softening
    r = np.random.default_rng(seed); x = cv2.GaussianBlur(base, (0, 0), 0.6).astype(np.float32) * 1.03 + r.normal(0, 2.0, base.shape)
    return np.clip(x, 0, 255).astype(np.uint8)
def hue_shift(base, can):    # brand red drifts towards orange
    hsv = cv2.cvtColor(base, cv2.COLOR_RGB2HSV).astype(np.int32); hsv[..., 0] = np.where(can, (hsv[..., 0] + 8) % 180, hsv[..., 0])
    return cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2RGB)
def warp(base):              # lettering distorted (what generative models do to type)
    h, w = base.shape[:2]; yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    return cv2.remap(base, xx + 7 * np.sin(yy / 6.0), yy + 7 * np.sin(xx / 6.0), cv2.INTER_LINEAR)
def smear(base): return cv2.GaussianBlur(base, (0, 0), 7)

def test_base_reads_and_identity_passes(world):
    ch, base = world; g = run_gates(base, base.copy(), ch); print(g)
    assert g["ocr_recall_base"] == 1.0 and g["PASS"] and g["de00_median"] < 1e-6

def test_mild_finish_passes(world):
    ch, base = world; g = run_gates(base, mild(base), ch); print(g); assert g["PASS"]

@pytest.mark.parametrize("name", ["hue", "warp", "smear"])
def test_bad_finish_is_rejected_then_fixed_by_protect_composite(world, name):
    ch, base = world; cand = {"hue": hue_shift(base, ch["can"]), "warp": warp(base), "smear": smear(base)}[name]
    g = run_gates(base, cand, ch); print(name, "raw  ", {k: round(v, 2) if isinstance(v, float) else v for k, v in g.items()}); assert not g["PASS"]
    fixed = composite_protect(base, cand, ch["brand"]); g2 = run_gates(base, fixed, ch); print(name, "fixed", {k: round(v, 2) if isinstance(v, float) else v for k, v in g2.items()})
    assert g2["pass_color"] and g2["pass_ocr"]      # protected region is identical to the base
