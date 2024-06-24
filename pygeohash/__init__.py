"""
.. module:: pygeohash
   :platform: Unix, Windows
   :synopsis: A module for interacting with geohashes in python

.. moduleauthor:: Will McGinnis <will@pedalwrencher.com>


"""

from .distances import geohash_approximate_distance, geohash_haversine_distance
from .geohash import LatLong, ExactLatLong, encode, decode, decode_exactly
from .stats import mean, northern, southern, eastern, western, variance, std
from .neighbor import get_adjacent

__author__ = 'willmcginnis'

__all__ = [
    'geohash_approximate_distance',
    'geohash_haversine_distance',
    'LatLong',
    'ExactLatLong',
    'encode',
    'decode',
    'decode_exactly',
    'mean',
    'northern',
    'southern',
    'eastern',
    'western',
    'variance',
    'std',
    'get_adjacent',
]

try:
    # Soft dependency
    import numpy, numba
    from .nbgeohash import nb_decode_exactly, nb_point_decode, nb_point_encode, nb_vector_encode, nb_vector_decode
    __all__ += [
        'nb_vector_encode',
        'nb_vector_decode',
        'nb_decode_exactly',
        'nb_point_decode',
        'nb_point_encode'
    ]

except ImportError:
    import logging
    logging.warning(f"Numpy and Numba are soft dependencies to use the numba geohashing functions. \nCan only import/use native python functions.")