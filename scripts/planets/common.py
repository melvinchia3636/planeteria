"""Shared I/O and shading for the generic planetary pipeline."""

from __future__ import annotations

import hashlib
import os

import numpy as np
import rasterio
from rasterio.enums import Resampling
from scipy.ndimage import gaussian_filter

from config import PLANETS

CACHE_DIR = ".cache"


def _cache_key(cfg, body, width, smooth):
    raw = "|".join(str(x) for x in (
        cfg["dem"], cfg.get("scale", 1.0), cfg.get("nodata"),
        cfg.get("subtract_median", False), width, bool(smooth)))
    return os.path.join(CACHE_DIR, "%s_%s.npz"
                        % (body, hashlib.md5(raw.encode()).hexdigest()[:10]))


def read_dem(body, width=8192, smooth=False, sigma=(1.0, 2.0)):
    """Return ``(z_metres, mpp_x0, mpp_y)`` on a ``width`` × ``width/2`` grid.

    ``mpp_x0`` is the ground metres-per-output-pixel at the equator; multiply by
    ``cos(lat)`` for true east–west distance. Works for both projected (metres)
    and geographic (degrees, needs ``radius``) rasters. Row 0 is 90°N, column 0
    is the westernmost longitude. The decimated field is cached under `.cache/`.
    """
    cfg = PLANETS[body]
    key = _cache_key(cfg, body, width, smooth)
    if os.path.exists(key):
        d = np.load(key)
        return d["z"], float(d["mx"]), float(d["my"])

    with rasterio.open(cfg["dem"]) as ds:
        h = width // 2
        z = ds.read(1, out_shape=(h, width), resampling=Resampling.average)
        z = z.astype(np.float32)
        sx = ds.width / width
        sy = ds.height / h
        geographic = bool(ds.crs and ds.crs.is_geographic)
        if geographic:
            r = cfg["radius"]
            mpp_x0 = np.radians(abs(ds.transform.a) * sx) * r
            mpp_y = np.radians(abs(ds.transform.e) * sy) * r
        else:
            mpp_x0 = abs(ds.transform.a) * sx
            mpp_y = abs(ds.transform.e) * sy
    scale = cfg.get("scale", 1.0)
    if scale != 1.0:
        z *= scale
    nd = cfg.get("nodata")
    if nd is not None:
        z[z <= nd + 1] = np.nan
    if cfg.get("subtract_median"):
        z = z - np.nanmedian(z)
    z = np.nan_to_num(z, nan=0.0)
    if smooth:
        z = gaussian_filter(z, sigma, mode="nearest")
    os.makedirs(CACHE_DIR, exist_ok=True)
    np.savez(key, z=z, mx=np.float32(mpp_x0), my=np.float32(mpp_y))
    return z, mpp_x0, mpp_y


def read_color(body, width=8192):
    """Surface colour as float32 [0,1] shape (h, w, 3); greyscale repeats."""
    cfg = PLANETS[body]
    with rasterio.open(cfg["color"]) as ds:
        h = width // 2
        arr = ds.read(out_shape=(ds.count, h, width), resampling=Resampling.average)
    arr = arr.astype(np.float32) / 255.0
    if arr.shape[0] == 1:
        arr = np.repeat(arr, 3, axis=0)
    return np.moveaxis(arr, 0, -1)


def hillshade(z, mpp_x0, mpp_y, azimuth=315.0, altitude=45.0, z_factor=1.0):
    """Latitude-aware hillshade in [0, 1]."""
    h = z.shape[0]
    lat = 90.0 - (np.arange(h) + 0.5) * (180.0 / h)
    mpp_x = mpp_x0 * np.cos(np.radians(lat))
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


# Generic hypsometric palette: cool lows → warm mids → white highs.
PALETTE = [
    (0.00, 22, 34, 74),
    (0.20, 70, 110, 170),
    (0.42, 150, 168, 150),
    (0.55, 190, 170, 120),
    (0.70, 180, 130, 90),
    (0.85, 222, 192, 162),
    (1.00, 250, 250, 250),
]


def colourise_norm(t):
    """Map a [0,1] field to an RGB float array via the palette."""
    xs = np.array([p[0] for p in PALETTE], dtype=np.float32)
    rgb = np.empty(t.shape + (3,), dtype=np.float32)
    for c in range(3):
        vals = np.array([p[c + 1] for p in PALETTE], dtype=np.float32)
        rgb[..., c] = np.interp(t, xs, vals)
    return rgb
