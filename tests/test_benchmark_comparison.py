"""Head-to-head speed benchmarks: pygeohash vs other geohash libraries.

Motivated by apache/superset#37524, where Superset migrated from
``python-geohash`` (a C++ extension that fails to build in toolchain-less
containers) to ``pygeohash`` (pre-built wheels) and noted the new library was
slower without publishing numbers. This module quantifies where pygeohash sits
across the field on the operations Superset relies on: ``encode``, ``decode``,
and bounding box.

Competitors (all compute the *standard* geohash so the comparison is
apples-to-apples):

==================  ==============  ===========================================
Library             Implementation Notes
==================  ==============  ===========================================
pygeohash           C extension    this project
python-geohash      C++ extension  ``import geohash``; the Superset baseline
geohashr            Rust           ``import geohashr``
pygeohash-fast      Rust           ``(lon, lat)`` argument order
libgeohash          pure Python
geolib              pure Python     ``from geolib import geohash``
geohash-tools       pure Python
==================  ==============  ===========================================

Deliberately excluded: ``geohash-hilbert`` (Hilbert-curve variant, not a
standard geohash) and ``mzgeohash`` (no precision parameter, so equal work
cannot be guaranteed).

Eight operations are measured:

===============  ====================================================
Operation        Work
===============  ====================================================
encode           ``(42.6, -5.6)`` to a precision-9 geohash
decode           ``ezs42e44y`` back to coordinates
bbox             bounding box of the ``ezs42e44y`` cell
validate         ``is_valid_geohash("ezs42e44y")``
adjacent         one cell north of ``ezs42e44y``
adjacent-border  one cell west of ``u00000``, across the antimeridian
box-small        ``geohashes_in_box`` over a 4-cell box, precision 9
box-large        ``geohashes_in_box`` over a 361-cell box, precision 6
===============  ====================================================

Every measured call asserts its result, decode and bounding box included, so
no library can win by computing less: decode results must match
``ezs42e44y``'s actual doubles bit for bit, bounding boxes must match
pygeohash's cell, adjacency must produce the pinned neighbor (including the
antimeridian wrap ``u00000`` -> ``gbpbpb``), and box enumeration must return
the pinned cells.

Adapters exist wherever a competitor's API allows one; where it does not, the
library drops out of that operation's table and the generated page says so.
``python-geohash`` has no single-neighbor lookup (``neighbors()`` computes
all eight, which is not comparable work), no standalone validity check, and
no box enumeration. ``pygeohash-fast`` ships only encode and decode. No
competitor exposes a standalone validity check or box enumeration, so those
tables list pygeohash only.

Each competitor is optional (install the ``benchmark`` extra). A library that
is not importable simply drops out of the comparison; the pygeohash cases
always run.

Run with::

    uv run pytest tests/test_benchmark_comparison.py --benchmark-enable \
        --benchmark-group-by=group --benchmark-sort=mean
"""

from dataclasses import dataclass
from typing import Callable, Optional

import pytest

import pygeohash as pgh

# Shared inputs so every library is measured on identical work.
LAT, LON = 42.6, -5.6
PRECISION = 9
GEOHASH = "ezs42e44y"

# Decode of GEOHASH: every library measured returns exactly these doubles, so
# the assertion is bit for bit.
DECODE_EXPECTED = (42.59998083114624, -5.600001811981201)

# Bounding box of GEOHASH's cell as (min_lat, min_lon, max_lat, max_lon); every
# bbox-capable library agrees on these values.
BBOX_EXPECTED = (42.59995937347412, -5.60002326965332, 42.60000228881836, -5.599980354309082)

# Adjacency: one step north of GEOHASH, and the antimeridian wrap west of the
# polar-border cell u00000 (pinned by tests/test_neighbor.py).
ADJACENT_INPUT = GEOHASH
ADJACENT_BORDER_INPUT = "u00000"
ADJACENT_EXPECTED = "ezs42e45n"
ADJACENT_BORDER_EXPECTED = "gbpbpb"

# geohashes_in_box: a 4-cell box around GEOHASH's cell at precision 9, and a
# 0.1 deg x 0.2 deg box at precision 6 covering 361 cells.
BOX_SMALL_BBOX = pgh.BoundingBox(42.6, -5.6, 42.60003, -5.59998)
BOX_SMALL_PRECISION = 9
BOX_SMALL_EXPECTED = ["ezs42e44y", "ezs42e44z", "ezs42e45n", "ezs42e45p"]
BOX_LARGE_BBOX = pgh.BoundingBox(42.6, -5.6, 42.7, -5.4)
BOX_LARGE_PRECISION = 6
BOX_LARGE_CELLS = 361
BOX_LARGE_FIRST = "ezs42e"
BOX_LARGE_LAST = "ezs4vj"


@dataclass
class Adapter:
    """Normalizes one library's API to zero-arg callables over shared inputs."""

    name: str
    encode: Optional[Callable[[], str]] = None
    decode: Optional[Callable[[], object]] = None
    bbox: Optional[Callable[[], object]] = None
    validate: Optional[Callable[[], bool]] = None
    adjacent: Optional[Callable[[], str]] = None
    adjacent_border: Optional[Callable[[], str]] = None
    box_small: Optional[Callable[[], list]] = None
    box_large: Optional[Callable[[], list]] = None


