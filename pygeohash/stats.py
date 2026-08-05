"""Statistical operations for collections of geohashes.

This module provides functions for calculating statistical properties
of collections of geohashes, including mean position, cardinal extremes
(northern, southern, eastern, western), variance, and standard deviation.
"""

from __future__ import annotations

import math
import statistics
from typing import Callable, Final, Sequence, TypeVar

from pygeohash.distances import geohash_haversine_distance
from pygeohash.geohash import decode, encode
from pygeohash.geohash_types import LatLong
from pygeohash.types import GeohashCollection, GeohashPrecision
from pygeohash.logging import get_logger

logger = get_logger(__name__)

__author__: Final[str] = "Will McGinnis"

T = TypeVar("T")

#: Resultant vector lengths at or below this value are treated as fully cancelled.
_CIRCULAR_MEAN_TOLERANCE: Final[float] = 1e-12


def _reject_bare_geohash_string(geohashes: GeohashCollection) -> None:
    """Reject a single geohash string passed where a collection is expected.

    A ``str`` satisfies ``Collection[str]``, so passing one geohash instead of a
    collection of geohashes would otherwise be treated as a collection of
    single-character geohashes and return a plausible but meaningless result.

    Args:
        geohashes (GeohashCollection): The value supplied by the caller.

    Raises:
        TypeError: If ``geohashes`` is a string rather than a collection of
            geohash strings.
    """
    if isinstance(geohashes, str):
        raise TypeError(
            "geohashes must be a collection of geohash strings, not a single geohash string. "
            f"Wrap a single geohash in a collection, for example [{geohashes!r}]."
        )


