"""Shared helpers for the Mars MOLA DEM + Viking colour mosaic.

Both rasters are **Simple Cylindrical Mars** (radius 3 396 190 m) georeferenced
in metres, spanning −180…180°E and 90°N…90°S:

    DEM     data/mars/Mars_MGS_MOLA_DEM_mosaic_global_463m.tif   (int16, m)
    colour  data/mars/Mars_Viking_ClrMosaic_global_925m.tif     (RGB)

Slopes use a latitude-dependent metres-per-pixel because the projection maps
longitude linearly (so ground east–west distance shrinks as cos(latitude)).
"""

from __future__ import annotations

import os
import urllib.request

import numpy as np
import rasterio
from rasterio.enums import Resampling
from scipy.ndimage import gaussian_filter

DEM = "data/mars/Mars_MGS_MOLA_DEM_mosaic_global_463m.tif"
DEM_URL = (
    "https://planetarymaps.usgs.gov/mosaic/"
    "Mars_MGS_MOLA_DEM_mosaic_global_463m.tif"
)
COLOUR = "data/mars/Mars_Viking_ClrMosaic_global_925m.tif"
COLOUR_URL = (
    "https://planetarymaps.usgs.gov/mosaic/"
    "Mars_Viking_ClrMosaic_global_925m.tif"
)

R_MARS = 3396190.0
NODATA = -32768.0


def ensure(path, url):
    if not os.path.exists(path):
        print("downloading %s ..." % url)
        urllib.request.urlretrieve(url, path)
    return path


def read_dem(width: int = 8192, smooth: bool = False, sigma=(1.0, 2.0)):
    """Return ``(elevation_metres, degrees_per_pixel)`` at ``width`` px wide."""
    ensure(DEM, DEM_URL)
    with rasterio.open(DEM) as ds:
        h = width // 2
        z = ds.read(1, out_shape=(h, width), resampling=Resampling.average)
        z = z.astype(np.float32)
        deg_per_px = 360.0 / width
    z[z <= NODATA + 1] = np.nan
    if smooth:
        z = gaussian_filter(z, sigma, mode="nearest")
    return z, deg_per_px


def read_colour(width: int = 8192, height: int | None = None):
    """Viking colour mosaic as float32 in [0, 1] on the same grid."""
    ensure(COLOUR, COLOUR_URL)
    if height is None:
        height = width // 2
    with rasterio.open(COLOUR) as ds:
        rgb = ds.read(out_shape=(3, height, width), resampling=Resampling.average)
    return rgb.astype(np.float32).transpose(1, 2, 0) / 255.0


def hillshade(z, deg_per_px, azimuth=315.0, altitude=45.0, z_factor=1.0):
    """Latitude-aware hillshade in [0, 1] for the Mars cylindrical grid."""
    h = z.shape[0]
    lat = 90.0 - (np.arange(h) + 0.5) * (180.0 / h)
    mpp_x = np.radians(deg_per_px) * R_MARS * np.cos(np.radians(lat))
    mpp_y = np.radians(180.0 / h) * R_MARS
    dz_r, dz_c = np.gradient(z)
    x = dz_r / mpp_y
    y = dz_c / mpp_x[:, None]
    slope = np.pi / 2.0 - np.arctan(z_factor * np.hypot(x, y))
    aspect = np.arctan2(-x, y)
    az = np.radians(360.0 - azimuth + 90.0)
    alt = np.radians(altitude)
    shaded = np.sin(alt) * np.sin(slope) + np.cos(alt) * np.cos(slope) * np.cos(
        az - aspect
    )
    return np.clip(shaded, 0.0, 1.0)
