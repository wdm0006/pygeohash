# pygeohash — Agent Guide

**Repo:** `wdm0006/pygeohash` — PyGeoHash v3.3.2, a zero-dependency Python library for geohash encode/decode, neighbors, distances, statistics, and optional visualization. MIT licensed; published to PyPI as `pygeohash`.

> This is a **library**, not a service. There is no app to boot, no port, no database, and no required env vars. "Local dev" = editable install (with C extension) + a green test/lint/typecheck suite.

## Stack

| Layer | Choice |
|---|---|
| Language | Python ≥ 3.8 (library floor); dev env pins **3.10** (`make setup`) |
| Build | setuptools + **C extension** (`pygeohash/cgeohash/geohash_module.c`, `-O3`) — gcc required |
| Package manager | **uv** (`uv venv` / `uv pip install` / `uv run`, wrapped by the Makefile) |
| Tests | pytest + pytest-cov + pytest-benchmark — 423 tests, ~7 s, 88 % coverage |
| Lint / format | ruff (line length 120, target py38; `E,F,B,S` rules) |
| Types | mypy (strict-ish: `disallow_untyped_defs` etc.); ships `py.typed` |
| Multi-version | tox: py38–py312 |
| Docs | Sphinx (`docs/`) |
| Runtime deps | none. Extras: `viz` (matplotlib, folium), `benchmark` (comparison libs). The `dev` extra already includes the viz deps. |
| Services | none — nothing to start, no ports, no env vars |

## Commands

uv lives at `~/.local/bin/uv` (not on default PATH). All Makefile targets wrap `uv run`.

```bash
make setup        # uv venv --python=3.10 (downloads managed CPython 3.10 if missing)
make install-dev  # uv pip install -e ".[dev]" — builds the C extension
make test         # uv run pytest (addopts force coverage, -v, log-cli INFO)
make lint         # mypy + ruff check (type-check is a prerequisite of this target)
make type-check   # mypy pygeohash tests/typing
make format       # ruff format .
make test-all     # tox across py38–py312
make benchmark    # pytest benchmarks with --benchmark-enable
make docs         # Sphinx html build
make build        # python -m build (sdist + wheel)
make viz-examples # regenerate documentation images
```

CI also gates formatting — run `uv run ruff format . --check` before pushing.

Single test: `make test PYTEST_ARGS="tests/test_geohash.py"`.

## Codebase map

See [codebase-map.md](codebase-map.md).

## Local Verification Summary

Validated on sandbox `cmp_WXrvD8BB` (live session `icudbl9xcq7lsqozvkg0`), 2026-09-05, from a fresh checkout:

| Check | Result | Evidence |
|---|---|---|
| `make setup` | ✅ | CPython 3.10.21 venv created by uv |
| `make install-dev` | ✅ | C extension built: `geohash_module.cpython-310-x86_64-linux-gnu.so` loads |
| `make test` | ✅ | **423 passed** in 6.67 s; coverage 88 % (707 stmts / 85 miss) |
| `make lint` | ✅ | mypy: "no issues found in 14 source files"; ruff: "All checks passed!" |
| `ruff format --check` | ✅ | "40 files already formatted" |
| Primary flow | ✅ | README quick-start reproduced exactly: `encode(42.6, -5.6)` → `ezs42e44yx96`; `decode("ezs42")` → (42.60498046875, -5.60302734375); `geohash_approximate_distance("bcd3u","bc83n")` → 625441 m; `get_adjacent("kd3ybyu","right")` → `kd3ybyv`; `viz.plot_geohash("9q8yyk")` → PNG artifact; `viz.folium_map("u4pruyd")` → HTML artifact |

**Gotchas (verified, not guessed):**

- The README's decode comment shows rounded `'42.6', '-5.6'`; the API actually returns the **cell center** (42.60498046875, -5.60302734375). Assert with tolerance, not string equality.
- `tests/test_benchmark_comparison.py` parametrizes only `pygeohash` unless the `benchmark` extra (python-geohash, geohashr, …) is installed — expected, not a failure.
- `.cursor/rules/project_overview.mdc` is stale (references a removed `numba` extra and v2.1.0). Trust `pyproject.toml` (v3.3.2, no numba extra).
- uv is not preinstalled on fresh sandboxes: `curl -LsSf https://astral.sh/uv/install.sh | sh`.
- Headless viz needs `matplotlib.use("Agg")` before importing `pygeohash.viz`.

## Sandbox snapshot

- **snapshotId:** `muhi8bs7ugnelgvqxdbc:default` (E2B template baked from this session)
- **builtAt:** 2026-09-05T21:16:27.358Z
- **computer:** `cmp_WXrvD8BB` · live session `icudbl9xcq7lsqozvkg0`
- Snapshot contents: uv 0.12.10 at `~/.local/bin`, `.venv` (CPython 3.10.21 + dev extras installed), compiled C extension, warm caches.

## Repo policy

See [config.yml](config.yml) — default branch `master`, squash merge (recent history #131–#140 is squash-merged).
