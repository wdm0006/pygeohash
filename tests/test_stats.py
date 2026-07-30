import math

import pytest

import pygeohash as pgh

# Two cells about 2 degrees apart, straddling the antimeridian.
WEST_OF_LINE = pgh.encode(0.0, 179.0)
EAST_OF_LINE = pgh.encode(0.0, -179.0)


def test_mean_across_antimeridian():
    """A collection straddling the antimeridian is centered near +/-180, not near Greenwich."""
    centroid = pgh.decode(pgh.mean([WEST_OF_LINE, EAST_OF_LINE]))

    assert abs(centroid.longitude) == pytest.approx(180.0, abs=1e-4)
    assert centroid.latitude == pytest.approx(0.0, abs=1e-4)


def test_mean_across_antimeridian_asymmetric():
    """An uneven cluster near the antimeridian leans toward its heavier side."""
    geohashes = [
        pgh.encode(10.0, 178.0),
        pgh.encode(10.0, 179.0),
        pgh.encode(10.0, -177.0),
    ]

    centroid = pgh.decode(pgh.mean(geohashes))

    assert centroid.longitude == pytest.approx(180.0, abs=1e-3)
    assert centroid.latitude == pytest.approx(10.0, abs=1e-4)


@pytest.mark.parametrize(
    "coordinates",
    [
        [(42.6, -5.6), (42.7, -5.5), (42.5, -5.7)],
        [(-33.9, 151.2), (-33.8, 151.3), (-34.0, 151.1)],
        [(0.0, 0.0), (0.1, 0.1), (-0.1, -0.1)],
        [(0.0, -45.0), (0.0, 0.0), (0.0, 45.0)],
        [(60.0, -120.0), (60.0, -119.9)],
    ],
)
def test_mean_matches_arithmetic_centroid_without_wrapping(coordinates):
    """Clusters that do not cross the antimeridian keep their arithmetic centroid."""
    geohashes = [pgh.encode(lat, lon) for lat, lon in coordinates]

    centroid = pgh.decode(pgh.mean(geohashes))

    assert centroid.latitude == pytest.approx(sum(lat for lat, _ in coordinates) / len(coordinates), abs=1e-4)
    assert centroid.longitude == pytest.approx(sum(lon for _, lon in coordinates) / len(coordinates), abs=1e-4)


def test_mean_of_wide_asymmetric_cluster_leans_toward_the_chord():
    """A circular mean of a wide, lopsided cluster differs slightly from the arithmetic one."""
    coordinates = [(51.5, -0.1), (48.9, 2.4), (52.5, 13.4)]
    geohashes = [pgh.encode(lat, lon) for lat, lon in coordinates]

    centroid = pgh.decode(pgh.mean(geohashes))
    arithmetic = sum(lon for _, lon in coordinates) / len(coordinates)

    assert centroid.longitude == pytest.approx(arithmetic, abs=0.01)
    assert centroid.longitude != pytest.approx(arithmetic, abs=1e-4)


def test_mean_of_antipodal_longitudes_is_deterministic():
    """Fully cancelling longitudes have no unique circular mean, so the arithmetic mean is used."""
    # decode("0") and decode("h") are centered exactly 180 degrees apart in longitude.
    geohashes = ["0", "h"]
    assert pgh.decode(geohashes[1]).longitude - pgh.decode(geohashes[0]).longitude == 180.0

    centroid = pgh.decode(pgh.mean(geohashes))

    assert centroid.longitude == pytest.approx(-67.5, abs=1e-4)
    assert pgh.mean(geohashes) == pgh.mean(geohashes)
    assert pgh.mean(list(reversed(geohashes))) == pgh.mean(geohashes)


def test_std_across_antimeridian_reflects_true_spread():
    """Spread statistics use the corrected centroid instead of an antipodal one."""
    # Roughly 2 degrees apart at the equator, so each cell sits ~111 km from the centroid.
    spread = pgh.std([WEST_OF_LINE, EAST_OF_LINE])

    assert spread == pytest.approx(111_195.0, rel=1e-3)
    assert pgh.variance([WEST_OF_LINE, EAST_OF_LINE]) == pytest.approx(spread**2, rel=1e-9)


def test_std_without_wrapping_is_unchanged():
    """A cluster away from the antimeridian keeps its previous spread."""
    assert pgh.variance(["u4pruyd", "u4pruyf", "u4pruyc"]) == pytest.approx(6665.5, abs=0.1)
    assert pgh.std(["u4pruyd", "u4pruyf", "u4pruyc"]) == pytest.approx(81.6, abs=0.1)


@pytest.mark.parametrize("precision", [1, 5, 8, 12])
def test_mean_honors_requested_precision(precision):
    assert len(pgh.mean([WEST_OF_LINE, EAST_OF_LINE], precision)) == precision


def test_mean_of_single_geohash_round_trips():
    assert pgh.mean([EAST_OF_LINE]) == EAST_OF_LINE


def test_empty_collection():
    assert pgh.mean([]) == ""
    assert pgh.mean([], 5) == ""
    assert pgh.variance([]) == 0.0
    assert pgh.std([]) == 0.0
    assert not math.isnan(pgh.std([]))
