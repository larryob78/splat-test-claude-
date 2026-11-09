"""Brand gates for a finishing pass + protect-and-composite. These check a CANDIDATE image against the clean BASE render.
Thresholds follow the project's red criterion (median dE00 <= 2.0, p95 <= 5.0) applied to 'how far did the finisher move the brand pixels'."""
import difflib, re, numpy as np, cv2
from skimage.color import rgb2lab, deltaE_ciede2000

_ocr = None
def _get_ocr():
    global _ocr
    if _ocr is None:
        from rapidocr_onnxruntime import RapidOCR; _ocr = RapidOCR()
    return _ocr

def _norm(s): return re.sub(r"[^A-Z0-9]", "", s.upper())

def ocr_tokens(img_u8, region=None):
    """Return the list of recognised strings (normalised) inside `region` (x0,y0,x1,y1) of an RGB uint8 image."""
    if region: x0, y0, x1, y1 = region; img_u8 = img_u8[y0:y1, x0:x1]
    res, _ = _get_ocr()(np.ascontiguousarray(img_u8)); return [_norm(r[1]) for r in (res or [])]

def token_recall(found, expected, thr=0.8):
    """Fraction of expected tokens matched (fuzzy) by any recognised string (or substring of the joined text)."""
    joined = "".join(found); hit = 0
    for e in map(_norm, expected):
        ok = e in joined or any(difflib.SequenceMatcher(None, e, f).ratio() >= thr for f in found)
        hit += bool(ok)
    return hit / max(1, len(expected))

def silhouette_iou(a, b): a, b = a.astype(bool), b.astype(bool); return float((a & b).sum() / max(1, (a | b).sum()))

def delta_e_in_mask(base_u8, cand_u8, mask):
    sel = mask.astype(bool)
    if not sel.any(): return dict(median=0., p95=0., n=0)
    lab = lambda x: rgb2lab(x[sel].reshape(-1, 1, 3) / 255.).reshape(-1, 3)
    d = deltaE_ciede2000(lab(base_u8), lab(cand_u8)); return dict(median=float(np.median(d)), p95=float(np.percentile(d, 95)), n=int(sel.sum()))

def composite_protect(base_u8, cand_u8, protect, feather_px=3):
    """Brand pixels come from BASE; everything else from the candidate. Feathered so there is no visible halo."""
    m = cv2.GaussianBlur(np.clip(protect.astype(np.float32), 0, 1), (0, 0), feather_px) if feather_px else protect.astype(np.float32)
    m = np.maximum(m, (protect > 0.5).astype(np.float32))[..., None]
    return (base_u8.astype(np.float32) * m + cand_u8.astype(np.float32) * (1 - m)).round().astype(np.uint8)

def run_gates(base_u8, cand_u8, ch, expected_tokens=None, region=None, de_median=2.0, de_p95=5.0, iou_min=0.98, ocr_min=None):
    prot = ch["brand"] > 0.5
    if region is None and prot.any():
        ys, xs = np.nonzero(prot); region = (max(0, xs.min() - 10), max(0, ys.min() - 10), xs.max() + 10, ys.max() + 10)
    base_tok = ocr_tokens(base_u8, region)
    if expected_tokens is None: expected_tokens = [t for t in base_tok if len(t) >= 3]   # regression mode: must still read what the clean render reads
    base_recall = token_recall(base_tok, expected_tokens)
    cand_recall = token_recall(ocr_tokens(cand_u8, region), expected_tokens)
    de = delta_e_in_mask(base_u8, cand_u8, prot)
    # silhouette of the candidate: pixels clearly different from the (uniform-ish) background are not available in general,
    # so compare edge maps of the can region instead (outline drift)
    ed = lambda im: cv2.Canny(cv2.cvtColor(im, cv2.COLOR_RGB2GRAY), 60, 150)
    cand_edges, base_edges = ed(cand_u8), ed(base_u8); k = np.ones((5, 5), np.uint8)
    near = cv2.dilate(base_edges, k) > 0; outline = float((cand_edges[near] > 0).sum() / max(1, (base_edges > 0).sum()))
    need = base_recall if ocr_min is None else ocr_min
    g = dict(ocr_recall_base=base_recall, ocr_recall_cand=cand_recall, de00_median=de["median"], de00_p95=de["p95"], protected_px=de["n"], edge_retention=outline)
    g["pass_ocr"] = cand_recall >= need - 1e-9; g["pass_color"] = de["median"] <= de_median and de["p95"] <= de_p95; g["pass_outline"] = outline >= 0.85
    g["PASS"] = bool(g["pass_ocr"] and g["pass_color"] and g["pass_outline"]); return g
