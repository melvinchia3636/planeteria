# moon-is-fun

Elevation globes and maps for eight worlds — **Moon, Earth, Mars, Mercury,
Venus, Ceres, Vesta, Pluto** — built from real DEMs with numpy/scipy/
scikit-image, a WebGL viewer, and no GIS tooling.

**→ open [`web/index.html`](web/index.html)** for the tabbed interactive globes,
or visit the live site at **https://melvinchia3636.github.io/planeteria/**.

## Layout

```
data/<body>/        DEM + surface rasters, extracted feature catalogues
scripts/planets/    the whole pipeline
  config.py           per-body configuration (rasters, styling, naming)
  common.py           DEM/colour readers + latitude-aware hillshade
  build.py            task CLI (relief, truecolor, contours, …)
output/<body>/      generated PNG maps (+ optional flat SVG)
web/<body>/         generated globe data (JS globals, loaded lazily)
web/index.html      the tabbed globe viewer
web/d3.min.js       bundled d3 build
```

## Setup

Install [uv](https://docs.astral.sh/uv/), drop each body's two rasters into
`data/<body>/` (see `scripts/planets/config.py` for the exact filenames), then:

```sh
make                 # build every body
make mars            # build one body
make flat-moon       # optional flat SVG + labelled SVG for one body
make flat-all        # flat SVG + labelled SVG for every body
```

or run task-by-task:

```sh
uv run scripts/planets/build.py all  mars   # every task for Mars
uv run scripts/planets/build.py relief moon # just the hypsometric relief map
```

Tasks: `relief`, `truecolor`, `contours`, `texture`, `height`, `catalog`,
`labels`, `flat`, `flatlabels`. Each writes to `output/<body>/` and
`web/<body>/` and defines the globals `window.<BODY>_{CONTOURS,LABELS,TEXTURE,
ELEV,HEIGHT}`.

## Publishing

The generated globe data under `web/` is gitignored, so the site is published
from a separate `gh-pages` branch rather than `main`:

```sh
make pages   # rebuild gh-pages from web/ and push
```

GitHub Pages serves that branch at
<https://melvinchia3636.github.io/planeteria/>. Rerun `make pages` after
rebuilding any body's web assets.

## Data sources

All elevation models, surface imagery and label products — with filenames,
providers and processing settings — are documented in
[`DATA_SOURCES.md`](DATA_SOURCES.md).

The Moon's DEM is a headerless `.IMG` with a PDS3 `.LBL`; GDAL's PDS driver
reads it via the label, and `common.read_dem` auto-detects projected (metres)
vs geographic (degrees, e.g. ETOPO) grids.

## The coloured relief / true-colour maps

`output/<body>/<body>_relief.png` is a hypsometric tint (cool lows → warm mids
→ white highs) multiplied by a latitude-aware hillshade; `<body>_truecolor.png`
multiplies the real surface mosaic by the same hillshade. Tune `zfactor`,
`relief` and the palette in `config.py` / `common.py`.

## The interactive globe

Open `web/index.html`. A tab per body; the body's data `<script>`s are loaded
**lazily** on first open, so the initial page only pulls in the Moon. Each globe
has a right-hand sidebar with:

* **surface** — `off` (planet-tinted dark sphere), `photo`, or `elevation`
* **3D** — displaces the sphere with the DEM into real terrain geometry, with a
  **relief** slider for vertical exaggeration (structure-only "clay" when
  surface is off)
* **contours**, **labels**, **auto-spin**

The sphere is a WebGL orthographic projection sharing d3's rotation, sampling
an equirectangular texture (embedded as a base64 data URL so it stays
origin-clean under `file://`); the contour/label canvas is composited on top.

## Adding a body

1. Drop the DEM + surface GeoTIFFs into `data/<body>/`.
2. Add a `data/<body>/` entry to `scripts/planets/config.py` (rasters, `scale`,
   `nodata`, `radius` if geographic, `interval`, theme colours).
3. `make <body>`.

## Performance

The per-body work is parallelised and cached:

* Decimated DEM fields are cached under `.cache/` (`common.read_dem`), so
  `relief`, `truecolor`, `contours`, `height` and `flat` share one read of the
  (often multi-GB) raster instead of re-decoding it each time.
* Surface textures are embedded as **WebP** (quality 80/90) rather than PNG —
  photographic equirectangular maps compress far better this way.
* Contours are **delta + varint** encoded at 0.01° precision and embedded as
  base64, then decoded back to GeoJSON in the browser.
* Contour extraction (marching squares + smoothing + Douglas-Peucker) runs
  across `cpu_count()-1` processes, distributing the contour levels.
* PNG output uses zlib level 1 (the encode step dominated the old runtime).

Typical Moon timings went from ~22 s (contours) / ~11 s (relief) to ~7 s / ~4 s.
The globe payload for all eight bodies dropped from ~172 MB to ~31 MB.
`make clean` clears `.cache/` too.

## Pipeline notes

* Contours are wrap-padded in longitude so lines crossing the ±180°/0° seam
  close; edge cases only terminate at a pole.
* Marching-squares paths are smoothed and, for the flat SVG, emitted as
  Catmull-Rom → cubic-Bézier curves.
* Labels come from the USGS/IAU gazetteer per body (Earth uses Natural Earth
  populated places); a greedy rectangle test drops colliding labels.
