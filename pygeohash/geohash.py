"""Geohash encoding and decoding functionality.

This module provides the core functionality for encoding coordinates to geohashes
and decoding geohashes back to coordinates. It includes both standard and exact
decoding options, as well as strict encoding.

This implementation uses a high-performance C extension for all operations.
"""

from __future__ import annotations

from typing import Dict

from pygeohash.cgeohash.geohash_module import (
    decode,
    decode_exactly,
    encode as c_encode,
    encode_strictly as c_encode_strictly,
    get_base32,
)
from pygeohash.geohash_types import ExactLatLong, LatLong

__base32 = get_base32()
__decodemap: Dict[str, int] = {base32_char: i for i, base32_char in enumerate(__base32)}


def encode(latitude: float, longitude: float, precision: int = 12) -> str:
    """Encode a latitude and longitude into a geohash.

    Args:
        latitude (float): The latitude to encode.
        longitude (float): The longitude to encode.
        precision (int, optional): The number of characters in the geohash. Defaults to 12.

    Returns:
        str: The geohash string.
    """
    return c_encode(latitude, longitude, precision)


def encode_strictly(latitude: float, longitude: float, precision: int = 12) -> str:
    """Encode a latitude and longitude into a geohash with strict midpoint handling.

    Args:
        latitude (float): The latitude to encode.
        longitude (float): The longitude to encode.
        precision (int, optional): The number of characters in the geohash. Defaults to 12.

    Returns:
        str: The geohash string.
    """
    return c_encode_strictly(latitude, longitude, precision)


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
