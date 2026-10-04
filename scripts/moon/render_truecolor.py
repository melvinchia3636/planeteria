"""Drape a real true-colour lunar albedo map with the LOLA hillshade.

The DEM carries no colour, so this pulls NASA SVS's public-domain "CGI Moon
Kit" LROC WAC colour map (equirectangular, centred on 0 deg) and multiplies it
by the hillshade computed from the LOLA elevation gradients. The colour map is
rolled 180 deg so it line up with the 0..360E DEM (verified by correlating
brightness against elevation).

    uv run scripts/moon/render_truecolor.py    ->  output/moon/lunar_truecolor.png
"""

from __future__ import annotations

import os
import time
import urllib.request

import common
import numpy as np
import rasterio
import render_relief
from rasterio.enums import Resampling

COLOR_URL = (
    "https://svs.gsfc.nasa.gov/vis/a000000/a004700/a004720/lroc_color_poles_8k.tif"
)
COLOR = "data/moon/lroc_color_poles_8k.tif"

WIDTH = 8192  # output width; matches the 8k WAC colour map 1:1
AZIMUTH = 315.0
ALTITUDE = 35.0
Z_FACTOR = 1.8
AMBIENT = 0.22  # shading floor (the albedo map supplies the base tone)
SATURATION = 1.0  # 1.0 = faithful LROC WAC colour; >1 boosts mineral tints
OUT = "output/moon/lunar_truecolor.png"


def fetch_colour(path=COLOR, url=COLOR_URL):
    if not os.path.exists(path):
        print("downloading %s ..." % url)
        urllib.request.urlretrieve(url, path)
    return path


def main():
    t0 = time.time()
    fetch_colour()

    W, H = WIDTH, WIDTH // 2
    with rasterio.open(common.LABEL) as ds:
        field = (
            ds.read(1, out_shape=(H, W), resampling=Resampling.average).astype(
                np.float32
            )
            * ds.scales[0]
        )
        mpp = abs(ds.transform.a) * (ds.width / W)
    with rasterio.open(COLOR) as cds:
        rgb = cds.read(out_shape=(3, H, W), resampling=Resampling.average)
        rgb = rgb.astype(np.float32).transpose(1, 2, 0) / 255.0  # (H, W, 3)
    rgb = np.roll(rgb, W // 2, axis=1)  # WAC centred on 0 deg -> 0..360E
    print("colour %s  field %s  %.1f m/px  %.1fs"
          % (rgb.shape, field.shape, mpp, time.time() - t0))

    if SATURATION != 1.0:
        grey = rgb.mean(axis=2, keepdims=True)
        rgb = grey + (rgb - grey) * SATURATION

    shade = render_relief.hillshade(
        field, mpp, azimuth=AZIMUTH, altitude=ALTITUDE, z_factor=Z_FACTOR
    )
    rgb *= (AMBIENT + (1.0 - AMBIENT) * shade)[..., None]

    out = np.clip(rgb * 255.0, 0, 255).astype(np.uint8).transpose(2, 0, 1)
    with rasterio.open(
        OUT,
        "w",
        driver="PNG",
        width=W,
        height=H,
        count=3,
        dtype="uint8",
    ) as dst:
        dst.write(out)
    print("saved %s  %.1fs" % (OUT, time.time() - t0))


if __name__ == "__main__":
    main()
