.DEFAULT_GOAL := help

PY ?= python3
UV ?= uv
UV_PYTHON ?= 3.12
UV_RUN := $(UV) run --python $(UV_PYTHON)

install: install-dev ## Install dependencies (dev mode)

install-dev: ## Install dependencies (dev mode)
	$(UV) sync --extra dev
	$(UV) pip install -e .

test: ## Run tests (without coverage)
	@$(UV_RUN) --with pytest python -m pytest tests/ -q

test-cov: ## Run tests with coverage (HTML report)
	$(UV_RUN) --with pytest --with pytest-cov python -m pytest tests/unit/ --cov=laakhay.ta --cov-report=term-missing --cov-report=html -v

test-cov-xml: ## Run tests with coverage (XML report for CI)
	$(UV_RUN) --with pytest --with pytest-cov python -m pytest tests/unit/ --cov=laakhay.ta --cov-report=term-missing --cov-report=xml -v

lint: ## Run ruff linter to check code quality
	$(UV_RUN) --with ruff ruff check laakhay/ tests/

lint-fix: ## Run ruff linter and auto-fix issues
	$(UV_RUN) --with ruff ruff check --fix laakhay/ tests/

format: ## Format code with ruff formatter
	$(UV_RUN) --with ruff ruff format laakhay/ tests/

format-check: ## Check if code is formatted correctly
	$(UV_RUN) --with ruff ruff format --check laakhay/ tests/

check: lint format-check ## Run all checks (lint + format check)

fix: lint-fix format ## Auto-fix all fixable issues (lint + format)

ci: lint format-check test ## Run CI checks (lint + format + test)

build: ## Build the package
	$(UV) build

help: ## Show this help
	@awk 'BEGIN {FS=":.*##"} /^[a-zA-Z_-]+:.*?##/ {printf "\033[36m%-12s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)
