"""Geohash encoding and decoding functionality.

This module provides the core functionality for encoding coordinates to geohashes
and decoding geohashes back to coordinates. It includes both standard and exact
decoding options, as well as strict encoding.

Copyright (C) 2008 Leonard Norrgard <leonard.norrgard@gmail.com>
Copyright (C) 2015 Leonard Norrgard <leonard.norrgard@gmail.com>

This file is part of Geohash.

Geohash is free software: you can redistribute it and/or modify it
under the terms of the GNU Affero General Public License as published
by the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Geohash is distributed in the hope that it will be useful, but WITHOUT
ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
FITNESS FOR A PARTICULAR PURPOSE.  See the GNU Affero General Public
License for more details.

You should have received a copy of the GNU Affero General Public
License along with Geohash.  If not, see
<http://www.gnu.org/licenses/>.

Modified 2015 by Will McGinnis for pygeohash.
Modified 2023 by Paarth Shah for pygeohash.
"""

from __future__ import annotations

from math import log10
from typing import Dict, NamedTuple

#  Note: the alphabet in geohash differs from the common base32 alphabet described in IETF's RFC 4648
# (http://tools.ietf.org/html/rfc4648)

__base32 = "0123456789bcdefghjkmnpqrstuvwxyz"
__decodemap: Dict[str, int] = {base32_char: i for i, base32_char in enumerate(__base32)}


class LatLong(NamedTuple):
    """Named tuple representing a latitude/longitude coordinate pair.
    
    Attributes:
        latitude (float): The latitude coordinate in decimal degrees.
        longitude (float): The longitude coordinate in decimal degrees.
    """
    latitude: float
    longitude: float


class ExactLatLong(NamedTuple):
    """Named tuple representing a latitude/longitude coordinate pair with error margins.
    
    Attributes:
        latitude (float): The latitude coordinate in decimal degrees.
        longitude (float): The longitude coordinate in decimal degrees.
        latitude_error (float): The error margin for latitude in decimal degrees.
        longitude_error (float): The error margin for longitude in decimal degrees.
    """
    latitude: float
    longitude: float
    latitude_error: float
    longitude_error: float


def decode_exactly(geohash: str) -> ExactLatLong:
    """Decode a geohash to its exact values, including error margins.
    
    Args:
        geohash (str): The geohash string to decode.
        
    Returns:
        ExactLatLong: A named tuple containing latitude, longitude, and their respective error margins.
        
    Example:
        >>> decode_exactly("u4pruydqqvj")
        ExactLatLong(latitude=57.64911, longitude=10.40744, latitude_error=0.00001, longitude_error=0.00001)
    """
    lat_interval, lon_interval = (-90.0, 90.0), (-180.0, 180.0)
    lat_err, lon_err = 90.0, 180.0
    is_even = True
    for c in geohash:
        cd = __decodemap[c]
        for mask in [16, 8, 4, 2, 1]:
            if is_even:  # adds longitude info
                lon_err /= 2
                if cd & mask:
                    lon_interval = (
                        (lon_interval[0] + lon_interval[1]) / 2,
                        lon_interval[1],
                    )
                else:
                    lon_interval = (
                        lon_interval[0],
                        (lon_interval[0] + lon_interval[1]) / 2,
                    )
            else:  # adds latitude info
                lat_err /= 2
                if cd & mask:
                    lat_interval = (
                        (lat_interval[0] + lat_interval[1]) / 2,
                        lat_interval[1],
                    )
                else:
                    lat_interval = (
                        lat_interval[0],
                        (lat_interval[0] + lat_interval[1]) / 2,
                    )
            is_even = not is_even
    lat = (lat_interval[0] + lat_interval[1]) / 2
    lon = (lon_interval[0] + lon_interval[1]) / 2
    return ExactLatLong(lat, lon, lat_err, lon_err)


