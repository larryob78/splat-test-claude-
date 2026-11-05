# Route C (hybrid digital twin) — status, retest 2026-11-05

Spec used (user-supplied): sleek 330 ml, H 145.4 mm, body Ø 58.0-58.4 (58.2 used), base Ø ~46.2;
label canvas 182 x 139 mm (safe 173 x 133.5, 2 mm overlap); brand red #F40009.
Pass criterion: CIEDE2000 on masked label, speculars (L*>92) excluded: median <= 2.0 AND p95 <= 5.0.
**Assumed (not supplied):** lid Ø 52, neck taper 9 mm, base taper 5 mm, label vertically centred, lacquer IOR 1.5,
ink roughness 0.18, aluminium roughness 0.22. Label art = flat #F40009 PLACEHOLDER (no licensed artwork/CAD).

## Executed results (renders only — no real can photographed; `python run_color_test.py`, outputs/color_test.json)
| Case | median dE00 | p95 dE00 | Mean Lab (target 51.0, 77.5, 62.7) |
|---|---|---|---|
| A uniform white dome, no floor, analytic exposure | 7.69 | 13.55 | 52.2, 60.6, 36.3 |
| B dome + floor + 18% grey-card normalisation | 7.46 | 12.83 | 52.1, 61.7, 37.4 |
| C single softbox key + grey-card normalisation | 10.41 | 35.22 | 41.0, 56.6, 37.9 |
| D CONTROL: matte ink, dome, analytic exposure | 0.20 | 0.69 | 51.5, 76.5, 61.5 |

**All glossy cases FAIL the criterion; the matte control passes.** Control D shows the measurement chain
(masking, Lab conversion, dE00) is correct. The failure in A-C is chroma loss (a* ~61 vs 77.5, b* ~36 vs 63): the
modelled lacquer reflects white light on top of the red, desaturating it. Spec-excluded highlights (L*>92) are <0.5%
of pixels, so exclusion does not remove this broad veil. The size of the veil depends on UNCALIBRATED gloss parameters,
so 7-8 dE is a property of my guessed material, not a finding about a real can.
Case C fails mainly because one-sided lighting makes cylinder shading span many L* levels: a hex-colour target
cannot be met with directional light.

## Implication for the acceptance test (needs a decision)
A fixed hex target is not a valid reference for a glossy printed can. Define the reference as either
(a) measured Lab of the real printed can under the same lighting (photo, grey-card/chart normalised), or
(b) spectrophotometer reading of the label. Otherwise even a perfect twin can fail, or a wrong one pass.

## What still blocks a pass without official artwork and CAD
1. No official artwork: placeholder is flat red; logo, typography and fine print cannot be tested at all.
2. No real-can photos: the pass criterion needs a photographed reference; nothing here is compared with reality.
3. Gloss/IOR/roughness uncalibrated: needs fitting to the real can's photos (chart + chrome ball frames).
4. Label sizing ambiguity: pi x 58.0-58.4 = 182.2-183.5 mm vs 182 mm canvas + 2 mm overlap, so seam handling is unresolved.
5. Assumed profile (lid Ø, neck/base taper, label vertical offset): caliper measurements needed; no CAD.
6. Acceptance reference undefined (see above).
7. Splat/NeRF routes (A/B) not run: no GPU, no footage; KIRI no-turntable/busy-background capture is unvalidated.
8. Papers unverified: arxiv.org / sciencedirect.com blocked in this session.

## Other facts
- 7/7 tests pass (renderer self-consistency, mesh dims 58.2 x 145.4 mm). They do not validate against a real can.
- Perf (CPU, 4 cores, earlier geometry): 2160x3240 @64spp = 72 s, no denoiser. The AOV integrator is ~40x slower than
  plain path tracing, so colour uses plain tracing plus a 4-spp mask pass.
- Capture protocol: docs_CAPTURE_PROTOCOL.md. Wrap check: outputs/wrap_check.png.
