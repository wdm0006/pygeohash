# pygeohash — Codebase Map

Folder-level overview (depth ≤ 2). The public API surface is re-exported from `pygeohash/__init__.py`.

| Path | Purpose |
|---|---|
| `pygeohash/` | Core package: `geohash.py` encode/decode (C fast path, pure-Python fallback), `neighbor.py` adjacent cells, `distances.py` approximate + haversine distances, `bounding_box.py` cell bounds, `stats.py` statistics over decoded points, `viz.py` matplotlib/folium plotting (viz extra), `types.py` + `geohash_types.py` typed containers, `logging.py`, `py.typed` marker |
| `pygeohash/cgeohash/` | C extension: `geohash_module.c` (compiled `-O3`), `geohash_module.pyi` stub, local `setup.py` |
| `tests/` | pytest suite: `test_geohash.py`, `test_neighbor.py`, `test_stats.py`, `test_bounding_box.py`, `test_types.py`, `test_viz.py`, `test_logging.py`, `test_geohash_accuracy.py` (validated vs geohash.org), `test_doctests.py`, `test_examples.py`, `test_benchmark*.py` |
| `tests/typing/` | typing-specific tests (`native_decode.py`) |
| `docs/` | Sphinx docs: `source/` rst pages (concepts, usage, api, types, benchmarks, examples) + `_static/` images, `Makefile`, `requirements.txt` |
| `examples/` | Runnable example scripts (basic ops, typed data, stats, visualization) + generated images |
| `scripts/` | Dev tooling: geohash test-data generator, viz example generator, cross-library benchmark, distribution smoke test |
| `.github/workflows/` | CI: `test.yml` (uv + tox), `code-quality.yml` (ruff format/check + mypy), `viz-extra.yml`, `publish-pypi.yml`, `publish-docs.yml`, `security.yml`, `validate-docs.yml` |
| `.cursor/rules/` | Editor guidance for pytest/python/sphinx/docs standards (⚠️ `project_overview.mdc` is stale — references a removed `numba` extra and v2.1.0) |
| Root | `pyproject.toml` (all tool config: pytest, coverage, ruff, mypy, tox, mutmut), `setup.py` (C extension build), `Makefile` (dev commands), `README.md`, `CONTRIBUTING.md`, `CHANGELOG.md`, `MANIFEST.in`, `LICENSE.txt` |
