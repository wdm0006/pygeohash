"""
.. module:: distances
   :platform: Unix, Windows
   :synopsis: A module for calculating distance measures with geohashes

.. moduleauthor:: Will McGinnis <will@pedalwrencher.com>


"""

import math
from pygeohash.geohash import decode

__author__ = 'Will McGinnis'

# the distance between geohashes based on matching characters, in meters.
_PRECISION = {
    0: 20000000,
    1: 5003530,
    2: 625441,
    3: 123264,
    4: 19545,
    5: 3803,
    6: 610,
    7: 118,
    8: 19,
    9: 3.71,
    10: 0.6,
}
__base32 = '0123456789bcdefghjkmnpqrstuvwxyz'


def geohash_approximate_distance(geohash_1, geohash_2, check_validity=False):
    """
    Returns the approximate great-circle distance between two geohashes in meters.

    :param geohash_1:
    :param geohash_2:
    :return:
    """

    if check_validity:
        if len([x for x in geohash_1 if x in __base32]) != len(geohash_1):
            raise ValueError('Geohash 1: %s is not a valid geohash' % (geohash_1, ))

        if len([x for x in geohash_2 if x in __base32]) != len(geohash_2):
            raise ValueError('Geohash 2: %s is not a valid geohash' % (geohash_2, ))

    # normalize the geohashes to the length of the shortest
    len_1 = len(geohash_1)
    len_2 = len(geohash_2)
    if len_1 > len_2:
        geohash_1 = geohash_1[:len_2]
    elif len_2 > len_1:
        geohash_2 = geohash_2[:len_1]

    # find how many leading characters are matching
    matching = 0
    for g1, g2 in zip(geohash_1, geohash_2):
        if g1 == g2:
            matching += 1
        else:
            break

    # we only have precision metrics up to 10 characters
    if matching > 10:
        matching = 10

    return _PRECISION[matching]


def geohash_haversine_distance(geohash_1, geohash_2):
    """
    converts the geohashes to lat/lon and then calculates the haversine great circle distance in meters.

    :param geohash_1:
    :param geohash_2:
    :return:
    """

    lat_1, lon_1 = decode(geohash_1)
    lat_2, lon_2 = decode(geohash_2)

    R = 6371000
    phi_1 = math.radians(lat_1)
    phi_2 = math.radians(lat_2)

    delta_phi = math.radians(lat_2-lat_1)
    delta_lambda = math.radians(lon_2-lon_1)

    a = math.sin(delta_phi/2.0) * math.sin(delta_phi/2.0) + math.cos(phi_1) * math.cos(phi_2) * math.sin(delta_lambda/2) * math.sin(delta_lambda/2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

    return R * c