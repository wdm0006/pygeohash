"""
.. module:: distances
   :platform: Unix, Windows
   :synopsis: A module for calculating distance measures with geohashes

.. moduleauthor:: Will McGinnis <will@pedalwrencher.com>


"""

import math
from typing import Iterable, Callable

from pygeohash.distances import geohash_haversine_distance
from pygeohash.geohash import decode, encode

__author__ = 'Will McGinnis'


def mean(geohashes: Iterable[str]) -> str:
    """
    Takes in an iterable of geohashes and returns the mean position of the group as a geohash.

    :param geohashes:
    :return:
    """

    latlons = [decode(x) for x in geohashes]
    count = len(latlons)
    return encode(float(sum([x[0] for x in latlons])) / count, float(sum([x[1] for x in latlons])) / count)


def _max_cardinal(geohashes: Iterable[str], key: Callable, reverse: bool) -> str:
    """
    Takes in an iterable of geohashes and returns the furthest position of the group for the cardinality as a geohash.
    """
    latlons = (decode(x) for x in geohashes)
    m = max if reverse else min
    lat_long = m(latlons, key=key)
    return encode(lat_long[0], lat_long[1])


def northern(geohashes: Iterable[str]) -> str:
    """
    Takes in an iterable of geohashes and returns the northernmost position of the group as a geohash.

    :param geohashes:
    :return:
    """
    return _max_cardinal(geohashes, lambda x: x[0], reverse=True)


def eastern(geohashes: Iterable[str]) -> str:
    """
    Takes in an iterable of geohashes and returns the easternmost position of the group as a geohash.

    :param geohashes:
    :return:
    """
    return _max_cardinal(geohashes, lambda x: x[1], reverse=True)


def western(geohashes: Iterable[str]) -> str:
    """
    Takes in an iterable of geohashes and returns the westernmost position of the group as a geohash.

    :param geohashes:
    :return:
    """
    return _max_cardinal(geohashes, lambda x: x[1], reverse=False)


def southern(geohashes: Iterable[str]) -> str:
    """
    Takes in an iterable of geohashes and returns the southernmost position of the group as a geohash.

    :param geohashes:
    :return:
    """
    return _max_cardinal(geohashes, lambda x: x[0], reverse=False)


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
