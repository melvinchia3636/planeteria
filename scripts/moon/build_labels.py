"""Build the label data for the d3 globe (web/moon/lunar_labels.js).

Same selection as the flat map: every mare/oceanus/lacus/bay/sinus plus craters
>= 100 km. Emitted as a JS global so it loads without fetch.

    uv run scripts/moon/build_labels.py   ->  web/moon/lunar_labels.js
"""
from __future__ import annotations

import csv
import json

import label_map

OUT = "web/moon/lunar_labels.js"
MIN_CRATER_KM = 100.0


def main():
    labels = []
    with open("data/moon/lunar_seas.csv") as f:
        for r in csv.DictReader(f):
            labels.append({"n": label_map.english(r.get("origin"), r["name"]),
                           "t": "sea", "lon": round(float(r["lon"]), 3),
                           "lat": round(float(r["lat"]), 3)})
    with open("data/moon/lunar_craters.csv") as f:
        for r in csv.DictReader(f):
            if float(r["diameter_km"]) >= MIN_CRATER_KM:
                labels.append({"n": r["name"], "t": "crater",
                               "lon": round(float(r["lon"]), 3),
                               "lat": round(float(r["lat"]), 3)})
    data = "window.LUNAR_LABELS=" + json.dumps(labels, separators=(",", ":")) + ";"
    with open(OUT, "w") as f:
        f.write(data)
    print("saved %s  %d labels  %d bytes" % (OUT, len(labels), len(data)))


if __name__ == "__main__":
    main()
