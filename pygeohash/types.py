"""Type definitions for the pygeohash library.

This module provides a centralized location for all type definitions used
throughout the pygeohash library. It includes both the core types for
coordinates and bounding boxes, as well as type aliases for commonly used
parameter types.
"""

from __future__ import annotations

import re
import sys
from typing import Dict, Final, List, Literal, TypeVar, Union, Iterable, NewType, cast

# Re-export core types
from .geohash_types import LatLong, ExactLatLong
from .bounding_box import BoundingBox

# Type variables
T = TypeVar('T')

# Validation types
Geohash = NewType('Geohash', str)
Latitude = NewType('Latitude', float)
Longitude = NewType('Longitude', float)

# Validation constants
_GEOHASH_PATTERN: Final[re.Pattern] = re.compile(r'^[0123456789bcdefghjkmnpqrstuvwxyz]+$')

def is_valid_geohash(value: str) -> bool:
    """Check if a string is a valid geohash.
    
    A valid geohash:
    1. Contains only characters from the base32 alphabet (0-9, b-h, j-k, m-n, p-z)
    2. Has a length between 1 and 12 characters
    
    Args:
        value: The string to check
        
    Returns:
        bool: True if the string is a valid geohash
    """
    return bool(
        value and 
        len(value) <= 12 and 
        _GEOHASH_PATTERN.match(value)
    )

def is_valid_latitude(value: float) -> bool:
    """Check if a number is a valid latitude.
    
    A valid latitude is between -90 and 90 degrees inclusive.
    
    Args:
        value: The number to check
        
    Returns:
        bool: True if the number is a valid latitude
    """
    return -90 <= value <= 90

def is_valid_longitude(value: float) -> bool:
    """Check if a number is a valid longitude.
    
    A valid longitude is between -180 and 180 degrees inclusive.
    
    Args:
        value: The number to check
        
    Returns:
        bool: True if the number is a valid longitude
    """
    return -180 <= value <= 180

def assert_valid_geohash(value: str) -> Geohash:
    """Convert a string to a validated Geohash type.
    
    Args:
        value: The string to validate and convert
        
    Returns:
        Geohash: The validated geohash
        
    Raises:
        ValueError: If the string is not a valid geohash
    """
    if not is_valid_geohash(value):
        raise ValueError(
            f"Invalid geohash '{value}'. Geohashes must be 1-12 characters "
            "long and contain only characters from the base32 alphabet "
            "(0-9, b-h, j-k, m-n, p-z)"
        )
    return cast(Geohash, value)

def assert_valid_latitude(value: float) -> Latitude:
    """Convert a number to a validated Latitude type.
    
    Args:
        value: The number to validate and convert
        
    Returns:
        Latitude: The validated latitude
        
    Raises:
        ValueError: If the number is not a valid latitude
    """
    if not is_valid_latitude(value):
        raise ValueError(
            f"Invalid latitude {value}. Latitude must be between -90 and 90 degrees"
        )
    return cast(Latitude, value)

def assert_valid_longitude(value: float) -> Longitude:
    """Convert a number to a validated Longitude type.
    
    Args:
        value: The number to validate and convert
        
    Returns:
        Longitude: The validated longitude
        
    Raises:
        ValueError: If the number is not a valid longitude
    """
    if not is_valid_longitude(value):
        raise ValueError(
            f"Invalid longitude {value}. Longitude must be between -180 and 180 degrees"
        )
    return cast(Longitude, value)

# Optional NumPy and Pandas type definitions
if TYPE_CHECKING:
    try:
        import numpy as np
        import pandas as pd
        from numpy.typing import NDArray

        # NumPy array types
        GeohashArray = NDArray[np.str_]
        LatitudeArray = NDArray[np.float64]
        LongitudeArray = NDArray[np.float64]
        
        # Pandas types
        GeohashSeries = pd.Series[str]
        LatitudeSeries = pd.Series[float]
        LongitudeSeries = pd.Series[float]
        
        # DataFrame with geohash columns
        class GeohashDataFrame(pd.DataFrame):
            geohash: GeohashSeries
            latitude: LatitudeSeries
            longitude: LongitudeSeries
    except ImportError:
        # Define stub types for type checking when packages aren't available
        GeohashArray = List[str]
        LatitudeArray = List[float]
        LongitudeArray = List[float]
        GeohashSeries = List[str]
        LatitudeSeries = List[float]
        LongitudeSeries = List[float]
        GeohashDataFrame = Dict[str, List[Union[str, float]]]
else:
    # Runtime type aliases (simple types for when packages aren't available)
    GeohashArray = List[str]
    LatitudeArray = List[float]
    LongitudeArray = List[float]
    GeohashSeries = List[str]
    LatitudeSeries = List[float]
    LongitudeSeries = List[float]
    GeohashDataFrame = Dict[str, List[Union[str, float]]]

# Direction literals
Direction = Literal["right", "left", "top", "bottom"]

# Precision types
GeohashPrecision = Union[int, Literal[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]]

# Constants
EARTH_RADIUS: Final[float] = 6_371_000  # Earth's radius in meters

# Precision distance mapping
PRECISION_TO_ERROR: Final[Dict[int, float]] = {
    0: 20000000,  # 20000km error
    1: 5003530,   # ~5000km error
    2: 625441,    # ~625km error
    3: 123264,    # ~123km error
    4: 19545,     # ~19.5km error
    5: 3803,      # ~3.8km error
    6: 610,       # ~610m error
    7: 118,       # ~118m error
    8: 19,        # ~19m error
    9: 3.71,      # ~3.7m error
    10: 0.6,      # ~0.6m error
}

# Collection types
GeohashCollection = Iterable[str]
GeohashList = List[str]

__all__ = [
    # Core types
    'LatLong',
    'ExactLatLong',
    'BoundingBox',
    
    # Type variables
    'T',
    
    # Validation types
    'Geohash',
    'Latitude',
    'Longitude',
    
    # Validation functions
    'is_valid_geohash',
    'is_valid_latitude',
    'is_valid_longitude',
    'assert_valid_geohash',
    'assert_valid_latitude',
    'assert_valid_longitude',
    
    # Literals and unions
    'Direction',
    'GeohashPrecision',
    
    # Constants
    'EARTH_RADIUS',
    'PRECISION_TO_ERROR',
    
    # Collection types
    'GeohashCollection',
    'GeohashList',
    
    # NumPy and Pandas types
    'GeohashArray',
    'LatitudeArray',
    'LongitudeArray',
    'GeohashSeries',
    'LatitudeSeries',
    'LongitudeSeries',
    'GeohashDataFrame',
] 