"""Extract IAU-named Martian features from the USGS Gazetteer shapefile.

Downloads the "MARS nomenclature center points" dataset and writes a small
catalogue (longitudes converted to −180…180 to match the DEM).

    uv run scripts/mars/extract_catalog.py  ->  data/mars/mars_features.csv
"""

from __future__ import annotations

import csv
import io
import urllib.request
import zipfile

import shapefile  # pyshp

URL = ("https://asc-planetarynames-data.s3.us-west-2.amazonaws.com/"
       "MARS_nomenclature_center_pts.zip")
SHAPE = "MARS_nomenclature_center_pts"
OUT = "data/mars/mars_features.csv"


def east_to_signed(lon):
    lon = float(lon)
    return lon - 360.0 if lon > 180.0 else lon


def main():
    print("downloading %s ..." % URL)
    with urllib.request.urlopen(URL) as resp:
        blob = resp.read()
    base = "/tmp/mars_nom"
    with zipfile.ZipFile(io.BytesIO(blob)) as z:
        z.extractall(base)
    reader = shapefile.Reader(base + "/" + SHAPE)

    rows = []
    fields = [f[0] for f in reader.fields[1:]]
    for rec in reader.records():
        r = dict(zip(fields, rec))
        name = r.get("name") or r.get("NAME")
        lon = r.get("center_lon", r.get("center_lon"))
        lat = r.get("center_lat")
        if not name or lon is None or lat is None:
            continue
        diam = r.get("diameter") or 0
        rows.append([
            name,
            round(east_to_signed(lon), 4),
            round(float(lat), 4),
            round(float(diam), 2),
            r.get("type") or "",
            (r.get("origin") or "").strip().strip('"'),
        ])
    rows.sort(key=lambda x: (-x[3], x[0]))

    with open(OUT, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["name", "lon", "lat", "diameter_km", "type", "origin"])
        w.writerows(rows)
    print("wrote %d features -> %s" % (len(rows), OUT))


if __name__ == "__main__":
    main()
