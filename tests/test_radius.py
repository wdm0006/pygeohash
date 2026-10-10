"""Independent spherical oracles for proximity candidate cells."""

import itertools
import math
import random

import pytest

import pygeohash as pgh
import pygeohash.bounding_box as bounds


def _distance(lat: float, lon: float, other_lat: float, other_lon: float) -> float:
    phi, other_phi = math.radians(lat), math.radians(other_lat)
    a = math.sin((other_phi - phi) / 2) ** 2
    a += math.cos(phi) * math.cos(other_phi) * math.sin(math.radians(other_lon - lon) / 2) ** 2
    return 2 * pgh.EARTH_RADIUS * math.asin(math.sqrt(min(1.0, max(0.0, a))))


def _destination(lat: float, lon: float, meters: float, bearing: float) -> tuple[float, float]:
    phi, lam = math.radians(lat), math.radians(lon)
    arc = meters / pgh.EARTH_RADIUS
    target_phi = math.asin(math.sin(phi) * math.cos(arc) + math.cos(phi) * math.sin(arc) * math.cos(bearing))
    target_lam = lam + math.atan2(
        math.sin(bearing) * math.sin(arc) * math.cos(phi), math.cos(arc) - math.sin(phi) * math.sin(target_phi)
    )
    return math.degrees(target_phi), (math.degrees(target_lam) + 180) % 360 - 180


def _oracle_distance(lat: float, lon: float, box: pgh.BoundingBox) -> float:
    # Numerically minimize along each meridian boundary, independently of the
    # production stationary-latitude formula. Include an interior meridian.
    meridians = [box.min_lon, box.max_lon]
    for equivalent in (lon - 360, lon, lon + 360):
        if box.min_lon <= equivalent <= box.max_lon:
            meridians.append(equivalent)
    best = math.inf
    for meridian in meridians:
        low, high = box.min_lat, box.max_lat
        for _ in range(55):
            left, right = low + (high - low) / 3, high - (high - low) / 3
            if _distance(lat, lon, left, meridian) <= _distance(lat, lon, right, meridian):
                high = right
            else:
                low = left
        best = min(best, *(_distance(lat, lon, phi, meridian) for phi in (box.min_lat, box.max_lat, (low + high) / 2)))
    return best


@pytest.mark.parametrize("seed", range(8))
def test_seeded_radius_point_coverage(seed: int) -> None:
    rng = random.Random(seed)  # noqa: S311
    centers = [(rng.uniform(-80, 80), rng.uniform(-180, 180))]
    centers += [(rng.uniform(81, 89), rng.choice([-1, 1]) * rng.uniform(179, 180))]
    centers += [(-rng.uniform(81, 89), rng.choice([-1, 1]) * rng.uniform(179, 180))]
    for lat, lon in centers:
        for precision in (3, 4, 5, 6):
            radius = rng.uniform(0.3, 1.5) * 100_000 / 4 ** (precision - 3)
            cells = pgh.geohashes_in_radius(lat, lon, radius, precision)
            assert cells == sorted(set(cells))
            assert pgh.encode(lat, lon, precision) in cells
            for _ in range(100):
                point = _destination(lat, lon, radius * rng.uniform(0, 0.999999), rng.uniform(0, 2 * math.pi))
                assert pgh.encode(*point, precision) in cells
            for cell in cells:
                assert _oracle_distance(lat, lon, pgh.get_bounding_box(cell)) <= radius + 1e-6


@pytest.mark.parametrize(
    "lat,lon,radius",
    [
        (0, 180, 200_000),
        (0, -180, 200_000),
        (85, 179.5, 900_000),
        (-85, -179.5, 900_000),
        (90, 42, 1),
        (-90, -42, 1),
        (60, 10, 4_000_000),
        (60, 10, 3_000_000),
        (0, 0, math.pi * pgh.EARTH_RADIUS),
        (0, 0, 2 * math.pi * pgh.EARTH_RADIUS),
    ],
)
def test_radius_matches_exhaustive_cell_oracle(lat: float, lon: float, radius: float) -> None:
    cells = set(pgh.geohashes_in_radius(lat, lon, radius, precision=2))
    expected = set()
    for chars in itertools.product("0123456789bcdefghjkmnpqrstuvwxyz", repeat=2):
        cell = "".join(chars)
        box = pgh.get_bounding_box(cell)
        nearest = _oracle_distance(lat, lon, box)
        if nearest <= radius + 1e-6:
            expected.add(cell)
        # A dense grid also checks coverage without depending on the optimizer.
        for row, col in itertools.product(range(5), repeat=2):
            phi = box.min_lat + (box.max_lat - box.min_lat) * row / 4
            lam = box.min_lon + (box.max_lon - box.min_lon) * col / 4
            if _distance(lat, lon, phi, lam) <= radius:
                assert cell in cells
    assert cells
    assert cells == expected


