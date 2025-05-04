import pytest
import pygeohash as pgh

__author__ = "willmcginnis"


def test_encode():
    assert pgh.encode(42.6, -5.6) == "ezs42e44yx96"
    assert pgh.encode(42.6, -5.6, precision=5) == "ezs42"
    assert pgh.encode(0.0, -5.6, precision=5) == "ebh00"


def test_encode_invalid_precision_type():
    """Test encode with invalid precision type."""
    with pytest.raises(ValueError, match="Precision must be an integer"):
        pgh.encode(42.6, -5.6, precision=5.5)
    with pytest.raises(ValueError, match="Precision must be an integer"):
        pgh.encode(42.6, -5.6, precision="5")


def test_encode_invalid_precision_range():
    """Test encode with precision outside the valid range (1-12)."""
    with pytest.raises(ValueError, match="Precision must be between 1 and 12"):
        pgh.encode(42.6, -5.6, precision=0)
    with pytest.raises(ValueError, match="Precision must be between 1 and 12"):
        pgh.encode(42.6, -5.6, precision=13)


def test_encode_valid_precision():
    """Test encode with valid precision values."""
    assert pgh.encode(42.6, -5.6, precision=1) == "e"
    assert pgh.encode(42.6, -5.6, precision=12) == "ezs42e44yx96"


def test_encode_strictly():
    assert pgh.encode(0.0, -5.6, precision=5) == "ebh00"
    assert pgh.encode_strictly(0.0, -5.6, precision=5) == "ebh00"


def test_encode_strictly_invalid_precision_type():
    """Test encode_strictly with invalid precision type."""
    with pytest.raises(ValueError, match="Precision must be an integer"):
        pgh.encode_strictly(42.6, -5.6, precision=5.5)


def test_encode_strictly_invalid_precision_range():
    """Test encode_strictly with precision outside the valid range (1-12)."""
    with pytest.raises(ValueError, match="Precision must be between 1 and 12"):
        pgh.encode_strictly(42.6, -5.6, precision=13)


def test_decode():
    decoded = pgh.decode("ezs42")
    assert pytest.approx(decoded.latitude, abs=0.1) == 42.6
    assert pytest.approx(decoded.longitude, abs=0.1) == -5.6


def test_decode_invalid_type():
    """Test decode with invalid input type."""
    with pytest.raises(ValueError, match="Geohash must be a string"):
        pgh.decode(123)
    with pytest.raises(ValueError, match="Geohash must be a string"):
        pgh.decode(None)


def test_decode_empty():
    """Test decode with empty string."""
    with pytest.raises(ValueError, match="Geohash cannot be empty"):
        pgh.decode("")


def test_decode_invalid_chars():
    """Test decode with invalid characters."""
    with pytest.raises(ValueError, match="Invalid character in geohash"):
        pgh.decode("ezs42a")  # 'a' is invalid
    with pytest.raises(ValueError, match="Invalid character in geohash"):
        pgh.decode("ezs!2")  # '!' is invalid


def test_decode_exactly_invalid_type():
    """Test decode_exactly with invalid input type."""
    with pytest.raises(ValueError, match="Geohash must be a string"):
        pgh.decode_exactly(123)


def test_decode_exactly_empty():
    """Test decode_exactly with empty string."""
    with pytest.raises(ValueError, match="Geohash cannot be empty"):
        pgh.decode_exactly("")


def test_decode_exactly_invalid_chars():
    """Test decode_exactly with invalid characters."""
    with pytest.raises(ValueError, match="Invalid character in geohash"):
        pgh.decode_exactly("ezs42a")  # 'a' is invalid


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
    assert pytest.approx(pgh.geohash_haversine_distance("testxyz", "testwxy"), abs=1e-4) == 5888.614420771857


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
