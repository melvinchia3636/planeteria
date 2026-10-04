"""Build the label data for the Earth globe (web/earth/earth_labels.js).

    uv run scripts/earth/build_labels.py  ->  web/earth/earth_labels.js
"""

from __future__ import annotations

import csv

OUT = "web/earth/earth_labels.js"
MAX_CITIES = 60  # non-capital cities, largest first


def main():
    with open("data/earth/places.csv") as f:
        rows = list(csv.DictReader(f))

    labels = []
    seen = set()
    cities = 0
    for r in rows:
        name = r["name"]
        if name in seen:
            continue
        capital = r["capital"] == "1"
        if not capital:
            if cities >= MAX_CITIES:
                continue
            cities += 1
        seen.add(name)
        labels.append({
            "n": name,
            "lon": round(float(r["lon"]), 3),
            "lat": round(float(r["lat"]), 3),
            "t": "capital" if capital else "city",
        })

    js = "window.EARTH_LABELS=" + __import__("json").dumps(
        labels, separators=(",", ":")
    ) + ";"
    with open(OUT, "w") as f:
        f.write(js)
    print("saved %s  %d labels  %d bytes" % (OUT, len(labels), len(js)))


if __name__ == "__main__":
    main()
