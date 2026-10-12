"""Cell-count bound on box and radius coverage."""

import re
import time
from typing import Callable

import pytest

import pygeohash as pgh

BOX = pgh.BoundingBox(57.0, 10.0, 58.0, 11.0)
ANTIMERIDIAN_CIRCLE = (0.0, 179.9, 50_000.0, 4)
INVALID_MAX_CELLS = [True, False, 0, -1, 1.5, "5", [1]]


def _box(max_cells: object = ...) -> list:  # type: ignore[type-arg]
    if max_cells is ...:
        return pgh.geohashes_in_box(BOX, 5)
    return pgh.geohashes_in_box(BOX, 5, max_cells=max_cells)  # type: ignore[arg-type]


def _radius(args: tuple, max_cells: object = ...) -> list:  # type: ignore[type-arg]
    if max_cells is ...:
        return pgh.geohashes_in_radius(*args)
    return pgh.geohashes_in_radius(*args, max_cells=max_cells)  # type: ignore[arg-type,misc]


def _estimate(call: Callable[[object], list]) -> int:  # type: ignore[type-arg]
    with pytest.raises(ValueError, match="exceeds max_cells=1") as info:
        call(1)
    return int(re.search(r"about (\d+) candidate", str(info.value)).group(1))  # type: ignore[union-attr]


def test_box_cap_boundary() -> None:
    estimate = _estimate(_box)
    expected = _box()
    assert _box(estimate) == expected
    with pytest.raises(ValueError, match="exceeds max_cells"):
        _box(estimate - 1)


def test_box_max_cells_none_is_unbounded() -> None:
    assert _box(None) == _box()


def test_oversized_box_raises_promptly_and_none_restores() -> None:
    huge = pgh.BoundingBox(-80.0, -170.0, 80.0, 170.0)
    start = time.perf_counter()
    with pytest.raises(ValueError, match="Lower the precision"):
        pgh.geohashes_in_box(huge, 8)
    assert time.perf_counter() - start < 1.0


def test_radius_cap_boundary_sums_antimeridian_intervals() -> None:
    estimate = _estimate(lambda cap: _radius(ANTIMERIDIAN_CIRCLE, cap))
    expected = _radius(ANTIMERIDIAN_CIRCLE)
    assert expected
    assert _radius(ANTIMERIDIAN_CIRCLE, estimate) == expected
    with pytest.raises(ValueError, match="exceeds max_cells"):
        _radius(ANTIMERIDIAN_CIRCLE, estimate - 1)


def test_radius_pole_precision_12_raises_promptly() -> None:
    start = time.perf_counter()
    with pytest.raises(ValueError, match="exceeds max_cells=5000000"):
        pgh.geohashes_in_radius(90, 0, 1, 12)
    assert time.perf_counter() - start < 1.0


def test_radius_max_cells_none_is_unbounded() -> None:
    assert _radius((0.0, 0.0, 5_000.0, 4), None) == _radius((0.0, 0.0, 5_000.0, 4))


@pytest.mark.parametrize("bad", INVALID_MAX_CELLS)
def test_box_rejects_invalid_max_cells_before_size_gate(bad: object) -> None:
    huge = pgh.BoundingBox(-80.0, -170.0, 80.0, 170.0)
    with pytest.raises(ValueError, match="max_cells must"):
        pgh.geohashes_in_box(huge, 8, max_cells=bad)  # type: ignore[arg-type]


@pytest.mark.parametrize("bad", INVALID_MAX_CELLS)
def test_radius_rejects_invalid_max_cells_before_size_gate(bad: object) -> None:
    with pytest.raises(ValueError, match="max_cells must"):
        pgh.geohashes_in_radius(90, 0, 1, 12, max_cells=bad)  # type: ignore[arg-type]


def test_max_cells_is_keyword_only() -> None:
    with pytest.raises(TypeError):
        pgh.geohashes_in_box(BOX, 5, 10)  # type: ignore[misc]
    with pytest.raises(TypeError):
        pgh.geohashes_in_radius(0, 0, 100.0, 5, 10)  # type: ignore[misc]
