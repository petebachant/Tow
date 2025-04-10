.PHONY: run ui shortcut build

run:
	@uv run tow"


ui:
	@uv run bash scripts/makeui.sh


build:
	@uv run pyinstaller scripts/tow-script.py \
	--onedir \
	--noconsole \
	--noconfirm \
	--name tow \
	--add-data "tow/icons:tow/icons" \
	--icon tow/icons/tow_icon.ico

shortcut: build
	@uv run scripts/create_shortcut.py
