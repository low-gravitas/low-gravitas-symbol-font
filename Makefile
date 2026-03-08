.PHONY: all update build install clean distclean

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

distclean: clean
	rm -rf vendor/
