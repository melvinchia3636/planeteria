"""Extract a place-name catalogue for the Earth globe.

Downloads the Natural Earth 110m populated-places GeoJSON (public domain) and
writes a small CSV of name/lon/lat/population/capital-flag.

    uv run scripts/earth/extract_catalog.py  ->  data/earth/places.csv
"""

from __future__ import annotations

import csv
import json
import urllib.request

URL = (
    "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/"
    "geojson/ne_110m_populated_places.geojson"
)
OUT = "data/earth/places.csv"


def main():
    print("downloading %s ..." % URL)
    with urllib.request.urlopen(URL) as r:
        data = json.load(r)

    rows = []
    for f in data["features"]:
        p = f["properties"]
        name = p.get("NAME")
        lon, lat = p.get("LONGITUDE"), p.get("LATITUDE")
        if not name or lon is None or lat is None:
            continue
        capital = 1 if "capital" in (p.get("FEATURECLA") or "").lower() else 0
        rows.append([name, lon, lat, int(p.get("POP_MAX") or 0), capital,
                     p.get("ADM0NAME") or ""])

    rows.sort(key=lambda r: (-r[4], -r[3]))
    with open(OUT, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["name", "lon", "lat", "pop", "capital", "country"])
        w.writerows(rows)
    print("wrote %d places -> %s" % (len(rows), OUT))


if __name__ == "__main__":
    main()