@pytest.fixture
def no_cell_enumeration(monkeypatch: pytest.MonkeyPatch) -> None:
    def unexpected_enumeration(*args: object, **kwargs: object) -> list[str]:
        pytest.fail("Invalid arguments reached cell enumeration")

    monkeypatch.setattr(bounds, "geohashes_in_box", unexpected_enumeration)


@pytest.mark.parametrize("radius", [1.0, 2 * math.pi * pgh.EARTH_RADIUS])
@pytest.mark.parametrize("axis", [0, 1])
@pytest.mark.parametrize("value", [True, False, math.nan, math.inf, -math.inf, "1", None])
def test_radius_rejects_invalid_coordinates(axis: int, value: float, radius: float, no_cell_enumeration: None) -> None:
    coords = [0.0, 0.0]
    coords[axis] = value
    message = "not a bool" if isinstance(value, bool) else "finite number"
    with pytest.raises(ValueError, match=message):
        pgh.geohashes_in_radius(*coords, radius, 1)


@pytest.mark.parametrize("lat,lon", [(91, 0), (-91, 0), (0, 181), (0, -181)])
def test_radius_rejects_out_of_world_coordinates(lat: float, lon: float, no_cell_enumeration: None) -> None:
    with pytest.raises(ValueError):
        pgh.geohashes_in_radius(lat, lon, 1, 1)


@pytest.mark.parametrize("value", [True, False, math.nan, math.inf, -math.inf, 0, -1, "1", None])
def test_radius_rejects_invalid_radius(value: float, no_cell_enumeration: None) -> None:
    with pytest.raises(ValueError):
        pgh.geohashes_in_radius(0, 0, value, 1)


@pytest.mark.parametrize("radius", [1.0, 2 * math.pi * pgh.EARTH_RADIUS])
@pytest.mark.parametrize("value", [True, False, 0, -1, 13, 1.5, math.nan, math.inf, "1", None])
def test_radius_rejects_invalid_precision(value: int, radius: float, no_cell_enumeration: None) -> None:
    with pytest.raises(ValueError):
        pgh.geohashes_in_radius(0, 0, radius, value)


def test_radius_public_export_and_defaults() -> None:
    from pygeohash.bounding_box import geohashes_in_radius

    assert pgh.geohashes_in_radius is geohashes_in_radius
    assert "geohashes_in_radius" in pgh.__all__
    assert pgh.geohashes_in_radius(42, -5, 1) == [pgh.encode(42, -5, 6)]
    assert pgh.encode(42, -5, 12) in pgh.geohashes_in_radius(42, -5, 0.0001, 12)


@pytest.mark.parametrize("lat", [-90.0, 90.0])
def test_arbitrarily_small_polar_radius(lat: float) -> None:
    cells = pgh.geohashes_in_radius(lat, 0.0, 1e-20, 2)
    expected = {pgh.encode(lat, -180 + 360 * col / 32 + 1, 2) for col in range(32)}
    assert set(cells) == expected


def test_nearest_point_on_meridian_is_not_clamped_center_latitude() -> None:
    cell = pgh.encode(60, 40, 2)
    box = pgh.get_bounding_box(cell)
    nearest = _oracle_distance(55, 0, box)
    clamped = min(_distance(55, 0, phi, box.min_lon) for phi in (box.min_lat, box.max_lat))
    assert clamped - nearest > 1000
    radius = (nearest + clamped) / 2
    assert cell in pgh.geohashes_in_radius(55, 0, radius, 2)


def test_circle_tangent_to_cell_boundary() -> None:
    radius = _distance(0, 0, 5.625, 0)
    cell = pgh.encode(5.625 + 0.01, 0.01, 2)
    assert cell in pgh.geohashes_in_radius(0, 0, radius, 2)
