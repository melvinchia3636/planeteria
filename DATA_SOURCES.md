# Data Sources

Every map and globe in this repository is derived from real, publicly available
planetary elevation and imagery datasets. The exact filenames the pipeline
expects are defined in [`scripts/planets/config.py`](scripts/planets/config.py);
drop the listed rasters into `data/<body>/` before running `make`.

## Summary

| Body | Elevation model | Surface imagery | Labels |
|---|---|---|---|
| Moon | LOLA `LDEM_128` (PDS3) | LROC WAC colour (NASA SVS) | IAU Gazetteer |
| Earth | ETOPO 2022 v1 30″ | Blue Marble: Next Generation | Natural Earth places |
| Mars | MGS MOLA 463 m | Viking colour mosaic 925 m | IAU Gazetteer |
| Mercury | MESSENGER DEM 665 m (v2) | MESSENGER colour mosaic 665 m (v3) | IAU Gazetteer |
| Venus | Magellan topography 4.6 km | Magellan C3-MDIR colourised 4.6 km | IAU Gazetteer |
| Ceres | Dawn FC HAMO DTM 60 ppd | Dawn FC 20 ppd | IAU Gazetteer |
| Vesta | Dawn HAMO DTM 48 ppd | Dawn FC HAMO mosaic 74 ppd | IAU Gazetteer |
| Pluto | New Horizons DEM 300 m (16-bit) | New Horizons mosaic 300 m (8-bit) | IAU Gazetteer |

