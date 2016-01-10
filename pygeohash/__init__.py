"""
.. module:: pygeohash
   :platform: Unix, Windows
   :synopsis: A module for interacting with geohashes in python

.. moduleauthor:: Will McGinnis <will@pedalwrencher.com>


"""

from .distances import geohash_approximate_distance, geohash_haversine_distance
from .geohash import encode, decode, decode_exactly

__author__ = 'willmcginnis'

__all__ = [
    'geohash_approximate_distance',
    'geohash_haversine_distance',
    'encode',
    'decode',
    'decode_exactly'
]
