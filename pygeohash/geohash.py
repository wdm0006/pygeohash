"""Geohash encoding and decoding functionality.

This module provides the core functionality for encoding coordinates to geohashes
and decoding geohashes back to coordinates. It includes both standard and exact
decoding options, as well as strict encoding.

This implementation uses a high-performance C extension for all operations.
"""

from __future__ import annotations

from typing import Dict

from pygeohash.cgeohash.geohash_module import (
    decode as c_decode,
    decode_exactly as c_decode_exactly,
    encode as c_encode,
    encode_strictly as c_encode_strictly,
    get_base32,
)
from pygeohash.geohash_types import ExactLatLong, LatLong, GeohashPrecision
from pygeohash.logging import get_logger

logger = get_logger(__name__)

__base32 = get_base32()
__decodemap: Dict[str, int] = {base32_char: i for i, base32_char in enumerate(__base32)}


def encode(latitude: float, longitude: float, precision: GeohashPrecision = 12) -> str:
    """Encode a latitude and longitude into a geohash.

    Args:
        latitude (float): The latitude to encode.
        longitude (float): The longitude to encode.
        precision (GeohashPrecision, optional): The number of characters in the geohash. Defaults to 12.

    Returns:
        str: The geohash string.
    """
    logger.debug("Encoding coordinates: lat=%f, lon=%f with precision %d", latitude, longitude, precision)
    result = c_encode(latitude, longitude, precision)
    logger.debug("Encoded to geohash: %s", result)
    return result


def encode_strictly(latitude: float, longitude: float, precision: GeohashPrecision = 12) -> str:
    """Encode a latitude and longitude into a geohash with strict validation.

    This function performs additional validation on the input coordinates
    before encoding them into a geohash.

    Args:
        latitude (float): The latitude to encode.
        longitude (float): The longitude to encode.
        precision (GeohashPrecision, optional): The number of characters in the geohash. Defaults to 12.

    Returns:
        str: The geohash string.

    Raises:
        ValueError: If the latitude or longitude values are invalid.
    """
    logger.debug("Strictly encoding coordinates: lat=%f, lon=%f with precision %d", latitude, longitude, precision)
    try:
        result = c_encode_strictly(latitude, longitude, precision)
        logger.debug("Strictly encoded to geohash: %s", result)
        return result
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
        geohash (str): The geohash string to decode.

    Returns:
        LatLong: A named tuple containing the latitude and longitude.
    """
    logger.debug("Decoding geohash: %s", geohash)
    lat, lon = c_decode(geohash)
    logger.debug("Decoded to coordinates: lat=%f, lon=%f", lat, lon)
    return LatLong(latitude=lat, longitude=lon)


def decode_exactly(geohash: str) -> ExactLatLong:
    """Decode a geohash into a latitude and longitude with error margins.

    This function provides more detailed information than the standard decode
    function by including the error margins for both latitude and longitude.

    Args:
        geohash (str): The geohash string to decode.

    Returns:
        ExactLatLong: A named tuple containing the latitude, longitude, and their
            respective error margins.
    """
    logger.debug("Exactly decoding geohash: %s", geohash)
    lat, lon, lat_err, lon_err = c_decode_exactly(geohash)
    logger.debug("Exactly decoded to coordinates: lat=%f±%f, lon=%f±%f", lat, lat_err, lon, lon_err)
    return ExactLatLong(latitude=lat, longitude=lon, latitude_error=lat_err, longitude_error=lon_err)


__all__ = [
    "decode",
    "decode_exactly",
    "encode",
    "encode_strictly",
    "LatLong",
    "ExactLatLong",
    "__base32",
    "__decodemap",
]
