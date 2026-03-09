.PHONY: all update build install clean distclean release site

all: build

update:
	./update.sh
	./download-upstream.sh

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

site: dist/LowGravitasSymbols.ttf
	mkdir -p site/
	fontforge -script scripts/generate-manifest.py dist/LowGravitasSymbols.ttf site/glyphs.json
	cp dist/LowGravitasSymbols.ttf site/
	cp VERSION site/

distclean: clean
	rm -rf vendor/
