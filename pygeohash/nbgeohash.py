"""Numba-accelerated geohash encoding and decoding.

This module provides Numba-accelerated implementations of geohash encoding
and decoding functions for improved performance. It includes both single-point
and vectorized operations for batch processing.

Note:
    This module requires Numba and NumPy to be installed. These are optional
    dependencies that can be installed with `pip install pygeohash[numba]`.
"""

from math import log10
from typing import List

import numpy as np
from numba import njit, types

from pygeohash.geohash import ExactLatLong, LatLong, __base32

__author__ = "ilyasmoutawwakil"


@njit(cache=True, fastmath=True)
def base32_to_int(s: types.char) -> types.uint8:
    """Convert a base32 character to its integer value.

    This function is optimized for Numba and is faster than using a dictionary
    lookup in the Numba environment.

    Args:
        s (types.char): A single character from the base32 alphabet.

    Returns:
        types.uint8: The integer value of the character.

    Raises:
        AssertionError: If the character is not in the base32 alphabet.
    """
    assert s in __base32
    res = ord(s) - 48
    if res > 9:
        res -= 40
    if res > 16:
        res -= 1
    if res > 18:
        res -= 1
    if res > 20:
        res -= 1
    return res


@njit(fastmath=True)
def nb_decode_exactly(geohash: str) -> ExactLatLong:
    """Decode a geohash to its exact values with error margins (Numba-accelerated).

    This is a Numba-accelerated version of decode_exactly that provides
    the same functionality but with better performance.

    Args:
        geohash (str): The geohash string to decode.

    Returns:
        ExactLatLong: A named tuple containing latitude, longitude, and their respective error margins.

    Example:
        >>> nb_decode_exactly("u4pruydqqvj")
        ExactLatLong(latitude=57.64911, longitude=10.40744, latitude_error=0.00001, longitude_error=0.00001)
    """
    lat_interval_neg, lat_interval_pos, lon_interval_neg, lon_interval_pos = (
        -90,
        90,
        -180,
        180,
    )
    lat_err, lon_err = 90.0, 180.0
    is_even = True
    for c in geohash:
        cd = base32_to_int(c)
        for mask in (16, 8, 4, 2, 1):
            if is_even:  # adds longitude info
                lon_err /= 2
                if cd & mask:
                    lon_interval_neg = (lon_interval_neg + lon_interval_pos) / 2
                else:
                    lon_interval_pos = (lon_interval_neg + lon_interval_pos) / 2
            else:  # adds latitude info
                lat_err /= 2
                if cd & mask:
                    lat_interval_neg = (lat_interval_neg + lat_interval_pos) / 2
                else:
                    lat_interval_pos = (lat_interval_neg + lat_interval_pos) / 2
            is_even = not is_even
    lat = (lat_interval_neg + lat_interval_pos) / 2
    lon = (lon_interval_neg + lon_interval_pos) / 2
    return ExactLatLong(lat, lon, lat_err, lon_err)


@njit(fastmath=True)
def nb_point_decode(geohash: str) -> LatLong:
    """Decode a geohash to latitude and longitude coordinates (Numba-accelerated).

    This is a Numba-accelerated version of decode that provides
    the same functionality but with better performance.

    Args:
        geohash (str): The geohash string to decode.

    Returns:
        LatLong: A named tuple containing latitude and longitude coordinates.

    Example:
        >>> nb_point_decode("u4pruyd")
        LatLong(latitude=57.649, longitude=10.407)
    """
    lat, lon, lat_err, lon_err = nb_decode_exactly(geohash)
    # Format to the number of decimals that are known
    lat_dec = max(1, round(-log10(lat_err))) - 1
    lon_dec = max(1, round(-log10(lon_err))) - 1
    lat = round(lat, lat_dec)
    lon = round(lon, lon_dec)

    return LatLong(lat, lon)


