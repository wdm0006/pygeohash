"""Geohash encoding and decoding functionality.

This module provides the core functionality for encoding coordinates to geohashes
and decoding geohashes back to coordinates. It includes both standard and exact
decoding options, as well as strict encoding.

This implementation uses a high-performance C extension for all operations.
"""

from __future__ import annotations

from typing import Dict, Iterable

from pygeohash.cgeohash.geohash_module import (
    decode as c_decode,
    decode_exactly as c_decode_exactly,
    decode_many as c_decode_many,
    encode as c_encode,
    encode_many as c_encode_many,
    encode_strictly as c_encode_strictly,
    get_base32,
)
from pygeohash.geohash_types import ExactLatLong, LatLong, GeohashPrecision
from pygeohash.logging import get_logger

logger = get_logger(__name__)

__base32 = get_base32()
__decodemap: Dict[str, int] = {base32_char: i for i, base32_char in enumerate(__base32)}

# Define the valid range for precision
MIN_PRECISION = 1
MAX_PRECISION = 12


def encode(latitude: float, longitude: float, precision: GeohashPrecision = 12) -> str:
    """Encode a latitude and longitude into a geohash.

    Args:
        latitude (float): The latitude to encode.
        longitude (float): The longitude to encode.
        precision (GeohashPrecision, optional): The number of characters in the geohash.
            Defaults to 12. Must be between 1 and 12, inclusive.

    Returns:
        str: The geohash string.

    Raises:
        ValueError: If the latitude or longitude values are invalid, or if the precision
            is not an integer or is outside the valid range (1-12). Booleans are
            rejected for all three arguments, even though ``bool`` is a subclass of
            ``int``.
    """
    # Fast path: the common case (exact-type floats in range, an in-range int
    # precision) goes straight to the C codec. The ``type(x) is ...`` identity
    # checks are cheaper than isinstance and naturally reject bool (type(True) is
    # bool, not int); NaN/inf fail the range comparisons. Anything else (ints,
    # bools, numeric subclasses, non-finite, out-of-range values) falls through
    # to the full validation below, which raises exactly the same errors as
    # before, in the same order.
    if (
        type(latitude) is float
        and type(longitude) is float
        and -90.0 <= latitude <= 90.0
        and -180.0 <= longitude <= 180.0
        and type(precision) is int
        and MIN_PRECISION <= precision <= MAX_PRECISION
    ):
        return c_encode(latitude, longitude, precision)

    # bool is a subclass of int, so it has to be rejected explicitly.
    if isinstance(precision, bool) or not isinstance(precision, int):
        raise ValueError(f"Precision must be an integer, but got {type(precision).__name__}.")
    if not (MIN_PRECISION <= precision <= MAX_PRECISION):
        raise ValueError(f"Precision must be between {MIN_PRECISION} and {MAX_PRECISION}, but got {precision}.")

    if isinstance(latitude, bool):
        raise ValueError(f"Latitude must be a number, but got {type(latitude).__name__}.")
    if isinstance(longitude, bool):
        raise ValueError(f"Longitude must be a number, but got {type(longitude).__name__}.")

    # Validate latitude range
    if not (-90.0 <= latitude <= 90.0):
        raise ValueError(f"Latitude must be between -90.0 and 90.0 degrees, but got {latitude}.")

    # Validate longitude range
    if not (-180.0 <= longitude <= 180.0):
        raise ValueError(f"Longitude must be between -180.0 and 180.0 degrees, but got {longitude}.")

    return c_encode(latitude, longitude, precision)


