"""Render the Moon with a realistic neutral (grey) shaded-relief look.

The LOLA DEM has no colour, only elevation, so this approximates the Moon's
true appearance the way the eye sees it: dark, smooth maria in the lowlands and
bright, rugged highlands, lit by a low Sun. Brightness blends a mild
elevation-driven albedo with the hillshade; the tone stays neutral/warm-grey
rather than a scientific rainbow.

    uv run scripts/moon/render_moon.py    ->  output/moon/lunar_moon.png
"""

from __future__ import annotations

import time

import common
import numpy as np
import rasterio

import render_relief

FACTOR = 8  # 128/8 = 16 px/deg -> 5760 x 2880
AZIMUTH = 315.0
ALTITUDE = 30.0  # a lower sun gives longer, moon-like shadows
Z_FACTOR = 1.8
PCT = (1.0, 99.0)
ALBEDO_MIN = 0.30  # dark maria
ALBEDO_MAX = 0.95  # bright highlands
AMBIENT = 0.22  # shading floor
GAMMA = 0.9
TINT = (255.0, 250.0, 240.0)  # faintly warm grey
OUT = "output/moon/lunar_moon.png"


def main():
    t0 = time.time()
    field, eff, mpp = common.read_dem(FACTOR, smooth=False)
    print(
        "field %s  eff %.1f ppd  %.1f m/px  %.1fs"
        % (field.shape, eff, mpp, time.time() - t0)
    )

    vmin, vmax = np.percentile(field, PCT)
    e = np.clip((field - vmin) / (vmax - vmin), 0.0, 1.0)
    albedo = ALBEDO_MIN + (ALBEDO_MAX - ALBEDO_MIN) * e

    shade = render_relief.hillshade(
        field, mpp, azimuth=AZIMUTH, altitude=ALTITUDE, z_factor=Z_FACTOR
    )
    lum = albedo * (AMBIENT + (1.0 - AMBIENT) * shade)
    lum = np.clip(lum, 0.0, 1.0) ** GAMMA

    gray = (lum * 255.0)[..., None]
    rgb = gray * (np.array(TINT) / 255.0)[None, None, :]
    out = np.clip(rgb, 0, 255).astype(np.uint8).transpose(2, 0, 1)

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
