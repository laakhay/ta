SHELL := /bin/sh

# Configurable Python executable
PY ?= python3

.PHONY: help install test unit lint format coverage clean build publish

help:
	@echo "Make targets:"
	@echo "  install     Install project and optional requirements.*."
	@echo "  test        Run all tests (alias for 'unit')."
	@echo "  unit        Run unit test suite (tests/unit, tests/analytics, tests/signals)."
	@echo "  lint        Run ruff lint if available."
	@echo "  format      Run ruff format/black if available."
	@echo "  coverage    Run tests with coverage report."
	@echo "  clean       Remove caches and compiled artifacts."
	@echo "  build       Build distribution packages."
	@echo "  publish     Publish to PyPI (requires PYPI_TOKEN)."

install:
	@$(PY) -m pip install -U pip setuptools wheel
	@if [ -s requirements.txt ]; then \
		$(PY) -m pip install -r requirements.txt; \
	else \
		echo "requirements.txt empty or missing; skipping"; \
	fi
	@if [ -s requirements.dev.txt ]; then \
		$(PY) -m pip install -r requirements.dev.txt; \
	else \
		echo "requirements.dev.txt empty or missing; skipping"; \
	fi
	@$(PY) -m pip install -e .

test: unit

unit:
	@$(PY) -m pytest -q tests/

coverage:
	@$(PY) -m pytest tests/ --cov=laakhay/ta --cov-report=html --cov-report=term

lint:
	@command -v ruff >/dev/null 2>&1 && ruff check . || echo "ruff not installed; skipping lint"

format:
	@command -v ruff >/dev/null 2>&1 && ruff format . || true
	@command -v black >/dev/null 2>&1 && black . || echo "formatters not installed; skipping black"

clean:
	@find . -name '__pycache__' -type d -prune -exec rm -rf {} + 2>/dev/null || true
	@find . -name '*.pyc' -delete || true
	@find . -name '*.pyo' -delete || true
	@rm -rf .pytest_cache || true
	@rm -rf htmlcov || true
	@rm -rf .coverage || true
	@rm -rf dist || true
	@rm -rf build || true
	@rm -rf *.egg-info || true

build: clean
	@$(PY) -m pip install --upgrade build
	@$(PY) -m build --sdist --wheel

publish: build
	@$(PY) -m pip install --upgrade twine
	@$(PY) -m twine upload dist/*