def encode_strictly(latitude: float, longitude: float, precision: GeohashPrecision = 12) -> str:
    """Encode a latitude and longitude into a geohash.

    This function currently behaves identically to :func:`encode`: it applies the
    same precision/latitude/longitude validation and returns the same geohash for
    every input. It is retained as a separate name for API/back-compatibility (and
    additionally logs an error if the underlying C encoder raises). Despite its
    name, it does not perform any extra validation or use different midpoint
    handling than :func:`encode`.

    Args:
        latitude (float): The latitude to encode.
        longitude (float): The longitude to encode.
        precision (GeohashPrecision, optional): The number of characters in the geohash.
            Defaults to 12. Must be between 1 and 12, inclusive.

    Returns:
        str: The geohash string.

    Raises:
        ValueError: If the latitude or longitude values are invalid, or if the precision
            is not an integer or is outside the valid range (1-12). Booleans are
            rejected for all three arguments, even though ``bool`` is a subclass of
            ``int``.
    """
    # Same fast path as encode(): exact-type floats in range with an in-range int
    # precision go straight to the C codec; anything else falls through to the
    # full validation below, which raises exactly the same errors as before. The
    # error log on a C-level failure is part of this function's contract, so the
    # fast path keeps it.
    if (
        type(latitude) is float
        and type(longitude) is float
        and -90.0 <= latitude <= 90.0
        and -180.0 <= longitude <= 180.0
        and type(precision) is int
        and MIN_PRECISION <= precision <= MAX_PRECISION
    ):
        try:
            return c_encode_strictly(latitude, longitude, precision)
        except ValueError as e:
            logger.error(
                "Failed to strictly encode coordinates: lat=%f, lon=%f with precision %d: %s",
                latitude,
                longitude,
                precision,
                str(e),
            )
            raise

    # bool is a subclass of int, so it has to be rejected explicitly.
    if isinstance(precision, bool) or not isinstance(precision, int):
        raise ValueError(f"Precision must be an integer, but got {type(precision).__name__}.")
    if not (MIN_PRECISION <= precision <= MAX_PRECISION):
        raise ValueError(f"Precision must be between {MIN_PRECISION} and {MAX_PRECISION}, but got {precision}.")

    if isinstance(latitude, bool):
        raise ValueError(f"Latitude must be a number, but got {type(latitude).__name__}.")
    if isinstance(longitude, bool):
        raise ValueError(f"Longitude must be a number, but got {type(longitude).__name__}.")

    # Validate latitude range
    if not (-90.0 <= latitude <= 90.0):
        raise ValueError(f"Latitude must be between -90.0 and 90.0 degrees, but got {latitude}.")

    # Validate longitude range
    if not (-180.0 <= longitude <= 180.0):
        raise ValueError(f"Longitude must be between -180.0 and 180.0 degrees, but got {longitude}.")

    try:
        return c_encode_strictly(latitude, longitude, precision)
    except ValueError as e:
        logger.error(
            "Failed to strictly encode coordinates: lat=%f, lon=%f with precision %d: %s",
            latitude,
            longitude,
            precision,
            str(e),
        )
        raise


def decode(geohash: str) -> LatLong:
    """Decode a geohash into a latitude and longitude.

    Args:
        geohash (str): The geohash string to decode. Input is case-insensitive, matching
            :func:`~pygeohash.types.is_valid_geohash` and :func:`~pygeohash.neighbor.get_adjacent`,
            so ``"U4PRUYD"`` and ``"U4pruYd"`` decode identically to ``"u4pruyd"``.

    Returns:
        LatLong: A named tuple containing the latitude and longitude.

    Raises:
        ValueError: If the geohash is not a string, is not between 1 and 12 characters,
            or contains invalid characters.
    """
    if not isinstance(geohash, str):
        raise ValueError(f"Geohash must be a string, but got {type(geohash).__name__}.")
    if not geohash:
        raise ValueError("Geohash cannot be empty.")
    if len(geohash) > MAX_PRECISION:
        raise ValueError(f"Geohash must be at most {MAX_PRECISION} characters long.")

    # The C extension raises ValueError("Invalid character in geohash") for any
    # non-base32 character, so we let it do the per-character validation instead
    # of paying for a Python-level scan on every call.
    return c_decode(geohash.lower())


