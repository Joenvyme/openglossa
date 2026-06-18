# OpenGlossa — developer tasks.
# Uses `uv` if available, otherwise falls back to plain python/pip.

UV := $(shell command -v uv 2>/dev/null)
ifeq ($(UV),)
  PY := python
  RUN := python
  PIP := pip
else
  PY := uv run python
  RUN := uv run
  PIP := uv pip
endif

.DEFAULT_GOAL := help

.PHONY: help
help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
	  sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-12s\033[0m %s\n", $$1, $$2}'

.PHONY: setup
setup: ## Install the project with all extras (dev included)
ifeq ($(UV),)
	$(PIP) install -e ".[all,dev]"
else
	uv sync --extra all --extra dev
endif

.PHONY: test
test: ## Run the test suite
	$(RUN) pytest

.PHONY: lint
lint: ## Lint with ruff
	$(RUN) ruff check src tests

.PHONY: fmt
fmt: ## Auto-format with ruff
	$(RUN) ruff format src tests
	$(RUN) ruff check --fix src tests

.PHONY: typecheck
typecheck: ## Static type check with mypy
	$(RUN) mypy src

.PHONY: schema
schema: ## Export JSON Schemas (TermRecord, TranslationUnit, TermCandidate)
	$(PY) -m openglossa.schemas

.PHONY: exports
exports: ## Build all export formats (TBX/TMX/CSV/JSONL/Parquet) + validate
	$(RUN) python -m openglossa build-exports

.PHONY: mcp
mcp: ## Run the MCP server (Streamable HTTP)
	$(PY) -m openglossa.mcp.server

.PHONY: clean
clean: ## Remove caches and build artifacts
	rm -rf build dist *.egg-info .pytest_cache .ruff_cache .mypy_cache
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
