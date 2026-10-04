"""One-time generator for tests/fixtures/interop_vectors.json.

This is a development tool, NOT part of the test suite and NOT imported by
pytest (it does not match ``test_*.py``). It requires the ``mercantile``
package, which is deliberately NOT a pygeohash test dependency; it was used
once, while authoring the 3.6.0 interop feature, to cross-check every golden
vector in ``interop_vectors.json`` against an independent slippy-tile
reference implementation.

External references used for the one-time cross-check:

- ``mercantile`` (installed ad hoc for this run): tile rows and quadkeys for
  every forward vector, plus bbox containment for every inverse vector.
- The Bing Maps Tile System specification's worked example (tile (3, 5, 3)
  has quadkey "213"), which pins the quadkey digit convention (digit =
  x + 2*y per level) independently of mercantile.
- CartoDB ``python-quadkey`` was also installed per the feature spec, but its
  2.x code is Python-2-only (``xrange`` in tile_system.py, legacy absolute
  imports) and cannot execute on Python 3.13, so it contributed no vectors.

Re-run only if you intend to regenerate the fixture file::

    python tests/fixtures/generate_interop_vectors.py

Every vector is generated with pygeohash.interop itself and then verified:
tile/quadkey vectors against mercantile (same cell-centre point, same Web
Mercator math), inverse vectors by containment (the returned geohash cell must
contain the true Web Mercator tile centre, with the tie rule resolving west).
"""

from __future__ import annotations

import json
import math
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import mercantile  # noqa: E402  (dev-only dependency, see module docstring)

import pygeohash  # noqa: E402
from pygeohash import interop as it  # noqa: E402

B32 = "0123456789bcdefghjkmnpqrstuvwxyz"

# Named locations spread across the globe, including the equator, the prime
# meridian, the antimeridian, and both Web Mercator edges.
LOCATIONS = [
    (42.6, -5.6),  # the classic "ezs42" neighbourhood
    (0.0, 0.0),  # equator / prime meridian
    (45.0, 45.0),
    (-45.0, -45.0),
    (51.5, -0.1),  # London
    (-33.9, 151.2),  # Sydney
    (85.0, 179.9),  # near the north edge of the Mercator band
    (-85.0, -179.9),
    (67.5, 157.5),
]

TIE_SHOWCASES = [
    # (x, y, zoom): centres that land exactly on geohash cell boundaries and
    # resolve west per the tie rule. (1, 1, 2) is Bing's documented example
    # tile (quadkey "03"); (0, 0, 0) is the root tile whose centre is (0, 0).
    (1, 1, 2),
    (0, 0, 0),
    (3, 5, 3),
]


def mercator_centre_lat(y: int, zoom: int) -> float:
    """True tile-centre latitude (Web Mercator midpoint), independent of interop."""
    return math.degrees(math.atan(math.sinh(math.pi * (1.0 - 2.0 * (y + 0.5) / (1 << zoom)))))


def cell_contains(box, lat: float, lon: float) -> bool:
    return box.min_lat <= lat <= box.max_lat and box.min_lon <= lon <= box.max_lon


def add_pair(geohash: str, vectors: dict) -> None:
    """Record geohash -> tile/quadkey, cross-checked, for a non-polar cell."""
    lat, lon = pygeohash.decode(geohash)
    tile = it.geohash_to_tile(geohash)
    ref = mercantile.tile(lon, lat, tile.zoom)
    assert (ref.x, ref.y, ref.z) == (tile.x, tile.y, tile.zoom), (geohash, tile, ref)
    qk = it.geohash_to_quadkey(geohash)
    assert qk == mercantile.quadkey(ref), (geohash, qk, mercantile.quadkey(ref))
    vectors["to_tile"].append({"g": geohash, "x": tile.x, "y": tile.y, "z": tile.zoom})
    vectors["to_quadkey"].append({"g": geohash, "qk": qk})

    # Inverse at default precision, cross-checked by containment of the true
    # Web Mercator centre (latitude) and exact column bits (longitude).
    g_back = it.tile_to_geohash(tile.x, tile.y, tile.zoom)
    clat = mercator_centre_lat(tile.y, tile.zoom)
    clon = (mercantile.bounds(ref).west + mercantile.bounds(ref).east) / 2.0
    box = pygeohash.get_bounding_box(g_back)
    assert cell_contains(box, clat, clon), (tile, g_back, clat, clon, box)
    assert it.geohash_to_tile(g_back).x == tile.x, (g_back, tile)
    qk_back = mercantile.quadkey(ref)
    g_qk = it.quadkey_to_geohash(qk_back)
    assert g_qk == g_back, (qk_back, g_qk, g_back)
    precision = len(g_back)
    vectors["from_tile"].append({"x": tile.x, "y": tile.y, "z": tile.zoom, "p": None, "g": g_back})
    vectors["from_quadkey"].append({"q": qk_back, "p": None, "g": g_qk})

    # Explicit-precision variants per tile, checked the same way.
    for p in {max(1, precision - 1), min(12, precision + 1)}:
        g_exp = it.tile_to_geohash(tile.x, tile.y, tile.zoom, p)
        box_exp = pygeohash.get_bounding_box(g_exp)
        assert cell_contains(box_exp, clat, clon), (tile, p, g_exp)
        g_qk_exp = it.quadkey_to_geohash(qk_back, p)
        assert g_qk_exp == g_exp, (qk_back, p, g_qk_exp, g_exp)
        vectors["from_tile"].append({"x": tile.x, "y": tile.y, "z": tile.zoom, "p": p, "g": g_exp})
        vectors["from_quadkey"].append({"q": qk_back, "p": p, "g": g_qk_exp})


