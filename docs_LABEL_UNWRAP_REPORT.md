# Label unwrap from turntable video IMG_0154 (2026-11-05) — approximate, NOT brand-grade

Input: iPhone 16 Pro Max, 1080x1920 portrait, 30 fps, 395 frames, **HDR HLG (BT.2020)**; 198 frames used (every 2nd), converted
to SDR with ffmpeg (zscale + Hable tone-map). Code: `brandsplats/capture/unwrap.py`, `run_unwrap.py`. Output: `outputs/real/label_unwrap_k10.png`.

## Method
Can silhouette tracked per frame (edge gradients) -> frames re-centred on the can axis -> rotation per frame by phase correlation at
the can centre -> each frame's central +-40 deg strip is mapped into a cylinder texture, per-pixel median over views (removes
highlights that stay fixed on screen). Perspective model with k = camera distance / can radius.

## What was measured
- Can axis wanders +-100 px across the clip (can off-centre on the turntable, or camera drift): the fixed-axis assumption failed, so the axis is tracked.
- Silhouette radius from edges: 221.8 px, frame-to-frame scatter 11.8 px (~5%): this directly scales every angle estimate.
- Rotation estimate depends on perspective factor k: inf 301.6 deg, k=14 280.8, k=10 272.8, k=8 266.0, k=6 254.9.
  View-consistency metric barely changes (5.18-5.38), so it does NOT identify k. k~8-10 chosen from (a) front-centre horizontal scale matching
  the vertical scale (~8.5 px/mm) and (b) a 2x-lens model (~9.8). Lens is not recorded in the file; k is an assumption.
- Simulated turntable validation (tests/test_unwrap_angles.py, concentric, noiseless): orthographic model over-estimated by 9.6%; with the perspective
  model 4.8% (true 117 deg, est 122.6). Residual ~5% bias is unexplained. Idealised: says nothing about real-footage accuracy.

## What is wrong in the result (visible in the PNG)
- **Barcode appears twice** around a 2% black gap (31 of 1540 columns uncovered): evidence the rotation is over-estimated by roughly 40 deg
  (the same barcode is seen at the start and end of the clip, so the true total is probably ~230-260 deg, not 273). Not fixed.
- Ghosting on "Cola" and smeared small print / QR / nutrition table; horizontal streaks at panel edges.
- Colours are dim and not valid for the dE00 test (HDR tone-mapping guess; no grey card/chart in frame).
- Vertical/horizontal scale tied by k assumption; true dimensions not measured with calipers.
- Texture seam position is arbitrary (angle origin = first frame).

## Verdict
Good enough to read the layout and artwork content of this can (logo, Santa, panels), not good enough as brand artwork or for colour/typography scoring.

## What would fix it (re-shoot)
1. Can centred on the turntable; camera farther away with a 3x-5x lens (k >> 10: less perspective, less sensitivity to k).
2. Full 360 deg + ~30 deg overlap, constant turntable speed: the loop then closes, giving a measurable closure error (which this clip cannot give).
3. SDR (Rec.709) video, locked exposure/WB, grey card + chart in the first frames, dry can, calipers measurements.