Planetary rasters are distributed by **USGS Astrogeology**
([astrogeology.usgs.gov](https://astrogeology.usgs.gov/)), primarily under
[`https://planetarymaps.usgs.gov/mosaic/`](https://planetarymaps.usgs.gov/mosaic/).
The Moon's colour map comes from the NASA Scientific Visualization Studio
[CGI Moon Kit](https://svs.gsfc.nasa.gov/4720). Earth data comes from
NOAA/NCEI and NASA.

---

## Moon

| Layer | File | Dataset | Source |
|---|---|---|---|
| Elevation | `data/moon/LDEM_128.IMG` + `LDEM_128.LBL` | LRO **L**unar **O**rbiter **L**aser **A**ltimeter gridded DEM, v3.0, 128 px/deg (≈500 m) | NASA PDS Geosciences Node / LOLA team |
| Surface | `data/moon/lroc_color_poles_8k.tif` | LROC WAC colour mosaic (8k) | NASA SVS [CGI Moon Kit](https://svs.gsfc.nasa.gov/4720) |
| Labels | `data/moon/moon_features.csv` | IAU named features (centre points) | USGS Gazetteer of Planetary Nomenclature |

The `.IMG` is headerless raw pixels; all metadata lives in the PDS3 `.LBL`
(little-endian int16, `scale = 0.5`, `nodata = -32768`, radius 1737.4 km,
90°N…90°S / 0…360°E). It is read through GDAL's PDS driver via `rasterio`,
opening the `.LBL`, never the `.IMG`. No header is hand-parsed.

## Earth

| Layer | File | Dataset | Source |
|---|---|---|---|
| Elevation | `data/earth/ETOPO_2022_v1_30s_N90W180_surface.tif` | ETOPO 2022 v1, 30 arc-second global relief (surface) | NOAA/NCEI [ETOPO 2022](https://www.ncei.noaa.gov/products/etopo-global-relief-model) |
| Surface | `data/earth/world.topo.bathy.200412.3x21600x10800.jpg` | Blue Marble: Next Generation, topography + bathymetry (Dec 2004) | NASA [Visible Earth](https://visibleearth.nasa.gov/collection/1484/blue-marble) |
| Labels | `data/earth/places.csv` | 110 m populated places (capitals + major cities) | [Natural Earth](https://www.naturalearthdata.com/) via [`nvkelso/natural-earth-vector`](https://github.com/nvkelso/natural-earth-vector) |

ETOPO is a *geographic* grid (degrees) rather than projected metres, so
`config.py` supplies `radius = 6371 km`; `common.read_dem` detects this and
converts.

## Mars

| Layer | File | Dataset | Source |
|---|---|---|---|
| Elevation | `data/mars/Mars_MGS_MOLA_DEM_mosaic_global_463m.tif` | MGS MOLA global DEM, 463 m | USGS Astrogeology / MOLA team |
| Surface | `data/mars/Mars_Viking_ClrMosaic_global_925m.tif` | Viking colour mosaic, 925 m | USGS Astrogeology |
| Labels | `data/mars/mars_features.csv` | IAU named features | USGS Gazetteer |

## Mercury

| Layer | File | Dataset | Source |
|---|---|---|---|
| Elevation | `data/mercury/Mercury_Messenger_USGS_DEM_Global_665m_v2.tif` | MESSENGER global DEM, 665 m, v2 | USGS Astrogeology / MESSENGER team |
| Surface | `data/mercury/Mercury_MESSENGER_ClrMosaic_global_665m_v3.tif` | MESSENGER colour mosaic, 665 m, v3 | USGS Astrogeology |
| Labels | `data/mercury/mercury_features.csv` | IAU named features | USGS Gazetteer |

## Venus

| Layer | File | Dataset | Source |
|---|---|---|---|
| Elevation | `data/venus/Venus_Magellan_Topography_Global_4641m.tif` | Magellan global topography, 4.6 km | USGS Astrogeology / Magellan team |
| Surface | `data/venus/Venus_Magellan_C3-MDIR_Colorized_Global_Mosaic_4641m.tif` | Magellan C3-MDIR colourised mosaic, 4.6 km | USGS Astrogeology |
| Labels | `data/venus/venus_features.csv` | IAU named features | USGS Gazetteer |

## Ceres

| Layer | File | Dataset | Source |
|---|---|---|---|
| Elevation | `data/ceres/Ceres_Dawn_FC_HAMO_DTM_DLR_Global_60ppd_Oct2016.tif` | Dawn FC HAMO digital terrain model, 60 px/deg (≈1.9 km) | DLR / Dawn team, via USGS Astrogeology |
| Surface | `data/ceres/Ceres_Dawn_FC_DLR_global_20ppd_Oct2015.tif` | Dawn FC global mosaic, 20 px/deg (≈5.5 km) | DLR / Dawn team, via USGS Astrogeology |
| Labels | `data/ceres/ceres_features.csv` | IAU named features | USGS Gazetteer |

## Vesta

| Layer | File | Dataset | Source |
|---|---|---|---|
| Elevation | `data/vesta/Vesta_Dawn_HAMO_DTM_DLR_Global_48ppd.tif` | Dawn HAMO DTM, 48 px/deg (≈2.4 km) | DLR / Dawn team, via USGS Astrogeology |
| Surface | `data/vesta/Vesta_Dawn_FC_HAMO_Mosaic_Global_74ppd.tif` | Dawn FC HAMO mosaic, 74 px/deg (≈1.5 km) | DLR / Dawn team, via USGS Astrogeology |
| Labels | `data/vesta/vesta_features.csv` | IAU named features | USGS Gazetteer |

The Vesta DTM stores absolute radius (metres), not elevation above a reference
sphere, so `config.py` sets `subtract_median = True`.

## Pluto

| Layer | File | Dataset | Source |
|---|---|---|---|
| Elevation | `data/pluto/Pluto_NewHorizons_Global_DEM_300m_Jul2017_16bit.tif` | New Horizons global DEM, 300 m, 16-bit (July 2017) | NASA/JHUAPL New Horizons / USGS Astrogeology |
| Surface | `data/pluto/Pluto_NewHorizons_Global_Mosaic_300m_Jul2017_8bit.tif` | New Horizons global mosaic, 300 m, 8-bit (July 2017) | NASA/JHUAPL New Horizons / USGS Astrogeology |
| Labels | `data/pluto/pluto_features.csv` | IAU named features | USGS Gazetteer |

---

## Nomenclature and place labels

- **Planetary bodies** — [IAU Gazetteer of Planetary Nomenclature](https://planetarynames.wr.usgs.gov/),
  maintained by USGS Astrogeology. The pipeline downloads the per-body
  `*_nomenclature_center_pts` shapefile bundles from
  `https://asc-planetarynames-data.s3.us-west-2.amazonaws.com/<BODY>_nomenclature_center_pts.zip`
  and extracts the name, longitude, latitude and feature type. See
  `NOTABLE_TYPES` / `SEA_TYPES` in `config.py` for the feature classes kept.
- **Earth** — [Natural Earth](https://www.naturalearthdata.com/) 1:110m
  populated places, fetched as GeoJSON from
  `https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_110m_populated_places.geojson`.

---

## Derived values in `config.py`

| Setting | Meaning |
|---|---|
| `scale` | Multiplier converting raw DN to metres (Moon: `0.5`) |
| `nodata` | Value masked out before processing (often `-32768`) |
| `radius` | Body radius in metres; required only for geographic (degree) DEMs |
| `subtract_median` | Treat the raster as absolute radius and subtract the median |
| `lon0` | Longitude of column 0 (`0` for the 0…360°E Moon DEM, `-180` otherwise) |
| `interval` | Contour interval in metres |
| `zfactor`, `relief` | Vertical exaggeration for hillshade and the 3D globe |

## Generated artefacts

Nothing under `output/`, `web/*/*.js`, or `.cache/` is source data — all of it is
derived from the rasters above by `scripts/planets/build.py`.

## Attribution and licensing

These datasets are the work of NASA, USGS, NOAA, DLR, ESA and the respective
mission teams. They are generally in the public domain or released for
reuse with attribution; consult each provider's page for the exact terms before
redistributing the rasters. This repository ships only code and derived maps,
not the original multi-gigabyte datasets (see `.gitignore`).
