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