def add_polar(geohash: str, vectors: dict) -> None:
    """Record a polar cell: raises by default, clips to the edge row."""
    lat, lon = pygeohash.decode(geohash)
    tile = it.geohash_to_tile(geohash, clip=True)
    clamped = min(max(lat, -85.05112878), 85.05112878)
    ref = mercantile.tile(lon, clamped, tile.zoom)
    assert (ref.x, ref.y, ref.z) == (tile.x, tile.y, tile.zoom), (geohash, tile, ref)
    vectors["polar_raises"].append({"g": geohash, "clip_x": tile.x, "clip_y": tile.y, "clip_z": tile.zoom})


def main() -> None:
    rng = random.Random(20260906)  # noqa: S311 - deterministic fixture generation, not security
    vectors: dict = {
        "_comment": (
            "Golden vectors for pygeohash.interop. Generated once by "
            "tests/fixtures/generate_interop_vectors.py and cross-checked against "
            "mercantile and the Bing Maps Tile System spec's worked examples "
            "(see that script's docstring). Loaded by tests/test_interop.py."
        ),
        "to_tile": [],
        "to_quadkey": [],
        "from_quadkey": [],
        "from_tile": [],
        "to_int": [],
        "from_int": [],
        "polar_raises": [],
    }

    # 1) Named locations at every precision.
    for lat, lon in LOCATIONS:
        for p in range(1, 13):
            g = pygeohash.encode(lat, lon, precision=p)
            centre = pygeohash.decode(g)
            if abs(centre[0]) > 85.05112878:
                add_polar(g, vectors)
            else:
                add_pair(g, vectors)

    # 2) Seeded random cells per precision: 8 ordinary + up to 4 polar.
    # Precision 1 has no polar cells (max centre latitude 67.5 degrees).
    for p in range(1, 13):
        added = 0
        attempts = 0
        while added < 8 and attempts < 500:
            attempts += 1
            g = "".join(rng.choice(B32) for _ in range(p))
            if abs(pygeohash.decode(g)[0]) > 85.05112878:
                continue
            add_pair(g, vectors)
            added += 1
        assert added == 8, (p, added)
        polar_added = 0
        attempts = 0
        while polar_added < 4 and attempts < 2000:
            attempts += 1
            g = "".join(rng.choice(B32) for _ in range(p))
            if abs(pygeohash.decode(g)[0]) <= 85.05112878:
                continue
            add_polar(g, vectors)
            polar_added += 1

    # 3) Tie showcases: boundary centres resolve west per the tie rule.
    for x, y, zoom in TIE_SHOWCASES:
        g = it.tile_to_geohash(x, y, zoom)
        vectors["from_tile"].append({"x": x, "y": y, "z": zoom, "p": None, "g": g})
        vectors["from_quadkey"].append({"q": mercantile.quadkey(mercantile.Tile(x, y, zoom)), "p": None, "g": g})

    # 4) Integer form: exact for every precision, plus boundary values.
    for g in ["0", "z", "ezs42", "u4pruydqqvj", "8" * 12, "z" * 12]:
        value = it.geohash_to_int(g)
        assert it.geohash_from_int(value, len(g)) == g
        vectors["to_int"].append({"g": g, "v": value})
        vectors["from_int"].append({"v": value, "p": len(g), "g": g})
    vectors["from_int"].append({"v": 0, "p": 1, "g": "0"})
    vectors["from_int"].append({"v": 31, "p": 1, "g": "z"})

    out = Path(__file__).parent / "interop_vectors.json"
    out.write_text(json.dumps(vectors, indent=2, sort_keys=False) + "\n", encoding="utf-8")
    print(
        "wrote",
        out,
        "with",
        {k: len(v) for k, v in vectors.items() if not k.startswith("_")},
    )


if __name__ == "__main__":
    main()
