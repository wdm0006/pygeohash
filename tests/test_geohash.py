import pytest
import pygeohash as pgh
from pygeohash.cgeohash import geohash_module

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


def test_encode_invalid_latitude():
    """Test encode with invalid latitude values."""
    with pytest.raises(ValueError, match="Latitude must be between -90.0 and 90.0 degrees"):
        pgh.encode(91.0, 0.0)
    with pytest.raises(ValueError, match="Latitude must be between -90.0 and 90.0 degrees"):
        pgh.encode(-91.0, 0.0)
    with pytest.raises(ValueError, match="Latitude must be between -90.0 and 90.0 degrees"):
        pgh.encode(999.0, 0.0)


def test_encode_invalid_longitude():
    """Test encode with invalid longitude values."""
    with pytest.raises(ValueError, match="Longitude must be between -180.0 and 180.0 degrees"):
        pgh.encode(0.0, 181.0)
    with pytest.raises(ValueError, match="Longitude must be between -180.0 and 180.0 degrees"):
        pgh.encode(0.0, -181.0)
    with pytest.raises(ValueError, match="Longitude must be between -180.0 and 180.0 degrees"):
        pgh.encode(0.0, 999.0)


@pytest.mark.parametrize("encoder", [pgh.encode, pgh.encode_strictly])
@pytest.mark.parametrize("value", [True, False])
def test_encode_rejects_boolean_latitude(encoder, value):
    """A bool must not be encoded as latitude 1.0/0.0 just because bool subclasses int."""
    with pytest.raises(ValueError, match="Latitude must be a number"):
        encoder(value, 0.0)


@pytest.mark.parametrize("encoder", [pgh.encode, pgh.encode_strictly])
@pytest.mark.parametrize("value", [True, False])
def test_encode_rejects_boolean_longitude(encoder, value):
    """A bool must not be encoded as longitude 1.0/0.0 just because bool subclasses int."""
    with pytest.raises(ValueError, match="Longitude must be a number"):
        encoder(0.0, value)


@pytest.mark.parametrize("encoder", [pgh.encode, pgh.encode_strictly])
@pytest.mark.parametrize("value", [True, False])
def test_encode_rejects_boolean_precision(encoder, value):
    """A bool precision must raise instead of silently meaning precision 1 (or 0)."""
    with pytest.raises(ValueError, match="Precision must be an integer"):
        encoder(42.6, -5.6, precision=value)


@pytest.mark.parametrize("encoder", [pgh.encode, pgh.encode_strictly])
def test_encode_accepts_integer_coordinates_and_precision(encoder):
    """Rejecting bools must not disturb ordinary int coordinates or precisions."""
    assert encoder(42, -5, 5) == encoder(42.0, -5.0, 5) == "ezkqy"
    assert encoder(0, 0, 1) == "s"


def test_encode_strictly():
    assert pgh.encode(0.0, -5.6, precision=5) == "ebh00"
    assert pgh.encode_strictly(0.0, -5.6, precision=5) == "ebh00"


def test_encode_strictly_matches_encode():
    """encode_strictly currently behaves identically to encode.

    Pin that equivalence across a representative set of coordinates and
    precisions so any future divergence is intentional and caught here.
    """
    coordinates = [
        (42.6, -5.6),
        (0.0, -5.6),
        (0.0, 0.0),
        (-90.0, -180.0),
        (90.0, 180.0),
        (37.7749, -122.4194),
        (-33.8688, 151.2093),
        (51.5074, -0.1278),
    ]
    for lat, lon in coordinates:
        for precision in range(1, 13):
            assert pgh.encode_strictly(lat, lon, precision) == pgh.encode(lat, lon, precision)


def test_encode_strictly_invalid_precision_type():
    """Test encode_strictly with invalid precision type."""
    with pytest.raises(ValueError, match="Precision must be an integer"):
        pgh.encode_strictly(42.6, -5.6, precision=5.5)


def test_encode_strictly_invalid_precision_range():
    """Test encode_strictly with precision outside the valid range (1-12)."""
    with pytest.raises(ValueError, match="Precision must be between 1 and 12"):
        pgh.encode_strictly(42.6, -5.6, precision=13)


