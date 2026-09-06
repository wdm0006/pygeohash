import math
import statistics

import pytest

import pygeohash as pgh
from pygeohash import stats

# Two cells about 2 degrees apart, straddling the antimeridian.
WEST_OF_LINE = pgh.encode(0.0, 179.0)
EAST_OF_LINE = pgh.encode(0.0, -179.0)

# Every public function that takes a collection of geohashes.
COLLECTION_FUNCTIONS = [
    pgh.northern,
    pgh.southern,
    pgh.eastern,
    pgh.western,
    pgh.mean,
    pgh.variance,
    pgh.std,
]

CLUSTER = ["u4pruyd", "u4pruyf", "u4pruyc"]


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


@pytest.mark.parametrize("function", COLLECTION_FUNCTIONS, ids=lambda function: function.__name__)
def test_bare_geohash_string_is_rejected(function):
    """A single geohash string is not a collection of geohashes, even though it iterates like one."""
    with pytest.raises(TypeError, match="collection of geohash strings"):
        function("u4pruyd")


@pytest.mark.parametrize("wrap", [list, tuple, set], ids=["list", "tuple", "set"])
def test_non_string_collections_are_unchanged(wrap):
    """Collections of geohashes keep their results whatever container they arrive in."""
    # Cardinal ties resolve in input order, and a set has none, so these cells are
    # chosen to share neither a latitude nor a longitude.
    north_east = pgh.encode(57.7, 10.5, 8)
    middle = pgh.encode(57.6, 10.4, 8)
    south_west = pgh.encode(57.5, 10.3, 8)
    corners = wrap([middle, north_east, south_west])

    assert pgh.northern(corners) == north_east
    assert pgh.southern(corners) == south_west
    assert pgh.eastern(corners) == north_east
    assert pgh.western(corners) == south_west

    assert pgh.mean(wrap(CLUSTER)) == "u4pruyf1m6dt"
    assert pgh.variance(wrap(CLUSTER)) == pytest.approx(6665.5, abs=0.1)
    assert pgh.std(wrap(CLUSTER)) == pytest.approx(81.6, abs=0.1)


def test_single_element_collection_is_accepted():
    """One geohash wrapped in a collection is the supported way to summarize a single cell."""
    assert pgh.northern(["u4pruyd"]) == "u4pruyd"
    assert pgh.southern(["u4pruyd"]) == "u4pruyd"
    assert pgh.eastern(["u4pruyd"]) == "u4pruyd"
    assert pgh.western(["u4pruyd"]) == "u4pruyd"
    assert pgh.mean(["u4pruyd"], 7) == "u4pruyd"
    assert pgh.variance(["u4pruyd"]) == pytest.approx(0.0, abs=1e-3)
    assert pgh.std(["u4pruyd"]) == pytest.approx(0.0, abs=1e-1)


@pytest.mark.parametrize("function", COLLECTION_FUNCTIONS, ids=lambda function: function.__name__)
def test_empty_collection_is_still_accepted(function):
    """The guard rejects strings only; an empty collection keeps its documented result."""
    assert function([]) in ("", 0.0)


# ---------------------------------------------------------------------------
# Circular-mean cancellation fallback and boundary semantics. These target the
# real (non-log-string) mutants of _circular_mean_longitude: a hypot that
# drops one of its two arguments, and the <= / < tolerance boundary.
# ---------------------------------------------------------------------------


def test_circular_mean_longitude_falls_back_when_vectors_cancel():
    """A pair symmetric about +/-90 cancels mean_sin exactly, so the arithmetic mean wins."""
    # sin(90) and sin(-90) cancel to exactly 0.0 and the cosines sum to ~1.2e-16, so the
    # resultant vector length is ~6.1e-17 -- far below the 1e-12 tolerance.
    assert stats._circular_mean_longitude([90.0, -90.0]) == 0.0


def test_circular_mean_longitude_vector_mean_survives_negligible_cosine():
    """A large mean_sin with a negligible mean_cos still takes the vector-mean branch."""
    # mean_sin = 1/3 while mean_cos = 6.1e-17. A hypot that dropped mean_sin would read
    # ~0, wrongly trigger the fallback, and return the arithmetic mean of 30 instead.
    result = stats._circular_mean_longitude([90.0, -90.0, 90.0])

    assert result == pytest.approx(90.0, abs=1e-6)
    assert result != pytest.approx(30.0, abs=1e-6)


def test_circular_mean_longitude_vector_mean_survives_negligible_sine():
    """A large mean_cos with a negligible mean_sin still takes the vector-mean branch."""
    # mean_cos = 1/3 while mean_sin = 4.1e-17. A hypot that dropped mean_cos would read
    # ~0, wrongly trigger the fallback, and return the arithmetic mean of 60 instead.
    result = stats._circular_mean_longitude([0.0, 0.0, 180.0])

    assert result == pytest.approx(0.0, abs=1e-6)
    assert result != pytest.approx(60.0, abs=1e-6)


