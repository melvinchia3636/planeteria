"""Encode a downsampled Earth heightmap for the 3D terrain globe.

    web/earth/earth_height.js   ->  window.EARTH_HEIGHT
"""

from __future__ import annotations

import base64
import json

import numpy as np
import rasterio
from rasterio.enums import Resampling

SRC = "data/earth/ETOPO_2022_v1_30s_N90W180_surface.tif"
SCALE = 1.0
WIDTH = 1024
NAME = "EARTH_HEIGHT"
OUT = "web/earth/earth_height.js"


def main():
    h = WIDTH // 2
    with rasterio.open(SRC) as ds:
        z = ds.read(1, out_shape=(h, WIDTH), resampling=Resampling.average)
        z = z.astype(np.float32) * SCALE
    z[z <= -90000] = 0.0
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