def test_c_encode_validates_precision_directly():
    """The C extension functions must bounds-check precision themselves.

    The public Python wrappers validate precision, but the C module is
    directly importable and writes into a fixed 13-byte stack buffer. An
    out-of-range precision (e.g. 13 or 50) would overflow that buffer, so the
    C layer must reject it with a ValueError before encoding.
    """
    from pygeohash.cgeohash.geohash_module import encode as c_encode, encode_strictly as c_encode_strictly

    for c_func in (c_encode, c_encode_strictly):
        for bad_precision in (0, 13, 50, -1):
            with pytest.raises(ValueError, match="precision must be between 1 and 12"):
                c_func(0.0, 0.0, bad_precision)
        # Valid precisions still encode correctly through the C layer.
        assert c_func(42.6, -5.6, 5) == "ezs42"
        assert c_func(42.6, -5.6, 12) == "ezs42e44yx96"


def test_c_encode_rejects_non_finite_coordinates():
    from pygeohash.cgeohash.geohash_module import encode as c_encode, encode_strictly as c_encode_strictly

    for c_func in (c_encode, c_encode_strictly):
        for latitude, longitude in (
            (float("inf"), 0.0),
            (float("-inf"), 0.0),
            (float("nan"), 0.0),
            (0.0, float("inf")),
            (0.0, float("-inf")),
            (0.0, float("nan")),
        ):
            with pytest.raises(ValueError, match="latitude and longitude must be finite"):
                c_func(latitude, longitude)


def test_c_encode_rejects_boolean_coordinates():
    """bool is a subclass of int, so the C encoders must reject it explicitly.

    Without an explicit guard the "d" format unit coerces True/False to
    1.0/0.0 before any validation runs, so a direct extension call would encode
    a boolean as a coordinate while the package-root wrappers raise.
    """
    from pygeohash.cgeohash.geohash_module import encode as c_encode, encode_strictly as c_encode_strictly

    for c_func in (c_encode, c_encode_strictly):
        for latitude, longitude in (
            (True, 0.0),
            (False, 0.0),
            (0.0, True),
            (0.0, False),
            (True, True),
        ):
            with pytest.raises(ValueError, match="latitude and longitude must be numbers, not booleans"):
                c_func(latitude, longitude, 5)


def test_c_encode_rejects_boolean_precision():
    from pygeohash.cgeohash.geohash_module import encode as c_encode, encode_strictly as c_encode_strictly

    for c_func in (c_encode, c_encode_strictly):
        for bad_precision in (True, False):
            with pytest.raises(ValueError, match="precision must be an integer, not a boolean"):
                c_func(0.0, 0.0, bad_precision)
            with pytest.raises(ValueError, match="precision must be an integer, not a boolean"):
                c_func(0.0, 0.0, precision=bad_precision)


def test_c_encode_accepts_ordinary_numeric_arguments():
    """The boolean guards must not disturb plain int/float arguments."""
    from pygeohash.cgeohash.geohash_module import encode as c_encode, encode_strictly as c_encode_strictly

    for c_func in (c_encode, c_encode_strictly):
        assert c_func(42.6, -5.6, 5) == "ezs42"
        assert c_func(42.6, -5.6) == "ezs42e44yx96"
        assert c_func(42, -5, 5) == "ezkqy"
        assert c_func(0.0, 0.0, 1) == "s"
        assert c_func(latitude=42.6, longitude=-5.6, precision=12) == "ezs42e44yx96"


def test_c_encode_preserves_finite_coordinate_normalization():
    from pygeohash.cgeohash.geohash_module import encode as c_encode, encode_strictly as c_encode_strictly

    for c_func in (c_encode, c_encode_strictly):
        assert c_func(91.0, 0.0, 5) == c_func(90.0, 0.0, 5)
        assert c_func(-91.0, 0.0, 5) == c_func(-90.0, 0.0, 5)
        assert c_func(0.0, 181.0, 5) == c_func(0.0, -179.0, 5)
        assert c_func(0.0, -181.0, 5) == c_func(0.0, 179.0, 5)


def test_encode_strictly_invalid_latitude():
    """Test encode_strictly with invalid latitude values."""
    with pytest.raises(ValueError, match="Latitude must be between -90.0 and 90.0 degrees"):
        pgh.encode_strictly(91.0, 0.0)
    with pytest.raises(ValueError, match="Latitude must be between -90.0 and 90.0 degrees"):
        pgh.encode_strictly(-91.0, 0.0)


def test_encode_strictly_invalid_longitude():
    """Test encode_strictly with invalid longitude values."""
    with pytest.raises(ValueError, match="Longitude must be between -180.0 and 180.0 degrees"):
        pgh.encode_strictly(0.0, 181.0)
    with pytest.raises(ValueError, match="Longitude must be between -180.0 and 180.0 degrees"):
        pgh.encode_strictly(0.0, -181.0)


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


