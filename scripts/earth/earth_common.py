"""Shared helpers for the ETOPO 2022 Earth elevation model + Blue Marble.

ETOPO 2022 is a **geographic** grid (EPSG:9518): the geotransform is in degrees
(−180…180°E, 90°N…90°S), elevations are metres. Slopes therefore need a
latitude-dependent metres-per-pixel, which `hillshade` applies per row.

    DEM     data/earth/ETOPO_2022_v1_30s_N90W180_surface.tif
    colour  data/earth/world.topo.bathy.200412.3x21600x10800.jpg  (Blue Marble)
"""

from __future__ import annotations

import os
import urllib.request

import numpy as np
import rasterio
from rasterio.enums import Resampling
from scipy.ndimage import gaussian_filter

DEM = "data/earth/ETOPO_2022_v1_30s_N90W180_surface.tif"
DEM_URL = (
    "https://www.ngdc.noaa.gov/mgg/global/relief/ETOPO2022/data/30s/"
    "30s_surface_elev_gtif/ETOPO_2022_v1_30s_N90W180_surface.tif"
)
MARBLE = "data/earth/world.topo.bathy.200412.3x21600x10800.jpg"
MARBLE_URL = (
    "https://eoimages.gsfc.nasa.gov/images/imagerecords/73000/73909/"
    "world.topo.bathy.200412.3x21600x10800.jpg"
)

R_EARTH = 6371000.0  # mean radius, metres
NODATA = -99999.0


def ensure(path, url):
    if not os.path.exists(path):
        print("downloading %s ..." % url)
        urllib.request.urlretrieve(url, path)
    return path


def read_dem(width: int = 8192, smooth: bool = False, sigma=(1.0, 2.0)):
    """Return ``(elevation_metres, degrees_per_pixel)`` at ``width`` px wide.

    Row 0 is 90°N, column 0 is 180°W. GDAL does the decimation with average
    resampling, so the 30-arcsecond source is never fully materialised.
    """
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
    """Blue Marble RGB as float32 in [0, 1], resampled to the same grid."""
    ensure(MARBLE, MARBLE_URL)
    if height is None:
        height = width // 2
    with rasterio.open(MARBLE) as ds:
        rgb = ds.read(out_shape=(3, height, width), resampling=Resampling.average)
    return rgb.astype(np.float32).transpose(1, 2, 0) / 255.0


def hillshade(z, deg_per_px, azimuth=315.0, altitude=45.0, z_factor=1.0):
    """Latitude-aware hillshade in [0, 1] for a geographic (degree) grid."""
    h = z.shape[0]
    lat = 90.0 - (np.arange(h) + 0.5) * (180.0 / h)
    mpp_x = np.radians(deg_per_px) * R_EARTH * np.cos(np.radians(lat))  # per row
    mpp_y = np.radians(180.0 / h) * R_EARTH
    dz_r, dz_c = np.gradient(z)          # per-pixel differences
    x = dz_r / mpp_y                     # d elevation / d(row metres)
    y = dz_c / mpp_x[:, None]            # d elevation / d(col metres)
    slope = np.pi / 2.0 - np.arctan(z_factor * np.hypot(x, y))
    aspect = np.arctan2(-x, y)
    az = np.radians(360.0 - azimuth + 90.0)
    alt = np.radians(altitude)
    shaded = np.sin(alt) * np.sin(slope) + np.cos(alt) * np.cos(slope) * np.cos(
        az - aspect
    )
    return np.clip(shaded, 0.0, 1.0)
