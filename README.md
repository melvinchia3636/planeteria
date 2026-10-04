# moon-is-fun

Contour maps, shaded-relief images and interactive draggable globes for the
**Moon** and **Earth**, built from real elevation models. Rendered with
numpy/scipy/scikit-image; DEMs are read through GDAL. No GIS tooling is needed.

The codebase is organised **by planet** under `data/`, `scripts/`, `output/`
and `web/`.

![flat map](output/moon/lunar_globe_v3_labeled.png)

## Moon

`data/moon/LDEM_128.IMG` (2 GB) is the LRO **L**unar **O**rbiter **L**aser
**A**ltimeter gridded digital elevation model, V3.0:

| property | value |
|---|---|
| grid | 23040 × 46080 (128 px/deg, global) |
| extent | 90°N…90°S, 0…360°E (Simple Cylindrical) |
| sample | 16-bit **little-endian** signed integer |
| height | `elevation_m = DN × 0.5` above a 1737.4 km sphere |

The `.IMG` is headerless raw pixels; all metadata lives in
`data/moon/LDEM_128.LBL`. The pipeline reads it through **GDAL's PDS driver**
(`scripts/moon/common.py` opens the label with `rasterio`), which supplies the
byte order, `scale`, `nodata`, CRS and geotransform — nothing about the format is
hand-parsed. (Cross-check: at 16-bit little-endian, `DN × 0.5` gives a global
range of −9.1…+10.8 km, matching the Moon.)

Named features come from the USGS/IAU [Gazetteer of Planetary
Nomenclature](https://planetarynames.wr.usgs.gov/) (Moon center points).

## Layout

```
├── data/<planet>/    elevation models, imagery + extracted catalogues
├── scripts/<planet>/ the Python pipeline for each body
├── output/<planet>/  generated maps (SVG / PNG)
├── web/<planet>/     the interactive d3 globe (index.html + generated JS)
├── web/d3.min.js     shared d3 build
├── pyproject.toml / Makefile
```

## Setup

Install [uv](https://docs.astral.sh/uv/), drop `LDEM_128.IMG` into
`data/moon/`, then:

```sh
make all       # every planet
make moon      # Moon only
```

or run individual steps (Moon):

```sh
uv run scripts/moon/extract_catalog.py    # data/moon/lunar_{craters,seas}.csv
uv run scripts/moon/render_flat.py        # output/moon/lunar_globe_v3.svg
uv run scripts/moon/label_map.py          # output/moon/lunar_globe_v3_labeled.svg
uv run scripts/moon/render_relief.py      # output/moon/lunar_relief.png
uv run scripts/moon/render_moon.py        # output/moon/lunar_moon.png
uv run scripts/moon/render_truecolor.py   # output/moon/lunar_truecolor.png
uv run scripts/moon/build_globe_data.py   # web/moon/lunar_contours.js
uv run scripts/moon/build_labels.py       # web/moon/lunar_labels.js
uv run scripts/moon/build_globe_texture.py# web/moon/lunar_truecolor.js
```

## The coloured relief map

`output/moon/lunar_relief.png` is a 5760 × 2880 equirectangular map: a hillshade
computed from the elevation gradients (scaled with the real metres-per-pixel
from the geotransform) multiplied by a hypsometric colour ramp, written as an
8-bit RGB PNG through GDAL. Tune `Z_FACTOR` (relief exaggeration), `PALETTE`
and `AZIMUTH`/`ALTITUDE` (sun position) in `scripts/moon/render_relief.py`.

`output/moon/lunar_moon.png` is the same hillshade shown the way the eye sees
the Moon — a neutral warm-grey albedo blending with the relief, dark maria and
bright highlands — from `scripts/moon/render_moon.py`.

`output/moon/lunar_truecolor.png` drapes a real albedo map over the hillshade.
Rendered at 8192 × 4096. The DEM stores elevation only, so
`scripts/moon/render_truecolor.py` pulls NASA SVS's public-domain [CGI Moon
Kit](https://svs.gsfc.nasa.gov/4720) LROC WAC colour map (8k equirectangular),
rolls it 180° to line up with the 0…360°E DEM (alignment verified by
correlating albedo brightness against elevation), and multiplies it by the same
hillshade. Raise `SATURATION` above 1.0 to exaggerate the mineral tints.

Mars is produced the same way: `output/mars/mars_relief.png` (hypsometric) and
`output/mars/mars_truecolor.png` (Viking colour × MOLA hillshade). The two
inputs come from USGS Astrogeology — download them into `data/mars/` first:

```
Mars_MGS_MOLA_DEM_mosaic_global_463m.tif   (2.1 GB)  elevation
Mars_Viking_ClrMosaic_global_925m.tif      (798 MB)  colour
```
from `https://planetarymaps.usgs.gov/mosaic/`.

## The interactive globe

Open `web/index.html` — a tabbed page with **Moon** (grey theme), **Earth**
(blue theme) and **Mars** (rust theme) globes, each with its own surface /
contours / labels / auto-spin toggles (surface is off by default). The
per-planet pages `web/moon/index.html` and `web/earth/index.html` still work
standalone.

Mars uses the MOLA DEM (`data/mars/Mars_MGS_MOLA_DEM_mosaic_global_463m.tif`)
for contours and hillshade and the Viking colour mosaic
(`Mars_Viking_ClrMosaic_global_925m.tif`) for the draped surface; its feature
names come from the USGS/IAU Mars gazetteer (`scripts/mars/extract_catalog.py`).

Everything loads straight off disk (plain `<script>` globals, `d3.min.js`
bundled locally).

* drag to rotate, scroll to zoom
* a **surface** selector per globe switches the sphere between **off** (plain
  gradient — the default), **photo** (true-colour mosaic) and **elevation**
  (hypsometric colour map)
* a **3D** toggle displaces the sphere by the DEM into real terrain geometry
  (shaded), independent of the surface colour; when surface is `off` it renders
  as a plain clay relief
* plus **contours**, **labels** and **auto-spin** toggles (contours + labels on
  by default)
* the sphere is a WebGL orthographic projection sampling an equirectangular
  texture, with the contour/label canvas composited on top
* each planet ships two textures as base64 data URLs
  (`<planet>_texture.js` photo, `<planet>_elev.js` elevation) so they stay
  origin-clean when opened from `file://`
* one simplified contour mesh (~660k points) keeps it light and smooth

## Exporting high-resolution PNGs

The flat map is a vector SVG, so render at any size with Inkscape:

```sh
inkscape --export-type=png --export-width=25600 \
         --export-filename=output/moon/lunar_globe_v3_labeled_25600.png \
         output/moon/lunar_globe_v3_labeled.svg
```

## Pipeline notes

* **Contours are closed loops.** The DEM is wrap-padded in longitude before
  contouring so lines crossing the 0°/360° seam close; anything left open only
  terminates at a pole.
* **Smooth vectors.** Marching-squares paths are smoothed and emitted as
  Catmull-Rom → cubic Bézier curves, so they stay clean at any zoom.
* **Labels.** Seas use their English phrase when the catalog has one
  ("Sea of Tranquillity"), else the Latin name (e.g. Mare Humboldtianum).
  A greedy rectangle test removes colliding labels.
