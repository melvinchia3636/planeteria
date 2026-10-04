"""Render a colourised shaded-relief map of the Moon from the LOLA DEM.

Reads the PDS DEM through GDAL (via `common.read_dem`), builds a hillshade from
the elevation gradients (correctly scaled using the geotransform), tints each
pixel by a hypsometric palette, multiplies the two, and writes a georeferenced
equirectangular PNG (8-bit RGB) through GDAL's PNG driver.

    uv run scripts/moon/render_relief.py    ->  output/moon/lunar_relief.png
"""

from __future__ import annotations

import time

import common
import numpy as np
import rasterio

FACTOR = 8  # DEM block-average (128/8 = 16 px per degree -> 5760 x 2880)
AZIMUTH = 315.0  # sun from the north-west
ALTITUDE = 45.0  # sun elevation, degrees
Z_FACTOR = 2.0  # vertical exaggeration of the relief
AMBIENT = 0.35  # shading floor so lowlands stay readable
GAMMA = 1.0  # colour gamma
PCT = (2.0, 98.0)  # robust elevation range for the colour ramp
OUT = "output/moon/lunar_relief.png"

# Hypsometric palette: (elevation fraction, r, g, b).
PALETTE = [
    (0.00, 10, 12, 40),
    (0.12, 21, 54, 124),
    (0.25, 26, 120, 160),
    (0.38, 40, 170, 140),
    (0.50, 150, 200, 80),
    (0.62, 240, 200, 70),
    (0.74, 235, 130, 55),
    (0.86, 200, 55, 45),
    (1.00, 250, 245, 235),
]


def hillshade(z, mpp, azimuth=AZIMUTH, altitude=ALTITUDE, z_factor=Z_FACTOR):
    """Standard hillshade in [0, 1]; `z` in metres, `mpp` = metres per pixel."""
    x, y = np.gradient(z, mpp, mpp)  # x = d/drow, y = d/dcol
    slope = np.pi / 2.0 - np.arctan(z_factor * np.hypot(x, y))
    aspect = np.arctan2(-x, y)
    az = np.radians(360.0 - azimuth + 90.0)
    alt = np.radians(altitude)
    shaded = np.sin(alt) * np.sin(slope) + np.cos(alt) * np.cos(slope) * np.cos(
        az - aspect
    )
    return np.clip(shaded, 0.0, 1.0)


def colourise(field, vmin, vmax, gamma=GAMMA):
    """Map elevations to an RGB uint8 array using the hypsometric palette."""
    t = np.clip((field - vmin) / (vmax - vmin), 0.0, 1.0)
    if gamma != 1.0:
        t = t ** gamma
    stops = np.array([p[0] for p in PALETTE])
    rgb = np.empty(field.shape + (3,), dtype=np.float32)
    for c in range(3):
        rgb[..., c] = np.interp(t, stops, [p[c + 1] for p in PALETTE])
    return rgb


def main():
    t0 = time.time()
    field, eff, mpp = common.read_dem(FACTOR, smooth=False)
    print(
        "field %s  eff %.1f ppd  %.1f m/px  %.1fs"
        % (field.shape, eff, mpp, time.time() - t0)
    )

    vmin, vmax = np.percentile(field, PCT)
    print("range %.0f .. %.0f m (%.1f..%.1f pct)" % (vmin, vmax, *PCT))

    shade = hillshade(field, mpp)
    rgb = colourise(field, vmin, vmax)
    rgb *= (AMBIENT + (1.0 - AMBIENT) * shade)[..., None]
    out = np.clip(rgb, 0, 255).astype(np.uint8).transpose(2, 0, 1)  # (3, H, W)

    with rasterio.open(
        OUT,
        "w",
        driver="PNG",
        width=out.shape[2],
        height=out.shape[1],
        count=3,
        dtype="uint8",
    ) as dst:
        dst.write(out)
    print("saved %s  %.1fs" % (OUT, time.time() - t0))


if __name__ == "__main__":
    main()