def test_circular_mean_longitude_cancellation_boundary_is_inclusive(monkeypatch):
    """A resultant vector length exactly at the tolerance still takes the fallback branch."""
    radians = [math.radians(longitude) for longitude in (90.0, -90.0, 90.0)]
    mean_sin = statistics.mean(math.sin(radian) for radian in radians)
    mean_cos = statistics.mean(math.cos(radian) for radian in radians)
    monkeypatch.setattr(stats, "_CIRCULAR_MEAN_TOLERANCE", math.hypot(mean_sin, mean_cos))

    # At equality the <= comparison falls back to the arithmetic mean (exactly 30.0);
    # a strict < would take the vector branch and return ~90 instead.
    assert stats._circular_mean_longitude([90.0, -90.0, 90.0]) == 30.0


def test_circular_mean_longitude_non_canceling_vectors_take_the_vector_mean():
    """Vectors that do not cancel produce the circular mean, not the arithmetic one."""
    assert stats._circular_mean_longitude([0.0, 90.0]) == pytest.approx(45.0, abs=1e-9)


# ---------------------------------------------------------------------------
# User-facing message surface: exception text is API, not a log string.
# ---------------------------------------------------------------------------


def test_bare_geohash_string_error_names_both_the_problem_and_the_fix():
    """The bare-string TypeError message is asserted in full, anchors included."""
    with pytest.raises(
        TypeError,
        match=(
            r"^geohashes must be a collection of geohash strings, not a single geohash string\. "
            r"Wrap a single geohash in a collection, for example \['u4pruyd'\]\.$"
        ),
    ):
        pgh.mean("u4pruyd")


# ---------------------------------------------------------------------------
# Mean / variance / std precision on known inputs.
# ---------------------------------------------------------------------------


def test_variance_and_std_precision_on_known_cluster():
    """Spread statistics match their known values with a tighter band than the doctest round."""
    assert pgh.variance(CLUSTER) == pytest.approx(6665.510679876878, rel=1e-9)
    assert pgh.std(CLUSTER) == pytest.approx(81.64257884141631, rel=1e-9)
    # std is exactly the square root of the variance over the same collection.
    assert pgh.std(CLUSTER) == pytest.approx(math.sqrt(pgh.variance(CLUSTER)), rel=1e-12)


def test_mean_and_spread_precision_on_antimeridian_cluster():
    """An asymmetric antimeridian cluster has an exact mean cell and known spread."""
    cluster = [pgh.encode(10.0, 178.0), pgh.encode(10.0, 179.0), pgh.encode(10.0, -177.0)]

    assert pgh.mean(cluster) == "xczbzury0zhe"
    assert pgh.mean(cluster, 8) == "xczbzury"
    assert pgh.variance(cluster) == pytest.approx(55959952279.75226, rel=1e-9)
    assert pgh.std(cluster) == pytest.approx(236558.55993760246, rel=1e-9)


# ---------------------------------------------------------------------------
# Directional extremes.
# ---------------------------------------------------------------------------


def test_directional_extremes_keep_raw_longitudes_at_the_antimeridian():
    """Eastern/western extremes compare raw longitudes; they do not wrap at the antimeridian."""
    east_cell = pgh.encode(0.0, 179.0)
    west_cell = pgh.encode(0.0, -179.0)

    assert pgh.eastern([east_cell, west_cell]) == east_cell
    assert pgh.western([east_cell, west_cell]) == west_cell


def test_directional_extremes_break_latitude_ties_by_input_order():
    """Equal-valued latitude extremes resolve to the first geohash in input order."""
    first = pgh.encode(10.0, 5.0, 4)
    second = pgh.encode(10.0, -5.0, 4)
    assert pgh.decode(first).latitude == pgh.decode(second).latitude  # a genuine tie

    assert pgh.northern([first, second]) == first
    assert pgh.northern([second, first]) == second
    assert pgh.southern([first, second]) == first
    assert pgh.southern([second, first]) == second


def test_directional_extremes_break_longitude_ties_by_input_order():
    """Equal-valued longitude extremes resolve to the first geohash in input order."""
    first = pgh.encode(5.0, 10.0, 4)
    second = pgh.encode(-5.0, 10.0, 4)
    assert pgh.decode(first).longitude == pgh.decode(second).longitude  # a genuine tie

    assert pgh.eastern([first, second]) == first
    assert pgh.eastern([second, first]) == second
    assert pgh.western([first, second]) == first
    assert pgh.western([second, first]) == second