def test_decode_non_ascii():
    """Non-ASCII input must be rejected cleanly, not read out of bounds.

    The C decoder indexes a 128-entry table by character; bytes >= 128 (such as
    multibyte UTF-8) must be treated as invalid rather than indexing past it.
    """
    for bad in ["café", "ñ", "ezs42°", "日本語", "ezs42\x80"]:
        with pytest.raises(ValueError, match="Invalid character in geohash"):
            pgh.decode(bad)
        with pytest.raises(ValueError, match="Invalid character in geohash"):
            pgh.decode_exactly(bad)


def test_decode_return_types():
    """decode/decode_exactly return the documented named tuples with named fields."""
    from pygeohash.geohash_types import ExactLatLong, LatLong

    latlong = pgh.decode("ezs42")
    assert isinstance(latlong, LatLong)
    assert latlong == (latlong.latitude, latlong.longitude)

    exact = pgh.decode_exactly("ezs42")
    assert isinstance(exact, ExactLatLong)
    assert exact.latitude_error > 0 and exact.longitude_error > 0


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


DECODE_APIS = [
    pytest.param(pgh.decode, id="public-decode"),
    pytest.param(pgh.decode_exactly, id="public-decode-exactly"),
    pytest.param(geohash_module.decode, id="native-decode"),
    pytest.param(geohash_module.decode_exactly, id="native-decode-exactly"),
]
EXACT_DECODERS = (pgh.decode_exactly, geohash_module.decode_exactly)
BOUNDARY_DECODE_RESULTS = {
    "u": ((67.5, 22.5), (67.5, 22.5, 22.5, 22.5)),
    "u4pruydqqvj8": (
        (57.64911004342139, 10.407439861446619),
        (57.64911004342139, 10.407439861446619, 8.381903171539307e-08, 1.6763806343078613e-07),
    ),
}


@pytest.mark.parametrize("decoder", DECODE_APIS)
@pytest.mark.parametrize(
    "geohash", [pytest.param("u" * 13, id="length-13"), pytest.param("u" * 1000, id="length-1000")]
)
def test_decode_rejects_over_precision_geohashes(decoder, geohash):
    """Both public and native decode boundaries reject non-canonical lengths."""
    with pytest.raises(ValueError, match="at most 12|between 1 and 12"):
        decoder(geohash)


@pytest.mark.parametrize(
    "decoder,native_name",
    [(pgh.decode, "c_decode"), (pgh.decode_exactly, "c_decode_exactly")],
)
def test_public_decode_rejects_over_precision_before_native_delegation(monkeypatch, decoder, native_name):
    """The public boundary validates length without relying on the native layer."""
    monkeypatch.setattr(f"pygeohash.geohash.{native_name}", lambda _geohash: pytest.fail("native decoder called"))

    with pytest.raises(ValueError, match="at most 12"):
        decoder("u" * 13)


@pytest.mark.parametrize("decoder", DECODE_APIS)
@pytest.mark.parametrize("geohash", ["u", "u4pruydqqvj8"])
def test_decode_accepts_boundary_lengths(decoder, geohash):
    """Canonical minimum and maximum precision geohashes remain decodable."""
    expected = BOUNDARY_DECODE_RESULTS[geohash][decoder in EXACT_DECODERS]
    assert decoder(geohash) == expected


@pytest.mark.parametrize("decoder", [geohash_module.decode, geohash_module.decode_exactly])
def test_native_decode_rejects_empty_and_invalid_geohashes(decoder):
    """The native boundary enforces minimum length and retains character validation."""
    with pytest.raises(ValueError, match="between 1 and 12"):
        decoder("")
    with pytest.raises(ValueError, match="Invalid character in geohash"):
        decoder("ezs42a")


CASE_VARIANTS = ["U4PRUYD", "U4pruYd", "u4PRUYd"]


@pytest.mark.parametrize("variant", CASE_VARIANTS)
def test_decode_is_case_insensitive(variant):
    """Uppercase and mixed-case input decodes exactly like the lowercase form."""
    assert pgh.decode(variant) == pgh.decode("u4pruyd")
    assert pgh.decode_exactly(variant) == pgh.decode_exactly("u4pruyd")


def test_validate_then_decode():
    """The validate-then-use contract holds: what assert_valid_geohash accepts, decode decodes."""
    validated = pgh.assert_valid_geohash("U4PRUYD")
    assert pgh.decode(validated) == pgh.decode("u4pruyd")


