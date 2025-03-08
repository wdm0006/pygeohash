"""pygeohash: A Python module for geohash encoding and operations.

This module provides functionality for encoding and decoding geohashes,
calculating distances between geohashes, finding adjacent geohashes,
and performing statistical operations on collections of geohashes.

The module uses a high-performance C implementation for core geohash operations.

Attributes:
    __author__ (str): The author of the module.
    __all__ (list): List of public functions and classes exported by the module.
"""

from .bounding_box import (
    BoundingBox,
    do_boxes_intersect,
    geohashes_in_box,
    get_bounding_box,
    is_point_in_box,
    is_point_in_geohash,
)
from .distances import geohash_approximate_distance, geohash_haversine_distance
from .geohash import decode, decode_exactly, encode, encode_strictly
from .geohash_types import ExactLatLong, LatLong
from .neighbor import get_adjacent
from .stats import eastern, mean, northern, southern, std, variance, western

__author__ = "willmcginnis"

__all__ = [
    "geohash_approximate_distance",
    "geohash_haversine_distance",
    "LatLong",
    "ExactLatLong",
    "BoundingBox",
    "encode",
    "encode_strictly",
    "decode",
    "decode_exactly",
    "get_bounding_box",
    "is_point_in_box",
    "is_point_in_geohash",
    "do_boxes_intersect",
    "geohashes_in_box",
    "mean",
    "northern",
    "southern",
    "eastern",
    "western",
    "variance",
    "std",
    "get_adjacent",
]

# Try to import visualization functions if dependencies are available
try:
    from .viz import folium_map, plot_geohash, plot_geohashes

    __all__ += [
        "plot_geohash",
        "plot_geohashes",
        "folium_map",
    ]
except ImportError:
    pass
