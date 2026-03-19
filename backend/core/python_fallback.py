"""Pure Python fallback for C++ core functions.

Used when the C++ pybind11 module cannot be loaded (e.g., OpenCV library conflicts).
Implements the same API as semiovis_core but in pure Python using opencv-python.
"""

import cv2
import numpy as np


def compute_saliency_spectral(img_rgb: np.ndarray, scale_factor: float = 1.0) -> np.ndarray:
    """Spectral Residual saliency (Hou & Zhang, 2007)."""
    gray = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2GRAY).astype(np.float32) / 255.0
    orig_h, orig_w = gray.shape

    if scale_factor != 1.0 and scale_factor > 0:
        gray = cv2.resize(gray, None, fx=scale_factor, fy=scale_factor, interpolation=cv2.INTER_AREA)

    h = cv2.getOptimalDFTSize(gray.shape[0])
    w = cv2.getOptimalDFTSize(gray.shape[1])
    padded = np.zeros((h, w), dtype=np.float32)
    padded[:gray.shape[0], :gray.shape[1]] = gray

    dft = cv2.dft(padded, flags=cv2.DFT_COMPLEX_OUTPUT)
    planes = cv2.split(dft)
    mag, phase = cv2.cartToPolar(planes[0], planes[1])
    log_amp = np.log(mag + 1e-10)
    avg_log = cv2.blur(log_amp, (3, 3))
    spectral_res = log_amp - avg_log
    exp_sr = np.exp(spectral_res)
    re, im = cv2.polarToCart(exp_sr, phase)
    inv_complex = cv2.merge([re, im])
    inv_out = cv2.idft(inv_complex)
    inv_split = cv2.split(inv_out)
    sal = cv2.magnitude(inv_split[0], inv_split[1])
    sal = sal ** 2
    sal = cv2.GaussianBlur(sal, (7, 7), 2.5)
    sal = sal[:gray.shape[0], :gray.shape[1]]
    sal = cv2.resize(sal, (orig_w, orig_h), interpolation=cv2.INTER_LINEAR)
    mn, mx = sal.min(), sal.max()
    if mx - mn > 1e-10:
        sal = (sal - mn) / (mx - mn)
    else:
        sal = np.zeros_like(sal)
    return sal.astype(np.float32)


def compute_saliency_itti(img_rgb: np.ndarray, scale_factor: float = 1.0) -> np.ndarray:
    """Simplified Itti-Koch saliency."""
    fimg = img_rgb.astype(np.float32) / 255.0
    orig_h, orig_w = fimg.shape[:2]
    if scale_factor != 1.0:
        fimg = cv2.resize(fimg, None, fx=scale_factor, fy=scale_factor)

    R, G, B = fimg[:, :, 0], fimg[:, :, 1], fimg[:, :, 2]
    intensity = (R + G + B) / 3.0
    RG = np.abs(R - G)
    BY = np.abs((R + G) / 2.0 - B)

    def build_pyr(src, levels=6):
        pyr = [src.copy()]
        for _ in range(1, levels):
            pyr.append(cv2.pyrDown(pyr[-1]))
        return pyr

    pyr_I = build_pyr(intensity)
    pyr_RG = build_pyr(RG)
    pyr_BY = build_pyr(BY)

    def cs(pyr, c, s):
        fine = pyr[c]
        coarse = cv2.resize(pyr[s], (fine.shape[1], fine.shape[0]))
        return np.abs(fine - coarse)

    ci = np.zeros_like(intensity)
    cc = np.zeros_like(intensity)
    for c in [1, 2]:
        for d in [2, 3]:
            s = c + d
            if s >= 6:
                continue
            t = cv2.resize(cs(pyr_I, c, s), (intensity.shape[1], intensity.shape[0]))
            ci += t
            t1 = cv2.resize(cs(pyr_RG, c, s), (intensity.shape[1], intensity.shape[0]))
            t2 = cv2.resize(cs(pyr_BY, c, s), (intensity.shape[1], intensity.shape[0]))
            cc += t1 + t2

    gray = cv2.cvtColor(fimg, cv2.COLOR_RGB2GRAY) if fimg.shape[2] == 3 else fimg
    co = np.zeros_like(gray)
    for theta in [0, np.pi / 4, np.pi / 2, 3 * np.pi / 4]:
        kernel = cv2.getGaborKernel((31, 31), 4.0, theta, 10.0, 0.5, 0, cv2.CV_32F)
        resp = cv2.filter2D(gray, cv2.CV_32F, kernel)
        co += np.abs(resp)

    def norm(m):
        mn, mx = m.min(), m.max()
        return (m - mn) / (mx - mn) if mx - mn > 1e-10 else np.zeros_like(m)

    sal = (norm(ci) + norm(cc) + norm(co)) / 3.0
    sal = cv2.GaussianBlur(sal, (7, 7), 2.5)
    sal = cv2.resize(sal, (orig_w, orig_h))
    sal = norm(sal)
    return sal.astype(np.float32)


