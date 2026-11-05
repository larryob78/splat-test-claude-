"""Synthetic studio HDRI (equirect, linear): dark gradient + two softboxes. Reproducible, not a measured light probe."""
import numpy as np, mitsuba as mi
def make_env(path, w=1024, h=512):
    v, u = np.mgrid[0:h, 0:w]; th = (v + .5) / h * np.pi; ph = (u + .5) / w * 2 * np.pi
    img = np.ones((h, w, 3), np.float32) * (0.02 + 0.03 * np.cos(th)[..., None] ** 2)
    def box(ph0, th0, sz, rgb, val):
        m = (np.abs(((ph - ph0 + np.pi) % (2*np.pi)) - np.pi) < sz) & (np.abs(th - th0) < sz)
        img[m] = np.array(rgb) * val
    box(np.radians(60), np.radians(70), np.radians(18), (1, 1, 1), 12.0)
    box(np.radians(230), np.radians(85), np.radians(12), (1, .9, .8), 8.0)
    mi.Bitmap(np.ascontiguousarray(img.astype(np.float32))).write(path)
