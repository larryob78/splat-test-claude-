"""Unwrap a turntable clip's label. Usage: python run_unwrap.py FRAMES_DIR OUT_DIR [k1,k2,...]  (k = camera distance / can radius; 'inf' = orthographic)"""
import glob, sys, json, numpy as np, cv2
from brandsplats.capture.unwrap import *
D, OUT = sys.argv[1], sys.argv[2]; ks = [None if x == "inf" else float(x) for x in (sys.argv[3] if len(sys.argv) > 3 else "inf").split(",")]
fs = sorted(glob.glob(D + "/f_*.png")); g = load_gray(fs); frames = [cv2.imread(f) for f in fs]
axes, R, Rt = track_axis(g, np.arange(600, 1450, 10), 545., 240.); top, bot = 360, 1560
res = []
for k in ks:
    th, sh, resp = estimate_angles(g, axes, R, top, bot, k=k)
    tex, cov, spread = build_texture(frames, th, axes, R, top, bot, k=k)
    mid = slice(int(.25 * tex.shape[0]), int(.75 * tex.shape[0]))
    r = dict(k=("inf" if k is None else k), rot_deg=round(float(np.degrees(th[-1])), 1), tex_w=tex.shape[1], tex_h=tex.shape[0],
             view_disagreement=round(float(spread[cov > 1].mean()), 2), px_per_mm_front=round(float(centre_gain(R, k) / 29.1), 2))
    print(r, flush=True); res.append(r); cv2.imwrite(f"{OUT}/label_unwrap_k{r['k']}.png", tex)
json.dump(dict(R_px=R, R_width_noise_px=float(np.std(Rt)), axis_range=[float(axes.min()), float(axes.max())], sweep=res), open(OUT + "/unwrap_sweep.json", "w"), indent=1)
