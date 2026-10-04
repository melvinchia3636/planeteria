"""Embed the Moon's surface textures as data-URL textures for the web globe.

Two origin-clean base64 textures so the globe can switch between the
true-colour mosaic and the hypsometric elevation map:

    web/moon/lunar_truecolor.js   ->  window.LUNAR_TEXTURE
    web/moon/lunar_elev.js        ->  window.LUNAR_ELEV
"""

from __future__ import annotations

import base64
import os
import tempfile

import rasterio
from rasterio.enums import Resampling


def encode(src, width, name, out):
    with rasterio.open(src) as ds:
        rgb = ds.read(out_shape=(3, width // 2, width), resampling=Resampling.average)
    fd, tmp = tempfile.mkstemp(suffix=".png")
    os.close(fd)
    try:
        with rasterio.open(
            tmp, "w", driver="PNG", width=width, height=width // 2,
            count=3, dtype="uint8",
        ) as dst:
            dst.write(rgb)
        with open(tmp, "rb") as f:
            b64 = base64.b64encode(f.read()).decode("ascii")
    finally:
        os.remove(tmp)
    data = 'window.%s="data:image/png;base64,%s";' % (name, b64)
    with open(out, "w") as f:
        f.write(data)
    print("saved %s  %dx%d  %.1f MB" % (out, width, width // 2, len(data) / 1e6))


def main():
    encode("output/moon/lunar_truecolor.png", 4096, "LUNAR_TEXTURE",
           "web/moon/lunar_truecolor.js")
    encode("output/moon/lunar_relief.png", 2048, "LUNAR_ELEV",
           "web/moon/lunar_elev.js")


if __name__ == "__main__":
    main()