def detect_vectors(img_gray: np.ndarray, rho=1.0, theta=np.pi/180, threshold=100,
                   min_line_length=50.0, max_line_gap=10.0) -> list:
    h, w = img_gray.shape
    edges = cv2.Canny(img_gray, 50, 150, apertureSize=3)
    lines = cv2.HoughLinesP(edges, rho, theta, threshold,
                             minLineLength=min_line_length, maxLineGap=max_line_gap)
    result = []
    if lines is None:
        return result
    diag = np.sqrt(w * w + h * h)
    for l in lines:
        x1, y1, x2, y2 = l[0]
        dx, dy = x2 - x1, y2 - y1
        angle = np.degrees(np.arctan2(abs(dy), abs(dx)))
        strength = np.sqrt(dx * dx + dy * dy) / diag
        if angle < 15 or angle > 165:
            direction = "horizontal"
        elif 75 < angle < 105:
            direction = "vertical"
        else:
            direction = "diagonal"
        result.append({"x1": x1/w, "y1": y1/h, "x2": x2/w, "y2": y2/h,
                       "angle": round(angle, 2), "strength": round(strength, 4),
                       "direction": direction})
    return result


def estimate_vanishing_point(img_gray: np.ndarray) -> dict:
    h, w = img_gray.shape
    edges = cv2.Canny(img_gray, 50, 150)
    lines = cv2.HoughLinesP(edges, 1.0, np.pi/180, 80, minLineLength=max(30, w*0.05), maxLineGap=10)
    if lines is None or len(lines) < 4:
        return {"vp_x": None, "vp_y": None, "v_angle": 0.0, "h_angle": 0.0}

    persp = []
    for l in lines:
        x1, y1, x2, y2 = l[0]
        angle = np.degrees(np.arctan2(abs(y2-y1), abs(x2-x1)))
        if 10 < angle < 80:
            a, b, c = y2-y1, x1-x2, x2*y1-x1*y2
            n = np.sqrt(a*a+b*b)
            if n > 0:
                persp.append((a/n, b/n, c/n))

    if len(persp) < 2:
        return {"vp_x": None, "vp_y": None, "v_angle": 0.0, "h_angle": 0.0}

    rng = np.random.RandomState(42)
    best_x, best_y, best_in = w/2, h/2, 0
    thresh = max(h, w) * 0.05
    for _ in range(min(500, len(persp)*len(persp))):
        i, j = rng.randint(0, len(persp), 2)
        if i == j: continue
        a1, b1, c1 = persp[i]
        a2, b2, c2 = persp[j]
        det = a1*b2 - a2*b1
        if abs(det) < 1e-10: continue
        ix = (b1*c2 - b2*c1) / det
        iy = (a2*c1 - a1*c2) / det
        if abs(ix) > w*3 or abs(iy) > h*3: continue
        inliers = sum(1 for a, b, c in persp if abs(a*ix+b*iy+c) < thresh)
        if inliers > best_in:
            best_in = inliers
            best_x, best_y = ix, iy

    if best_in < 3:
        return {"vp_x": None, "vp_y": None, "v_angle": 0.0, "h_angle": 0.0}

    return {"vp_x": best_x/w, "vp_y": best_y/h,
            "v_angle": np.degrees(np.arctan2(h/2 - best_y, w)),
            "h_angle": np.degrees(np.arctan2(best_x - w/2, h))}


def detect_framing_lines(img_gray: np.ndarray, threshold1=50.0, threshold2=150.0) -> dict:
    h, w = img_gray.shape
    edges = cv2.Canny(img_gray, threshold1, threshold2)
    lines = cv2.HoughLinesP(edges, 1.0, np.pi/180, 80, minLineLength=max(50, w*0.15), maxLineGap=10)
    frame_lines = []
    hc = vc = 0
    if lines is not None:
        for l in lines:
            x1, y1, x2, y2 = l[0]
            angle = np.degrees(np.arctan2(abs(y2-y1), abs(x2-x1)))
            length = np.sqrt((x2-x1)**2 + (y2-y1)**2)
            if angle < 10 and length > w*0.3:
                hc += 1
                frame_lines.append({"x1": x1/w, "y1": y1/h, "x2": x2/w, "y2": y2/h, "orientation": "horizontal"})
            elif angle > 80 and length > h*0.3:
                vc += 1
                frame_lines.append({"x1": x1/w, "y1": y1/h, "x2": x2/w, "y2": y2/h, "orientation": "vertical"})
    return {"framing_score": min(1.0, (hc+vc)/6.0), "lines": frame_lines}


