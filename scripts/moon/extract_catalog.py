"""Extract IAU-named lunar features from the USGS Gazetteer shapefile.

Downloads the "MOON nomenclature center points" dataset published by the USGS
Astrogeology Science Center and writes the two small catalogues the maps use:

    data/moon/lunar_craters.csv   name, lon, lat, diameter_km
    data/moon/lunar_seas.csv      name, kind, lon, lat, diameter_km, origin

    uv run scripts/extract_catalog.py
"""
from __future__ import annotations

import csv
import io
import urllib.request
import zipfile

import shapefile  # pyshp

URL = ("https://asc-planetarynames-data.s3.us-west-2.amazonaws.com/"
       "MOON_nomenclature_center_pts.zip")
SHAPE = "MOON_nomenclature_center_pts"
SEA_TYPES = {"Mare, maria", "Oceanus, oceani", "Lacus, lacūs",
             "Palus, paludes", "Sinus, sinūs"}


def main():
    print("downloading", URL)
    with urllib.request.urlopen(URL) as resp:
        blob = resp.read()
    with zipfile.ZipFile(io.BytesIO(blob)) as z:
        base = "/tmp/moon_nom"
        z.extractall(base)
    reader = shapefile.Reader(base + "/" + SHAPE)

    craters, seas = [], []
    for rec in reader.records():
        name = rec["name"]
        lon, lat = round(rec["center_lon"], 4), round(rec["center_lat"], 4)
        diam = round(rec["diameter"], 2)
        if rec["type"] == "Crater, craters":
            craters.append((name, lon, lat, diam))
        elif rec["type"] in SEA_TYPES:
            seas.append((name, rec["type"].split(",")[0], lon, lat, diam,
                         rec["origin"]))
    craters.sort(key=lambda r: -r[3])
    seas.sort(key=lambda r: -r[4])

    with open("data/moon/lunar_craters.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["name", "lon", "lat", "diameter_km"])
        w.writerows(craters)
    with open("data/moon/lunar_seas.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["name", "kind", "lon", "lat", "diameter_km", "origin"])
        w.writerows(seas)
    print("wrote %d craters, %d seas" % (len(craters), len(seas)))


if __name__ == "__main__":
    main()
