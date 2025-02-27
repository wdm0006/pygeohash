"""
.. module:: distances
   :platform: Unix, Windows
   :synopsis: A module for calculating distance measures with geohashes

.. moduleauthor:: Will McGinnis <will@pedalwrencher.com>


"""

import math
from typing import Dict

from pygeohash.geohash import __base32, decode_exactly

__author__ = "Will McGinnis"

# the distance between geohashes based on matching characters, in meters.
_PRECISION: Dict[int, float] = {
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


def geohash_approximate_distance(geohash_1: str, geohash_2: str, check_validity: bool = False) -> float:
    """
    Returns the approximate great-circle distance between two geohashes in meters.

    :param geohash_1:
    :param geohash_2:
    :return:
    """

    if check_validity:
        if len([x for x in geohash_1 if x in __base32]) != len(geohash_1):
            raise ValueError(f"Geohash 1: {geohash_1} is not a valid geohash")

        if len([x for x in geohash_2 if x in __base32]) != len(geohash_2):
            raise ValueError(f"Geohash 2: {geohash_2} is not a valid geohash")

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
    matching = min(matching, 10)

    return _PRECISION[matching]


def geohash_haversine_distance(geohash_1: str, geohash_2: str) -> float:
    """
    converts the geohashes to lat/lon and then calculates the haversine great circle distance in meters.

    :param geohash_1:
    :param geohash_2:
    :return:
    """

    lat_1, lon_1, _, _ = decode_exactly(geohash_1)
    lat_2, lon_2, _, _ = decode_exactly(geohash_2)

    R = 6_371_000
    phi_1 = math.radians(lat_1)
    phi_2 = math.radians(lat_2)

    delta_phi = math.radians(lat_2 - lat_1)
    delta_lambda = math.radians(lon_2 - lon_1)

    a = math.sin(delta_phi / 2.0) * math.sin(delta_phi / 2.0) + math.cos(phi_1) * math.cos(phi_2) * math.sin(
        delta_lambda / 2
    ) * math.sin(delta_lambda / 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c
