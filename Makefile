.PHONY: run ui

run:
	@python -c "from tow import tow; tow.main()"


ui:
	@bash scripts/makeui.sh