def decode_exactly(geohash: str) -> ExactLatLong:
    """Decode a geohash into a latitude and longitude with error margins.

    This function provides more detailed information than the standard decode
    function by including the error margins for both latitude and longitude.

    Args:
        geohash (str): The geohash string to decode. Input is case-insensitive, matching
            :func:`~pygeohash.types.is_valid_geohash` and :func:`~pygeohash.neighbor.get_adjacent`,
            so ``"U4PRUYD"`` and ``"U4pruYd"`` decode identically to ``"u4pruyd"``.

    Returns:
        ExactLatLong: A named tuple containing the latitude, longitude, and their
            respective error margins.

    Raises:
        ValueError: If the geohash is not a string, is not between 1 and 12 characters,
            or contains invalid characters.
    """
    if not isinstance(geohash, str):
        raise ValueError(f"Geohash must be a string, but got {type(geohash).__name__}.")
    if not geohash:
        raise ValueError("Geohash cannot be empty.")
    if len(geohash) > MAX_PRECISION:
        raise ValueError(f"Geohash must be at most {MAX_PRECISION} characters long.")

    # See decode(): the C extension folds case, validates characters, and
    # raises on its own.
    return c_decode_exactly(geohash)


def encode_many(latitudes: Iterable[float], longitudes: Iterable[float], precision: GeohashPrecision = 12) -> list[str]:
    """Encode many coordinate pairs into geohashes in one call.

    The result equals ``[encode(a, b, precision) for a, b in zip(latitudes, longitudes)]``
    element for element, but the shared ``precision`` is validated once and the loop
    runs in C. Each pair gets exactly the validation :func:`encode` applies, and a
    rejected pair raises the same exception type and message as the scalar call with
    ``" (at index N)"`` appended. NumPy is not imported; NumPy arrays work through
    ordinary iteration.

    Args:
        latitudes (Iterable[float]): Latitudes, as a list, tuple, ``array.array``,
            NumPy array, generator, or any other iterable.
        longitudes (Iterable[float]): Longitudes, with the same length as ``latitudes``.
        precision (GeohashPrecision, optional): The number of characters in each geohash.
            Defaults to 12. Must be between 1 and 12, inclusive.

    Returns:
        list[str]: One lowercase geohash per pair; an empty list for empty input.

    Raises:
        ValueError: If ``precision`` is invalid (reported without an index), if the two
            inputs have different lengths, or if any pair is rejected by :func:`encode`.
        TypeError: If an input is not iterable, or if a pair fails with ``TypeError``
            in :func:`encode`.
    """
    if isinstance(precision, bool) or not isinstance(precision, int):
        raise ValueError(f"Precision must be an integer, but got {type(precision).__name__}.")
    if not (MIN_PRECISION <= precision <= MAX_PRECISION):
        raise ValueError(f"Precision must be between {MIN_PRECISION} and {MAX_PRECISION}, but got {precision}.")
    return c_encode_many(latitudes, longitudes, precision, encode)


def decode_many(geohashes: Iterable[str]) -> list[LatLong]:
    """Decode many geohashes into cell centers in one call.

    The result equals ``[decode(g) for g in geohashes]`` element for element. Each
    geohash gets exactly the validation :func:`decode` applies (including its
    case-insensitivity), and a rejected geohash raises the same exception type and
    message as the scalar call with ``" (at index N)"`` appended.

    Args:
        geohashes (Iterable[str]): Geohash strings, as a list, tuple, generator, or any
            other iterable. A single ``str`` is rejected.

    Returns:
        list[LatLong]: One :class:`~pygeohash.geohash_types.LatLong` per geohash; an
            empty list for empty input.

    Raises:
        TypeError: If ``geohashes`` is a bare ``str`` or is not iterable.
        ValueError: If any element is rejected by :func:`decode`.
    """
    if isinstance(geohashes, str):
        raise TypeError(
            "geohashes must be an iterable of geohash strings, not a single str; pass [geohash] to decode one geohash."
        )
    return c_decode_many(geohashes, decode)


__all__ = [
    "decode",
    "decode_exactly",
    "decode_many",
    "encode",
    "encode_many",
    "encode_strictly",
    "LatLong",
    "ExactLatLong",
    "__base32",
    "__decodemap",
]
