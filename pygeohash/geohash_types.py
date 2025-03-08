"""Type definitions for the geohash module.

This module provides type definitions used by both the pure Python and
C-extension implementations of the geohash functionality.
"""

from __future__ import annotations

from typing import NamedTuple


class LatLong(NamedTuple):
    """Named tuple representing a latitude/longitude coordinate pair.

    Attributes:
        latitude (float): The latitude coordinate in decimal degrees.
        longitude (float): The longitude coordinate in decimal degrees.
    """

    latitude: float
    longitude: float


class ExactLatLong(NamedTuple):
    """Named tuple representing a latitude/longitude coordinate pair with error margins.

    Attributes:
        latitude (float): The latitude coordinate in decimal degrees.
        longitude (float): The longitude coordinate in decimal degrees.
        latitude_error (float): The error margin for latitude in decimal degrees.
        longitude_error (float): The error margin for longitude in decimal degrees.
    """

    latitude: float
    longitude: float
    latitude_error: float
    longitude_error: float
