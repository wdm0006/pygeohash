"""Tests for the distance module: known pairs, precision-table tiers, and extremes."""

import pytest

from pygeohash import geohash_approximate_distance, geohash_haversine_distance

# Exact expected haversine distances in meters (verified numerically). The tight
# relative tolerance pins the 6_371_000-meter Earth radius and the math.radians
# degree conversions: any constant or conversion mutant shifts these values out
# of band. The public API is meters-only; there is no unit-conversion surface.
NEAR_PAIR = ("u4pruyd", "u4pruyf")  # adjacent cells in Aarhus
FAR_PAIR = ("u4pruyd", "9q8yyk")  # Aarhus to Los Angeles
NEAR_METERS = 152.70299374405343
FAR_METERS = 8529224.883629857


def test_haversine_known_near_pair_in_meters():
    """Adjacent Aarhus cells are ~152.7 m apart."""
    assert geohash_haversine_distance(*NEAR_PAIR) == pytest.approx(NEAR_METERS, rel=1e-9)


def test_haversine_known_far_pair_in_meters():
    """Aarhus to Los Angeles is ~8,529 km."""
    assert geohash_haversine_distance(*FAR_PAIR) == pytest.approx(FAR_METERS, rel=1e-9)


def test_haversine_is_symmetric():
    """Distance is symmetric: swapping the pair yields the same meters."""
    assert geohash_haversine_distance(*FAR_PAIR) == geohash_haversine_distance(*reversed(FAR_PAIR))


def test_haversine_identical_geohash_is_exactly_zero():
    """A geohash measured against itself is exactly 0.0."""
    assert geohash_haversine_distance("u4pruyd", "u4pruyd") == 0.0


def test_haversine_antipodal_cells_exceed_half_the_equatorial_circumference():
    """Two equator cells at longitudes 0 and 180 are ~20,013.7 km apart."""
    distance = geohash_haversine_distance("s00000", "xbpbpb")

    assert distance == pytest.approx(20013720.978927333, rel=1e-6)
    assert distance > 20_000_000.0


def test_haversine_pole_to_pole_is_half_a_meridian():
    """Cells at the north and south poles are ~20,014.5 km apart."""
    north = geohash_haversine_distance("upbpbp", "h00000")

    assert north == pytest.approx(20014475.98405435, rel=1e-6)
    assert north > 20_000_000.0


def test_approximate_distance_matches_the_precision_table():
    """Each matching-character tier of the table returns its documented meters value."""
    assert geohash_approximate_distance("u4pruyd", "u4pruyf") == 610  # 6 matching
    assert geohash_approximate_distance("u4pruydqq", "u4pruydqw") == 19  # 8 matching
    assert geohash_approximate_distance("u4pruydqqv", "u4pruydqqw") == pytest.approx(3.71)  # 9
    assert geohash_approximate_distance("u4pruydqqvj8", "u4pruydqqvj9") == pytest.approx(0.6)  # capped at 10


def test_approximate_distance_no_matching_characters_returns_the_world_tier():
    """Zero matching characters falls through to the 20,000 km world tier."""
    assert geohash_approximate_distance("u4pruyd", "9q8yyk") == 20_000_000


def test_approximate_distance_is_case_sensitive_without_the_validity_check():
    """Without check_validity a case difference is no match at all."""
    assert geohash_approximate_distance("U4PRUYD", "u4pruyd") == 20_000_000


def test_approximate_distance_folds_case_with_the_validity_check():
    """With check_validity the same case-differing pair folds to an exact match."""
    assert geohash_approximate_distance("U4PRUYD", "u4pruyd", True) == 0.0


def test_approximate_distance_identical_geohashes_short_circuit_to_zero():
    """Identical inputs return 0.0 before any table lookup."""
    assert geohash_approximate_distance("u4pruyd", "u4pruyd") == 0.0


@pytest.mark.parametrize(
    ("geohash_1", "geohash_2", "message"),
    [
        ("!!invalid!!", "u4pruyd", "Geohash 1: !!invalid!! is not a valid geohash"),
        ("u4pruyd", "!!invalid!!", "Geohash 2: !!invalid!! is not a valid geohash"),
    ],
)
def test_approximate_distance_validity_check_names_the_offending_geohash(geohash_1, geohash_2, message):
    """The ValueError message is API surface and is asserted with anchors."""
    with pytest.raises(ValueError, match=rf"^{message}$"):
        geohash_approximate_distance(geohash_1, geohash_2, True)
