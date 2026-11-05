"""Turntable video -> flat (cylindrical) label texture.

Assumptions (all checked or reported, none hidden): fixed camera, can rotating about a vertical axis,
camera roughly at can mid-height looking horizontally (small perspective), can radius known from the silhouette.
Rotation per frame is estimated from the image (phase correlation at the can centre), NOT assumed.
Colours are only as good as the input frames (tone-mapped HDR in the first run) - see report.
"""
import glob, cv2, numpy as np

def load_gray(paths, scale=1.0):
    out = []
    for p in paths:
        im = cv2.imread(p)
        out.append(cv2.cvtColor(im, cv2.COLOR_BGR2GRAY).astype(np.float32))
    return np.array(out)

def silhouette(gray_stack):
    """Can = pixels whose value changes over time (label turns); background is static. Returns mask + geometry."""
    sd = gray_stack.std(0)
    sd = cv2.GaussianBlur(sd, (0, 0), 3)
    _, m = cv2.threshold(sd.astype(np.uint8), 0, 1, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    n, lab, stats, _ = cv2.connectedComponentsWithStats(m)
    k = 1 + np.argmax(stats[1:, cv2.CC_STAT_AREA]); m = (lab == k).astype(np.uint8)
    cnts, _ = cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    m = np.zeros_like(m); cv2.drawContours(m, cnts, -1, 1, -1)       # fill holes
    ys, xs = np.nonzero(m)
    top, bot = ys.min(), ys.max()
    rows = np.arange(top + int(.25 * (bot - top)), top + int(.75 * (bot - top)))   # straight wall region
    L = np.array([np.nonzero(m[r])[0].min() for r in rows]); R = np.array([np.nonzero(m[r])[0].max() for r in rows])
    return dict(mask=m, top=int(top), bot=int(bot), axis_x=float(((L + R) / 2).mean()), radius=float(((R - L) / 2).mean()),
                axis_x_std=float(((L + R) / 2).std()), width_std=float((R - L).std()))

def track_axis(gray_stack, rows, cx0, r0, smooth=15):
    """Per-frame can centre/width from the silhouette edges (strongest horizontal gradients), followed frame to frame.
    Edge detection is noisy (~7-11 px row scatter on this clip), so the axis is median-smoothed over `smooth` frames."""
    cx, Rr, L_, R_ = cx0, r0, [], []
    for f in gray_stack:
        gx = cv2.Sobel(cv2.GaussianBlur(f, (0, 0), 2.5), cv2.CV_32F, 1, 0, ksize=3)
        Ls = [int(cx - Rr - 110) + np.argmax(gx[r, int(cx - Rr - 110):int(cx - Rr + 110)]) for r in rows]
        Rs = [int(cx + Rr - 110) + np.argmin(gx[r, int(cx + Rr - 110):int(cx + Rr + 110)]) for r in rows]
        L, R = np.median(Ls), np.median(Rs); cx = .5 * cx + .5 * (L + R) / 2; Rr = .5 * Rr + .5 * (R - L) / 2
        L_.append(L); R_.append(R)
    L_, R_ = np.array(L_), np.array(R_)
    k = smooth; pad = lambda a: np.pad(a, k // 2, mode="edge")
    sm = lambda a: np.array([np.median(pad(a)[i:i + k]) for i in range(len(a))])
    return sm((L_ + R_) / 2), float(np.median((R_ - L_) / 2)), (R_ - L_) / 2

def proj(phi, R, k):
    """Screen x offset from the can axis of the surface point at angle phi from the camera-facing line.
    k = camera distance / can radius (None = orthographic). R = silhouette half-width in px (tangent points)."""
    if k is None: return R * np.sin(phi)
    return R * np.sqrt(k * k - 1) * np.sin(phi) / (k - np.cos(phi))

def centre_gain(R, k):
    """d(screen x)/d(angle) at the front-centre, px/rad."""
    return R if k is None else R * np.sqrt(k * k - 1) / (k - 1)

def estimate_angles(gray_stack, axes, R, top, bot, k=None):
    """Cumulative rotation (rad) of the surface point at the can axis. Frames are compared AFTER re-centring on the
    tracked axis, so the can's wobble across the frame is removed. Content moving left => angle increases."""
    y0, y1 = int(top + .15 * (bot - top)), int(top + .85 * (bot - top)); hw = int(.5 * R)
    win = cv2.createHanningWindow((2 * hw, y1 - y0), cv2.CV_32F); sh, resp = [], []
    for i in range(len(gray_stack) - 1):
        a = gray_stack[i][y0:y1, int(axes[i]) - hw:int(axes[i]) + hw]; b = gray_stack[i + 1][y0:y1, int(axes[i + 1]) - hw:int(axes[i + 1]) + hw]
        (dx, dy), r = cv2.phaseCorrelate(a, b, win); sh.append(dx); resp.append(r)
    sh = np.array(sh); return np.concatenate([[0], np.cumsum(-sh / centre_gain(R, k))]), sh, np.array(resp)

def build_texture(frames_bgr, theta, axes, R, top, bot, phi_max_deg=40.0, k=None):
    """Per texture pixel: median over all views that see that surface angle within +-phi_max of the can's front."""
    W = int(round(2 * np.pi * centre_gain(R, k))); H = bot - top + 1; phi_max = np.radians(phi_max_deg)
    u = (np.arange(W) + .5) / W * 2 * np.pi; per_col = [[] for _ in range(W)]
    for i, t in enumerate(theta):
        phi = (u - t + np.pi) % (2 * np.pi) - np.pi
        for j in np.nonzero(np.abs(phi) < phi_max)[0]: per_col[j].append((i, axes[i] + proj(phi[j], R, k)))
    tex = np.zeros((H, W, 3), np.uint8); cov = np.zeros(W, np.int32); spread = np.zeros(W, np.float32)
    for j in range(W):
        cols = []
        for i, x in per_col[j]:
            xi = int(np.floor(x)); f = x - xi
            if 0 <= xi < frames_bgr[i].shape[1] - 1:
                cols.append((1 - f) * frames_bgr[i][top:bot + 1, xi].astype(np.float32) + f * frames_bgr[i][top:bot + 1, xi + 1].astype(np.float32))
        cov[j] = len(cols)
        if cols:
            st = np.stack(cols); tex[:, j] = np.median(st, 0).astype(np.uint8); spread[j] = np.median(np.abs(st - np.median(st, 0)))  # view disagreement (lower = sharper/more consistent)
    return tex, cov, spread
