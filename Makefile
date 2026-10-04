UV := uv run
MOON := scripts/moon
EARTH := scripts/earth
MARS := scripts/mars

.PHONY: all moon earth mars clean

all: moon earth mars

# ---------------------------------------------------------------- Moon -------
moon: moon-catalog moon-flat moon-labels moon-relief moon-surface moon-truecolor \
      moon-globe

## IAU-named craters + seas catalogues (downloads the USGS Gazetteer)
moon-catalog: data/moon/lunar_craters.csv data/moon/lunar_seas.csv
data/moon/lunar_craters.csv data/moon/lunar_seas.csv:
	$(UV) $(MOON)/extract_catalog.py

## Flat contour map (SVG)
moon-flat: output/moon/lunar_globe_v3.svg
output/moon/lunar_globe_v3.svg:
	$(UV) $(MOON)/render_flat.py

## Labelled flat contour map
moon-labels: output/moon/lunar_globe_v3_labeled.svg
output/moon/lunar_globe_v3_labeled.svg: output/moon/lunar_globe_v3.svg
	$(UV) $(MOON)/label_map.py

## Colourised shaded-relief map
moon-relief: output/moon/lunar_relief.png
output/moon/lunar_relief.png:
	$(UV) $(MOON)/render_relief.py

## Realistic grey shaded relief
moon-surface: output/moon/lunar_moon.png
output/moon/lunar_moon.png:
	$(UV) $(MOON)/render_moon.py

## True-colour LROC albedo draped with the hillshade (downloads the map)
moon-truecolor: output/moon/lunar_truecolor.png
output/moon/lunar_truecolor.png:
	$(UV) $(MOON)/render_truecolor.py

## Interactive globe data
moon-globe: web/moon/lunar_contours.js web/moon/lunar_labels.js \
            web/moon/lunar_truecolor.js web/moon/lunar_elev.js \
            web/moon/lunar_height.js
web/moon/lunar_contours.js:
	$(UV) $(MOON)/build_globe_data.py
web/moon/lunar_labels.js: data/moon/lunar_seas.csv data/moon/lunar_craters.csv
	$(UV) $(MOON)/build_labels.py
web/moon/lunar_truecolor.js web/moon/lunar_elev.js: output/moon/lunar_truecolor.png output/moon/lunar_relief.png
	$(UV) $(MOON)/build_globe_texture.py
web/moon/lunar_height.js: data/moon/LDEM_128.LBL
	$(UV) $(MOON)/build_globe_relief.py

# --------------------------------------------------------------- Earth -------
earth: earth-catalog earth-flat earth-labels earth-relief earth-truecolor \
       earth-globe

## Natural Earth place labels (downloads a small dataset)
earth-catalog: data/earth/places.csv
data/earth/places.csv:
	$(UV) $(EARTH)/extract_catalog.py

## Flat contour map (SVG)
earth-flat: output/earth/earth_globe.svg
output/earth/earth_globe.svg:
	$(UV) $(EARTH)/render_flat.py

## Labelled flat contour map
earth-labels: output/earth/earth_globe_labeled.svg
output/earth/earth_globe_labeled.svg: output/earth/earth_globe.svg data/earth/places.csv
	$(UV) $(EARTH)/label_map.py

## Colourised shaded-relief map
earth-relief: output/earth/earth_relief.png
output/earth/earth_relief.png:
	$(UV) $(EARTH)/render_relief.py

## True-colour Blue Marble draped with the hillshade (downloads the imagery)
earth-truecolor: output/earth/earth_truecolor.png
output/earth/earth_truecolor.png:
	$(UV) $(EARTH)/render_truecolor.py

## Interactive globe data
earth-globe: web/earth/earth_contours.js web/earth/earth_labels.js \
             web/earth/earth_texture.js web/earth/earth_elev.js \
             web/earth/earth_height.js
web/earth/earth_contours.js:
	$(UV) $(EARTH)/build_globe_data.py
web/earth/earth_labels.js: data/earth/places.csv
	$(UV) $(EARTH)/build_labels.py
web/earth/earth_texture.js web/earth/earth_elev.js: output/earth/earth_truecolor.png output/earth/earth_relief.png
	$(UV) $(EARTH)/build_globe_texture.py
web/earth/earth_height.js: data/earth/ETOPO_2022_v1_30s_N90W180_surface.tif
	$(UV) $(EARTH)/build_globe_relief.py

# ----------------------------------------------------------------- Mars ------
mars: mars-catalog mars-relief mars-truecolor mars-globe

## IAU-named Martian features (downloads the USGS Gazetteer)
mars-catalog: data/mars/mars_features.csv
data/mars/mars_features.csv:
	$(UV) $(MARS)/extract_catalog.py

## Colourised shaded-relief map
mars-relief: output/mars/mars_relief.png
output/mars/mars_relief.png:
	$(UV) $(MARS)/render_relief.py

## True-colour Viking mosaic draped with the hillshade (downloads the imagery)
mars-truecolor: output/mars/mars_truecolor.png
output/mars/mars_truecolor.png:
	$(UV) $(MARS)/render_truecolor.py

## Interactive globe data
mars-globe: web/mars/mars_contours.js web/mars/mars_labels.js \
            web/mars/mars_texture.js web/mars/mars_elev.js \
            web/mars/mars_height.js
web/mars/mars_contours.js:
	$(UV) $(MARS)/build_globe_data.py
web/mars/mars_labels.js: data/mars/mars_features.csv
	$(UV) $(MARS)/build_labels.py
web/mars/mars_texture.js web/mars/mars_elev.js: output/mars/mars_truecolor.png output/mars/mars_relief.png
	$(UV) $(MARS)/build_globe_texture.py
web/mars/mars_height.js: data/mars/Mars_MGS_MOLA_DEM_mosaic_global_463m.tif
	$(UV) $(MARS)/build_globe_relief.py

# ----------------------------------------------------------------- All -------
clean:
	rm -f output/moon/*.svg output/moon/*.png output/earth/*.svg output/earth/*.png
	rm -f output/mars/*.svg output/mars/*.png
	rm -f web/moon/lunar_*.js web/earth/earth_*.js web/mars/mars_*.js
