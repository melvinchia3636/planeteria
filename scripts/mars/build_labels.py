"""Build the label data for the Mars globe (web/mars/mars_labels.js).

    uv run scripts/mars/build_labels.py  ->  web/mars/mars_labels.js
"""

from __future__ import annotations

import csv
import json

OUT = "web/mars/mars_labels.js"
MAX_LABELS = 150
NOTABLE = {"mons", "valles", "planum", "planitia", "chasma", "tholus",
           "terra", "patera", "labyrinthus", "rupes", "chaos"}


def main():
    with open("data/mars/mars_features.csv") as f:
        rows = list(csv.DictReader(f))

    picked, seen = [], set()
    for r in rows:
        name = r["name"]
        if name in seen:
            continue
        kind = (r["type"].split(",")[0] or "").strip().lower()
        diam = float(r["diameter_km"] or 0)
        major = kind in NOTABLE
        if not major and not (kind == "crater" and diam >= 350.0):
            continue
        seen.add(name)
        picked.append({
            "n": name,
            "lon": round(float(r["lon"]), 3),
            "lat": round(float(r["lat"]), 3),
            "t": "major" if major else "crater",
        })
        if len(picked) >= MAX_LABELS:
            break

    js = "window.MARS_LABELS=" + json.dumps(picked, separators=(",", ":")) + ";"
    with open(OUT, "w") as f:
        f.write(js)
    print("saved %s  %d labels  %d bytes" % (OUT, len(picked), len(js)))


if __name__ == "__main__":
    main()
