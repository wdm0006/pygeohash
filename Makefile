.PHONY: help setup install install-dev test test-cov lint format clean build docs lint-fix test-all benchmark viz-examples install-viz

# Default target
help:
	@echo "Available commands:"
	@echo "  make setup        - Install uv and other required tools"
	@echo "  make install      - Install the package"
	@echo "  make install-dev  - Install the package with development dependencies"
	@echo "  make install-viz  - Install the package with visualization dependencies"
	@echo "  make test         - Run tests"
	@echo "  make test-cov     - Run tests with coverage"
	@echo "  make test-all     - Run tests on all supported Python versions using tox"
	@echo "  make benchmark    - Run performance benchmarks"
	@echo "  make lint         - Run linting checks"
	@echo "  make lint-fix     - Run linting checks and fix auto-fixable issues"
	@echo "  make format       - Format code with ruff"
	@echo "  make clean        - Clean build artifacts"
	@echo "  make build        - Build package distributions"
	@echo "  make docs         - Build documentation"
	@echo "  make viz-examples - Generate visualization examples for documentation"

# Setup development environment
setup:
	pip install uv
	uv venv --python=3.8

# Install the package
install:
	uv pip install -e .

# Install the package with development dependencies
install-dev:
	@echo "Installing development dependencies..."
	uv pip install -e ".[dev]"

# Install visualization dependencies
install-viz:
	@echo "Installing visualization dependencies..."
	uv pip install -e ".[viz]"

# Run tests
test:
	uv run pytest $(PYTEST_ARGS)

# Run tests with coverage
test-cov:
	uv run pytest --cov=elote --cov-report=term --cov-report=html $(PYTEST_ARGS)

# Run linting
lint:
	uv run ruff check . 

# Run linting and fix auto-fixable issues
lint-fix:
	uv run ruff check --fix .

# Format code
format:
	uv run ruff format .

# Clean build artifacts
clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf .pytest_cache/
	rm -rf .ruff_cache/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

# Build package distributions
build: clean
	uv run python -m build

# Build documentation
docs:
	cd docs && uv run $(MAKE) html SPHINXBUILD="python -m sphinx" 
	@echo "Opening documentation in Google Chrome..."
	@if [ "$(shell uname)" = "Darwin" ]; then \
		open -a "Google Chrome" docs/build/html/index.html; \
	else \
		if command -v google-chrome > /dev/null; then \
			google-chrome docs/build/html/index.html; \
		elif command -v google-chrome-stable > /dev/null; then \
			google-chrome-stable docs/build/html/index.html; \
		elif command -v chromium > /dev/null; then \
			chromium docs/build/html/index.html; \
		else \
			echo "Could not find Google Chrome. Please open docs/build/html/index.html manually."; \
		fi; \
	fi

# Run tests on all supported Python versions
test-all:
	uv run tox 

# Run benchmarks
benchmark:
	uv run pytest tests/test_benchmarks.py -v --benchmark-enable $(PYTEST_ARGS) 

# Generate visualization examples
viz-examples:
	@echo "Generating visualization examples for documentation..."
	@mkdir -p docs/source/_static/images
	@echo "Installing visualization dependencies..."
	uv pip install -e ".[viz]"
	uv run python scripts/generate_viz_examples.py 