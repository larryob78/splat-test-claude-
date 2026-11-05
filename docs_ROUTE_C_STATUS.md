# Route C (hybrid digital twin) — status, 2026-11-05

Run: `python -m pytest -q tests && python run_experiments.py` (CPU only, Mitsuba 3.9.1 `scalar_rgb`).

## What was executed and measured
- Parametric 330 ml can mesh: bbox 66 x 115 x 66 mm (nominal dims, NOT caliper-measured).
- 6/6 tests pass: mesh dimensions, linear intensity scaling, light superposition (mean within 2%),
  env-rotation 360° identity, seed reproducibility (atol 1e-6; bitwise equality fails due to threaded
  float summation, max diff 1.2e-7), ΔE2000 sanity.
- Timings on 4 CPU cores: 8-view turntable at 384x576/64spp = 21 s; 2160x3240 @64spp = 72 s
  (noisy; no denoiser; true 3840x2160 not yet tested).
- Outputs: `outputs/turntable.png`, `relight_key_position.png`, `relight_color_intensity.png`,
  `relight_env_rotation.png`, `can_4k.png`.

## What this does NOT show
- No real can has been photographed or compared. PSNR/SSIM/ΔE harness exists but has no real reference yet.
- Label is a PLACEHOLDER, not official Coca-Cola artwork; brand fidelity is untested.
- Material parameters (Al conductor, roughness 0.18/0.22, IOR 1.5) are uncalibrated guesses.
- Env map is synthetic, not a measured probe. Tests prove renderer self-consistency, not physical accuracy.
- Routes A (Gaussian splatting) and B (NeRF) are not started: need a GPU and real footage.
- Paper verification blocked (arxiv.org / sciencedirect.com not reachable).

## Needed next
1. Official artwork/dieline file + caliper measurements (diameter, height, neck, base) of the real can.
2. Real photos (held-out views incl. ColorChecker) to fit materials and score the render.
3. GPU access (DGX Spark / Colab / Kaggle) for Routes A/B.
4. Allow arxiv.org and sciencedirect.com for paper verification.
