"""Wrapper parity coverage for the codec fast paths.

The encode wrappers take a fast path for canonical inputs -- exact-type in-range
float coordinates with an in-range int precision -- and fall through to the
original validation for everything else; the decode wrappers are unchanged and
keep their case-insensitive handling. These tests pin identical results and
identical errors for every input class on both wrappers, including the Unicode
cases that make any change to .lower() handling unsound.
"""

import pytest
import pygeohash as pgh
from pygeohash.cgeohash import geohash_module as gm

P12 = "ezs42e44yx96"

# Geohashes of every length 1-12 (nested prefixes of the pinned p12 hash).
LENGTH_SUFFIXES = [P12[:length] for length in range(1, 13)]


class _FloatSub(float):
    """A float subclass: must still encode correctly via the slow path."""


class _IntSub(int):
    """An int subclass (bool's sibling): must still be accepted as precision."""


class _StrSub(str):
    """A str subclass: must still decode correctly via either path."""


def test_encode_fast_path_delegates_to_c_codec():
    """Canonical float/int inputs produce exactly what the C codec produces."""
    coordinates = [
        (42.6, -5.6),
        (0.0, 0.0),
        (-90.0, -180.0),
        (90.0, 180.0),
        (-33.8688, 151.2093),
    ]
    for latitude, longitude in coordinates:
        for precision in (1, 5, 12):
            assert pgh.encode(latitude, longitude, precision) == gm.encode(latitude, longitude, precision)
    # The no-precision default (12) takes the same path.
    assert pgh.encode(42.6, -5.6) == gm.encode(42.6, -5.6, 12)


def test_encode_strictly_fast_path_delegates_to_c_codec():
    """encode_strictly's fast path returns exactly what its C codec returns."""
    assert pgh.encode_strictly(42.6, -5.6) == gm.encode_strictly(42.6, -5.6, 12)
    assert pgh.encode_strictly(42.6, -5.6, 5) == gm.encode_strictly(42.6, -5.6, 5)


@pytest.mark.parametrize(
    "slot,value",
    [
        pytest.param("latitude", _FloatSub(42.6), id="float-subclass-latitude"),
        pytest.param("longitude", _FloatSub(-5.6), id="float-subclass-longitude"),
    ],
)
def test_encode_float_subclass_still_encodes(slot, value):
    """Float subclasses are not exact floats; they must still encode (slow path)."""
    latitude, longitude = 42.6, -5.6
    if slot == "latitude":
        latitude = value
    else:
        longitude = value
    assert pgh.encode(latitude, longitude, 5) == "ezs42"


def test_encode_int_subclass_precision_still_accepted():
    """An int subclass precision is not an exact int; it must still be accepted."""
    assert pgh.encode(42.6, -5.6, _IntSub(5)) == "ezs42"


@pytest.mark.parametrize("encoder", [pgh.encode, pgh.encode_strictly])
@pytest.mark.parametrize(
    "latitude,longitude,message",
    [
        (float("nan"), 0.0, "Latitude must be between -90.0 and 90.0 degrees"),
        (float("inf"), 0.0, "Latitude must be between -90.0 and 90.0 degrees"),
        (float("-inf"), 0.0, "Latitude must be between -90.0 and 90.0 degrees"),
        (0.0, float("nan"), "Longitude must be between -180.0 and 180.0 degrees"),
        (0.0, float("inf"), "Longitude must be between -180.0 and 180.0 degrees"),
        (0.0, float("-inf"), "Longitude must be between -180.0 and 180.0 degrees"),
    ],
)
def test_encode_rejects_non_finite_coordinates_with_wrapper_message(encoder, latitude, longitude, message):
    """Non-finite coordinates fail the wrapper's range check with its own message.

    The C layer has a separate "must be finite" error for direct calls; the
    public wrappers must keep raising their range ValueError, which the fast
    path's bound checks make deterministic.
    """
    with pytest.raises(ValueError, match=message):
        encoder(latitude, longitude)


