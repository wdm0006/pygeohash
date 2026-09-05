---
name: local-dev
description: Bring a fresh pygeohash sandbox to a working dev environment (uv + Python 3.10 + C extension) and verify with pytest/ruff/mypy
---

# local-dev — pygeohash onboarding record

Recorded 2026-09-05 on sandbox `cmp_WXrvD8BB` (live session `icudbl9xcq7lsqozvkg0`). Every step below was run and verified end-to-end from a fresh checkout.

## Environment facts (fresh sandbox)

- System python3 is 3.13.14 — **not** the dev target. The Makefile pins 3.10.
- gcc 14.2.0 and make 4.4.1 are present; **uv is not preinstalled**.
- No external services, databases, ports, or env vars. Never invent a `docker compose up` here.

## Steps (in order)

1. `curl -LsSf https://astral.sh/uv/install.sh | sh` (installs to `~/.local/bin/uv`)
2. `export PATH="$HOME/.local/bin:$PATH"` (needed in every fresh shell)
3. `make setup` — downloads managed CPython 3.10.21 and creates `.venv`
4. `make install-dev` — `uv pip install -e ".[dev]"`; compiles `pygeohash/cgeohash/geohash_module.c` into a `.so`
5. `make test` — 423 passed / 6.67 s / 88 % coverage (pytest addopts force `--cov`, `-v`, log-cli INFO)
6. `make lint` — mypy ("no issues found in 14 source files") + ruff check; also `uv run ruff format . --check` (40 files clean)

## Primary flow (the library API is the "app")

```python
import matplotlib

matplotlib.use("Agg")  # headless
import pygeohash as pgh
from pygeohash.viz import plot_geohash, folium_map

pgh.encode(latitude=42.6, longitude=-5.6)  # 'ezs42e44yx96'
lat, lng = pgh.decode(geohash="ezs42")  # (42.60498046875, -5.60302734375)
pgh.geohash_approximate_distance("bcd3u", "bc83n")  # 625441
pgh.get_adjacent("kd3ybyu", "right")  # 'kd3ybyv'
plot_geohash("9q8yyk", color="red")  # matplotlib figure
folium_map("u4pruyd")  # folium map object
```

## Gotchas

- `decode` returns the **cell center**, not the rounded `'42.6', '-5.6'` shown in the README comment — assert with tolerance.
- Benchmark comparison tests parametrize only `pygeohash` unless the `benchmark` extra is installed; that is expected.
- `.cursor/rules/project_overview.mdc` is stale (numba extra, v2.1.0) — `pyproject.toml` is the source of truth (v3.3.2).
- Sandbox state persists across sequential `execute-command` calls on the same live session; parallel calls may land on different sandbox instances — keep repo workloads sequential.

## Cold-start timing

uv install ~2 s · venv ~3 s · install-dev ~4 s · tests ~7 s · lint ~5 s — under a minute total.