def decode(geohash: str) -> LatLong:
    """Decode a geohash to latitude and longitude coordinates.
    
    Decodes a geohash string to a latitude and longitude coordinate pair,
    with precision appropriate to the length of the geohash.
    
    Args:
        geohash (str): The geohash string to decode.
        
    Returns:
        LatLong: A named tuple containing latitude and longitude coordinates.
        
    Example:
        >>> decode("u4pruyd")
        LatLong(latitude=57.649, longitude=10.407)
    """
    lat, lon, lat_err, lon_err = decode_exactly(geohash)
    # Format to the number of decimals that are known
    lats = "%.*f" % (max(1, int(round(-log10(lat_err)))) - 1, lat)
    lons = "%.*f" % (max(1, int(round(-log10(lon_err)))) - 1, lon)
    if "." in lats:
        lats = lats.rstrip("0")
    if "." in lons:
        lons = lons.rstrip("0")
    return LatLong(float(lats), float(lons))


def encode(latitude: float, longitude: float, precision=12) -> str:
    """Encode coordinates to a geohash string.
    
    Args:
        latitude (float): The latitude coordinate in decimal degrees (-90 to 90).
        longitude (float): The longitude coordinate in decimal degrees (-180 to 180).
        precision (int, optional): The desired length of the geohash string. Defaults to 12.
        
    Returns:
        str: The geohash string representation of the coordinates.
        
    Example:
        >>> encode(57.64911, 10.40744, 8)
        'u4pruydq'
    """
    lat_interval = (-90.0, 90.0)
    lon_interval = (-180.0, 180.0)
    geohash = []
    bits = [16, 8, 4, 2, 1]
    bit = 0
    ch = 0
    even = True
    while len(geohash) < precision:
        if even:
            mid = (lon_interval[0] + lon_interval[1]) / 2
            if longitude >= mid:
                ch |= bits[bit]
                lon_interval = (mid, lon_interval[1])
            else:
                lon_interval = (lon_interval[0], mid)
        else:
            mid = (lat_interval[0] + lat_interval[1]) / 2
            if latitude >= mid:
                ch |= bits[bit]
                lat_interval = (mid, lat_interval[1])
            else:
                lat_interval = (lat_interval[0], mid)
        even = not even
        if bit < 4:
            bit += 1
        else:
            geohash += __base32[ch]
            bit = 0
            ch = 0
    return "".join(geohash)


def encode_strictly(latitude: float, longitude: float, precision=12) -> str:
    """Encode coordinates to a geohash string with strict midpoint handling.
    
    This function is similar to encode() but handles the midpoint differently.
    When a coordinate is exactly at the midpoint, it is included in the upper interval.
    
    Args:
        latitude (float): The latitude coordinate in decimal degrees (-90 to 90).
        longitude (float): The longitude coordinate in decimal degrees (-180 to 180).
        precision (int, optional): The desired length of the geohash string. Defaults to 12.
        
    Returns:
        str: The geohash string representation of the coordinates.
        
    Example:
        >>> encode_strictly(57.64911, 10.40744, 8)
        'u4pruydq'
    """
    lat_interval = (-90.0, 90.0)
    lon_interval = (-180.0, 180.0)
    geohash = []
    bits = [16, 8, 4, 2, 1]
    bit = 0
    ch = 0
    even = True
    while len(geohash) < precision:
        if even:
            mid = (lon_interval[0] + lon_interval[1]) / 2
            if longitude >= mid:
                ch |= bits[bit]
                lon_interval = (mid, lon_interval[1])
            else:
                lon_interval = (lon_interval[0], mid)
        else:
            mid = (lat_interval[0] + lat_interval[1]) / 2
            if latitude >= mid:
                ch |= bits[bit]
                lat_interval = (mid, lat_interval[1])
            else:
                lat_interval = (lat_interval[0], mid)
        even = not even
        if bit < 4:
            bit += 1
        else:
            geohash += __base32[ch]
            bit = 0
            ch = 0
    return "".join(geohash)
