"""
.. module:: distances
   :platform: Unix, Windows
   :synopsis: A module for calculating distance measures with geohashes

.. moduleauthor:: Will McGinnis <will@pedalwrencher.com>


"""

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


def geohash_approximate_distance(geohash_1, geohash_2):
    """
    Returns the approximate great-circle distance between two geohashes.

    :param geohash_1:
    :param geohash_2:
    :return:
    """

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