@pytest.mark.parametrize("variant", CASE_VARIANTS)
def test_downstream_consumers_accept_uppercase(variant):
    """Consumers routed through decode/decode_exactly accept uppercase too."""
    assert pgh.get_bounding_box(variant) == pgh.get_bounding_box("u4pruyd")

    center = pgh.decode("u4pruyd")
    assert pgh.is_point_in_geohash(center.latitude, center.longitude, variant) is True

    assert pgh.geohash_haversine_distance(variant, "u4pruyf") == pgh.geohash_haversine_distance("u4pruyd", "u4pruyf")

    uppercase_collection = [variant, "EZS42"]
    lowercase_collection = ["u4pruyd", "ezs42"]
    assert pgh.mean(uppercase_collection) == pgh.mean(lowercase_collection)
    assert pgh.variance(uppercase_collection) == pgh.variance(lowercase_collection)
    assert pgh.std(uppercase_collection) == pgh.std(lowercase_collection)
    # northern/eastern return the selected input verbatim, so the uppercase form comes back as-is.
    assert pgh.northern(uppercase_collection) == variant
    assert pgh.eastern(uppercase_collection) == variant


@pytest.mark.parametrize("bad", ["a1i", "A1I", "ezs42a", "EZS42A", "ezs!2", "EZS!2"])
def test_decode_rejects_out_of_alphabet_in_either_case(bad):
    """Case normalization does not widen the alphabet: 'a', 'i', 'l', 'o' and punctuation still raise."""
    with pytest.raises(ValueError, match="Invalid character in geohash"):
        pgh.decode(bad)
    with pytest.raises(ValueError, match="Invalid character in geohash"):
        pgh.decode_exactly(bad)


def test_check_validity():
    with pytest.raises(ValueError):
        pgh.geohash_approximate_distance("shibu", "shiba", check_validity=True)


def test_approximate_distance_checks_identical_invalid_geohashes():
    with pytest.raises(ValueError):
        pgh.geohash_approximate_distance("invalid", "invalid", check_validity=True)


@pytest.mark.parametrize("geohash", ["", "u4pruydqqvjkc"])
def test_approximate_distance_rejects_invalid_length(geohash):
    with pytest.raises(ValueError):
        pgh.geohash_approximate_distance(geohash, "u4pruyd", check_validity=True)


@pytest.mark.parametrize(
    "geohash_1, geohash_2",
    [
        ("U4PRUYD", "U4PRUYF"),
        ("u4PRuyD", "U4pRUyf"),
    ],
)
def test_approximate_distance_normalizes_validated_geohashes(geohash_1, geohash_2):
    expected = pgh.geohash_approximate_distance(geohash_1.lower(), geohash_2.lower(), check_validity=True)
    assert pgh.geohash_approximate_distance(geohash_1, geohash_2, check_validity=True) == expected


def test_approximate_distance_skips_validation_by_default(monkeypatch):
    def fail_validation(_geohash):
        raise AssertionError("validation should not run")

    monkeypatch.setattr("pygeohash.distances.is_valid_geohash", fail_validation)
    assert pgh.geohash_approximate_distance("", "") == 0.0
    assert pgh.geohash_approximate_distance("u4pruydqqvjkc", "u4pruydqqvjkd") == 0.6


@pytest.mark.parametrize("geohash", ["s", "u4pruydqqvjk"])
def test_approximate_distance_is_zero_for_identical_geohashes(geohash):
    assert pgh.geohash_approximate_distance(geohash, geohash) == 0.0


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


def test_cardinal_extremes_return_input_geohashes():
    geohashes = ["u4pruyd", "u4pruyf", "u4pruyc"]

    assert pgh.northern(geohashes) == "u4pruyf"
    assert pgh.southern(geohashes) == "u4pruyd"
    assert pgh.eastern(geohashes) == "u4pruyd"
    assert pgh.western(geohashes) == "u4pruyc"


def test_cardinal_extremes_return_members_of_mixed_precision_collection():
    geohashes = ["u", "g", "s000"]

    for cardinal_extreme in (pgh.northern, pgh.southern, pgh.eastern, pgh.western):
        assert cardinal_extreme(geohashes) in geohashes


def test_cardinal_extreme_tie_returns_first_geohash():
    geohashes = ["u4pruyd", "u4pruyf", "u4pruyc"]

    assert pgh.eastern(geohashes) == geohashes[0]
