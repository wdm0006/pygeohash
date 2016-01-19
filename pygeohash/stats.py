"""
.. module:: distances
   :platform: Unix, Windows
   :synopsis: A module for calculating distance measures with geohashes

.. moduleauthor:: Will McGinnis <will@pedalwrencher.com>


"""

from pygeohash.geohash import decode, encode

__author__ = 'Will McGinnis'


def mean(geohashes):
    """
    Takes in an iterable of geohashes and returns the mean position of the group as a geohash.

    :param geohashes:
    :return:
    """

    latlons = [decode(x) for x in geohashes]
    count = len(latlons)
    return encode(float(sum([x[0] for x in latlons])) / count, float(sum([x[1] for x in latlons])) / count)


def northern(geohashes):
    """
    Takes in an iterable of geohashes and returns the northernmost position of the group as a geohash.

    :param geohashes:
    :return:
    """

    latlons = [decode(x) for x in geohashes]
    latlons = sorted(latlons, key=lambda x: x[0], reverse=True)
    return encode(latlons[0][0], latlons[0][1])


def eastern(geohashes):
    """
    Takes in an iterable of geohashes and returns the easternmost position of the group as a geohash.

    :param geohashes:
    :return:
    """

    latlons = [decode(x) for x in geohashes]
    latlons = sorted(latlons, key=lambda x: x[1], reverse=True)
    return encode(latlons[0][0], latlons[0][1])


def western(geohashes):
    """
    Takes in an iterable of geohashes and returns the westernmost position of the group as a geohash.

    :param geohashes:
    :return:
    """

    latlons = [decode(x) for x in geohashes]
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