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


@dataclass
class Adapter:
    """Normalizes one library's API to zero-arg callables over shared inputs."""

    name: str
    encode: Optional[Callable[[], str]] = None
    decode: Optional[Callable[[], object]] = None
    bbox: Optional[Callable[[], object]] = None


# pygeohash is this project; always present.
ADAPTERS = [
    Adapter(
        "pygeohash",
        encode=lambda: pgh.encode(LAT, LON, precision=PRECISION),
        decode=lambda: pgh.decode(GEOHASH),
        bbox=lambda: pgh.get_bounding_box(GEOHASH),
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
        )
    )
except ImportError:  # pragma: no cover - optional comparison dependency
    pass


_ENCODERS = [a for a in ADAPTERS if a.encode]
_DECODERS = [a for a in ADAPTERS if a.decode]
_BBOXERS = [a for a in ADAPTERS if a.bbox]


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
    assert result is not None  # return shapes differ; just confirm it produced one


@pytest.mark.parametrize("adapter", _BBOXERS, ids=lambda a: a.name)
def test_bbox(benchmark, adapter):
    """Look up the bounding box of a geohash cell."""
    benchmark.group = "bbox"
    result = benchmark(adapter.bbox)
    assert result is not None
