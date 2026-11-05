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
    diameter_mm: float = 66.0      # body outer diameter (nominal, unverified)
    height_mm: float = 115.0       # total height incl. rim (nominal, unverified)
    neck_taper_mm: float = 10.0    # height of top taper
    top_diameter_mm: float = 54.0  # lid diameter after taper
    base_taper_mm: float = 6.0     # bottom taper height
    base_diameter_mm: float = 52.0
    dome_depth_mm: float = 8.0     # concave bottom dome depth

    def profile(self):
        """(radius, height, v) samples from bottom centre to top centre, in metres."""
        r, h = self.diameter_mm / 2, self.height_mm
        pts = []
        # concave dome bottom, centre -> base ring
        for t in np.linspace(0, 1, 8):
            pts.append((self.base_diameter_mm / 2 * t * 0.9, self.dome_depth_mm * (1 - t) ** 2 * 0.0 + self.dome_depth_mm * (1 - t), 0.0))
        pts.append((self.base_diameter_mm / 2, 0.0, 0.0))
        y0 = self.base_taper_mm
        y1 = h - self.neck_taper_mm
        for t in np.linspace(0, 1, 6)[1:]:
            pts.append((self.base_diameter_mm / 2 + (r - self.base_diameter_mm / 2) * np.sin(t * np.pi / 2), y0 * t, 0.0))
        # printable straight wall
        for t in np.linspace(0, 1, 12)[1:]:
            pts.append((r, y0 + (y1 - y0) * t, t))
        # neck taper
        for t in np.linspace(0, 1, 8)[1:]:
            s = np.sin(t * np.pi / 2)
            pts.append((r + (self.top_diameter_mm / 2 - r) * s, y1 + self.neck_taper_mm * t, 1.0))
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
            UV.append([i / n_around, v])
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
        for u in UV: f.write("vt %.6f %.6f\n" % (u[0], 1.0 - u[1]))  # image row 0 = top
        for n in N: f.write("vn %.6f %.6f %.6f\n" % tuple(n))
        for a, b, c in F + 1:
            f.write(f"f {a}/{a}/{a} {b}/{b}/{b} {c}/{c}/{c}\n")
