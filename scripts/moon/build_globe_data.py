"""Build the GeoJSON contour data used by the d3 globe (web/moon/).

Emits one simplified dataset as a JS global so `web/moon/index.html` can load it
with a plain <script> tag (no fetch / CORS issues when opened from disk):

    web/moon/lunar_contours.js   ->  window.CONTOURS

Coordinates are [longitude, latitude] in degrees wrapped to the 0..360 grid.

    uv run scripts/moon/build_globe_data.py
"""

from __future__ import annotations

import json
import time

import common
import numpy as np
from scipy.ndimage import gaussian_filter1d
from skimage.measure import approximate_polygon, find_contours

FACTOR = 8
INTERVAL = 500.0
PATH_SIGMA = 1.0
MIN_PERIMETER = 5.0
PAD = 40
TOLERANCE = 0.04   # Douglas-Peucker simplification, degrees (~0.6 px at 16 ppd)
DECIMALS = 3
OUT = "web/moon/lunar_contours.js"


def main():
    t0 = time.time()
    field, eff = common.load_field(FACTOR)
    field = np.pad(field, ((0, 0), (PAD, PAD)), mode="wrap")

    off = INTERVAL / 2
    lo = np.floor((field.min() - off) / INTERVAL) * INTERVAL + off
    hi = np.ceil((field.max() - off) / INTERVAL) * INTERVAL + off
    levels = np.arange(lo, hi + 1, INTERVAL)

    rings = []
    for lv in levels:
        for c in find_contours(field, lv):
            if len(c) < 2:
                continue
            if np.hypot(np.diff(c[:, 0]), np.diff(c[:, 1])).sum() < MIN_PERIMETER:
                continue
            closed = np.hypot(c[0, 0] - c[-1, 0], c[0, 1] - c[-1, 1]) < 1e-6
            yy, xx = (c[:-1, 0], c[:-1, 1]) if closed else (c[:, 0], c[:, 1])
            mode = "wrap" if closed else "nearest"
            xx = gaussian_filter1d(xx, PATH_SIGMA, mode=mode)
            yy = gaussian_filter1d(yy, PATH_SIGMA, mode=mode)
            lon = (xx - PAD + 0.5) / eff
            lat = 90.0 - (yy + 0.5) / eff
            rings.append((np.column_stack([lon, lat]), closed))
    print("%d levels | %d rings  %.1fs" % (len(levels), len(rings), time.time() - t0))

    coords = []
    for ring, closed in rings:
        a = approximate_polygon(ring, tolerance=TOLERANCE)
        if len(a) < (3 if closed else 2):
            continue
        r = [[round(float(x), DECIMALS), round(float(y), DECIMALS)] for x, y in a]
        if closed:
            r[-1] = r[0]
        coords.append(r)
    geo = {"type": "MultiLineString", "coordinates": coords}
    data = "window.CONTOURS=" + json.dumps(geo, separators=(",", ":")) + ";"
    with open(OUT, "w") as f:
        f.write(data)
    print("saved %s  lines %d  %.1f MB  %.1fs"
          % (OUT, len(coords), len(data) / 1e6, time.time() - t0))


if __name__ == "__main__":
    main()
