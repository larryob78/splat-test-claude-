import numpy as np
from skimage.metrics import structural_similarity
from skimage.color import rgb2lab, deltaE_ciede2000

def psnr(a, b, peak=1.0):
    mse = np.mean((a - b) ** 2); return float("inf") if mse == 0 else 10 * np.log10(peak**2 / mse)
def ssim(a, b): return structural_similarity(a, b, channel_axis=-1, data_range=1.0)
def srgb_to_lin(x): x = np.asarray(x, float); return np.where(x <= .04045, x / 12.92, ((x + .055) / 1.055) ** 2.4)
def delta_e2000(lin_rgb_a, lin_rgb_b):
    """CIEDE2000 between two linear-sRGB colours (D65). Use on ColorChecker-normalised photos for real brand-red checks."""
    enc = lambda x: np.where(x <= .0031308, 12.92 * x, 1.055 * np.power(np.clip(x, 0, None), 1/2.4) - .055)
    a = rgb2lab(np.clip(enc(np.asarray(lin_rgb_a, float)), 0, 1).reshape(1, 1, 3))
    b = rgb2lab(np.clip(enc(np.asarray(lin_rgb_b, float)), 0, 1).reshape(1, 1, 3))
    return float(deltaE_ciede2000(a, b)[0, 0])
