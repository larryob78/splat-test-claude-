"""Validates the rotation estimator on a SIMULATED turntable (known yaw per frame). Idealised: concentric can, no wobble,
no noise, no handheld motion — so it checks formula/sign/scale only, not accuracy on real footage."""
import numpy as np, cv2, pytest
from PIL import Image
from brandsplats.hybrid.can_mesh import CanSpec, build_can_mesh, write_obj
from brandsplats.hybrid.scene import Rig, Light, render, srgb
from brandsplats.capture.unwrap import estimate_angles, track_axis

def test_estimator_recovers_known_rotation(tmp_path):
    sp = CanSpec(); V, N, UV, F = build_can_mesh(sp); write_obj(f"{tmp_path}/can.obj", V, N, UV, F)
    rng = np.random.default_rng(1); W, H = 1820, 1454
    base = cv2.GaussianBlur(rng.random((H, W)).astype(np.float32), (0, 0), 14); base = (base > np.median(base)).astype(np.float32)
    fine = cv2.GaussianBlur(rng.random((H, W)).astype(np.float32), (0, 0), 3); fine = (fine > np.median(fine)).astype(np.float32)
    art = cv2.GaussianBlur(np.stack([base * .9 + .05, fine * .9 + .05, np.clip(base * fine, 0, 1) * .9 + .05], 2), (0, 0), 1.2)
    Image.fromarray((art * 255).astype(np.uint8)).save(f"{tmp_path}/art.png"); Image.fromarray(np.full((H, W), 255, np.uint8)).save(f"{tmp_path}/m.png")
    step, nfr = 3.0, 40; frames = []
    for k in range(nfr):
        im = render(Rig(width=540, height=960, fov=11, cam_elevation_deg=0, cam_distance=.65, can_yaw_deg=k * step,
                        env_kind="constant", env_scale=1., lights=[], floor=False, ink_diffuse_only=True), f"{tmp_path}/can.obj", f"{tmp_path}/art.png", f"{tmp_path}/m.png", spp=8)
        frames.append(cv2.cvtColor(srgb(im), cv2.COLOR_RGB2GRAY).astype(np.float32))
    g = np.array(frames)
    R = 0.5 * 58.2 * (540 / (2 * .65 * np.tan(np.radians(5.5)) * 1000))           # true radius in px from the camera geometry
    axes = np.full(nfr, 270.); k = .65 / (.0582 / 2); th, sh, resp = estimate_angles(g, axes, R, 150, 800, k=k)
    print(f'R px {R:.1f}; expected shift/frame {R*np.radians(step):.2f}px; measured median {np.median(sh):.2f}px')
    est = np.degrees(th[-1]); true = step * (nfr - 1)
    print(f"true {true:.1f} deg, estimated {est:.1f} deg (signed), min phase response {resp.min():.2f}")
    assert abs(abs(est) - true) / true < 0.06   # tolerance after perspective correction (k = D/R known in the simulation)
