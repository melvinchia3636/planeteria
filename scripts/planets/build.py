"""Generic pipeline for every planetary body.

    uv run scripts/planets/build.py <task> <body>

tasks: relief | truecolor | contours | texture | height | catalog | labels |
       flat | flatlabels | all

``all`` = relief, truecolor, contours, texture, height, catalog, labels.
Reads/writes under data/<body>/, output/<body>/, web/<body>/ and defines the
globals  window.<BODY>_CONTOURS / _LABELS / _TEXTURE / _ELEV / _HEIGHT.
"""

from __future__ import annotations

import base64
import csv
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.request
import zipfile
from concurrent.futures import ProcessPoolExecutor

import common
import numpy as np
import rasterio
from config import NOTABLE_TYPES, PLANETS, SEA_TYPES
from rasterio.enums import Resampling
from scipy.ndimage import gaussian_filter1d
from skimage.measure import approximate_polygon, find_contours

RELIEF_WIDTH = 8192
CONTOUR_WIDTH = 4096
HEIGHT_WIDTH = 1024
PATH_SIGMA = 1.0
MIN_PERIMETER = 5.0
PAD = 40
TOLERANCE = 0.08
DECIMALS = 3
S = 10.0  # SVG units per degree (flat maps)

PLACES_URL = (
    "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/"
    "master/geojson/ne_110m_populated_places.geojson"
)
RIGHT_WORDS = ("sea", "ocean", "lake", "bay", "marsh", "pool")


def _dirs(body):
    for d in ("output/" + body, "web/" + body, "data/" + body):
        os.makedirs(d, exist_ok=True)


def _features_path(body):
    return "data/%s/%s_features.csv" % (body, body)


# --------------------------------------------- parallel contour extraction ---
_STATE = {}


def _w_init(path, pad, dpp, lon0, mode):
    _STATE.clear()
    _STATE.update(
        field=np.load(path, mmap_mode="r"), pad=pad, dpp=dpp, lon0=lon0, mode=mode
    )


def _w_level(lv):
    field, pad = _STATE["field"], _STATE["pad"]
    dpp, lon0, mode = _STATE["dpp"], _STATE["lon0"], _STATE["mode"]
    out = []
    for c in find_contours(field, lv):
        if len(c) < 2:
            continue
        if np.hypot(np.diff(c[:, 0]), np.diff(c[:, 1])).sum() < MIN_PERIMETER:
            continue
        closed = np.hypot(c[0, 0] - c[-1, 0], c[0, 1] - c[-1, 1]) < 1e-6
        if closed:
            yy, xx = c[:-1, 0], c[:-1, 1]
            xx = gaussian_filter1d(xx, PATH_SIGMA, mode="wrap")
            yy = gaussian_filter1d(yy, PATH_SIGMA, mode="wrap")
        else:
            yy, xx = c[:, 0], c[:, 1]
            xx = gaussian_filter1d(xx, PATH_SIGMA, mode="nearest")
            yy = gaussian_filter1d(yy, PATH_SIGMA, mode="nearest")
        if mode == "contour":
            lon = (xx - pad + 0.5) * dpp + lon0
            lat = 90.0 - (yy + 0.5) * dpp
            a = approximate_polygon(np.column_stack([lon, lat]), tolerance=TOLERANCE)
            if len(a) < (3 if closed else 2):
                continue
            r = [[round(float(x), DECIMALS), round(float(y), DECIMALS)] for x, y in a]
            if closed:
                r[-1] = r[0]
            out.append(r)
        else:  # flat: return SVG-space polylines
            xx, yy = xx[::3], yy[::3]
            if len(xx) < (3 if closed else 2):
                continue
            xs = (xx - pad + 0.5) * (S * dpp)
            ys = (yy + 0.5) * (S * dpp)
            out.append((xs, ys, closed))
    return out


def _levels(field, interval):
    lo, hi = np.percentile(field, (1, 99))
    off = interval / 2
    lo = np.floor((lo - off) / interval) * interval + off
    hi = np.ceil((hi - off) / interval) * interval + off
    return np.arange(lo, hi + 1, interval)


