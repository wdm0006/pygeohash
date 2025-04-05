"""Statistical operations for collections of geohashes.

This module provides functions for calculating statistical properties
of collections of geohashes, including mean position, cardinal extremes
(northern, southern, eastern, western), variance, and standard deviation.
"""

from __future__ import annotations

import math
import statistics
from typing import Callable, Final, TypeVar

from pygeohash.distances import geohash_haversine_distance
from pygeohash.geohash import decode, encode
from pygeohash.geohash_types import LatLong
from pygeohash.types import GeohashCollection, GeohashPrecision
from pygeohash.logging import get_logger

logger = get_logger(__name__)

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


def _max_cardinal(geohashes: GeohashCollection, key_func: Callable[[LatLong], float], reverse: bool) -> str:
    """Find the extreme geohash in a collection based on a key function.

    Args:
        geohashes (GeohashCollection): Collection of geohash strings.
        key_func (Callable[[LatLong], float]): Function to extract the value to compare.
        reverse (bool): Whether to find maximum (True) or minimum (False).

    Returns:
        str: The geohash at the extreme position.
    """
    logger.debug("Finding %s for %d geohashes", "maximum" if reverse else "minimum", len(geohashes))

    if not geohashes:
        logger.warning("Empty geohash collection provided")
        return ""

    coordinates = (decode(x) for x in geohashes)
    if reverse:
        coordinate = max(coordinates, key=lambda x: key_func(x))
    else:
        coordinate = min(coordinates, key=lambda x: key_func(x))

    result = encode(coordinate.latitude, coordinate.longitude)
    logger.debug("Found %s geohash: %s", "maximum" if reverse else "minimum", result)
    return result


def northern(geohashes: GeohashCollection) -> str:
    """Find the northernmost geohash in a collection.

    Args:
        geohashes (GeohashCollection): Collection of geohash strings.

    Returns:
        str: The northernmost geohash.

    Example:
        >>> northern(["u4pruyd", "u4pruyf", "u4pruyc"])
        'u4pruyf'
    """
    logger.debug("Finding northernmost geohash in collection of %d geohashes", len(geohashes))
    result = _max_cardinal(geohashes, __latitude, True)
    logger.debug("Found northernmost geohash: %s", result)
    return result


def southern(geohashes: GeohashCollection) -> str:
    """Find the southernmost geohash in a collection.

    Args:
        geohashes (GeohashCollection): Collection of geohash strings.

    Returns:
        str: The southernmost geohash.

    Example:
        >>> southern(["u4pruyd", "u4pruyf", "u4pruyc"])
        'u4pruyc'
    """
    logger.debug("Finding southernmost geohash in collection of %d geohashes", len(geohashes))
    result = _max_cardinal(geohashes, __latitude, False)
    logger.debug("Found southernmost geohash: %s", result)
    return result


def eastern(geohashes: GeohashCollection) -> str:
    """Find the easternmost geohash in a collection.

    Args:
        geohashes (GeohashCollection): Collection of geohash strings.

    Returns:
        str: The easternmost geohash.

    Example:
        >>> eastern(["u4pruyd", "u4pruyf", "u4pruyc"])
        'u4pruyf'
    """
    logger.debug("Finding easternmost geohash in collection of %d geohashes", len(geohashes))
    result = _max_cardinal(geohashes, __longitude, True)
    logger.debug("Found easternmost geohash: %s", result)
    return result


def western(geohashes: GeohashCollection) -> str:
    """Find the westernmost geohash in a collection.

    Args:
        geohashes (GeohashCollection): Collection of geohash strings.

    Returns:
        str: The westernmost geohash.

    Example:
        >>> western(["u4pruyd", "u4pruyf", "u4pruyc"])
        'u4pruyc'
    """
    logger.debug("Finding westernmost geohash in collection of %d geohashes", len(geohashes))
    result = _max_cardinal(geohashes, __longitude, False)
    logger.debug("Found westernmost geohash: %s", result)
    return result


def mean(geohashes: GeohashCollection, precision: GeohashPrecision = 12) -> str:
    """Calculate the mean position of a collection of geohashes.

    Args:
        geohashes (GeohashCollection): Collection of geohash strings.
        precision (GeohashPrecision, optional): The precision of the resulting geohash. Defaults to 12.

    Returns:
        str: A geohash representing the mean position.

    Example:
        >>> mean(["u4pruyd", "u4pruyf", "u4pruyc"])
        'u4pruye'
    """
    logger.debug("Calculating mean position for %d geohashes with precision %d", len(geohashes), precision)

    if not geohashes:
        logger.warning("Empty geohash collection provided")
        return ""

    coordinates = [decode(x) for x in geohashes]
    logger.debug("Decoded %d coordinates for mean calculation", len(coordinates))
    mean_lat = statistics.mean(c.latitude for c in coordinates)
    mean_lon = statistics.mean(c.longitude for c in coordinates)

    result = encode(mean_lat, mean_lon, precision)
    logger.debug("Mean position calculated: %s (lat=%f, lon=%f)", result, mean_lat, mean_lon)
    return result


def variance(geohashes: GeohashCollection) -> float:
    """Calculate the variance of a collection of geohashes.

    This function calculates the mean of squared distances from the mean position
    to each geohash in the collection.

    Args:
        geohashes (GeohashCollection): Collection of geohash strings.

    Returns:
        float: The variance in meters squared.

    Example:
        >>> variance(["u4pruyd", "u4pruyf", "u4pruyc"])
        2500.0
    """
    logger.debug("Calculating variance for %d geohashes", len(geohashes))

    if not geohashes:
        logger.warning("Empty geohash collection provided")
        return 0.0

    mean_geohash = mean(geohashes)
    squared_distances = [(geohash_haversine_distance(gh, mean_geohash)) ** 2 for gh in geohashes]
    result = statistics.mean(squared_distances)

    logger.debug("Calculated variance: %f square meters", result)
    return result


def std(geohashes: GeohashCollection) -> float:
    """Calculate the standard deviation of a collection of geohashes.

    This function calculates the square root of the variance, which represents
    the average distance from the mean position to each geohash in the collection.

    Args:
        geohashes (GeohashCollection): Collection of geohash strings.

    Returns:
        float: The standard deviation in meters.

    Example:
        >>> std(["u4pruyd", "u4pruyf", "u4pruyc"])
        50.0
    """
    logger.debug("Calculating standard deviation for %d geohashes", len(geohashes))
    result = math.sqrt(variance(geohashes))
    logger.debug("Calculated standard deviation: %f meters", result)
    return result
