.DEFAULT_GOAL := help

PY ?= python3
UV ?= uv

install: install-dev ## Install dependencies (dev mode)

install-dev: ## Install dependencies (dev mode)
	$(UV) sync --extra dev
	$(UV) pip install -e .

test: ## Run tests
	$(UV) run pytest tests/ -v

test-cov: ## Run tests with coverage (HTML report)
	$(UV) run pytest tests/unit/ --cov=laakhay.ta --cov-report=term-missing --cov-report=html -v

test-cov-xml: ## Run tests with coverage (XML report for CI)
	$(UV) run pytest tests/unit/ --cov=laakhay.ta --cov-report=term-missing --cov-report=xml -v

lint: ## Run ruff linter to check code quality
	$(UV) run ruff check laakhay/ tests/

lint-fix: ## Run ruff linter and auto-fix issues
	$(UV) run ruff check --fix laakhay/ tests/

format: ## Format code with ruff formatter
	$(UV) run ruff format laakhay/ tests/

format-check: ## Check if code is formatted correctly
	$(UV) run ruff format --check laakhay/ tests/

check: lint format-check ## Run all checks (lint + format check)

fix: lint-fix format ## Auto-fix all fixable issues (lint + format)

build: ## Build the package
	$(UV) build

help: ## Show this help
	@awk 'BEGIN {FS=":.*##"} /^[a-zA-Z_-]+:.*?##/ {printf "\033[36m%-12s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

