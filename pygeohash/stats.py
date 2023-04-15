"""
.. module:: distances
   :platform: Unix, Windows
   :synopsis: A module for calculating distance measures with geohashes

.. moduleauthor:: Will McGinnis <will@pedalwrencher.com>


"""

import math
import statistics
from typing import Iterable, Callable, Generator, Literal, List

from pygeohash.distances import geohash_haversine_distance
from pygeohash.geohash import decode, encode, LatLong

__author__ = 'Will McGinnis'


def __latitude(coordinate: LatLong) -> float:
    return coordinate.latitude


def __longitude(coordinate: LatLong) -> float:
    return coordinate.longitude


def _max_cardinal(geohashes: Iterable[str], key: Callable[[LatLong], float], reverse: bool) -> str:
    """
    Takes in an iterable of geohashes and returns the furthest position of the group for the cardinality as a geohash.
    """
    coordinates: Generator[LatLong] = (decode(x) for x in geohashes)
    m = max if reverse else min
    coordinate = m(coordinates, key=key)
    return encode(coordinate.latitude, coordinate.longitude)


def northern(geohashes: Iterable[str]) -> str:
    """
    Takes in an iterable of geohashes and returns the northernmost position of the group as a geohash.

    :param geohashes:
    :return:
    """
    return _max_cardinal(geohashes, __latitude, reverse=True)


def eastern(geohashes: Iterable[str]) -> str:
    """
    Takes in an iterable of geohashes and returns the easternmost position of the group as a geohash.

    :param geohashes:
    :return:
    """
    return _max_cardinal(geohashes, __longitude, reverse=True)


def western(geohashes: Iterable[str]) -> str:
    """
    Takes in an iterable of geohashes and returns the westernmost position of the group as a geohash.

    :param geohashes:
    :return:
    """
    return _max_cardinal(geohashes, __longitude, reverse=False)


def southern(geohashes: Iterable[str]) -> str:
    """
    Takes in an iterable of geohashes and returns the southernmost position of the group as a geohash.

    :param geohashes:
    :return:
    """
    return _max_cardinal(geohashes, __latitude, reverse=False)


def mean(geohashes: Iterable[str]) -> str:
    """
    Takes in an iterable of geohashes and returns the mean position of the group as a geohash.

    :param geohashes:
    :return:
    """
    coordinates: List[LatLong] = [decode(x) for x in geohashes]
    return encode(
        statistics.mean(x.latitude for x in coordinates),
        statistics.mean(x.longitude for x in coordinates),
    )


def variance(geohashes: Iterable[str]) -> float:
    """
    Calculates the variance of a set of geohashes (in meters)

    :param geohashes:
    :return:
    """

    mean_v = mean(geohashes)
    dists = [geohash_haversine_distance(x, mean_v) for x in geohashes]
    var = sum([x ** 2 for x in dists]) / float(len(dists))
    return var


def std(geohashes: Iterable[str]) -> float:
    """
    Calculates the standard deviation of a set of geohashes (in meters)

    :param geohashes:
    :return:
    """

    return math.sqrt(variance(geohashes))
