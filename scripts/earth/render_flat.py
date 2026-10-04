"""Render the global Earth contour map as a flat cylindrical SVG.

Same approach as the Moon map: marching squares -> smoothed
Catmull-Rom cubic-Bézier paths, longitude wrap-padded so seam crossings close.

    uv run scripts/earth/render_flat.py    ->  output/earth/earth_globe.svg
"""

from __future__ import annotations

import time

import earth_common
import numpy as np
from scipy.ndimage import gaussian_filter1d
from skimage.measure import find_contours

WIDTH = 4096  # DEM sample width (~0.088 deg/px)
INTERVAL = 1000.0  # contour interval, metres
PATH_SIGMA = 1.0
DECIMATE = 3
MIN_PERIMETER = 5.0
PAD = 40
S = 10.0  # SVG units per degree
STROKE = 0.25
OUT = "output/earth/earth_globe.svg"


def cr_bezier(xs, ys, closed):
    n = len(xs)
    parts = ["M%.1f,%.1f" % (xs[0], ys[0])]
    segs = range(n) if closed else range(n - 1)
    for i in segs:
        if closed:
            a, b, e = (i - 1) % n, (i + 1) % n, (i + 2) % n
        else:
            a, b = max(i - 1, 0), i + 1
            e = min(i + 2, n - 1)
        c1x, c1y = xs[i] + (xs[b] - xs[a]) / 6.0, ys[i] + (ys[b] - ys[a]) / 6.0
        c2x, c2y = xs[b] - (xs[e] - xs[i]) / 6.0, ys[b] - (ys[e] - ys[i]) / 6.0
        parts.append(
            "C%.1f,%.1f %.1f,%.1f %.1f,%.1f" % (c1x, c1y, c2x, c2y, xs[b], ys[b])
        )
    if closed:
        parts.append("Z")
    return "".join(parts)


def main():
    t0 = time.time()
    field, dpp = earth_common.read_dem(WIDTH)
    field = np.nan_to_num(field, nan=0.0)
    field = np.pad(field, ((0, 0), (PAD, PAD)), mode="wrap")
    print("field %s  %.4f deg/px  %.1fs" % (field.shape, dpp, time.time() - t0))

    off = INTERVAL / 2
    lo = np.floor((field.min() - off) / INTERVAL) * INTERVAL + off
    hi = np.ceil((field.max() - off) / INTERVAL) * INTERVAL + off
    levels = np.arange(lo, hi + 1, INTERVAL)
    scale = S * dpp

    paths, n_closed, n_open = [], 0, 0
    for lv in levels:
        for c in find_contours(field, lv):
            if len(c) < 2:
                continue
            if np.hypot(np.diff(c[:, 0]), np.diff(c[:, 1])).sum() < MIN_PERIMETER:
                continue
            closed = np.hypot(c[0, 0] - c[-1, 0], c[0, 1] - c[-1, 1]) < 1e-6
            if closed:
                yy, xx = c[:-1, 0], c[:-1, 1]
                xx = gaussian_filter1d(xx, PATH_SIGMA, mode="wrap")[::DECIMATE]
                yy = gaussian_filter1d(yy, PATH_SIGMA, mode="wrap")[::DECIMATE]
                n_closed += 1
            else:
                yy, xx = c[:, 0], c[:, 1]
                xx = gaussian_filter1d(xx, PATH_SIGMA, mode="nearest")[::DECIMATE]
                yy = gaussian_filter1d(yy, PATH_SIGMA, mode="nearest")[::DECIMATE]
                n_open += 1
            xs = (xx - PAD + 0.5) * scale
            ys = (yy + 0.5) * scale
            if len(xs) < (3 if closed else 2):
                continue
            paths.append(cr_bezier(xs, ys, closed))
    print("%d levels | paths %d (closed %d, open %d)  %.1fs"
          % (len(levels), len(paths), n_closed, n_open, time.time() - t0))

    W, H = 360.0 * S, 180.0 * S
    svg = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %.0f %.0f" '
        'width="%.0f" height="%.0f">' % (W, H, W, H),
        '<rect width="100%%" height="100%%" fill="#ffffff"/>',
        '<g fill="none" stroke="#000000" stroke-width="%s" '
        'stroke-linejoin="round" stroke-linecap="round">' % STROKE,
    ]
    svg += ['<path d="%s"/>' % d for d in paths]
    svg.append("</g></svg>")
    data = "\n".join(svg)
    with open(OUT, "w") as f:
        f.write(data)
    print("saved %s  %.1f MB  %.1fs" % (OUT, len(data) / 1e6, time.time() - t0))


if __name__ == "__main__":
    main()
