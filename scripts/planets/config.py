"""Configuration for the generic planetary pipeline.

Each body maps to a DEM raster and a surface raster plus the styling the web
globe uses. Rasters may be projected (metres, as every USGS/PDS body here) or
geographic (degrees, e.g. ETOPO) — `common.read_dem` detects which and needs a
`radius` for the geographic case.

Add a body here, drop its two rasters in ``data/<body>/``, then run
``build.py all <body>``.
"""

PLANETS = {
    "moon": {
        "display": "MOON",
        "subtitle": "LOLA LDEM_128 · 500 m contours",
        "dem": "data/moon/LDEM_128.LBL",           # PDS3 label (GDAL PDS driver)
        "color": "data/moon/lroc_color_poles_8k.tif",
        "scale": 0.5,                              # DN -> metres
        "nodata": -32768.0,
        "radius": None,                            # projected (metres)
        "lon0": 0.0,                               # DEM spans 0..360°E
        "interval": 500.0, "relief": 0.05, "zfactor": 2.0,
        "catalog": "iau", "gazetteer": "MOON_nomenclature_center_pts",
        "label_rule": "moon", "label_kind": "sea",
        "accent": "#c9d3e0", "dim": "#8f9bb3",
        "gradient": ["#232833", "#12151d", "#080a10"],
        "clay": [0.68, 0.69, 0.72],
        "graticule": "#2b3140", "sphere": "#6b7488",
        "contourOn": "rgba(205,214,228,0.45)", "contourOff": "#c9d3e0",
        "rotate": [-20, -18],
    },
    "earth": {
        "display": "EARTH",
        "subtitle": "ETOPO 2022 · 1000 m contours",
        "dem": "data/earth/ETOPO_2022_v1_30s_N90W180_surface.tif",
        "color": "data/earth/world.topo.bathy.200412.3x21600x10800.jpg",
        "scale": 1.0,
        "nodata": -99999.0,
        "radius": 6371000.0,                       # geographic (degrees)
        "lon0": -180.0,
        "interval": 1000.0, "relief": 0.05, "zfactor": 6.0,
        "catalog": "places", "gazetteer": None,
        "label_rule": "places", "label_kind": "city",
        "accent": "#6fb4ff", "dim": "#4a7fb5",
        "gradient": ["#0e2140", "#081426", "#050a14"],
        "clay": [0.36, 0.55, 0.80],
        "graticule": "#244a70", "sphere": "#4a7fb5",
        "contourOn": "rgba(120,190,255,0.5)", "contourOff": "#5fb0ff",
        "rotate": [-10, -20],
    },
    "mars": {
        "display": "MARS",
        "subtitle": "MOLA · 1000 m contours",
        "dem": "data/mars/Mars_MGS_MOLA_DEM_mosaic_global_463m.tif",
        "color": "data/mars/Mars_Viking_ClrMosaic_global_925m.tif",
        "scale": 1.0, "nodata": -32768.0, "radius": None, "lon0": -180.0,
        "interval": 1000.0, "relief": 0.05, "zfactor": 1.2,
        "catalog": "iau", "gazetteer": "MARS_nomenclature_center_pts",
        "label_rule": "feature", "label_kind": "feature",
        "accent": "#e8a878", "dim": "#b5764a",
        "gradient": ["#3a1a10", "#241009", "#140704"],
        "clay": [0.76, 0.44, 0.27],
        "graticule": "#5a3320", "sphere": "#a05a33",
        "contourOn": "rgba(245,190,140,0.5)", "contourOff": "#e8a878",
        "rotate": [-40, -20],
    },
    "mercury": {
        "display": "MERCURY",
        "subtitle": "MESSENGER · 1000 m contours",
        "dem": "data/mercury/Mercury_Messenger_USGS_DEM_Global_665m_v2.tif",
        "color": "data/mercury/Mercury_MESSENGER_ClrMosaic_global_665m_v3.tif",
        "scale": 1.0, "nodata": -32768.0, "radius": None, "lon0": -180.0,
        "interval": 1000.0, "relief": 0.06, "zfactor": 1.3,
        "catalog": "iau", "gazetteer": "MERCURY_nomenclature_center_pts",
        "label_rule": "feature", "label_kind": "feature",
        "accent": "#d3c2a0", "dim": "#93856a",
        "gradient": ["#2b2519", "#171309", "#0a0805"],
        "clay": [0.72, 0.67, 0.57],
        "graticule": "#4a4030", "sphere": "#a8946f",
        "contourOn": "rgba(240,220,180,0.5)", "contourOff": "#d3c2a0",
        "rotate": [-10, -20],
    },
    "venus": {
        "display": "VENUS",
        "subtitle": "Magellan · 1000 m contours",
        "dem": "data/venus/Venus_Magellan_Topography_Global_4641m.tif",
        "color": "data/venus/Venus_Magellan_C3-MDIR_Colorized_Global_Mosaic_4641m.tif",
        "scale": 1.0, "nodata": -32768.0, "radius": None, "lon0": -180.0,
        "interval": 1000.0, "relief": 0.05, "zfactor": 1.3,
        "catalog": "iau", "gazetteer": "VENUS_nomenclature_center_pts",
        "label_rule": "feature", "label_kind": "feature",
        "accent": "#ffcf8a", "dim": "#b58a4a",
        "gradient": ["#3a2a10", "#241807", "#140d04"],
        "clay": [0.85, 0.62, 0.32],
        "graticule": "#5a4020", "sphere": "#c89050",
        "contourOn": "rgba(255,215,150,0.5)", "contourOff": "#ffcf8a",
        "rotate": [-20, -15],
    },
    "ceres": {
        "display": "CERES",
        "subtitle": "Dawn · 2000 m contours",
        "dem": "data/ceres/Ceres_Dawn_FC_HAMO_DTM_DLR_Global_60ppd_Oct2016.tif",
        "color": "data/ceres/Ceres_Dawn_FC_DLR_global_20ppd_Oct2015.tif",
        "scale": 1.0, "nodata": -32768.0, "radius": None, "lon0": -180.0,
        "interval": 2000.0, "relief": 0.06, "zfactor": 1.3,
        "catalog": "iau", "gazetteer": "CERES_nomenclature_center_pts",
        "label_rule": "feature", "label_kind": "feature",
        "accent": "#aebfd8", "dim": "#6f7f97",
        "gradient": ["#1a2030", "#0e131d", "#070a10"],
        "clay": [0.62, 0.63, 0.68],
        "graticule": "#33404f", "sphere": "#7f8ea3",
        "contourOn": "rgba(180,200,230,0.5)", "contourOff": "#aebfd8",
        "rotate": [-20, -20],
    },
    "vesta": {
        "display": "VESTA",
        "subtitle": "Dawn · 2000 m contours",
        "dem": "data/vesta/Vesta_Dawn_HAMO_DTM_DLR_Global_48ppd.tif",
        "color": "data/vesta/Vesta_Dawn_FC_HAMO_Mosaic_Global_74ppd.tif",
        "scale": 1.0, "nodata": -3.0e38, "radius": None, "lon0": -180.0,
        "subtract_median": True,                   # DTM is absolute radius (m)
        "interval": 2000.0, "relief": 0.06, "zfactor": 1.3,
        "catalog": "iau", "gazetteer": "VESTA_nomenclature_center_pts",
        "label_rule": "feature", "label_kind": "feature",
        "accent": "#d0b6a6", "dim": "#8f7566",
        "gradient": ["#2a201a", "#171009", "#0a0705"],
        "clay": [0.70, 0.62, 0.55],
        "graticule": "#4a3a30", "sphere": "#a08a78",
        "contourOn": "rgba(230,200,180,0.5)", "contourOff": "#d0b6a6",
        "rotate": [-20, -20],
    },
    "pluto": {
        "display": "PLUTO",
        "subtitle": "New Horizons · 1000 m contours",
        "dem": "data/pluto/Pluto_NewHorizons_Global_DEM_300m_Jul2017_16bit.tif",
        "color": "data/pluto/Pluto_NewHorizons_Global_Mosaic_300m_Jul2017_8bit.tif",
        "scale": 1.0, "nodata": -32768.0, "radius": None, "lon0": -180.0,
        "interval": 1000.0, "relief": 0.05, "zfactor": 1.3,
        "catalog": "iau", "gazetteer": "PLUTO_nomenclature_center_pts",
        "label_rule": "feature", "label_kind": "feature",
        "accent": "#e6b88c", "dim": "#a07a52",
        "gradient": ["#2e2018", "#1a110b", "#0a0605"],
        "clay": [0.80, 0.64, 0.50],
        "graticule": "#4a3428", "sphere": "#b08a68",
        "contourOn": "rgba(245,210,170,0.5)", "contourOff": "#e6b88c",
        "rotate": [-180, -20],
    },
}

# IAU feature types worth labelling on the maps (lower-cased first word).
NOTABLE_TYPES = {
    "mons", "montes", "valles", "planum", "plana", "planitia", "planitiae",
    "chasma", "chasmata", "tholus", "tholi", "terra", "terrae", "patera",
    "paterae", "labyrinthus", "labyrinthi", "rupes", "rupēs", "chaos",
    "scopulus", "scopuli", "fossa", "fossae", "dorsum", "dorsa", "macula",
    "maculae", "cavus", "cavi", "collis", "colles", "fluctus", "undae",
    "rimae", "rima", "linea", "lineae", "regio", "regiones",
}

# Lunar "sea" feature types (labelled by their English phrase).
SEA_TYPES = {"Mare, maria", "Oceanus, oceani", "Lacus, lacūs",
             "Palus, paludes", "Sinus, sinūs"}