def _extract_rings(body, z, width, levels, mode):
    field = np.pad(z, ((0, 0), (PAD, PAD)), mode="wrap")
    path = os.path.join(".cache", "%s_%d_pad.npy" % (body, width))
    os.makedirs(".cache", exist_ok=True)
    np.save(path, field)
    dpp = 360.0 / width
    lon0 = PLANETS[body]["lon0"]
    nproc = max(1, (os.cpu_count() or 2) - 1)
    rings = []
    if nproc > 1:
        with ProcessPoolExecutor(
            max_workers=nproc,
            initializer=_w_init,
            initargs=(path, PAD, dpp, lon0, mode),
        ) as ex:
            for res in ex.map(_w_level, levels, chunksize=1):
                rings.extend(res)
    else:
        _w_init(path, PAD, dpp, lon0, mode)
        for lv in levels:
            rings.extend(_w_level(lv))
    return rings


# --------------------------------------------------------------- rasters -----
def task_relief(body):
    cfg = PLANETS[body]
    z, mx, my = common.read_dem(body, RELIEF_WIDTH)
    shade = common.hillshade(z, mx, my, z_factor=cfg["zfactor"])
    lo, hi = np.percentile(z, (2, 98))
    rgb = common.colourise_norm(np.clip((z - lo) / (hi - lo), 0, 1))
    rgb *= (0.35 + 0.65 * shade)[..., None]
    out = np.clip(rgb, 0, 255).astype(np.uint8).transpose(2, 0, 1)
    path = "output/%s/%s_relief.png" % (body, body)
    with rasterio.open(
        path,
        "w",
        driver="PNG", ZLEVEL="1",
        width=z.shape[1],
        height=z.shape[0],
        count=3,
        dtype="uint8",
    ) as dst:
        dst.write(out)
    print("saved", path)


def task_truecolor(body):
    cfg = PLANETS[body]
    z, mx, my = common.read_dem(body, RELIEF_WIDTH)
    rgb = common.read_color(body, RELIEF_WIDTH)
    shade = common.hillshade(z, mx, my, z_factor=cfg["zfactor"])
    rgb = rgb * (0.30 + 0.70 * shade)[..., None]
    out = np.clip(rgb * 255.0, 0, 255).astype(np.uint8).transpose(2, 0, 1)
    path = "output/%s/%s_truecolor.png" % (body, body)
    with rasterio.open(
        path,
        "w",
        driver="PNG", ZLEVEL="1",
        width=z.shape[1],
        height=z.shape[0],
        count=3,
        dtype="uint8",
    ) as dst:
        dst.write(out)
    print("saved", path)


