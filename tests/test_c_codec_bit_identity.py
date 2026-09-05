"""Bit-identity cross-checks for the C codec (phase 2 optimization).

The optimized C codec must produce bit-identical results to the pre-change
implementation. Two independent oracles guard that:

1. ``tests/fixtures/c_codec_bit_identity.json`` - a committed corpus of 1,178
   cases (encode strings, decoded values stored as ``float.hex()`` so bit
   patterns survive JSON, and full error paths) captured by running the
   pre-change implementation on a seeded random + edge-case protocol.
2. A pure-Python transcription of the pre-change algorithm (identical
   floating point operation order), compared bit-exactly against the live
   extension on freshly randomized inputs at test time.

The tests call the extension functions directly (not the package wrappers):
the wrappers add case normalization that is out of scope here and is covered
by the rest of the suite.
"""

import json
import random
from functools import partial
from pathlib import Path

import pytest

from pygeohash.cgeohash import geohash_module as cgm

BASE32 = "0123456789bcdefghjkmnpqrstuvwxyz"
DECODE_MAP = {ord(c): i for i, c in enumerate(BASE32)}

FIXTURE = Path(__file__).parent / "fixtures" / "c_codec_bit_identity.json"


def _ref_decode_exactly(geohash):
    """Bit-exact transcription of the pre-change decode_to_doubles loop."""
    data = geohash.encode("utf-8")
    if not 1 <= len(data) <= 12:
        raise ValueError("Geohash must be between 1 and 12 characters long")
    lat_interval = [-90.0, 90.0]
    lon_interval = [-180.0, 180.0]
    lat_err = 90.0
    lon_err = 180.0
    is_even = True
    for byte in data:
        cd = DECODE_MAP.get(byte, -1)
        if cd == -1:
            raise ValueError("Invalid character in geohash")
        for mask in (16, 8, 4, 2, 1):
            if is_even:  # longitude
                lon_err /= 2.0
                if cd & mask:
                    lon_interval[0] = (lon_interval[0] + lon_interval[1]) / 2.0
                else:
                    lon_interval[1] = (lon_interval[0] + lon_interval[1]) / 2.0
            else:  # latitude
                lat_err /= 2.0
                if cd & mask:
                    lat_interval[0] = (lat_interval[0] + lat_interval[1]) / 2.0
                else:
                    lat_interval[1] = (lat_interval[0] + lat_interval[1]) / 2.0
            is_even = not is_even
    return (
        (lat_interval[0] + lat_interval[1]) / 2.0,
        (lon_interval[0] + lon_interval[1]) / 2.0,
        lat_err,
        lon_err,
    )


def _ref_encode(latitude, longitude, precision):
    """Bit-exact transcription of the pre-change encode bisection loop."""
    if precision < 1 or precision > 12:
        raise ValueError("precision must be between 1 and 12")
    if latitude < -90.0:
        latitude = -90.0
    if latitude > 90.0:
        latitude = 90.0
    while longitude < -180.0:
        longitude += 360.0
    while longitude > 180.0:
        longitude -= 360.0
    lat_interval = [-90.0, 90.0]
    lon_interval = [-180.0, 180.0]
    bits = [16, 8, 4, 2, 1]
    bit = 0
    ch = 0
    is_even = True
    out = []
    hash_index = 0
    while hash_index < precision:
        if is_even:  # longitude
            mid = (lon_interval[0] + lon_interval[1]) / 2.0
            if longitude >= mid:
                ch |= bits[bit]
                lon_interval[0] = mid
            else:
                lon_interval[1] = mid
        else:  # latitude
            mid = (lat_interval[0] + lat_interval[1]) / 2.0
            if latitude >= mid:
                ch |= bits[bit]
                lat_interval[0] = mid
            else:
                lat_interval[1] = mid
        is_even = not is_even
        if bit < 4:
            bit += 1
        else:
            out.append(BASE32[ch])
            bit = 0
            ch = 0
            hash_index += 1
    return "".join(out)


def _coord(value):
    """Restore a fixture coordinate: hex float, or a non-float as-is."""
    if isinstance(value, str):
        # float.hex() renders NaN and the infinities without the 0x prefix;
        # those, and normal hex floats, round-trip through float.fromhex.
        stripped = value.lstrip("-+").lower()
        if stripped.startswith("0x") or stripped in ("nan", "inf"):
            return float.fromhex(value)
    return value


def _outcome(call):
    """Run call(); return ('ok', result) or ('err', TypeName, message)."""
    try:
        return ("ok", call())
    except Exception as exc:  # noqa: BLE001 - oracle must see every failure
        return ("err", type(exc).__name__, str(exc))


def test_fixture_replay_encode():
    """Replay every fixture encode case against the live extension."""
    for i, case in enumerate(_load_fixture()):
        if case["kind"] != "encode":
            continue
        lat = _coord(case["lat"])
        lon = _coord(case["lon"])
        args = (lat, lon)
        if case["precision"] is not None:
            args = args + (case["precision"],)
        actual = _outcome(partial(cgm.encode, *args))
        if "error" in case:
            expected = ("err", case["error"][0], case["error"][1])
        else:
            expected = ("ok", case["result"])
        assert actual == expected, f"encode fixture case {i}: {args!r}"


