"""Colourised shaded-relief map of Mars from the MOLA DEM.

Hypsometric tint (cool lowlands → warm highlands → white peaks) multiplied by a
latitude-aware hillshade.

    uv run scripts/mars/render_relief.py    ->  output/mars/mars_relief.png
"""

from __future__ import annotations

import time

import mars_common
import numpy as np
import rasterio

WIDTH = 8192
AZIMUTH = 315.0
ALTITUDE = 45.0
Z_FACTOR = 1.2
AMBIENT = 0.35
OUT = "output/mars/mars_relief.png"

PALETTE = [
    (-8000, 30, 20, 80),
    (-3000, 60, 60, 140),
    (-500, 120, 120, 180),
    (0, 150, 120, 110),
    (1000, 175, 115, 85),
    (3000, 200, 130, 90),
    (6000, 220, 165, 120),
    (10000, 235, 200, 165),
    (21000, 250, 248, 245),
]


def colourise(z, stops):
    xs = np.array([s[0] for s in stops], dtype=np.float32)
    rgb = np.empty(z.shape + (3,), dtype=np.float32)
    for c in range(3):
        vals = np.array([s[c + 1] for s in stops], dtype=np.float32)
        rgb[..., c] = np.interp(z, xs, vals)
    return rgb


def main():
    t0 = time.time()
    z, dpp = mars_common.read_dem(WIDTH)
    z = np.nan_to_num(z, nan=0.0)
    print("field %s  %.4f deg/px  %.1fs" % (z.shape, dpp, time.time() - t0))

    shade = mars_common.hillshade(
        z, dpp, azimuth=AZIMUTH, altitude=ALTITUDE, z_factor=Z_FACTOR
    )
    rgb = colourise(z, PALETTE)
    rgb *= (AMBIENT + (1.0 - AMBIENT) * shade)[..., None]
    out = np.clip(rgb, 0, 255).astype(np.uint8).transpose(2, 0, 1)

    with rasterio.open(
        OUT, "w", driver="PNG", width=z.shape[1], height=z.shape[0],
        count=3, dtype="uint8",
    ) as dst:
        dst.write(out)
    print("saved %s  %.1fs" % (OUT, time.time() - t0))


if __name__ == "__main__":
    main()
