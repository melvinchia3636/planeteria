"""Shared helpers for the LOLA LDEM_128 lunar elevation model.

The DEM is read through GDAL's **PDS driver**, which understands the PDS3 label
(`data/moon/LDEM_128.LBL`) and exposes the georeferencing for free:

    driver   PDS, 46080 x 23040, int16
    scale    0.5  -> height_metres = DN * 0.5 (above the 1737.4 km sphere)
    nodata   -32768
    crs      SIMPLE_CYLINDRICAL MOON (equirectangular, 1737.4 km sphere)

The raw `.IMG` is headerless, so GDAL must be pointed at the *label*.
"""
from __future__ import annotations

import numpy as np
import rasterio
from rasterio.enums import Resampling
from scipy.ndimage import gaussian_filter

LABEL = "data/moon/LDEM_128.LBL"

# Grid / geometry constants (read back from the dataset at runtime).
PPD = 128
NROWS, NCOLS = 180 * PPD, 360 * PPD


def read_dem(factor: int = 8, smooth: bool = False, sigma=(1.0, 2.0), label: str = LABEL):
    """Read the DEM decimated by `factor` and return
    ``(field_metres, eff_ppd, metres_per_pixel)``.

    GDAL performs the decimation with average resampling in C, so the full
    2 GB array is never materialised in Python. The result is a float32 grid of
    elevations in metres above the 1737.4 km reference sphere; row 0 is 90N and
    columns run east from 0 to 360. Pass ``smooth=True`` to low-pass the field.
    """
    with rasterio.open(label) as ds:
        out_shape = (ds.height // factor, ds.width // factor)
        dn = ds.read(1, out_shape=out_shape, resampling=Resampling.average)
        field = dn.astype(np.float32) * ds.scales[0]
        eff_ppd = (ds.width / 360.0) / factor
        mpp = abs(ds.transform.a) * factor
    if smooth:
        field = gaussian_filter(field, sigma, mode="nearest")
    return field, eff_ppd, mpp


def load_field(factor: int = 8, sigma=(1.0, 2.0), label: str = LABEL):
    """Smoothed ``(field_metres, effective_ppd)`` convenience wrapper."""
    field, eff_ppd, _ = read_dem(factor, smooth=True, sigma=sigma, label=label)
    return field, eff_ppd