def test_fixture_replay_decode():
    """Replay every fixture decode case against the live extension."""
    for i, case in enumerate(_load_fixture()):
        if case["kind"] != "decode":
            continue
        geohash = case["geohash"]

        if "error" in case:
            expected = ("err", case["error"][0], case["error"][1])
            assert _outcome(partial(cgm.decode_exactly, geohash)) == expected, (
                f"decode_exactly fixture case {i}: {geohash!r}"
            )
            assert _outcome(partial(cgm.decode, geohash)) == expected, f"decode fixture case {i}: {geohash!r}"
            continue

        exact = cgm.decode_exactly(geohash)
        assert (
            exact.latitude.hex(),
            exact.longitude.hex(),
            exact.latitude_error.hex(),
            exact.longitude_error.hex(),
        ) == tuple(case["exactly"]), f"decode_exactly fixture case {i}: {geohash!r}"

        plain = cgm.decode(geohash)
        assert (plain.latitude.hex(), plain.longitude.hex()) == tuple(case["decode"]), (
            f"decode fixture case {i}: {geohash!r}"
        )


def test_randomized_encode_against_reference():
    """Freshly randomized encodes match the pre-change algorithm bit-exactly."""
    rng = random.Random(0xD40)  # noqa: S311 - seeded, not cryptographic
    for _ in range(300):
        lat = rng.uniform(-90.0, 90.0)
        lon = rng.uniform(-180.0, 180.0)
        precision = rng.randint(1, 12)
        assert cgm.encode(lat, lon, precision) == _ref_encode(lat, lon, precision), (
            lat,
            lon,
            precision,
        )


def test_randomized_decode_against_reference():
    """Freshly randomized decodes match the pre-change algorithm bit-exactly."""
    rng = random.Random(0xD41)  # noqa: S311 - seeded, not cryptographic
    for _ in range(300):
        lat = rng.uniform(-90.0, 90.0)
        lon = rng.uniform(-180.0, 180.0)
        precision = rng.randint(1, 12)
        geohash = cgm.encode(lat, lon, precision)
        lat_out, lon_out, lat_err, lon_err = _ref_decode_exactly(geohash)
        exact = cgm.decode_exactly(geohash)
        assert exact.latitude.hex() == lat_out.hex()
        assert exact.longitude.hex() == lon_out.hex()
        assert exact.latitude_error.hex() == lat_err.hex()
        assert exact.longitude_error.hex() == lon_err.hex()
        plain = cgm.decode(geohash)
        assert plain.latitude.hex() == lat_out.hex()
        assert plain.longitude.hex() == lon_out.hex()


def test_edge_cases_against_reference():
    """Poles, antimeridian, zero, and every precision match the reference."""
    points = [
        (0.0, 0.0),
        (-0.0, 0.0),
        (90.0, 180.0),
        (90.0, -180.0),
        (-90.0, 180.0),
        (-90.0, -180.0),
        (0.0, 180.0),
        (0.0, -180.0),
        (0.0, 179.9999999999999),
        (0.0, -179.9999999999999),
        (89.9999999999999, 0.0),
        (-89.9999999999999, 0.0),
        (45.0, -45.0),
        (5e-324, -5e-324),
    ]
    for lat, lon in points:
        for precision in range(1, 13):
            assert cgm.encode(lat, lon, precision) == _ref_encode(lat, lon, precision), (lat, lon, precision)


def test_error_paths():
    """Direct-call error paths: same types, same messages, same precedence."""
    nan = float("nan")
    inf = float("inf")
    encode_errors = [
        ((True, 0.0, 12), ValueError, "latitude and longitude must be numbers, not booleans"),
        ((0.0, False, 12), ValueError, "latitude and longitude must be numbers, not booleans"),
        ((0.0, 0.0, True), ValueError, "precision must be an integer, not a boolean"),
        ((nan, 0.0, 12), ValueError, "latitude and longitude must be finite"),
        ((0.0, inf, 12), ValueError, "latitude and longitude must be finite"),
        ((0.0, 0.0, 0), ValueError, "precision must be between 1 and 12"),
        ((0.0, 0.0, 13), ValueError, "precision must be between 1 and 12"),
        ((0.0, 0.0, -1), ValueError, "precision must be between 1 and 12"),
        (("x", 0.0, 12), TypeError, "must be real number, not str"),
        ((0.0, 0.0, 6.5), TypeError, "'float' object cannot be interpreted as an integer"),
    ]
    for args, exc_type, message in encode_errors:
        with pytest.raises(exc_type, match=message.replace("(", "\\(").replace(")", "\\)")):
            cgm.encode(*args)
        with pytest.raises(exc_type, match=message.replace("(", "\\(").replace(")", "\\)")):
            cgm.encode_strictly(*args)

    with pytest.raises(ValueError, match="Geohash must be between 1 and 12 characters long"):
        cgm.decode("")
    with pytest.raises(ValueError, match="Geohash must be between 1 and 12 characters long"):
        cgm.decode("ezs42e44yx96z")
    with pytest.raises(ValueError, match="Invalid character in geohash"):
        cgm.decode("EZS42")  # direct call: no case normalization below the wrappers
    with pytest.raises(ValueError, match="Invalid character in geohash"):
        cgm.decode("ezs42e44yx9a")


def _load_fixture():
    with FIXTURE.open() as fh:
        return json.load(fh)
