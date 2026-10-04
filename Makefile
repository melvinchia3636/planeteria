UV := uv run
PLANETS := scripts/planets
BODIES := moon earth mars mercury venus ceres vesta pluto

.PHONY: all $(BODIES) flat-all png-all labeled clean

all: $(BODIES)

## Build every web/relief asset for a body, e.g.  make mars
$(BODIES):
	$(UV) $(PLANETS)/build.py all $@

## Flat contour SVG + labelled SVG for every body
flat-all: $(addprefix flat-,$(BODIES))

## Optional flat contour SVG + labelled SVG for one body, e.g.  make flat-moon
flat-%:
	$(UV) $(PLANETS)/build.py flat $*
	$(UV) $(PLANETS)/build.py flatlabels $*

## Rasterise the flat SVG(s) to medium + very-high-res PNGs, every body
png-all: $(addprefix png-,$(BODIES))

## Rasterise one body's flat SVG(s), e.g.  make png-moon
png-%:
	$(UV) $(PLANETS)/build.py png $*

## Collect every *_labeled* asset into output/labeled/ (hardlinks, no extra disk)
labeled:
	mkdir -p output/labeled
	@for b in $(BODIES); do ln -f output/$$b/$${b}_globe_labeled.png output/labeled/; done

clean:
	rm -f output/*/*.svg output/*/*.png
	rm -rf output/labeled
	rm -f web/*/*.js
	rm -rf .cache
