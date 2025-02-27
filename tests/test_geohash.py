import pytest
import pygeohash as pgh

__author__ = "willmcginnis"


def test_encode():
    assert pgh.encode(42.6, -5.6) == "ezs42e44yx96"
    assert pgh.encode(42.6, -5.6, precision=5) == "ezs42"
    assert pgh.encode(0.0, -5.6, precision=5) == "ebh00"


def test_encode_strictly():
    assert pgh.encode(0.0, -5.6, precision=5) == "ebh00"
    assert pgh.encode_strictly(0.0, -5.6, precision=5) == "ebh00"


def test_decode():
    assert pgh.decode("ezs42") == pgh.LatLong(42.6, -5.6)


def test_check_validity():
    with pytest.raises(ValueError):
        pgh.geohash_approximate_distance("shibu", "shiba", check_validity=True)


def test_distance():
    # test the fast geohash distance approximations
    assert pgh.geohash_approximate_distance("bcd3u", "bc83n") == 625441
    assert pgh.geohash_approximate_distance("bcd3uasd", "bcd3n") == 19545
    assert pgh.geohash_approximate_distance("bcd3u", "bcd3uasd") == 3803
    assert pgh.geohash_approximate_distance("bcd3ua", "bcd3uasdub") == 610

    # test the haversine great circle distance calculations
    assert pytest.approx(
        pgh.geohash_haversine_distance("testxyz", "testwxy"),
        abs=1e-4
    ) == 5888.614420771857


def test_stats():
    coordinates = [
        pgh.LatLong(50, 0),
        pgh.LatLong(-50, 0),
        pgh.LatLong(0, -50),
        pgh.LatLong(0, 50),
    ]
    coordinates = [pgh.encode(*coordinate) for coordinate in coordinates]

    # mean
    mean = pgh.mean(coordinates)
    assert mean == "s00000000000"

    # north
    north = pgh.northern(coordinates)
    assert north == "u0bh2n0p0581"

    # south
    south = pgh.southern(coordinates)
    assert south == "hp0581b0bh2n"

    # east
    east = pgh.eastern(coordinates)
    assert east == "t0581b0bh2n0"

    # west
    west = pgh.western(coordinates)
    assert west == "dbh2n0p0581b"

    var = pgh.variance(coordinates)
    assert pytest.approx(var, abs=0.01) == 30910779169327.953

    std = pgh.std(coordinates)
    assert pytest.approx(std, abs=1e-4) == 5559746.322389894
