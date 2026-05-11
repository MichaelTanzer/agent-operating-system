.PHONY: lint ci

MARKDOWNLINT ?= npx --yes markdownlint-cli2

lint:
	$(MARKDOWNLINT) "**/*.md"

ci: lint
