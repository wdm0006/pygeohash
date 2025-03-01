"""Statistical operations for collections of geohashes.

This module provides functions for calculating statistical properties
of collections of geohashes, including mean position, cardinal extremes
(northern, southern, eastern, western), variance, and standard deviation.
"""

import math
import statistics
from typing import Callable, Generator, Iterable, List

from pygeohash.distances import geohash_haversine_distance
from pygeohash.geohash import LatLong, decode, encode

__author__ = "Will McGinnis"


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


def _max_cardinal(geohashes: Iterable[str], key: Callable[[LatLong], float], reverse: bool) -> str:
    """Find the extreme geohash in a collection based on a key function.
    
    Args:
        geohashes (Iterable[str]): Collection of geohash strings.
        key (Callable[[LatLong], float]): Function to extract the value to compare.
        reverse (bool): Whether to find maximum (True) or minimum (False).
        
    Returns:
        str: The geohash at the extreme position.
    """
    coordinates: Generator[LatLong] = (decode(x) for x in geohashes)
    m = max if reverse else min
    coordinate = m(coordinates, key=key)
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
    return _max_cardinal(geohashes, __latitude, reverse=True)


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
    return _max_cardinal(geohashes, __longitude, reverse=True)


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
    return _max_cardinal(geohashes, __longitude, reverse=False)


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
    return _max_cardinal(geohashes, __latitude, reverse=False)


def mean(geohashes: Iterable[str]) -> str:
    """Calculate the mean position of a collection of geohashes.
    
    Args:
        geohashes (Iterable[str]): Collection of geohash strings.
        
    Returns:
        str: A geohash representing the mean position.
        
    Example:
        >>> mean(["u4pruyd", "u4pruyf", "u4pruyc"])
        'u4pruye'
    """
    coordinates: List[LatLong] = [decode(x) for x in geohashes]
    return encode(
        statistics.mean(x.latitude for x in coordinates),
        statistics.mean(x.longitude for x in coordinates),
    )


def variance(geohashes: Iterable[str]) -> float:
    """Calculate the spatial variance of a collection of geohashes.
    
    The variance is calculated as the mean of squared distances from each
    geohash to the mean position.
    
    Args:
        geohashes (Iterable[str]): Collection of geohash strings.
        
    Returns:
        float: The spatial variance in square meters.
        
    Example:
        >>> variance(["u4pruyd", "u4pruyf", "u4pruyc"])
        12500.0
    """
    mean_v = mean(geohashes)
    dists = [geohash_haversine_distance(x, mean_v) for x in geohashes]
    var = sum([x**2 for x in dists]) / float(len(dists))
    return var


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
