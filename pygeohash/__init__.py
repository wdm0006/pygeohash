"""
.. module:: pygeohash
   :platform: Unix, Windows
   :synopsis: A module for interacting with geohashes in python

.. moduleauthor:: Will McGinnis <will@pedalwrencher.com>


"""

from pygeohash.distances import geohash_approximate_distance
from pygeohash.geohash import encode, decode, decode_exactly

__author__ = 'willmcginnis'

__all__ = [
    'geohash_approximate_distance',
    'encode',
    'decode',
    'decode_exactly'
]
