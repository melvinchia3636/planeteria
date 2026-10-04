"""True-colour Earth: Blue Marble draped with the ETOPO hillshade.

Blue Marble (NASA, public domain) already carries the surface colour and its
own gentle bathymetry shading, so the ETOPO hillshade is applied fully on land
and only lightly over the oceans to avoid double-darkening.

    uv run scripts/earth/render_truecolor.py  ->  output/earth/earth_truecolor.png
"""

from __future__ import annotations

import time

import earth_common
import numpy as np
import rasterio

WIDTH = 8192
AZIMUTH = 315.0
ALTITUDE = 45.0
Z_FACTOR = 6.0
AMBIENT = 0.25
OCEAN_FLOOR = 0.92  # keep Blue Marble's own ocean shading
OUT = "output/earth/earth_truecolor.png"


def main():
    t0 = time.time()
    z, dpp = earth_common.read_dem(WIDTH)
    z = np.nan_to_num(z, nan=0.0)
    rgb = earth_common.read_colour(WIDTH)
    print("colour %s  field %s  %.1fs" % (rgb.shape, z.shape, time.time() - t0))

    shade = earth_common.hillshade(
        z, dpp, azimuth=AZIMUTH, altitude=ALTITUDE, z_factor=Z_FACTOR
    )
    w = np.clip((z + 1500.0) / 1500.0, 0.0, 1.0)  # 0 ocean -> 1 land
    shade_eff = w * shade + (1.0 - w) * OCEAN_FLOOR

    rgb *= (AMBIENT + (1.0 - AMBIENT) * shade_eff)[..., None]
    out = np.clip(rgb * 255.0, 0, 255).astype(np.uint8).transpose(2, 0, 1)

    with rasterio.open(
        OUT, "w", driver="PNG", width=z.shape[1], height=z.shape[0],
        count=3, dtype="uint8",
    ) as dst:
        dst.write(out)
    print("saved %s  %.1fs" % (OUT, time.time() - t0))


if __name__ == "__main__":
    main()
