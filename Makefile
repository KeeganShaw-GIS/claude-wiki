.PHONY: build clean install

build:
	pyinstaller --onefile --name claude-wiki main.py
	@echo "Binary: dist/claude-wiki"

clean:
	rm -rf dist/ build/ claude-wiki.spec

install: build
	cp dist/claude-wiki /usr/local/bin/claude-wiki
	@echo "Installed to /usr/local/bin/claude-wiki"