def _encode_png(src, width, name, out):
    with rasterio.open(src) as ds:
        rgb = ds.read(out_shape=(3, width // 2, width), resampling=Resampling.average)
    fd, tmp = tempfile.mkstemp(suffix=".png")
    os.close(fd)
    try:
        with rasterio.open(
            tmp,
            "w",
            driver="PNG", ZLEVEL="1",
            width=width,
            height=width // 2,
            count=3,
            dtype="uint8",
        ) as dst:
            dst.write(rgb)
        with open(tmp, "rb") as f:
            b64 = base64.b64encode(f.read()).decode("ascii")
    finally:
        os.remove(tmp)
    with open(out, "w") as f:
        f.write('window.%s="data:image/png;base64,%s";' % (name, b64))
    print("saved %s  %dx%d  %.1f MB" % (out, width, width // 2, len(b64) / 1e6))


def task_texture(body):
    u = body.upper()
    _encode_png(
        "output/%s/%s_truecolor.png" % (body, body),
        4096,
        u + "_TEXTURE",
        "web/%s/%s_texture.js" % (body, body),
    )
    _encode_png(
        "output/%s/%s_relief.png" % (body, body),
        2048,
        u + "_ELEV",
        "web/%s/%s_elev.js" % (body, body),
    )


def task_height(body):
    z, _, _ = common.read_dem(body, HEIGHT_WIDTH)
    data = np.clip(z, -32768, 32767).astype("<i2")
    obj = {
        "w": HEIGHT_WIDTH,
        "h": HEIGHT_WIDTH // 2,
        "min": float(z.min()),
        "max": float(z.max()),
        "b64": base64.b64encode(data.tobytes()).decode("ascii"),
    }
    path = "web/%s/%s_height.js" % (body, body)
    with open(path, "w") as f:
        f.write(
            "window.%s_HEIGHT=%s;"
            % (body.upper(), json.dumps(obj, separators=(",", ":")))
        )
    print("saved", path)


# ------------------------------------------------------------- contours ------
def task_contours(body):
    cfg = PLANETS[body]
    field, _, _ = common.read_dem(body, CONTOUR_WIDTH)
    levels = _levels(field, cfg["interval"])
    coords = _extract_rings(body, field, CONTOUR_WIDTH, levels, "contour")
    data = "window.%s_CONTOURS=%s;" % (
        body.upper(),
        json.dumps(
            {"type": "MultiLineString", "coordinates": coords}, separators=(",", ":")
        ),
    )
    path = "web/%s/%s_contours.js" % (body, body)
    with open(path, "w") as f:
        f.write(data)
    print(
        "saved %s  %d levels  %d lines  %.1f MB"
        % (path, len(levels), len(coords), len(data) / 1e6)
    )



# ------------------------------------------------------------- catalogs ------
def task_catalog(body):
    cfg = PLANETS[body]
    rows = []
    if cfg["catalog"] == "places":
        with urllib.request.urlopen(PLACES_URL) as r:
            data = json.load(r)
        for f in data["features"]:
            p = f["properties"]
            name, lon, lat = p.get("NAME"), p.get("LONGITUDE"), p.get("LATITUDE")
            if not name or lon is None or lat is None:
                continue
            cap = 1 if "capital" in (p.get("FEATURECLA") or "").lower() else 0
            rows.append(
                [
                    name,
                    round(lon, 4),
                    round(lat, 4),
                    int(p.get("POP_MAX") or 0),
                    cap,
                    p.get("ADM0NAME") or "",
                ]
            )
        rows.sort(key=lambda x: (-x[4], -x[3]))
        header = ["name", "lon", "lat", "pop", "capital", "country"]
    else:
        url = (
            "https://asc-planetarynames-data.s3.us-west-2.amazonaws.com/"
            "%s.zip" % cfg["gazetteer"]
        )
        print("downloading", url)
        with urllib.request.urlopen(url) as resp:
            blob = resp.read()
        base = "/tmp/%s_nom" % body
        with zipfile.ZipFile(io.BytesIO(blob)) as z:
            z.extractall(base)
        import shapefile

        reader = shapefile.Reader(base + "/" + cfg["gazetteer"])
        fields = [f[0] for f in reader.fields[1:]]
        for rec in reader.records():
            r = dict(zip(fields, rec))
            name = r.get("name") or r.get("NAME")
            lon, lat = r.get("center_lon"), r.get("center_lat")
            if not name or lon is None or lat is None:
                continue
            lon = float(lon)
            if cfg.get("lon0", -180.0) < 0 and lon > 180:
                lon -= 360
            rows.append(
                [
                    name,
                    round(lon, 4),
                    round(float(lat), 4),
                    round(float(r.get("diameter") or 0), 2),
                    r.get("type") or "",
                    (r.get("origin") or "").strip('"'),
                ]
            )
        rows.sort(key=lambda x: (-x[3], x[0]))
        header = ["name", "lon", "lat", "diameter_km", "type", "origin"]

    with open(_features_path(body), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)
    print("wrote %d features -> %s" % (len(rows), _features_path(body)))


def _english(origin, latin):
    if origin:
        s = origin.strip().strip('"').rstrip(".").strip()
        head = s.split()[0].lower() if s.split() else ""
        if head in RIGHT_WORDS and len(s) <= 34:
            return s
    return latin


def pick_labels(body, city_limit=60):
    """Return a list of ``{n, lon, lat, t}`` for the body's label style."""
    cfg = PLANETS[body]
    with open(_features_path(body)) as f:
        rows = list(csv.DictReader(f))
    out, seen = [], set()
    rule = cfg["label_rule"]

    if rule == "places":
        cities = 0
        for r in rows:
            if r["name"] in seen:
                continue
            cap = r["capital"] == "1"
            if not cap:
                if cities >= city_limit:
                    continue
                cities += 1
            seen.add(r["name"])
            out.append(
                {
                    "n": r["name"],
                    "lon": round(float(r["lon"]), 3),
                    "lat": round(float(r["lat"]), 3),
                    "t": "capital" if cap else "city",
                }
            )
        return out

    if rule == "moon":
        seas, craters = [], []
        for r in rows:
            if r["type"] in SEA_TYPES:
                seas.append(
                    (
                        _english(r.get("origin"), r["name"]),
                        float(r["lon"]),
                        float(r["lat"]),
                        float(r["diameter_km"]),
                    )
                )
            elif r["type"] == "Crater, craters" and float(r["diameter_km"]) >= 100.0:
                craters.append((r["name"], float(r["lon"]), float(r["lat"])))
        seas.sort(key=lambda t: -t[3])
        for n, lon, lat, _ in seas:
            out.append({"n": n, "lon": round(lon, 3), "lat": round(lat, 3), "t": "sea"})
        for n, lon, lat in craters:
            out.append(
                {"n": n, "lon": round(lon, 3), "lat": round(lat, 3), "t": "crater"}
            )
        return out

    for r in rows:
        if r["name"] in seen:
            continue
        kind = (r["type"].split(",")[0] or "").strip().lower()
        major = kind in NOTABLE_TYPES
        if not major and not (
            kind == "crater" and float(r["diameter_km"] or 0) >= 350.0
        ):
            continue
        seen.add(r["name"])
        out.append(
            {
                "n": r["name"],
                "lon": round(float(r["lon"]), 3),
                "lat": round(float(r["lat"]), 3),
                "t": "major" if major else "crater",
            }
        )
        if len(out) >= 150:
            break
    return out


def task_labels(body):
    picked = pick_labels(body)
    path = "web/%s/%s_labels.js" % (body, body)
    with open(path, "w") as f:
        f.write(
            "window.%s_LABELS=%s;"
            % (body.upper(), json.dumps(picked, separators=(",", ":")))
        )
    print("saved %s  %d labels" % (path, len(picked)))


# ------------------------------------------------------------- flat SVG ------
def _cr_bezier(xs, ys, closed):
    n = len(xs)
    parts = ["M%.1f,%.1f" % (xs[0], ys[0])]
    segs = range(n) if closed else range(n - 1)
    for i in segs:
        if closed:
            a, b, e = (i - 1) % n, (i + 1) % n, (i + 2) % n
        else:
            a, b = max(i - 1, 0), i + 1
            e = min(i + 2, n - 1)
        c1x, c1y = xs[i] + (xs[b] - xs[a]) / 6.0, ys[i] + (ys[b] - ys[a]) / 6.0
        c2x, c2y = xs[b] - (xs[e] - xs[i]) / 6.0, ys[b] - (ys[e] - ys[i]) / 6.0
        parts.append(
            "C%.1f,%.1f %.1f,%.1f %.1f,%.1f" % (c1x, c1y, c2x, c2y, xs[b], ys[b])
        )
    if closed:
        parts.append("Z")
    return "".join(parts)


def task_flat(body):
    cfg = PLANETS[body]
    field, _, _ = common.read_dem(body, CONTOUR_WIDTH)
    levels = _levels(field, cfg["interval"])
    rings = _extract_rings(body, field, CONTOUR_WIDTH, levels, "flat")
    paths = [_cr_bezier(xs, ys, closed) for xs, ys, closed in rings]
    W, H = 360.0 * S, 180.0 * S
    bg = cfg["gradient"][0]
    svg = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %.0f %.0f" '
        'width="%.0f" height="%.0f">' % (W, H, W, H),
        '<rect width="100%%" height="100%%" fill="%s"/>' % bg,
        '<g fill="none" stroke="#ffffff" stroke-width="0.25" '
        'stroke-linejoin="round" stroke-linecap="round">',
    ]
    svg += ['<path d="%s"/>' % d for d in paths]
    svg.append("</g></svg>")
    path = "output/%s/%s_globe.svg" % (body, body)
    with open(path, "w") as f:
        f.write("\n".join(svg))
    print("saved %s  %d paths" % (path, len(paths)))



def task_flatlabels(body):
    import html

    cfg = PLANETS[body]
    lon0 = cfg["lon0"]
    placed = []

    def overlaps(box):
        x0, y0, x1, y1 = box
        return any(
            x0 < a1 and x1 > a0 and y0 < b1 and y1 > b0 for a0, b0, a1, b1 in placed
        )

    def place(name, lon, lat, font):
        x, y = (lon - lon0) * S, (90.0 - lat) * S
        if not (0 <= x <= 360 * S and 0 <= y <= 180 * S):
            return None
        tx, w = x + 6, len(name) * font * 0.58
        box = (tx - 3, y - font, tx + w + 3, y + font * 0.4)
        if overlaps(box):
            return None
        placed.append(box)
        return (name, x, y)

    items = []
    for e in pick_labels(body):
        sea = e["t"] == "sea"
        it = place(e["n"], e["lon"], e["lat"], 14.0 if sea else 9.0)
        if it:
            items.append((it[0], it[1], it[2], sea))

    bg = cfg["gradient"][0]
    parts = ['<g id="labels">']
    for name, x, y, sea in items:
        font = (
            "Georgia, 'Times New Roman', serif"
            if sea
            else "Helvetica, Arial, sans-serif"
        )
        parts.append(
            '<circle cx="%.1f" cy="%.1f" r="3" fill="#ffffff" stroke="none"/>' % (x, y)
        )
        parts.append(
            '<text x="%.1f" y="%.1f" font-family="%s" font-size="%g" '
            'fill="#ffffff" stroke="%s" stroke-width="3" '
            'paint-order="stroke" stroke-linejoin="round">%s</text>'
            % (x + 7, y + 4, font, 14.0 if sea else 9.0, bg, html.escape(name))
        )
    parts.append("</g>")

    src = "output/%s/%s_globe.svg" % (body, body)
    with open(src) as f:
        svg = f.read()
    i = svg.rfind("</svg>")
    out = svg[:i] + "".join(parts) + svg[i:]
    path = "output/%s/%s_globe_labeled.svg" % (body, body)
    with open(path, "w") as f:
        f.write(out)
    print("saved %s  %d labels" % (path, len(items)))


MEDIUM_W = 4000      # px width of the medium PNG
HIGH_W = 25600       # px width of the very-high-res PNG


def _find_rasterizer():
    for name in ("inkscape", "rsvg-convert", "magick", "convert"):
        path = shutil.which(name)
        if path:
            return path
    return None


def _rasterize(svg, out, width):
    tool = _find_rasterizer()
    if tool is None:
        raise SystemExit("no SVG rasteriser found (need Inkscape or ImageMagick)")
    if os.path.basename(tool).startswith("inkscape"):
        cmd = [tool, svg, "--export-type=png", "--export-width=%d" % width,
               "--export-filename=%s" % out]
    else:  # ImageMagick
        cmd = [tool, "-background", "white", "-density", "3000", svg,
               "-resize", "%dx" % width, out]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL,
                   stderr=subprocess.DEVNULL)
    print("saved %s  %dpx" % (out, width))


def task_png(body):
    src = "output/%s/%s_globe_labeled.svg" % (body, body)
    suffix = "_labeled"
    if not os.path.exists(src):
        src = "output/%s/%s_globe.svg" % (body, body)
        suffix = ""
    if not os.path.exists(src):
        print("no SVG for %s (run: build.py flat %s)" % (body, body))
        return
    _rasterize(src, "output/%s/%s_globe%s.png" % (body, body, suffix), MEDIUM_W)
    _rasterize(src, "output/%s/%s_globe%s_%d.png" % (body, body, suffix, HIGH_W),
               HIGH_W)


TASKS = {
    "relief": task_relief,
    "truecolor": task_truecolor,
    "contours": task_contours,
    "texture": task_texture,
    "height": task_height,
    "catalog": task_catalog,
    "labels": task_labels,
    "flat": task_flat,
    "flatlabels": task_flatlabels,
    "png": task_png,
}
ALL = ["relief", "truecolor", "contours", "texture", "height", "catalog", "labels"]


def main():
    if len(sys.argv) != 3 or sys.argv[1] not in list(TASKS) + ["all"]:
        print("usage: build.py <%s|all> <body>" % "|".join(TASKS))
        sys.exit(1)
    task, body = sys.argv[1], sys.argv[2]
    if body not in PLANETS:
        print("unknown body:", body, "->", ", ".join(PLANETS))
        sys.exit(1)
    _dirs(body)
    names = ALL if task == "all" else [task]
    for name in names:
        t0 = time.time()
        TASKS[name](body)
        print("  [%s %s %.1fs]" % (body, name, time.time() - t0))


if __name__ == "__main__":
    main()
