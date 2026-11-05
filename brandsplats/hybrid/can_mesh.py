"""Parametric 330 ml beverage-can mesh (surface of revolution) with cylindrical UVs.

Dimensions are NOMINAL defaults for a standard 330 ml can and MUST be replaced
with calipers measurements of the physical can before any fidelity claim.
The printable body band maps to u in [0,1] around the circumference and
v in [0,1] along the straight wall.
"""
from dataclasses import dataclass
import numpy as np

@dataclass
class CanSpec:
    # Sleek 330 ml (user-supplied 2026-11-05): height 145.4, body dia 58.0-58.4 (mid 58.2), base ~46.2.
    diameter_mm: float = 58.2
    height_mm: float = 145.4
    base_diameter_mm: float = 46.2
    # NOT supplied -> ASSUMED, flagged in reports:
    neck_taper_mm: float = 9.0
    top_diameter_mm: float = 52.0
    base_taper_mm: float = 5.0
    dome_depth_mm: float = 8.0
    # Label wrap canvas (user-supplied): 182 x 139 mm; safe 173 x 133.5; 2 mm overlap
    label_w_mm: float = 182.0
    label_h_mm: float = 139.0
    label_safe_w_mm: float = 173.0
    label_safe_h_mm: float = 133.5
    label_overlap_mm: float = 2.0
    @property
    def label_y0_mm(self): return (self.height_mm - self.label_h_mm) / 2   # ASSUMED vertically centred

    def profile(self):
        """(radius, height, v) samples from bottom centre to top centre, in metres."""
        r, h = self.diameter_mm / 2, self.height_mm
        pts = []
        # concave dome bottom, centre -> base ring
        for t in np.linspace(0, 1, 8):
            pts.append((self.base_diameter_mm / 2 * t * 0.9, self.dome_depth_mm * (1 - t), 0.0))
        pts.append((self.base_diameter_mm / 2, 0.0, 0.0))
        y0 = self.base_taper_mm
        y1 = h - self.neck_taper_mm
        for t in np.linspace(0, 1, 6)[1:]:
            pts.append((self.base_diameter_mm / 2 + (r - self.base_diameter_mm / 2) * np.sin(t * np.pi / 2), y0 * t, y0 * t / h))
        # printable straight wall
        for t in np.linspace(0, 1, 12)[1:]:
            pts.append((r, y0 + (y1 - y0) * t, (y0 + (y1 - y0) * t) / h))
        # neck taper
        for t in np.linspace(0, 1, 8)[1:]:
            s = np.sin(t * np.pi / 2)
            pts.append((r + (self.top_diameter_mm / 2 - r) * s, y1 + self.neck_taper_mm * t, (y1 + self.neck_taper_mm * t) / h))
        pts.append((self.top_diameter_mm / 2 - 2, h - 1.5, 1.0))
        pts.append((0.0, h - 1.5, 1.0))
        a = np.array(pts)
        a[:, :2] *= 1e-3
        return a

def build_can_mesh(spec: CanSpec = CanSpec(), n_around: int = 256):
    prof = spec.profile()
    # drop duplicate consecutive points
    keep = [0] + [i for i in range(1, len(prof)) if np.linalg.norm(prof[i, :2] - prof[i - 1, :2]) > 1e-9]
    prof = prof[keep]
    n_p = len(prof)
    # smooth normals from profile tangent
    tang = np.gradient(prof[:, :2], axis=0)
    nrm2 = np.stack([tang[:, 1], -tang[:, 0]], 1)
    nrm2 /= np.linalg.norm(nrm2, axis=1, keepdims=True) + 1e-12
    th = np.linspace(0, 2 * np.pi, n_around + 1)  # duplicated seam for UVs
    V, N, UV = [], [], []
    for j in range(n_p):
        r, y, v = prof[j]
        for i, t in enumerate(th):
            V.append([r * np.cos(t), y, r * np.sin(t)])
            N.append([nrm2[j, 0] * np.cos(t), nrm2[j, 1], nrm2[j, 0] * np.sin(t)])
            UV.append([1.0 - i / n_around, v])  # u runs clockwise seen from above so the label is not mirrored
    F = []
    w = n_around + 1
    for j in range(n_p - 1):
        for i in range(n_around):
            a, b, c, d = j * w + i, j * w + i + 1, (j + 1) * w + i, (j + 1) * w + i + 1
            F += [[a, c, b], [b, c, d]]
    return np.array(V, np.float32), np.array(N, np.float32), np.array(UV, np.float32), np.array(F, np.uint32)

def write_obj(path, V, N, UV, F):
    with open(path, "w") as f:
        for v in V: f.write("v %.6f %.6f %.6f\n" % tuple(v))
        for u in UV: f.write("vt %.6f %.6f\n" % (u[0], u[1]))  # Mitsuba: v=0 is image BOTTOM
        for n in N: f.write("vn %.6f %.6f %.6f\n" % tuple(n))
        for a, b, c in F + 1:
            f.write(f"f {a}/{a}/{a} {b}/{b}/{b} {c}/{c}/{c}\n")