# pygeohash is this project; always present.
ADAPTERS = [
    Adapter(
        "pygeohash",
        encode=lambda: pgh.encode(LAT, LON, precision=PRECISION),
        decode=lambda: pgh.decode(GEOHASH),
        bbox=lambda: pgh.get_bounding_box(GEOHASH),
        validate=lambda: pgh.is_valid_geohash(GEOHASH),
        adjacent=lambda: pgh.get_adjacent(ADJACENT_INPUT, "top"),
        adjacent_border=lambda: pgh.get_adjacent(ADJACENT_BORDER_INPUT, "left"),
        box_small=lambda: pgh.geohashes_in_box(BOX_SMALL_BBOX, precision=BOX_SMALL_PRECISION),
        box_large=lambda: pgh.geohashes_in_box(BOX_LARGE_BBOX, precision=BOX_LARGE_PRECISION),
    )
]

try:
    import geohash as _python_geohash

    ADAPTERS.append(
        Adapter(
            "python-geohash",
            encode=lambda: _python_geohash.encode(LAT, LON, PRECISION),
            decode=lambda: _python_geohash.decode(GEOHASH),
            bbox=lambda: _python_geohash.bbox(GEOHASH),
        )
    )
except ImportError:  # pragma: no cover - depends on a C++ toolchain at install
    pass

try:
    import geohashr as _geohashr

    ADAPTERS.append(
        Adapter(
            "geohashr",
            encode=lambda: _geohashr.encode(LAT, LON, PRECISION),
            decode=lambda: _geohashr.decode(GEOHASH),
            bbox=lambda: _geohashr.bbox(GEOHASH),
            adjacent=lambda: _geohashr.neighbor(ADJACENT_INPUT, "n"),
            adjacent_border=lambda: _geohashr.neighbor(ADJACENT_BORDER_INPUT, "w"),
        )
    )
except ImportError:  # pragma: no cover - optional comparison dependency
    pass

try:
    import pygeohash_fast as _pygeohash_fast

    # pygeohash-fast takes (lon, lat); decode returns (lon, lat, ...). No bbox.
    ADAPTERS.append(
        Adapter(
            "pygeohash-fast",
            encode=lambda: _pygeohash_fast.encode(LON, LAT, PRECISION),
            decode=lambda: _pygeohash_fast.decode(GEOHASH),
        )
    )
except ImportError:  # pragma: no cover - optional comparison dependency
    pass

try:
    import libgeohash as _libgeohash

    ADAPTERS.append(
        Adapter(
            "libgeohash",
            encode=lambda: _libgeohash.encode(LAT, LON, PRECISION),
            decode=lambda: _libgeohash.decode(GEOHASH),
            bbox=lambda: _libgeohash.bbox(GEOHASH),
            adjacent=lambda: _libgeohash.adjacent(ADJACENT_INPUT, "n"),
            adjacent_border=lambda: _libgeohash.adjacent(ADJACENT_BORDER_INPUT, "w"),
        )
    )
except ImportError:  # pragma: no cover - optional comparison dependency
    pass

try:
    import geolib.geohash as _geolib_geohash

    ADAPTERS.append(
        Adapter(
            "geolib",
            encode=lambda: _geolib_geohash.encode(LAT, LON, PRECISION),
            decode=lambda: _geolib_geohash.decode(GEOHASH),
            bbox=lambda: _geolib_geohash.bounds(GEOHASH),
            adjacent=lambda: _geolib_geohash.adjacent(ADJACENT_INPUT, "n"),
            adjacent_border=lambda: _geolib_geohash.adjacent(ADJACENT_BORDER_INPUT, "w"),
        )
    )
except ImportError:  # pragma: no cover - optional comparison dependency
    pass

try:
    import geohash_tools as _geohash_tools

    # geohash-tools offers no bounding box helper.
    ADAPTERS.append(
        Adapter(
            "geohash-tools",
            encode=lambda: _geohash_tools.encode(LAT, LON, PRECISION),
            decode=lambda: _geohash_tools.decode(GEOHASH),
            # geohash-tools offers no bounding box helper.
            adjacent=lambda: _geohash_tools.adjacent(ADJACENT_INPUT, "top"),
            adjacent_border=lambda: _geohash_tools.adjacent(ADJACENT_BORDER_INPUT, "left"),
        )
    )
except ImportError:  # pragma: no cover - optional comparison dependency
    pass


_ENCODERS = [a for a in ADAPTERS if a.encode]
_DECODERS = [a for a in ADAPTERS if a.decode]
_BBOXERS = [a for a in ADAPTERS if a.bbox]
_VALIDATORS = [a for a in ADAPTERS if a.validate]
_NEIGHBORS = [a for a in ADAPTERS if a.adjacent]
_NEIGHBORS_BORDER = [a for a in ADAPTERS if a.adjacent_border]
_SMALL_BOXERS = [a for a in ADAPTERS if a.box_small]
_LARGE_BOXERS = [a for a in ADAPTERS if a.box_large]


