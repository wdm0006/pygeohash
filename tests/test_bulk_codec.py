"""Element-for-element equivalence of encode_many/decode_many with the scalar API."""

import array
import math
import random
from typing import Any, Callable

import pytest

import pygeohash as pgh

rng = random.Random(159)  # noqa: S311
LATS = [rng.uniform(-90, 90) for _ in range(10_000)]
LONS = [rng.uniform(-180, 180) for _ in range(10_000)]


@pytest.mark.parametrize("precision", range(1, 13))
def test_encode_many_matches_scalar_loop(precision: int) -> None:
    expected = [pgh.encode(a, b, precision) for a, b in zip(LATS, LONS, strict=True)]
    assert pgh.encode_many(LATS, LONS, precision) == expected


def test_encode_many_default_precision_is_12() -> None:
    assert pgh.encode_many(LATS[:50], LONS[:50]) == [pgh.encode(a, b, 12) for a, b in zip(LATS, LONS, strict=True)][:50]


@pytest.mark.parametrize("precision", range(1, 13))
def test_decode_many_matches_scalar_loop(precision: int) -> None:
    hashes = pgh.encode_many(LATS, LONS, precision)
    decoded = pgh.decode_many(hashes)
    assert decoded == [pgh.decode(h) for h in hashes]
    assert all(type(point) is pgh.LatLong for point in decoded)


def test_decode_many_is_case_insensitive() -> None:
    assert pgh.decode_many(["EZS42", "u4PrUyd"]) == [pgh.decode("ezs42"), pgh.decode("u4pruyd")]


def test_lat_lon_order_is_not_swapped() -> None:
    assert pgh.encode_many([42.6], [-5.6], 5) == ["ezs42"]
    assert pgh.decode_many(["ezs42"])[0].latitude == pytest.approx(42.6, abs=0.01)


def test_scalar_accepted_numeric_shapes_are_accepted() -> None:
    assert pgh.encode_many([42, 42.5], [-5, -5.5], 6) == [pgh.encode(42, -5, 6), pgh.encode(42.5, -5.5, 6)]


@pytest.mark.parametrize("make", [list, tuple, iter, lambda seq: (x for x in seq), lambda seq: array.array("d", seq)])
def test_encode_many_accepts_iterable_shapes(make: Callable[[Any], Any]) -> None:
    lats, lons = LATS[:20], LONS[:20]
    assert pgh.encode_many(make(lats), make(lons), 8) == [pgh.encode(a, b, 8) for a, b in zip(lats, lons, strict=True)]


@pytest.mark.parametrize("make", [tuple, iter, lambda seq: (x for x in seq)])
def test_decode_many_accepts_iterable_shapes(make: Callable[[Any], Any]) -> None:
    hashes = pgh.encode_many(LATS[:20], LONS[:20], 7)
    assert pgh.decode_many(make(hashes)) == [pgh.decode(h) for h in hashes]


def test_numpy_arrays() -> None:
    np = pytest.importorskip("numpy")
    lats, lons = np.array(LATS[:50]), np.array(LONS[:50])
    assert pgh.encode_many(lats, lons, 9) == [pgh.encode(a, b, 9) for a, b in zip(LATS[:50], LONS[:50], strict=True)]
    lats32, lons32 = lats.astype(np.float32), lons.astype(np.float32)
    assert pgh.encode_many(lats32, lons32, 6) == [pgh.encode(a, b, 6) for a, b in zip(lats32, lons32, strict=True)]
    hashes = pgh.encode_many(lats, lons, 5)
    assert pgh.decode_many(np.array(hashes)) == pgh.decode_many(hashes)


def test_empty_input() -> None:
    assert pgh.encode_many([], []) == []
    assert pgh.decode_many([]) == []
    assert pgh.decode_many(iter(())) == []


BAD_COORDINATES = [
    (True, 1.0),
    (1.0, False),
    (math.nan, 1.0),
    (1.0, math.inf),
    (-math.inf, 1.0),
    (91.0, 1.0),
    (1.0, -180.5),
    ("a", 1.0),
    (1.0, None),
]


@pytest.mark.parametrize("bad_index", [0, 3])
@pytest.mark.parametrize("lat, lon", BAD_COORDINATES)
def test_encode_many_errors_match_scalar_with_index(lat: Any, lon: Any, bad_index: int) -> None:
    with pytest.raises(Exception) as scalar:
        pgh.encode(lat, lon, 6)
    lats, lons = [1.0] * 5, [2.0] * 5
    lats[bad_index], lons[bad_index] = lat, lon
    with pytest.raises(Exception) as bulk:
        pgh.encode_many(lats, lons, 6)
    assert type(bulk.value) is type(scalar.value)
    assert str(bulk.value) == f"{scalar.value} (at index {bad_index})"


BAD_GEOHASHES = ["", "a", "u4pruydqqvj8x", "u4pr!", 123, None, b"u4pru", ["u"], "u4pru\x00"]


@pytest.mark.parametrize("bad_index", [0, 3])
@pytest.mark.parametrize("value", BAD_GEOHASHES)
def test_decode_many_errors_match_scalar_with_index(value: Any, bad_index: int) -> None:
    with pytest.raises(Exception) as scalar:
        pgh.decode(value)
    items: list[Any] = ["u4pru"] * 5
    items[bad_index] = value
    with pytest.raises(Exception) as bulk:
        pgh.decode_many(items)
    assert type(bulk.value) is type(scalar.value)
    assert str(bulk.value) == f"{scalar.value} (at index {bad_index})"


@pytest.mark.parametrize("precision", [0, 13, -1, 6.5, "6", None, True])
def test_encode_many_precision_errors_match_scalar(precision: Any) -> None:
    with pytest.raises(Exception) as scalar:
        pgh.encode(1.0, 2.0, precision)
    for lats, lons in (([1.0], [2.0]), ([], [])):
        with pytest.raises(Exception) as bulk:
            pgh.encode_many(lats, lons, precision)
        assert type(bulk.value) is type(scalar.value)
        assert str(bulk.value) == str(scalar.value)


def test_unequal_lengths_raise() -> None:
    with pytest.raises(ValueError, match="same length"):
        pgh.encode_many([1.0, 2.0], [1.0])
    with pytest.raises(ValueError, match="same length"):
        pgh.encode_many([1.0], [1.0, 2.0])
    with pytest.raises(ValueError, match="same length"):
        pgh.encode_many((x for x in [1.0, 2.0]), (x for x in [1.0]))
    with pytest.raises(ValueError, match="same length"):
        pgh.encode_many((x for x in [1.0]), (x for x in [1.0, 2.0]))


def test_decode_many_rejects_bare_string() -> None:
    with pytest.raises(TypeError):
        pgh.decode_many("u4pruyd")


def test_non_iterable_inputs_raise_type_error() -> None:
    with pytest.raises(TypeError):
        pgh.encode_many(5, [1.0])  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        pgh.decode_many(5)  # type: ignore[arg-type]