def test_decode_fast_path_matches_lowercased_codec_call():
    """Every canonical length decodes identically with .lower() skipped."""
    for geohash in LENGTH_SUFFIXES:
        assert pgh.decode(geohash) == gm.decode(geohash)
        exact = pgh.decode_exactly(geohash)
        native = gm.decode_exactly(geohash)
        assert exact == native


@pytest.mark.parametrize(
    "variant",
    ["U4PRUYDQQVJ8", "u4PRUYDQQVJ8", "U4pruydqqvj8", "u4PrUyDqQvJ8", "EZS42", "eZs42", "EZS42E44YX96"],
)
def test_decode_case_variants_match_lowercase(variant):
    """Uppercase and mixed-case input decodes exactly like the lowercase form."""
    assert pgh.decode(variant) == pgh.decode(variant.lower())
    assert pgh.decode_exactly(variant) == pgh.decode_exactly(variant.lower())


def test_decode_kelvin_sign_normalizes_like_lower():
    """The Kelvin sign lowercases INTO the base32 alphabet (U+212A -> 'k').

    It is cased-uppercase, so it must not take the verbatim fast path: skipping
    .lower() for it would turn a successful decode into a spurious error.
    """
    assert pgh.decode("\u212a4pruyd") == pgh.decode("k4pruyd")
    assert pgh.decode_exactly("\u212a4pruyd") == pgh.decode_exactly("k4pruyd")


def test_decode_turkish_dotted_i_rejected_like_lower():
    """U+0130 lowercases to two characters ('i' + combining dot) and stays invalid.

    The length-changing lowercase mapping must still land on the same
    "Invalid character in geohash" error the original path raised.
    """
    with pytest.raises(ValueError, match="Invalid character in geohash"):
        pgh.decode("\u0130")
    with pytest.raises(ValueError, match="Invalid character in geohash"):
        pgh.decode_exactly("\u0130")


@pytest.mark.parametrize("bad", ["café", "日本語", "ezs42°", "ezs42\x80", "ñ"])
def test_decode_unicode_fixpoints_and_uncased_rejected(bad):
    """Non-ASCII input is rejected with the same error on either path."""
    with pytest.raises(ValueError, match="Invalid character in geohash"):
        pgh.decode(bad)
    with pytest.raises(ValueError, match="Invalid character in geohash"):
        pgh.decode_exactly(bad)


@pytest.mark.parametrize("decoder", [pgh.decode, pgh.decode_exactly])
def test_decode_str_subclass(decoder):
    """A str subclass decodes through either path to the same result."""
    assert decoder(_StrSub("u4pruyd")) == decoder("u4pruyd")
    assert decoder(_StrSub("U4PRUYD")) == decoder("u4pruyd")


@pytest.mark.parametrize("decoder", [pgh.decode, pgh.decode_exactly])
def test_decode_invalid_type_error_preserved(decoder):
    """Non-string input still raises the wrapper's own message, not a TypeError."""
    with pytest.raises(ValueError, match="Geohash must be a string"):
        decoder(123)
    with pytest.raises(ValueError, match="Geohash must be a string"):
        decoder(None)


@pytest.mark.parametrize("decoder", [pgh.decode, pgh.decode_exactly])
def test_decode_empty_and_overlong_errors_preserved(decoder):
    """Empty and over-precision strings keep their wrapper-level errors."""
    with pytest.raises(ValueError, match="Geohash cannot be empty"):
        decoder("")
    with pytest.raises(ValueError, match="Geohash must be at most 12 characters long"):
        decoder("u" * 13)


@pytest.mark.parametrize("decoder", [pgh.decode, pgh.decode_exactly])
def test_decode_invalid_lowercase_char_error_preserved(decoder):
    """Lowercase out-of-alphabet input still raises the codec's character error."""
    with pytest.raises(ValueError, match="Invalid character in geohash"):
        decoder("ezs42a")
    with pytest.raises(ValueError, match="Invalid character in geohash"):
        decoder("u4pruydqqvja")
