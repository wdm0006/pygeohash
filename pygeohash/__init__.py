"""
.. module:: pygeohash
   :platform: Unix, Windows
   :synopsis: A module for interacting with geohashes in python

.. moduleauthor:: Will McGinnis <will@pedalwrencher.com>


"""

from .distances import geohash_approximate_distance, geohash_haversine_distance
from .geohash import (
    ExactLatLong,
    LatLong,
    decode,
    decode_exactly,
    encode,
    encode_strictly,
)
from .neighbor import get_adjacent
from .stats import eastern, mean, northern, southern, std, variance, western

__author__ = "willmcginnis"

__all__ = [
    "geohash_approximate_distance",
    "geohash_haversine_distance",
    "LatLong",
    "ExactLatLong",
    "encode",
    "encode_strictly",
    "decode",
    "decode_exactly",
    "mean",
    "northern",
    "southern",
    "eastern",
    "western",
    "variance",
    "std",
    "get_adjacent",
]

try:
    # Soft dependency
    import numba
    import numpy

    from .nbgeohash import (
        nb_decode_exactly,
        nb_point_decode,
        nb_point_encode,
        nb_vector_decode,
        nb_vector_encode,
    )

    __all__ += [
        "nb_point_encode",
        "nb_point_decode",
        "nb_vector_encode",
        "nb_vector_decode",
        "nb_decode_exactly",
        "nb_point_decode",
        "nb_point_encode",
    ]

except ImportError:
    import logging

    logging.warning(
        "Numpy and Numba are soft dependencies to use the numba geohashing functions. \n"
        "Can only import/use native python functions."
    )
