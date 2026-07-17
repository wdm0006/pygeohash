"""pygeohash: A Python module for geohash encoding and operations.

This module provides functionality for encoding and decoding geohashes,
calculating distances between geohashes, finding adjacent geohashes,
and performing statistical operations on collections of geohashes.

The module uses a high-performance C implementation for core geohash operations.

Attributes:
    __author__ (str): The author of the module.
    __all__ (list): List of public functions and classes exported by the module.
"""

from importlib import import_module
from typing import TYPE_CHECKING, Dict, List

from pygeohash.geohash import decode, decode_exactly, encode, encode_strictly
from pygeohash.geohash_types import ExactLatLong, GeohashPrecision, LatLong
from pygeohash.logging import (
    add_file_handler,
    add_stream_handler,
    get_logger,
    logger,
    remove_all_handlers,
    set_log_level,
)

if TYPE_CHECKING:
    from pygeohash.bounding_box import (
        BoundingBox,
        do_boxes_intersect,
        geohashes_in_box,
        get_bounding_box,
        is_point_in_box,
        is_point_in_geohash,
    )
    from pygeohash.distances import geohash_approximate_distance, geohash_haversine_distance
    from pygeohash.neighbor import get_adjacent
    from pygeohash.stats import eastern, mean, northern, southern, std, variance, western
    from pygeohash.types import (
        EARTH_RADIUS,
        PRECISION_TO_ERROR,
        Direction,
        Geohash,
        GeohashArray,
        GeohashCollection,
        GeohashDataFrame,
        GeohashList,
        GeohashSeries,
        Latitude,
        LatitudeArray,
        LatitudeSeries,
        Longitude,
        LongitudeArray,
        LongitudeSeries,
        assert_valid_geohash,
        assert_valid_latitude,
        assert_valid_longitude,
        is_valid_geohash,
        is_valid_latitude,
        is_valid_longitude,
    )
    from pygeohash.viz import folium_map, plot_geohash, plot_geohashes

__author__ = "willmcginnis"

__all__ = [
    # Core functions
    "encode",
    "encode_strictly",
    "decode",
    "decode_exactly",
    # Distance calculations
    "geohash_approximate_distance",
    "geohash_haversine_distance",
    # Types
    "LatLong",
    "ExactLatLong",
    "BoundingBox",
    "Direction",
    "GeohashPrecision",
    "GeohashCollection",
    "GeohashList",
    "Geohash",
    "Latitude",
    "Longitude",
    "LatitudeArray",
    "LongitudeArray",
    "GeohashArray",
    "GeohashSeries",
    "LatitudeSeries",
    "LongitudeSeries",
    "GeohashDataFrame",
    # Constants
    "EARTH_RADIUS",
    "PRECISION_TO_ERROR",
    # Bounding box operations
    "get_bounding_box",
    "is_point_in_box",
    "is_point_in_geohash",
    "do_boxes_intersect",
    "geohashes_in_box",
    # Statistical operations
    "mean",
    "northern",
    "southern",
    "eastern",
    "western",
    "variance",
    "std",
    # Neighbor operations
    "get_adjacent",
    # Validation functions
    "assert_valid_geohash",
    "assert_valid_latitude",
    "assert_valid_longitude",
    "is_valid_geohash",
    "is_valid_latitude",
    "is_valid_longitude",
    # Logging functions
    "logger",
    "get_logger",
    "set_log_level",
    "add_stream_handler",
    "add_file_handler",
    "remove_all_handlers",
    # Visualization functions
    "plot_geohash",
    "plot_geohashes",
    "folium_map",
]

_LAZY_IMPORTS: Dict[str, str] = {
    name: module
    for module, names in (
        (
            "pygeohash.bounding_box",
            (
                "BoundingBox",
                "do_boxes_intersect",
                "geohashes_in_box",
                "get_bounding_box",
                "is_point_in_box",
                "is_point_in_geohash",
            ),
        ),
        ("pygeohash.distances", ("geohash_approximate_distance", "geohash_haversine_distance")),
        ("pygeohash.neighbor", ("get_adjacent",)),
        ("pygeohash.stats", ("eastern", "mean", "northern", "southern", "std", "variance", "western")),
        (
            "pygeohash.types",
            (
                "EARTH_RADIUS",
                "PRECISION_TO_ERROR",
                "Direction",
                "Geohash",
                "GeohashArray",
                "GeohashCollection",
                "GeohashDataFrame",
                "GeohashList",
                "GeohashSeries",
                "Latitude",
                "LatitudeArray",
                "LatitudeSeries",
                "Longitude",
                "LongitudeArray",
                "LongitudeSeries",
                "assert_valid_geohash",
                "assert_valid_latitude",
                "assert_valid_longitude",
                "is_valid_geohash",
                "is_valid_latitude",
                "is_valid_longitude",
            ),
        ),
        ("pygeohash.viz", ("folium_map", "plot_geohash", "plot_geohashes")),
    )
    for name in names
}


def __getattr__(name: str) -> object:
    module = _LAZY_IMPORTS.get(name)
    if module is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    value: object = getattr(import_module(module), name)
    globals()[name] = value
    return value


def __dir__() -> List[str]:
    return sorted(set(globals()) | set(__all__))
