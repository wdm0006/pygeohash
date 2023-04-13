"""
.. module:: distances
   :platform: Unix, Windows
   :synopsis: A module for calculating distance measures with geohashes

.. moduleauthor:: Will McGinnis <will@pedalwrencher.com>


"""

import math
from typing import Iterable

from pygeohash.distances import geohash_haversine_distance
from pygeohash.geohash import decode, encode

__author__ = 'Will McGinnis'


def mean(geohashes: Iterable[str]):
    """
    Takes in an iterable of geohashes and returns the mean position of the group as a geohash.

    :param geohashes:
    :return:
    """

    latlons = [decode(x) for x in geohashes]
    count = len(latlons)
    return encode(float(sum([x[0] for x in latlons])) / count, float(sum([x[1] for x in latlons])) / count)


def northern(geohashes: Iterable[str]):
    """
    Takes in an iterable of geohashes and returns the northernmost position of the group as a geohash.

    :param geohashes:
    :return:
    """

    latlons = (decode(x) for x in geohashes)
    latlons = sorted(latlons, key=lambda x: x[0], reverse=True)
    return encode(latlons[0][0], latlons[0][1])


def eastern(geohashes: Iterable[str]):
    """
    Takes in an iterable of geohashes and returns the easternmost position of the group as a geohash.

    :param geohashes:
    :return:
    """

    latlons = (decode(x) for x in geohashes)
    latlons = sorted(latlons, key=lambda x: x[1], reverse=True)
    return encode(latlons[0][0], latlons[0][1])


def western(geohashes: Iterable[str]):
    """
    Takes in an iterable of geohashes and returns the westernmost position of the group as a geohash.

    :param geohashes:
    :return:
    """

    latlons = (decode(x) for x in geohashes)
    latlons = sorted(latlons, key=lambda x: x[1], reverse=False)
    return encode(latlons[0][0], latlons[0][1])


def southern(geohashes):
    """
    Takes in an iterable of geohashes and returns the southernmost position of the group as a geohash.

    :param geohashes:
    :return:
    """

    latlons = [decode(x) for x in geohashes]
    latlons = sorted(latlons, key=lambda x: x[0], reverse=False)
    return encode(latlons[0][0], latlons[0][1])


def variance(geohashes: Iterable[str]):
    """
    Calculates the variance of a set of geohashes (in meters)

    :param geohashes:
    :return:
    """

    mean_v = mean(geohashes)
    dists = [geohash_haversine_distance(x, mean_v) for x in geohashes]
    var = sum([x ** 2 for x in dists]) / float(len(dists))
    return var


def std(geohashes: Iterable[str]):
    """
    Calculates the standard deviation of a set of geohashes (in meters)

    :param geohashes:
    :return:
    """

    return math.sqrt(variance(geohashes))
