import random

import pytest
import pygeohash as pgh

__author__ = "willmcginnis"


def test_north_hemisphere_simple_odd():
    assert pgh.get_adjacent("gbsuv", "right") == "gbsuy"
    assert pgh.get_adjacent("gbsuv", "left") == "gbsuu"
    assert pgh.get_adjacent("gbsuv", "top") == "gbsvj"
    assert pgh.get_adjacent("gbsuv", "bottom") == "gbsut"


def test_north_hemisphere_border_even():
    assert pgh.get_adjacent("u00000", "right") == "u00002"
    assert pgh.get_adjacent("u00000", "left") == "gbpbpb"
    assert pgh.get_adjacent("u00000", "top") == "u00001"
    assert pgh.get_adjacent("u00000", "bottom") == "spbpbp"


def test_south_hemisphere_simple_odd():
    assert pgh.get_adjacent("kd3ybyu", "right") == "kd3ybyv"
    assert pgh.get_adjacent("kd3ybyu", "left") == "kd3ybyg"
    assert pgh.get_adjacent("kd3ybyu", "top") == "kd3ybzh"
    assert pgh.get_adjacent("kd3ybyu", "bottom") == "kd3ybys"


def test_south_hemisphere_border_even():
    assert pgh.get_adjacent("k0000000", "right") == "k0000002"
    assert pgh.get_adjacent("k0000000", "left") == "7bpbpbpb"
    assert pgh.get_adjacent("k0000000", "top") == "k0000001"
    assert pgh.get_adjacent("k0000000", "bottom") == "hpbpbpbp"


def test_north_pole_even():
    assert pgh.get_adjacent("gzzzzz", "right") == "upbpbp"
    assert pgh.get_adjacent("gzzzzz", "left") == "gzzzzx"
    assert pgh.get_adjacent("gzzzzz", "bottom") == "gzzzzy"
    with pytest.raises(ValueError):
        pgh.get_adjacent("gzzzzz", "top")


def test_south_pole_odd():
    assert pgh.get_adjacent("5bpbpbh", "right") == "5bpbpbj"
    assert pgh.get_adjacent("5bpbpbh", "left") == "5bpbpb5"
    assert pgh.get_adjacent("5bpbpbh", "top") == "5bpbpbk"
    with pytest.raises(ValueError):
        pgh.get_adjacent("5bpbpbh", "bottom")


def test_zero_length_geohash():
    """Test that a zero-length geohash raises a ValueError with the correct message."""
    with pytest.raises(ValueError, match="^The geohash length cannot be 0. Possible when close to poles$"):
        pgh.get_adjacent("", "top")


INVALID_GEOHASHES = [
    "a4pruyd",  # 'a' is not in the geohash alphabet
    "u4pr!yd",  # punctuation mid-string
    "u4pru!",  # invalid last character
    "u4pruydqqvjuu4pr",  # 16 characters, over the 12-character maximum
    "u4pruyd ",  # trailing whitespace
    "u4pr yd",  # embedded space
]


@pytest.mark.parametrize("geohash", INVALID_GEOHASHES)
@pytest.mark.parametrize("direction", ["right", "left", "top", "bottom"])
def test_invalid_geohash_raises(geohash, direction):
    with pytest.raises(ValueError, match="Invalid geohash"):
        pgh.get_adjacent(geohash, direction)


def test_invalid_last_character_message_is_geohash_specific():
    """An invalid final character must not leak str.index's 'substring not found'."""
    with pytest.raises(ValueError, match=r"^Invalid geohash: 'u4pru!'\."):
        pgh.get_adjacent("u4pru!", "top")


@pytest.mark.parametrize("direction", ["up", "down", "north", "TOP", "", "Right"])
def test_invalid_direction_raises_value_error(direction):
    with pytest.raises(ValueError, match="Must be one of 'right', 'left', 'top', 'bottom'"):
        pgh.get_adjacent("u4pruyd", direction)


def test_uppercase_geohash_is_still_accepted():
    assert pgh.get_adjacent("U4PRUYD", "top") == "u4pruyf"


def test_maximum_precision_geohash_is_accepted():
    assert pgh.get_adjacent("u4pruydqqvju", "top") == "u4pruydqqvjv"


ANTIMERIDIAN_PAIRS = [
    # (western-edge geohash, eastern-edge geohash) -- each is the other's east/west neighbor
    ("8", "x"),
    ("80", "xb"),
    ("80000", "xbpbp"),
    ("800000", "xbpbpb"),
    ("b10hbp2", "zcpuzzr"),
    ("21bp0h8n", "rczzpuxy"),
    ("b48j248j2", "zfxvrfxvr"),
]


@pytest.mark.parametrize("west, east", ANTIMERIDIAN_PAIRS)
def test_antimeridian_wraps_east(west, east):
    assert pgh.get_adjacent(east, "right") == west


@pytest.mark.parametrize("west, east", ANTIMERIDIAN_PAIRS)
def test_antimeridian_wraps_west(west, east):
    assert pgh.get_adjacent(west, "left") == east


