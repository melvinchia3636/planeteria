"""Colourised shaded-relief map of Earth from ETOPO 2022.

Hypsometric tint (blue oceans, green→brown→white land) multiplied by a
latitude-aware hillshade. Oceans get only a gentle shade so the bathymetry
tint stays readable; land gets the full relief.

    uv run scripts/earth/render_relief.py    ->  output/earth/earth_relief.png
"""

from __future__ import annotations

import time

import earth_common
import numpy as np
import rasterio

WIDTH = 8192
AZIMUTH = 315.0
ALTITUDE = 45.0
Z_FACTOR = 6.0  # ETOPO metres are fine-grained; exaggerate for visible relief
AMBIENT = 0.35
OUT = "output/earth/earth_relief.png"

# (elevation_m, r, g, b); two stops near 0 give a crisp coastline.
PALETTE = [
    (-11000, 8, 16, 58),
    (-6000, 16, 48, 110),
    (-3000, 31, 111, 168),
    (-500, 99, 182, 214),
    (0, 169, 214, 229),
    (1, 56, 140, 60),
    (300, 120, 170, 80),
    (800, 200, 190, 120),
    (2000, 180, 140, 90),
    (3500, 150, 110, 80),
    (5000, 210, 205, 195),
    (8900, 255, 255, 255),
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
    z, dpp = earth_common.read_dem(WIDTH)
    z = np.nan_to_num(z, nan=0.0)
    print("field %s  %.4f deg/px  %.1fs" % (z.shape, dpp, time.time() - t0))

    shade = earth_common.hillshade(
        z, dpp, azimuth=AZIMUTH, altitude=ALTITUDE, z_factor=Z_FACTOR
    )
    w = np.clip((z + 1500.0) / 1500.0, 0.0, 1.0)  # 0 ocean -> 1 land
    shade_eff = w * shade + (1.0 - w) * 0.85

    rgb = colourise(z, PALETTE)
    rgb *= (AMBIENT + (1.0 - AMBIENT) * shade_eff)[..., None]
    out = np.clip(rgb, 0, 255).astype(np.uint8).transpose(2, 0, 1)

    with rasterio.open(
        OUT, "w", driver="PNG", width=z.shape[1], height=z.shape[0],
        count=3, dtype="uint8",
    ) as dst:
        dst.write(out)
    print("saved %s  %.1fs" % (OUT, time.time() - t0))


if __name__ == "__main__":
    main()
