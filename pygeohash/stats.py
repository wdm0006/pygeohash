"""Statistical operations for collections of geohashes.

This module provides functions for calculating statistical properties
of collections of geohashes, including mean position, cardinal extremes
(northern, southern, eastern, western), variance, and standard deviation.
"""

from __future__ import annotations

import math
import statistics
from typing import Callable, Generator, Iterable, List, Final, TypeVar

from pygeohash.distances import geohash_haversine_distance
from pygeohash.geohash import decode, encode
from pygeohash.geohash_types import LatLong

__author__: Final[str] = "Will McGinnis"

T = TypeVar("T")


def __latitude(coordinate: LatLong) -> float:
    """Extract the latitude from a LatLong coordinate.

    Args:
        coordinate (LatLong): The coordinate to extract latitude from.

    Returns:
        float: The latitude value.
    """
    return coordinate.latitude


def __longitude(coordinate: LatLong) -> float:
    """Extract the longitude from a LatLong coordinate.

    Args:
        coordinate (LatLong): The coordinate to extract longitude from.

    Returns:
        float: The longitude value.
    """
    return coordinate.longitude


def _max_cardinal(geohashes: Iterable[str], key_func: Callable[[LatLong], float], reverse: bool) -> str:
    """Find the extreme geohash in a collection based on a key function.

    Args:
        geohashes (Iterable[str]): Collection of geohash strings.
        key_func (Callable[[LatLong], float]): Function to extract the value to compare.
        reverse (bool): Whether to find maximum (True) or minimum (False).

    Returns:
        str: The geohash at the extreme position.
    """
    coordinates: Generator[LatLong, None, None] = (decode(x) for x in geohashes)
    if reverse:
        coordinate = max(coordinates, key=lambda x: key_func(x))
    else:
        coordinate = min(coordinates, key=lambda x: key_func(x))
    return encode(coordinate.latitude, coordinate.longitude)


def northern(geohashes: Iterable[str]) -> str:
    """Find the northernmost geohash in a collection.

    Args:
        geohashes (Iterable[str]): Collection of geohash strings.

    Returns:
        str: The northernmost geohash.

    Example:
        >>> northern(["u4pruyd", "u4pruyf", "u4pruyc"])
        'u4pruyf'
    """
    return _max_cardinal(geohashes, __latitude, True)


def southern(geohashes: Iterable[str]) -> str:
    """Find the southernmost geohash in a collection.

    Args:
        geohashes (Iterable[str]): Collection of geohash strings.

    Returns:
        str: The southernmost geohash.

    Example:
        >>> southern(["u4pruyd", "u4pruyf", "u4pruyc"])
        'u4pruyc'
    """
    return _max_cardinal(geohashes, __latitude, False)


def eastern(geohashes: Iterable[str]) -> str:
    """Find the easternmost geohash in a collection.

    Args:
        geohashes (Iterable[str]): Collection of geohash strings.

    Returns:
        str: The easternmost geohash.

    Example:
        >>> eastern(["u4pruyd", "u4pruyf", "u4pruyc"])
        'u4pruyf'
    """
    return _max_cardinal(geohashes, __longitude, True)


def western(geohashes: Iterable[str]) -> str:
    """Find the westernmost geohash in a collection.

    Args:
        geohashes (Iterable[str]): Collection of geohash strings.

    Returns:
        str: The westernmost geohash.

    Example:
        >>> western(["u4pruyd", "u4pruyf", "u4pruyc"])
        'u4pruyc'
    """
    return _max_cardinal(geohashes, __longitude, False)


def mean(geohashes: Iterable[str], precision: int = 12) -> str:
    """Calculate the mean position of a collection of geohashes.

    Args:
        geohashes (Iterable[str]): Collection of geohash strings.
        precision (int, optional): The precision of the resulting geohash. Defaults to 12.

    Returns:
        str: A geohash representing the mean position.

    Example:
        >>> mean(["u4pruyd", "u4pruyf", "u4pruyc"])
        'u4pruye'
    """
    coordinates: List[LatLong] = [decode(x) for x in geohashes]
    mean_lat: float = statistics.mean(c.latitude for c in coordinates)
    mean_lon: float = statistics.mean(c.longitude for c in coordinates)
    return encode(mean_lat, mean_lon, precision)


def variance(geohashes: Iterable[str]) -> float:
    """Calculate the spatial variance of a collection of geohashes.

    The variance is calculated as the mean squared distance from each point
    to the mean position.

    Args:
        geohashes (Iterable[str]): Collection of geohash strings.

    Returns:
        float: The spatial variance in square meters.

    Example:
        >>> variance(["u4pruyd", "u4pruyf", "u4pruyc"])
        12500.0
    """
    geohash_list: List[str] = list(geohashes)
    mean_geohash: str = mean(geohash_list)
    distances: List[float] = [geohash_haversine_distance(gh, mean_geohash) for gh in geohash_list]
    return statistics.mean(d * d for d in distances)


def std(geohashes: Iterable[str]) -> float:
    """Calculate the spatial standard deviation of a collection of geohashes.

    The standard deviation is the square root of the variance.

    Args:
        geohashes (Iterable[str]): Collection of geohash strings.

    Returns:
        float: The spatial standard deviation in meters.

    Example:
        >>> std(["u4pruyd", "u4pruyf", "u4pruyc"])
        111.8
    """
    return math.sqrt(variance(geohashes))
