"""Overlay capital / city labels on the flat Earth contour SVG.

    uv run scripts/earth/label_map.py  ->  output/earth/earth_globe_labeled.svg
"""

from __future__ import annotations

import csv
import html

SVG_IN = "output/earth/earth_globe.svg"
SVG_OUT = "output/earth/earth_globe_labeled.svg"
PLACES_CSV = "data/earth/places.csv"

S = 10.0
MAX_CITIES = 60
CAP_FONT = 12.0
CITY_FONT = 9.0

placed: list[tuple[float, float, float, float]] = []


def overlaps(box):
    x0, y0, x1, y1 = box
    return any(x0 < a1 and x1 > a0 and y0 < b1 and y1 > b0
               for a0, b0, a1, b1 in placed)


def place(name, lon, lat, font):
    x, y = (lon + 180.0) * S, (90.0 - lat) * S
    if not (0 <= x <= 360 * S and 0 <= y <= 180 * S):
        return None
    tx = x + 6
    w = len(name) * font * 0.58
    box = (tx - 3, y - font, tx + w + 3, y + font * 0.4)
    if overlaps(box):
        return None
    placed.append(box)
    return (name, x, y)


def main():
    with open(PLACES_CSV) as f:
        rows = list(csv.DictReader(f))

    capitals, cities = [], []
    seen = set()
    for r in rows:
        if r["name"] in seen:
            continue
        seen.add(r["name"])
        if r["capital"] == "1":
            capitals.append(r)
        elif len(cities) < MAX_CITIES:
            cities.append(r)

    caps = [it for it in (place(r["name"], float(r["lon"]), float(r["lat"]),
                                CAP_FONT) for r in capitals) if it]
    cits = [it for it in (place(r["name"], float(r["lon"]), float(r["lat"]),
                                CITY_FONT) for r in cities) if it]
    print("capitals %d/%d, cities %d/%d"
          % (len(caps), len(capitals), len(cits), len(cities)))

    parts = ['<g id="labels">']
    parts.append('<g font-family="Georgia, \'Times New Roman\', serif" '
                 'font-weight="bold" font-size="%g" fill="#7a1f1f" stroke="#fff" '
                 'stroke-width="3" paint-order="stroke" stroke-linejoin="round">'
                 % CAP_FONT)
    for name, x, y in caps:
        parts.append('<circle cx="%.1f" cy="%.1f" r="3.5" fill="#7a1f1f" '
                     'stroke="none"/>' % (x, y))
        parts.append('<text x="%.1f" y="%.1f">%s</text>'
                     % (x + 8, y + 4, html.escape(name)))
    parts.append('</g>')
    parts.append('<g font-family="Helvetica, Arial, sans-serif" font-size="%g" '
                 'fill="#111" stroke="#fff" stroke-width="2" '
                 'paint-order="stroke" stroke-linejoin="round">' % CITY_FONT)
    for name, x, y in cits:
        parts.append('<circle cx="%.1f" cy="%.1f" r="2.5" fill="#111" '
                     'stroke="none"/>' % (x, y))
        parts.append('<text x="%.1f" y="%.1f">%s</text>'
                     % (x + 5, y + 3, html.escape(name)))
    parts.append('</g></g>')

    with open(SVG_IN) as f:
        svg = f.read()
    i = svg.rfind("</svg>")
    svg = svg[:i] + "".join(parts) + svg[i:]
    with open(SVG_OUT, "w") as f:
        f.write(svg)
    print("saved %s  (%.1f MB)" % (SVG_OUT, len(svg) / 1e6))


if __name__ == "__main__":
    main()