@pytest.mark.parametrize("west, east", ANTIMERIDIAN_PAIRS)
def test_antimeridian_round_trip(west, east):
    assert pgh.get_adjacent(pgh.get_adjacent(east, "right"), "left") == east
    assert pgh.get_adjacent(pgh.get_adjacent(west, "left"), "right") == west


def test_antimeridian_neighbors_share_a_latitude_band():
    """The wrapped neighbor must sit at the same latitude, on the far side of +-180."""
    east_box = pgh.get_bounding_box("xbpbp")
    west_box = pgh.get_bounding_box(pgh.get_adjacent("xbpbp", "right"))
    assert (west_box.min_lat, west_box.max_lat) == (east_box.min_lat, east_box.max_lat)
    assert east_box.max_lon == 180.0
    assert west_box.min_lon == -180.0


def test_pole_has_no_neighbor_beyond_it():
    with pytest.raises(ValueError, match="beyond the north pole"):
        pgh.get_adjacent("gzzzzz", "top")
    with pytest.raises(ValueError, match="beyond the south pole"):
        pgh.get_adjacent("5bpbpbh", "bottom")
    with pytest.raises(ValueError, match="beyond the north pole"):
        pgh.get_adjacent("z", "top")
    with pytest.raises(ValueError, match="beyond the south pole"):
        pgh.get_adjacent("0", "bottom")


def _oracle_neighbors(geohash, include_self=False):
    """Neighbors derived from cell geometry: center +/- cell size, wrapped, re-encoded."""
    exact = pgh.decode_exactly(geohash)
    height, width = 2 * exact.latitude_error, 2 * exact.longitude_error
    cells = set()
    for dlat in (-1, 0, 1):
        for dlon in (-1, 0, 1):
            if dlat == 0 and dlon == 0:
                continue
            lat = exact.latitude + dlat * height
            if not -90 <= lat <= 90:
                continue
            lon = (exact.longitude + dlon * width + 180) % 360 - 180
            cells.add(pgh.encode(lat, lon, len(geohash)))
    if include_self:
        cells.add(geohash.lower())
    return sorted(cells)


def test_get_neighbors_known_cell():
    assert pgh.get_neighbors("u4pruyd") == _oracle_neighbors("u4pruyd")
    assert len(pgh.get_neighbors("u4pruyd")) == 8
    assert "u4pruyd" not in pgh.get_neighbors("u4pruyd")
    assert pgh.get_neighbors("u4pruyd", include_self=True) == sorted(pgh.get_neighbors("u4pruyd") + ["u4pruyd"])


def test_get_neighbors_matches_geometric_oracle_seeded_sweep():
    rng = random.Random(166)  # noqa: S311
    for precision in range(1, 10):
        for _ in range(150):
            cell = pgh.encode(rng.uniform(-90, 90), rng.uniform(-180, 180), precision)
            assert pgh.get_neighbors(cell) == _oracle_neighbors(cell), cell
            assert pgh.get_neighbors(cell, include_self=True) == _oracle_neighbors(cell, include_self=True), cell


@pytest.mark.parametrize("precision", [1, 2, 5])
@pytest.mark.parametrize("north", [True, False])
def test_get_neighbors_polar_cells_have_five_neighbors(precision, north):
    lat = 89.99999 if north else -89.99999
    for lon in (-179.9, -90.0, 0.0, 33.3, 179.9):
        cell = pgh.encode(lat, lon, precision)
        neighbors = pgh.get_neighbors(cell)
        assert len(neighbors) == 5
        assert neighbors == _oracle_neighbors(cell)
        assert len(pgh.get_neighbors(cell, include_self=True)) == 6


@pytest.mark.parametrize("west, east", ANTIMERIDIAN_PAIRS)
def test_get_neighbors_antimeridian_cells_have_eight_neighbors_across_the_seam(west, east):
    for cell, across in ((east, west), (west, east)):
        neighbors = pgh.get_neighbors(cell)
        assert len(neighbors) == 8
        assert across in neighbors


def test_get_neighbors_polar_antimeridian_corner():
    cell = pgh.encode(89.99999, 179.99999, 3)
    assert pgh.get_neighbors(cell) == _oracle_neighbors(cell)
    assert len(pgh.get_neighbors(cell)) == 5


def test_get_neighbors_precision_one_is_unique_and_sorted():
    for cell in pgh.geohash_from_int(0, 1), *"0123456789bcdefghjkmnpqrstuvwxyz":
        neighbors = pgh.get_neighbors(cell)
        assert neighbors == _oracle_neighbors(cell)
        assert neighbors == sorted(set(neighbors))


def test_get_neighbors_normalizes_case():
    assert pgh.get_neighbors("U4PRUYD", include_self=True) == pgh.get_neighbors("u4pruyd", include_self=True)
    assert "u4pruyd" in pgh.get_neighbors("U4PRUYD", include_self=True)


@pytest.mark.parametrize("geohash", INVALID_GEOHASHES)
def test_get_neighbors_rejects_invalid_geohash_like_get_adjacent(geohash):
    with pytest.raises(ValueError) as adjacent_error:
        pgh.get_adjacent(geohash, "top")
    with pytest.raises(ValueError) as neighbors_error:
        pgh.get_neighbors(geohash)
    assert str(neighbors_error.value) == str(adjacent_error.value)
