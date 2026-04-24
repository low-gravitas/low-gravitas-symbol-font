.PHONY: all update update-upstreams build install clean distclean release

all: build

update-upstreams:
	python3 scripts/update-upstreams.py

update: update-upstreams
	./update.sh

build: vendor/src/glyphs
	./build.sh

install: dist/LowGravitasSymbols.ttf
	cp dist/LowGravitasSymbols.ttf ~/Library/Fonts/

clean:
	rm -rf build/ dist/

release:
	@VERSION=$$(cat VERSION) && \
	git tag -a "v$$VERSION" -m "v$$VERSION" && \
	git push origin "v$$VERSION"

distclean: clean
	rm -rf vendor/
