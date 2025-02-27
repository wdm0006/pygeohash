.PHONY: clean clean-test clean-pyc clean-build docs help lint format test test-all coverage install dev-install install-dev
.DEFAULT_GOAL := help

define BROWSER_PYSCRIPT
import os, webbrowser, sys

from urllib.request import pathname2url

webbrowser.open("file://" + pathname2url(os.path.abspath(sys.argv[1])))
endef
export BROWSER_PYSCRIPT

define PRINT_HELP_PYSCRIPT
import re, sys

for line in sys.stdin:
	match = re.match(r'^([a-zA-Z_-]+):.*?## (.*)$$', line)
	if match:
		target, help = match.groups()
		print("%-20s %s" % (target, help))
endef
export PRINT_HELP_PYSCRIPT

BROWSER := python -c "$$BROWSER_PYSCRIPT"

help:
	@python -c "$$PRINT_HELP_PYSCRIPT" < $(MAKEFILE_LIST)

clean: clean-build clean-pyc clean-test ## remove all build, test, coverage and Python artifacts

clean-build: ## remove build artifacts
	rm -fr build/
	rm -fr dist/
	rm -fr .eggs/
	find . -name '*.egg-info' -exec rm -fr {} +
	find . -name '*.egg' -exec rm -f {} +

clean-pyc: ## remove Python file artifacts
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +
	find . -name '__pycache__' -exec rm -fr {} +

clean-test: ## remove test and coverage artifacts
	rm -fr .tox/
	rm -f .coverage
	rm -fr htmlcov/
	rm -fr .pytest_cache
	rm -f coverage.xml

lint: install-dev ## check style with ruff
	uv run ruff check . --line-length=120

format: install-dev ## format code with ruff
	uv run ruff format . --line-length=120

install-dev: ## install package in development mode with all dependencies
	uv pip install -e ".[dev,numba]"

test: install-dev ## run tests quickly with the default Python
	uv run pytest

test-all: install-dev ## run tests on every Python version with tox
	uv run tox

coverage: install-dev ## check code coverage quickly with the default Python
	uv run pytest --cov=nbgeohash tests/
	uv run coverage report -m
	uv run coverage html
	$(BROWSER) htmlcov/index.html

docs: ## generate Sphinx HTML documentation, including API docs
	rm -f docs/nbgeohash.rst
	rm -f docs/modules.rst
	sphinx-apidoc -o docs/ nbgeohash
	$(MAKE) -C docs clean
	$(MAKE) -C docs html
	$(BROWSER) docs/_build/html/index.html

install: ## install the package to the active Python's site-packages
	uv pip install ".[dev,numba]"

dev-install: ## install the package in development mode (alias for install-dev)
	uv pip install -e ".[dev,numba]"

build: clean ## builds source and wheel package
	uv pip install build
	python -m build
	ls -l dist

release: build ## package and upload a release
	uv pip install twine
	twine upload dist/* 