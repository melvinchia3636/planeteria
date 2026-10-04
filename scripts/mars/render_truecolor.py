"""True-colour Mars: Viking colour mosaic draped with the MOLA hillshade.

    uv run scripts/mars/render_truecolor.py  ->  output/mars/mars_truecolor.png
"""

from __future__ import annotations

import time

import mars_common
import numpy as np
import rasterio

WIDTH = 8192
AZIMUTH = 315.0
ALTITUDE = 40.0
Z_FACTOR = 1.2
AMBIENT = 0.25
OUT = "output/mars/mars_truecolor.png"


def main():
    t0 = time.time()
    z, dpp = mars_common.read_dem(WIDTH)
    z = np.nan_to_num(z, nan=0.0)
    rgb = mars_common.read_colour(WIDTH)
    print("colour %s  field %s  %.1fs" % (rgb.shape, z.shape, time.time() - t0))

    shade = mars_common.hillshade(
        z, dpp, azimuth=AZIMUTH, altitude=ALTITUDE, z_factor=Z_FACTOR
    )
    rgb *= (AMBIENT + (1.0 - AMBIENT) * shade)[..., None]
    out = np.clip(rgb * 255.0, 0, 255).astype(np.uint8).transpose(2, 0, 1)

    with rasterio.open(
        OUT, "w", driver="PNG", width=z.shape[1], height=z.shape[0],
        count=3, dtype="uint8",
    ) as dst:
        dst.write(out)
    print("saved %s  %.1fs" % (OUT, time.time() - t0))


if __name__ == "__main__":
    main()