def compute_spatial_zones(saliency_map: np.ndarray, img_rgb: np.ndarray,
                          n_cols: int = 3, n_rows: int = 3) -> list:
    h, w = img_rgb.shape[:2]
    gray = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2GRAY)
    hsv = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2HSV)
    global_mean = gray.mean()
    zones = []
    for r in range(n_rows):
        for c in range(n_cols):
            y1, y2 = r*h//n_rows, (r+1)*h//n_rows
            x1, x2 = c*w//n_cols, (c+1)*w//n_cols
            zs = saliency_map[y1:y2, x1:x2]
            zg = gray[y1:y2, x1:x2]
            zh = hsv[y1:y2, x1:x2]
            ms = float(zs.mean())
            edges = cv2.Canny(zg, 50, 150)
            ed = float(np.count_nonzero(edges)) / max(1, edges.size)
            tc = abs(float(zg.mean()) - global_mean) / 255
            hue_std = float(zh[:,:,0].std())
            cc = min(1.0, hue_std / 90)
            lap = cv2.Laplacian(zg, cv2.CV_64F)
            sh = min(1.0, float(lap.std()**2 / 1000))
            avg_hue = float(zh[:,:,0].mean())
            avg_sat = float(zh[:,:,1].mean()) / 255
            if avg_sat < 0.15: ct = "neutral"
            elif avg_hue < 30 or avg_hue > 160: ct = "warm"
            elif 80 < avg_hue < 140: ct = "cool"
            else: ct = "neutral"
            vw = 0.5*ms + 0.2*ed + 0.15*tc + 0.15*sh
            vp = "top" if r == 0 else ("bottom" if r == n_rows-1 else "center")
            hp = "left" if c == 0 else ("right" if c == n_cols-1 else "center")
            pl = "center" if vp == "center" and hp == "center" else f"{vp}-{hp}"
            zones.append({"zone_id": f"{r}_{c}", "row": r, "col": c,
                          "position_label": pl, "semiotic_label": "",
                          "mean_saliency": ms, "visual_weight": vw,
                          "color_temperature": ct, "edge_density": ed,
                          "object_count": 0, "tonal_contrast": tc,
                          "colour_contrast": cc, "has_human_figure": False,
                          "foreground_ratio": 0.0, "sharpness": sh,
                          "information_value_score": vw})
    return zones


