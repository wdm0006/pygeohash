"""
.. module:: pygeohash
   :platform: Unix, Windows
   :synopsis: A module for interacting with geohashes in python

.. moduleauthor:: Will McGinnis <will@pedalwrencher.com>


"""

from .distances import geohash_approximate_distance, geohash_haversine_distance
from .geohash import encode, decode, decode_exactly
from .stats import mean, northern, southern, eastern, western, variance, std

__author__ = 'willmcginnis'

__all__ = [
    'geohash_approximate_distance',
    'geohash_haversine_distance',
    'encode',
    'decode',
    'decode_exactly',
    'mean',
    'northern',
    'southern',
    'eastern',
    'western',
    'variance',
    'std'
]

try:
    # Soft dependency
    import numpy, numba
    from .nbgeohash import nb_decode_exactly, nb_encode, nb_decode, nb_vector_encode, nb_vector_decode
    __all__ += [
        'nb_encode',
        'nb_decode',
        'nb_vector_encode',
        'nb_vector_decode',
        'nb_decode_exactly'
    ]

except ImportError:
    import logging
    logging.warn(f"Numpy and Numba are soft dependencies to use the numba geohashing functions. \nCan only import/use native python functions.")