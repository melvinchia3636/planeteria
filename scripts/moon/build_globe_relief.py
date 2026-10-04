"""Encode a downsampled lunar heightmap for the 3D terrain globe.

Writes a compact base64 Int16Array of elevations (metres) so the web viewer can
build a displaced sphere mesh:

    web/moon/lunar_height.js   ->  window.LUNAR_HEIGHT
"""

from __future__ import annotations

import base64
import json

import numpy as np
import rasterio
from rasterio.enums import Resampling

SRC = "data/moon/LDEM_128.LBL"
SCALE = 0.5
WIDTH = 1024
NAME = "LUNAR_HEIGHT"
OUT = "web/moon/lunar_height.js"


def main():
    h = WIDTH // 2
    with rasterio.open(SRC) as ds:
        z = ds.read(1, out_shape=(h, WIDTH), resampling=Resampling.average)
        z = z.astype(np.float32) * SCALE
    z = np.nan_to_num(z, nan=0.0)
    data = np.clip(z, -32768, 32767).astype("<i2")
    obj = {
        "w": WIDTH, "h": h,
        "min": float(z.min()), "max": float(z.max()),
        "b64": base64.b64encode(data.tobytes()).decode("ascii"),
    }
    js = "window.%s=%s;" % (NAME, json.dumps(obj, separators=(",", ":")))
    with open(OUT, "w") as f:
        f.write(js)
    print("saved %s  %dx%d  %.0f..%.0f m  %.2f MB"
          % (OUT, WIDTH, h, z.min(), z.max(), len(js) / 1e6))


if __name__ == "__main__":
    main()