def compute_modality_cues(img_rgb: np.ndarray) -> dict:
    hsv = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2HSV)
    gray = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2GRAY)
    h, w = gray.shape
    sat = float(hsv[:,:,1].mean()) / 255
    mask = (hsv[:,:,1] > 25).astype(np.uint8) * 255
    bins = 12
    hist = [0]*bins
    for r in range(h):
        for c in range(0, w, 4):  # sample every 4th pixel for speed
            if mask[r,c] > 0:
                hist[min(int(hsv[r,c,0])*bins//180, bins-1)] += 1
    occ = sum(1 for b in hist if b > h*w//800)
    diff = min(1.0, occ / 8.0)
    s_mean, s_std = cv2.meanStdDev(hsv[:,:,1], mask=mask)
    mod = min(1.0, float(s_std[0][0]) / 80)
    border = max(1, min(h,w)//5)
    pmask = np.zeros((h,w), dtype=np.uint8)
    pmask[:border,:]=255; pmask[h-border:,:]=255; pmask[:,:border]=255; pmask[:,w-border:]=255
    edges = cv2.Canny(gray, 50, 150)
    pe = cv2.bitwise_and(edges, pmask)
    ctx = min(1.0, float(np.count_nonzero(pe)) / max(1, np.count_nonzero(pmask)) * 10)
    lap = cv2.Laplacian(gray, cv2.CV_64F)
    rep = min(1.0, float(lap.std()) / 40)
    gx = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
    gy = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
    mag = cv2.magnitude(gx, gy)
    top_g = float(mag[:h//2,:].mean())
    bot_g = float(mag[h//2:,:].mean())
    gr = top_g / (bot_g + 1e-10)
    dep = min(1.0, abs(1.0 - gr) * 2)
    g_mean, g_std = cv2.meanStdDev(gray)
    ill = min(1.0, float(g_std[0][0]) / 80)
    hist_g = cv2.calcHist([gray.astype(np.float32)], [0], None, [16], [0, 256])
    occ_b = sum(1 for i in range(16) if hist_g[i][0] > h*w/(16*4))
    bri = occ_b / 16
    return {"colour_saturation": sat, "colour_differentiation": diff,
            "colour_modulation": mod, "contextualization": ctx,
            "representation": rep, "depth": dep,
            "illumination": ill, "brightness": bri}


def extract_color_palette(img_rgb: np.ndarray, k: int = 6, max_iter: int = 100) -> list:
    h, w = img_rgb.shape[:2]
    small = cv2.resize(img_rgb, (min(w, 200), min(h, 200))) if h*w > 200*200 else img_rgb
    pixels = small.reshape(-1, 3).astype(np.float32)
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, max_iter, 1.0)
    _, labels, centres = cv2.kmeans(pixels, k, None, criteria, 3, cv2.KMEANS_PP_CENTERS)
    counts = np.bincount(labels.flatten(), minlength=k)
    total = labels.shape[0]
    palette = []
    for i in np.argsort(-counts):
        r, g, b = int(centres[i][0]), int(centres[i][1]), int(centres[i][2])
        palette.append({"rgb": (r, g, b), "hex": f"#{r:02x}{g:02x}{b:02x}",
                        "proportion": float(counts[i]) / total})
    return palette


def compute_texture_features(img_gray: np.ndarray) -> dict:
    proc = cv2.resize(img_gray, (min(500, img_gray.shape[1]), min(500, img_gray.shape[0])))
    fimg = proc.astype(np.float32) / 255.0
    total_e = 0
    orients = []
    for theta in [0, np.pi/4, np.pi/2, 3*np.pi/4]:
        kernel = cv2.getGaborKernel((31, 31), 4.0, theta, 10.0, 0.5, 0, cv2.CV_32F)
        resp = cv2.filter2D(fimg, cv2.CV_32F, kernel)
        e = float((resp**2).mean())
        orients.append({"orientation_deg": np.degrees(theta), "energy": e})
        total_e += e
    return {"gabor_energy": total_e, "gabor_orientations": orients,
            "lbp_histogram": [], "texture_homogeneity": 0.5,
            "texture_contrast": 0.5, "dominant_orientation": orients[np.argmax([o["energy"] for o in orients])]["orientation_deg"]}


def estimate_depth_map(img_rgb: np.ndarray, model_path: str = "") -> np.ndarray:
    h, w = img_rgb.shape[:2]
    gray = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2GRAY)
    lap = cv2.Laplacian(gray, cv2.CV_32F)
    abs_lap = np.abs(lap)
    abs_lap = cv2.GaussianBlur(abs_lap, (51, 51), 15.0)
    vert = np.tile(np.linspace(0, 1, h, dtype=np.float32).reshape(-1, 1), (1, w))
    mn, mx = abs_lap.min(), abs_lap.max()
    if mx - mn > 1e-10:
        abs_lap = (abs_lap - mn) / (mx - mn)
    depth = 0.6 * vert + 0.4 * abs_lap
    mn, mx = depth.min(), depth.max()
    if mx - mn > 1e-10:
        depth = (depth - mn) / (mx - mn)
    return depth.astype(np.float32)


def compute_reading_path(saliency_map: np.ndarray, max_waypoints: int = 10) -> list:
    h, w = saliency_map.shape
    win = max(15, min(h, w) // 20)
    if win % 2 == 0: win += 1
    dilated = cv2.dilate(saliency_map, cv2.getStructuringElement(cv2.MORPH_RECT, (win, win)))
    threshold = saliency_map.min() + (saliency_map.max() - saliency_map.min()) * 0.2
    peaks = []
    for r in range(win//2, h - win//2, win//2):
        for c in range(win//2, w - win//2, win//2):
            v = saliency_map[r, c]
            if v >= threshold and abs(v - dilated[r, c]) < 1e-6:
                peaks.append((c, r, float(v)))
    peaks.sort(key=lambda p: -p[2])
    min_d = max(h, w) // 10
    filtered = []
    for p in peaks:
        if all((p[0]-f[0])**2 + (p[1]-f[1])**2 >= min_d**2 for f in filtered):
            filtered.append(p)
            if len(filtered) >= max_waypoints: break
    return [{"x": p[0]/w, "y": p[1]/h, "saliency": p[2],
             "label": f"waypoint_{i+1}"} for i, p in enumerate(filtered)]