def _circular_mean_longitude(longitudes: Sequence[float]) -> float:
    """Calculate the circular mean of a sequence of longitudes in degrees.

    Longitude is circular, so an arithmetic mean places the centroid of a
    collection spanning the antimeridian near the prime meridian instead. This
    averages the unit vectors of the longitudes and converts the resultant back
    to degrees.

    When the resultant vector cancels out (for example two antipodal
    longitudes), no unique circular mean exists and the arithmetic mean of the
    longitudes is returned.

    Args:
        longitudes (Sequence[float]): Longitudes in degrees.

    Returns:
        float: The mean longitude in degrees, within [-180, 180].
    """
    radians = [math.radians(longitude) for longitude in longitudes]
    mean_sin = statistics.mean(math.sin(radian) for radian in radians)
    mean_cos = statistics.mean(math.cos(radian) for radian in radians)

    if math.hypot(mean_sin, mean_cos) <= _CIRCULAR_MEAN_TOLERANCE:
        logger.debug("Longitude vectors cancelled out; falling back to the arithmetic mean")
        return statistics.mean(longitudes)

    return math.degrees(math.atan2(mean_sin, mean_cos))


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
        geohashes (GeohashCollection): Collection of geohash strings. A single geohash
            must be wrapped in a collection, for example ``["u4pruyd"]``.
        key_func (Callable[[LatLong], float]): Function to extract the value to compare.
        reverse (bool): Whether to find maximum (True) or minimum (False).

    Returns:
        str: The geohash at the extreme position.

    Raises:
        TypeError: If ``geohashes`` is a single geohash string.
    """
    _reject_bare_geohash_string(geohashes)

    logger.debug("Finding %s for %d geohashes", "maximum" if reverse else "minimum", len(geohashes))

    if not geohashes:
        logger.warning("Empty geohash collection provided")
        return ""

    if reverse:
        result = max(geohashes, key=lambda geohash: key_func(decode(geohash)))
    else:
        result = min(geohashes, key=lambda geohash: key_func(decode(geohash)))

    logger.debug("Found %s geohash: %s", "maximum" if reverse else "minimum", result)
    return result


def northern(geohashes: GeohashCollection) -> str:
    """Find the northernmost geohash in a collection.

    Args:
        geohashes (GeohashCollection): Collection of geohash strings. A single geohash
            must be wrapped in a collection, for example ``["u4pruyd"]``.

    Returns:
        str: The northernmost geohash.

    Raises:
        TypeError: If ``geohashes`` is a single geohash string.

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
        geohashes (GeohashCollection): Collection of geohash strings. A single geohash
            must be wrapped in a collection, for example ``["u4pruyd"]``.

    Returns:
        str: The southernmost geohash.

    Raises:
        TypeError: If ``geohashes`` is a single geohash string.

    Example:
        >>> southern(["u4pruyd", "u4pruyf", "u4pruyc"])
        'u4pruyd'
    """
    logger.debug("Finding southernmost geohash in collection of %d geohashes", len(geohashes))
    result = _max_cardinal(geohashes, __latitude, False)
    logger.debug("Found southernmost geohash: %s", result)
    return result


def eastern(geohashes: GeohashCollection) -> str:
    """Find the easternmost geohash in a collection.

    Args:
        geohashes (GeohashCollection): Collection of geohash strings. A single geohash
            must be wrapped in a collection, for example ``["u4pruyd"]``.

    Returns:
        str: The easternmost geohash.

    Raises:
        TypeError: If ``geohashes`` is a single geohash string.

    Example:
        >>> eastern(["u4pruyd", "u4pruyf", "u4pruyc"])
        'u4pruyd'
    """
    logger.debug("Finding easternmost geohash in collection of %d geohashes", len(geohashes))
    result = _max_cardinal(geohashes, __longitude, True)
    logger.debug("Found easternmost geohash: %s", result)
    return result


def western(geohashes: GeohashCollection) -> str:
    """Find the westernmost geohash in a collection.

    Args:
        geohashes (GeohashCollection): Collection of geohash strings. A single geohash
            must be wrapped in a collection, for example ``["u4pruyd"]``.

    Returns:
        str: The westernmost geohash.

    Raises:
        TypeError: If ``geohashes`` is a single geohash string.

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

    Latitude is averaged arithmetically. Longitude is averaged circularly, so a
    collection spanning the antimeridian is centered near ±180 rather than near
    the prime meridian. If the longitude vectors cancel out exactly (for example
    two antipodal longitudes) no unique circular mean exists, and the arithmetic
    mean of the longitudes is used instead.

    Args:
        geohashes (GeohashCollection): Collection of geohash strings. A single geohash
            must be wrapped in a collection, for example ``["u4pruyd"]``.
        precision (GeohashPrecision, optional): The precision of the resulting geohash. Defaults to 12.

    Returns:
        str: A geohash representing the mean position, or an empty string for an
            empty collection.

    Raises:
        TypeError: If ``geohashes`` is a single geohash string.

    Example:
        >>> mean(["u4pruyd", "u4pruyf", "u4pruyc"])
        'u4pruyf1m6dt'
    """
    _reject_bare_geohash_string(geohashes)

    logger.debug("Calculating mean position for %d geohashes with precision %d", len(geohashes), precision)

    if not geohashes:
        logger.warning("Empty geohash collection provided")
        return ""

    coordinates = [decode(x) for x in geohashes]
    logger.debug("Decoded %d coordinates for mean calculation", len(coordinates))
    mean_lat = statistics.mean(c.latitude for c in coordinates)
    mean_lon = _circular_mean_longitude([c.longitude for c in coordinates])

    result = encode(mean_lat, mean_lon, precision)
    logger.debug("Mean position calculated: %s (lat=%f, lon=%f)", result, mean_lat, mean_lon)
    return result


def variance(geohashes: GeohashCollection) -> float:
    """Calculate the variance of a collection of geohashes.

    This function calculates the mean of squared distances from the mean position
    to each geohash in the collection.

    Args:
        geohashes (GeohashCollection): Collection of geohash strings. A single geohash
            must be wrapped in a collection, for example ``["u4pruyd"]``.

    Returns:
        float: The variance in meters squared.

    Raises:
        TypeError: If ``geohashes`` is a single geohash string.

    Example:
        >>> round(variance(["u4pruyd", "u4pruyf", "u4pruyc"]), 1)
        6665.5
    """
    _reject_bare_geohash_string(geohashes)

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
        geohashes (GeohashCollection): Collection of geohash strings. A single geohash
            must be wrapped in a collection, for example ``["u4pruyd"]``.

    Returns:
        float: The standard deviation in meters.

    Raises:
        TypeError: If ``geohashes`` is a single geohash string.

    Example:
        >>> round(std(["u4pruyd", "u4pruyf", "u4pruyc"]), 1)
        81.6
    """
    _reject_bare_geohash_string(geohashes)

    logger.debug("Calculating standard deviation for %d geohashes", len(geohashes))
    result = math.sqrt(variance(geohashes))
    logger.debug("Calculated standard deviation: %f meters", result)
    return result
