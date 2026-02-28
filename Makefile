.DEFAULT_GOAL := help

PY ?= python3
UV ?= uv
UV_PYTHON ?= 3.12
UV_RUN := $(UV) run --python $(UV_PYTHON)
RUST_WORKSPACE ?= .
PYTHON_DIR ?= python/src
MATURIN_MANIFEST ?= crates/ta-py/Cargo.toml

install: install-dev ## Install dependencies (dev mode)

install-dev: ## Install dependencies (dev mode)
	$(UV) sync --extra dev
	$(UV_RUN) --with maturin maturin develop --manifest-path $(MATURIN_MANIFEST)
	$(UV) pip install -e . --no-build-isolation

test: test-py test-rs ## Run all tests (Python + Rust)

test-py: ## Run Python tests (without coverage)
	@$(UV_RUN) --with pytest python -m pytest tests/ -q

test-rs: ## Run Rust workspace tests
	cargo test --workspace --manifest-path $(RUST_WORKSPACE)/Cargo.toml

test-cov: ## Run tests with coverage (HTML report)
	$(UV_RUN) --with pytest --with pytest-cov python -m pytest tests/unit/ --cov=laakhay.ta --cov-report=term-missing --cov-report=html -v

test-cov-xml: ## Run tests with coverage (XML report for CI)
	$(UV_RUN) --with pytest --with pytest-cov python -m pytest tests/unit/ --cov=laakhay.ta --cov-report=term-missing --cov-report=xml -v

lint: lint-py lint-rs ## Run all lint checks (Python + Rust)

lint-py: ## Run ruff linter for Python code
	$(UV_RUN) --with ruff ruff check $(PYTHON_DIR)/laakhay/ tests/

lint-rs: ## Run clippy for Rust workspace
	cargo clippy --workspace --manifest-path $(RUST_WORKSPACE)/Cargo.toml --all-targets -- -D warnings

lint-fix: lint-fix-py ## Auto-fix all lint issues where available

lint-fix-py: ## Run ruff linter and auto-fix Python issues
	$(UV_RUN) --with ruff ruff check --fix $(PYTHON_DIR)/laakhay/ tests/

format: format-py format-rs ## Format Python + Rust code

format-py: ## Format Python code with ruff formatter
	$(UV_RUN) --with ruff ruff format $(PYTHON_DIR)/laakhay/ tests/

format-rs: ## Format Rust code
	cargo fmt --all --manifest-path $(RUST_WORKSPACE)/Cargo.toml

format-check: format-check-py format-check-rs ## Check formatting (Python + Rust)

format-check-py: ## Check Python formatting
	$(UV_RUN) --with ruff ruff format --check $(PYTHON_DIR)/laakhay/ tests/

format-check-rs: ## Check Rust formatting
	cargo fmt --all --check --manifest-path $(RUST_WORKSPACE)/Cargo.toml

check: lint format-check test ## Run all checks (lint + format + tests)

fix: lint-fix format ## Auto-fix all fixable issues (lint + format)

ci: lint format-check test ## Run full CI-equivalent checks

build: ## Build the package
	$(UV_RUN) --with maturin maturin build --manifest-path $(MATURIN_MANIFEST) --release

check-rs: ## Run cargo check for Rust workspace
	cargo check --workspace --manifest-path $(RUST_WORKSPACE)/Cargo.toml

ci-quick: format-check-rs lint-rs lint-py ## Fast local CI guard

# Compatibility aliases (can be removed later)
rust-check: check-rs ## Alias for check-rs
rust-test: test-rs ## Alias for test-rs
rust-fmt: format-check-rs ## Alias for format-check-rs
rust-lint: lint-rs ## Alias for lint-rs

help: ## Show this help
	@awk 'BEGIN {FS=":.*##"} /^[a-zA-Z_-]+:.*?##/ {printf "\033[36m%-12s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)
