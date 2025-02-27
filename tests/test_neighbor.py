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
