"""Overlay crater and mare labels on the flat contour SVG.

Reads the IAU catalog extracts in data/ and writes a labelled copy of the map.
Seas use their English phrase when the catalog gives one ("Sea of Tranquillity"),
otherwise the Latin name (person-named maria like Mare Humboldtianum). A simple
greedy rectangle test drops any label that would collide with an earlier one.

    uv run scripts/moon/label_map.py   ->  output/moon/lunar_globe_v3_labeled.svg
"""
from __future__ import annotations

import csv
import html
import re

SVG_IN = "output/moon/lunar_globe_v3.svg"
SVG_OUT = "output/moon/lunar_globe_v3_labeled.svg"
SEAS_CSV = "data/moon/lunar_seas.csv"
CRATERS_CSV = "data/moon/lunar_craters.csv"

S = 10.0
MIN_CRATER_KM = 100.0
SEA_FONT = 14.0
CRATER_FONT = 9.0

RIGHT_WORDS = ("sea", "ocean", "lake", "bay", "marsh", "pool")

placed: list[tuple[float, float, float, float]] = []


def overlaps(box):
    x0, y0, x1, y1 = box
    return any(x0 < a1 and x1 > a0 and y0 < b1 and y1 > b0
               for a0, b0, a1, b1 in placed)


def english(origin, latin):
    if origin:
        s = origin.strip().strip('"').strip().rstrip(".").strip()
        head = s.split()[0].lower() if s.split() else ""
        if head in RIGHT_WORDS and len(s) <= 34:
            return s
    return latin


def place(name, lon, lat, font, sea):
    x, y = lon * S, (90.0 - lat) * S
    if not (0 <= x <= 360 * S and 0 <= y <= 180 * S):
        return None
    off = 11 if sea else 6
    tx = x + off
    w = len(name) * font * 0.58
    box = (tx - 3, y - font, tx + w + 3, y + font * 0.4)
    if overlaps(box):
        return None
    placed.append(box)
    return (name, x, y)


def load(path):
    with open(path) as f:
        return list(csv.DictReader(f))


def main():
    seas = sorted(
        ((english(r.get("origin"), r["name"]), float(r["lon"]), float(r["lat"]),
          float(r["diameter_km"])) for r in load(SEAS_CSV)),
        key=lambda t: -t[3])
    craters = [(r["name"], float(r["lon"]), float(r["lat"]))
               for r in load(CRATERS_CSV) if float(r["diameter_km"]) >= MIN_CRATER_KM]

    sea_items = []
    for name, lon, lat, _ in seas:
        it = place(name, lon, lat, SEA_FONT, True)
        if it:
            sea_items.append(it)
    cr_items = []
    for name, lon, lat in craters:
        it = place(name, lon, lat, CRATER_FONT, False)
        if it:
            cr_items.append(it)
    print("seas %d/%d, craters %d/%d"
          % (len(sea_items), len(seas), len(cr_items), len(craters)))

    parts = ['<g id="labels">']
    parts.append('<g font-family="Georgia, \'Times New Roman\', serif" '
                 'font-style="italic" font-weight="bold" font-size="%g" '
                 'fill="#12233f" stroke="#fff" stroke-width="3" '
                 'paint-order="stroke" stroke-linejoin="round">' % SEA_FONT)
    for name, x, y in sea_items:
        parts.append('<circle cx="%.1f" cy="%.1f" r="4" fill="#12233f" '
                     'stroke="none"/>' % (x, y))
        parts.append('<text x="%.1f" y="%.1f">%s</text>'
                     % (x + 11, y + 5, html.escape(name)))
    parts.append('</g>')
    parts.append('<g font-family="Helvetica, Arial, sans-serif" font-size="%g" '
                 'fill="#000" stroke="#fff" stroke-width="2.2" '
                 'paint-order="stroke" stroke-linejoin="round">' % CRATER_FONT)
    for name, x, y in cr_items:
        parts.append('<circle cx="%.1f" cy="%.1f" r="3" fill="#000" '
                     'stroke="none"/>' % (x, y))
        parts.append('<text x="%.1f" y="%.1f">%s</text>'
                     % (x + 6, y + 3, html.escape(name)))
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