def normalized_decode(adapter, result):
    """Map one library's decode return shape to a (latitude, longitude) pair."""
    if adapter.name == "pygeohash-fast":  # returns (lon, lat, lat_err, lon_err)
        return (result[1], result[0])
    if adapter.name == "geolib":  # Point(lat=Decimal(...), lon=Decimal(...))
        return (float(result.lat), float(result.lon))
    return (result[0], result[1])  # (lat, lon) tuple or LatLong


def normalized_bbox(adapter, result):
    """Map one library's bounding-box shape to (min_lat, min_lon, max_lat, max_lon)."""
    if isinstance(result, dict):  # python-geohash, geohashr, libgeohash: s/w/n/e keys
        return (result["s"], result["w"], result["n"], result["e"])
    if adapter.name == "geolib":  # Bounds(sw=SouthWest(lat, lon), ne=NorthEast(lat, lon))
        return (result.sw.lat, result.sw.lon, result.ne.lat, result.ne.lon)
    return (result[0], result[1], result[2], result[3])  # BoundingBox named tuple


@pytest.fixture(scope="session", autouse=True)
def warmup():
    """Run every measured callable once, untimed, before any benchmark executes.

    First-touch cost (lazy imports, allocator growth, per-library caches) used
    to leak into the first suite run's medians and from there into the
    median-of-medians the docs publish: geohashr's encode median swung
    149 -> 231 ns across whole-suite repeats on the reference machine before
    this pass existed.
    """
    for adapter in ADAPTERS:
        for operation in adapter.__dataclass_fields__:
            if operation == "name":
                continue
            call = getattr(adapter, operation)
            if call is not None:
                call()


@pytest.mark.parametrize("adapter", _ENCODERS, ids=lambda a: a.name)
def test_encode(benchmark, adapter):
    """Encode (lat, lon) to a precision-9 geohash."""
    benchmark.group = "encode"
    result = benchmark(adapter.encode)
    assert result == GEOHASH  # every adapter must agree on the standard geohash


@pytest.mark.parametrize("adapter", _DECODERS, ids=lambda a: a.name)
def test_decode(benchmark, adapter):
    """Decode a geohash back to coordinates."""
    benchmark.group = "decode"
    result = benchmark(adapter.decode)
    assert normalized_decode(adapter, result) == DECODE_EXPECTED


@pytest.mark.parametrize("adapter", _BBOXERS, ids=lambda a: a.name)
def test_bbox(benchmark, adapter):
    """Look up the bounding box of a geohash cell."""
    benchmark.group = "bbox"
    result = benchmark(adapter.bbox)
    assert normalized_bbox(adapter, result) == BBOX_EXPECTED


@pytest.mark.parametrize("adapter", _VALIDATORS, ids=lambda a: a.name)
def test_is_valid_geohash(benchmark, adapter):
    """Check that the shared input cell passes validation."""
    benchmark.group = "validate"
    assert benchmark(adapter.validate) is True


@pytest.mark.parametrize("adapter", _NEIGHBORS, ids=lambda a: a.name)
def test_adjacent(benchmark, adapter):
    """Step one cell north of the shared input cell."""
    benchmark.group = "adjacent"
    assert benchmark(adapter.adjacent) == ADJACENT_EXPECTED


@pytest.mark.parametrize("adapter", _NEIGHBORS_BORDER, ids=lambda a: a.name)
def test_adjacent_border(benchmark, adapter):
    """Step west from a polar-border cell across the antimeridian."""
    benchmark.group = "adjacent-border"
    assert benchmark(adapter.adjacent_border) == ADJACENT_BORDER_EXPECTED


@pytest.mark.parametrize("adapter", _SMALL_BOXERS, ids=lambda a: a.name)
def test_geohashes_in_box_small(benchmark, adapter):
    """Enumerate the 4-cell box around the shared input cell at precision 9."""
    benchmark.group = "box-small"
    assert benchmark(adapter.box_small) == BOX_SMALL_EXPECTED


@pytest.mark.parametrize("adapter", _LARGE_BOXERS, ids=lambda a: a.name)
def test_geohashes_in_box_large(benchmark, adapter):
    """Enumerate the 0.1 deg x 0.2 deg box at precision 6: 361 cells."""
    benchmark.group = "box-large"
    result = benchmark(adapter.box_large)
    assert len(result) == BOX_LARGE_CELLS
    assert result == sorted(result)
    assert len(set(result)) == BOX_LARGE_CELLS
    assert result[0] == BOX_LARGE_FIRST and result[-1] == BOX_LARGE_LAST
    # Every returned cell must actually intersect the box: overlap in both axes
    # (boundary cells' centers can fall marginally outside the box itself).
    for geohash in result:
        cell = pgh.get_bounding_box(geohash)
        assert cell.min_lat <= BOX_LARGE_BBOX.max_lat and cell.max_lat >= BOX_LARGE_BBOX.min_lat
        assert cell.min_lon <= BOX_LARGE_BBOX.max_lon and cell.max_lon >= BOX_LARGE_BBOX.min_lon