@njit(fastmath=True)
def nb_vector_decode(geohashes: List[str]) -> types.Tuple:
    """Decode multiple geohashes to arrays of latitudes and longitudes (Numba-accelerated).

    This function provides efficient batch decoding of multiple geohashes.
    It's significantly faster than decoding each geohash individually,
    especially for large collections.

    Args:
        geohashes (List[str]): A list of geohash strings to decode.

    Returns:
        types.Tuple: A tuple of two NumPy arrays (latitudes, longitudes).

    Example:
        >>> lats, lons = nb_vector_decode(["u4pruyd", "u4pruyf", "u4pruyc"])
        >>> lats
        array([57.649, 57.649, 57.648])
        >>> lons
        array([10.407, 10.407, 10.406])
    """
    n = len(geohashes)
    lats = np.empty(n)
    lons = np.empty(n)
    for i, geohash in enumerate(geohashes):
        lat, lon, lat_err, lon_err = nb_decode_exactly(str(geohash))
        # Format to the number of decimals that are known
        lat_dec = max(1, round(-log10(lat_err))) - 1
        lon_dec = max(1, round(-log10(lon_err))) - 1
        lats[i] = round(lat, lat_dec)
        lons[i] = round(lon, lon_dec)

    return lats, lons


@njit(fastmath=True)
def nb_point_encode(latitude: types.float64, longitude: types.float64, precision: types.int8 = 12) -> types.string:
    """Encode coordinates to a geohash string (Numba-accelerated).

    This is a Numba-accelerated version of encode that provides
    the same functionality but with better performance.

    Args:
        latitude (types.float64): The latitude coordinate in decimal degrees (-90 to 90).
        longitude (types.float64): The longitude coordinate in decimal degrees (-180 to 180).
        precision (types.int8, optional): The desired length of the geohash string. Defaults to 12.

    Returns:
        types.string: The geohash string representation of the coordinates.

    Example:
        >>> nb_point_encode(57.64911, 10.40744, 8)
        'u4pruydq'
    """
    lat_interval_neg, lat_interval_pos, lon_interval_neg, lon_interval_pos = (
        -90,
        90,
        -180,
        180,
    )
    geohash = np.zeros(precision, dtype="<U1")
    bits = np.array([16, 8, 4, 2, 1])
    bit = 0
    ch = 0
    n = 0
    even = True
    while n < precision:
        if even:
            mid = (lon_interval_neg + lon_interval_pos) / 2
            if longitude > mid:
                ch |= bits[bit]
                lon_interval_neg = mid
            else:
                lon_interval_pos = mid
        else:
            mid = (lat_interval_neg + lat_interval_pos) / 2
            if latitude > mid:
                ch |= bits[bit]
                lat_interval_neg = mid
            else:
                lat_interval_pos = mid
        even = not even

        if bit < 4:
            bit += 1
        else:
            geohash[n] = __base32[ch]
            bit = 0
            ch = 0
            n += 1

    return "".join(geohash)


@njit(fastmath=True)
def nb_vector_encode(latitudes: types.Array, longitudes: types.Array, precision: types.int8 = 12) -> types.Array:
    """Encode multiple coordinates to geohash strings (Numba-accelerated).

    This function provides efficient batch encoding of multiple coordinate pairs.
    It's significantly faster than encoding each coordinate pair individually,
    especially for large collections.

    Args:
        latitudes (types.Array): Array of latitude coordinates in decimal degrees.
        longitudes (types.Array): Array of longitude coordinates in decimal degrees.
        precision (types.int8, optional): The desired length of the geohash strings. Defaults to 12.

    Returns:
        types.Array: Array of geohash strings.

    Example:
        >>> nb_vector_encode(np.array([57.649, 57.650]), np.array([10.407, 10.408]), 6)
        array(['u4pruy', 'u4pruy'], dtype='<U12')
    """
    n = len(latitudes)
    geohashes = np.empty(n, dtype="<U12")
    for i in range(n):
        geohashes[i] = nb_point_encode(latitudes[i], longitudes[i], precision)
    return geohashes
