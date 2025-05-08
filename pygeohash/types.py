"""Type definitions for the pygeohash library.

This module provides a centralized location for all type definitions used
throughout the pygeohash library. It includes both the core types for
coordinates and bounding boxes, as well as type aliases for commonly used
parameter types.
"""

from __future__ import annotations

from pygeohash.geohash_types import LatLong, ExactLatLong, GeohashPrecision
from pygeohash.bounding_box import BoundingBox

import re
from typing import Dict, Final, List, Literal, TypeVar, Union, Tuple, Collection
from typing import TYPE_CHECKING
import sys

from pygeohash.logging import get_logger

_HAS_NUMPY: bool = False
_HAS_PANDAS: bool = False

if TYPE_CHECKING:
    import numpy as np
    import numpy.typing as npt
    import pandas as pd
    from pandas import DataFrame, Series

    _HAS_NUMPY = True
    _HAS_PANDAS = True
else:
    # Optional dependencies for runtime
    try:
        import numpy as np
        import numpy.typing as npt

        _HAS_NUMPY = True
    except ImportError:

        class np:
            pass

        class npt:
            pass

    try:
        import pandas as pd
        from pandas import DataFrame, Series

        _HAS_PANDAS = True
    except ImportError:

        class DataFrame:
            pass

        class Series:
            pass

        class pd:
            pass


logger = get_logger(__name__)

# Type variables
T = TypeVar("T")

# Validation types
Geohash = str
Latitude = float
Longitude = float
Coordinate = Tuple[float, float]

# Validation constants
_GEOHASH_PATTERN: Final[re.Pattern] = re.compile(r"^[0123456789bcdefghjkmnpqrstuvwxyz]+$")

# Type definitions for numpy arrays
if TYPE_CHECKING:
    GeohashArray = "npt.NDArray[np.str_]"
    LatitudeArray = "npt.NDArray[np.float64]"
    LongitudeArray = "npt.NDArray[np.float64]"
else:
    if _HAS_NUMPY:
        GeohashArray = npt.NDArray[np.str_]
        LatitudeArray = npt.NDArray[np.float64]
        LongitudeArray = npt.NDArray[np.float64]
    else:

        class GeohashArray:
            pass

        class LatitudeArray:
            pass

        class LongitudeArray:
            pass


def is_valid_geohash(value: Union[str, object]) -> bool:
    """Validate if a string is a valid geohash.

    Args:
        value: String to validate

    Returns:
        bool: True if valid geohash, False otherwise
    """
    if not isinstance(value, str):
        return False

    valid_chars = set("0123456789bcdefghjkmnpqrstuvwxyz")
    return all(c in valid_chars for c in value.lower())


def is_valid_latitude(value: Union[float, int, object]) -> bool:
    """Validate if a number is a valid latitude.

    Args:
        value: Number to validate

    Returns:
        bool: True if valid latitude, False otherwise
    """
    if not isinstance(value, (int, float)):
        return False
    return -90 <= float(value) <= 90


def is_valid_longitude(value: Union[float, int, object]) -> bool:
    """Validate if a number is a valid longitude.

    Args:
        value: Number to validate

    Returns:
        bool: True if valid longitude, False otherwise
    """
    if not isinstance(value, (int, float)):
        return False
    return -180 <= float(value) <= 180


def assert_valid_geohash(value: str) -> Geohash:
    """Assert that a value is a valid geohash and return it typed.

    Args:
        value: Value to validate

    Returns:
        Geohash: The validated geohash

    Raises:
        ValueError: If value is not a valid geohash
    """
    if not is_valid_geohash(value):
        raise ValueError(f"Invalid geohash: {value}")
    return value


def assert_valid_latitude(value: Union[float, int]) -> Latitude:
    """Assert that a value is a valid latitude and return it typed.

    Args:
        value: Value to validate

    Returns:
        Latitude: The validated latitude

    Raises:
        ValueError: If value is not a valid latitude
    """
    if not is_valid_latitude(value):
        raise ValueError(f"Invalid latitude: {value}")
    return float(value)


def assert_valid_longitude(value: Union[float, int]) -> Longitude:
    """Assert that a value is a valid longitude and return it typed.

    Args:
        value: Value to validate

    Returns:
        Longitude: The validated longitude

    Raises:
        ValueError: If value is not a valid longitude
    """
    if not is_valid_longitude(value):
        raise ValueError(f"Invalid longitude: {value}")
    return float(value)


# Type checking helpers
def is_geohash_series(obj: object) -> bool:
    """Check if object is a pandas Series of geohashes."""
    if not _HAS_PANDAS:
        return False
    from pandas import Series

    return isinstance(obj, Series) and all(is_valid_geohash(str(x)) for x in obj)


def is_latitude_series(obj: object) -> bool:
    """Check if object is a pandas Series of latitudes."""
    if not _HAS_PANDAS:
        return False
    from pandas import Series

    return isinstance(obj, Series) and all(is_valid_latitude(x) for x in obj)


def is_longitude_series(obj: object) -> bool:
    """Check if object is a pandas Series of longitudes."""
    if not _HAS_PANDAS:
        return False
    from pandas import Series

    return isinstance(obj, Series) and all(is_valid_longitude(x) for x in obj)


def is_geohash_dataframe(obj: object) -> bool:
    """Check if object is a DataFrame with geohash columns."""
    if not _HAS_PANDAS:
        return False
    from pandas import DataFrame

    return isinstance(obj, DataFrame) and any(is_geohash_series(obj[col]) for col in obj.columns)


# Direction literals
Direction = Literal["right", "left", "top", "bottom"]

# Constants
EARTH_RADIUS: Final[float] = 6_371_000  # Earth's radius in meters

# Precision distance mapping
PRECISION_TO_ERROR: Final[Dict[int, float]] = {
    0: 20000000,  # 20000km error
    1: 5003530,  # ~5000km error
    2: 625441,  # ~625km error
    3: 123264,  # ~123km error
    4: 19545,  # ~19.5km error
    5: 3803,  # ~3.8km error
    6: 610,  # ~610m error
    7: 118,  # ~118m error
    8: 19,  # ~19m error
    9: 3.71,  # ~3.7m error
    10: 0.6,  # ~0.6m error
}

# Collection types
GeohashCollection = Collection[str]
GeohashList = List[str]

# Pandas type variables and aliases
if TYPE_CHECKING:
    GeohashSeriesType = TypeVar("GeohashSeriesType", bound="pd.Series[str]")
    LatitudeSeriesType = TypeVar("LatitudeSeriesType", bound="pd.Series[float]")
    LongitudeSeriesType = TypeVar("LongitudeSeriesType", bound="pd.Series[float]")
    GeohashDataFrameType = TypeVar("GeohashDataFrameType", bound="pd.DataFrame")
    if sys.version_info >= (3, 9):
        GeohashSeries = Series[str]
        LatitudeSeries = Series[float]
        LongitudeSeries = Series[float]
    else:
        GeohashSeries = Series
        LatitudeSeries = Series
        LongitudeSeries = Series
    GeohashDataFrame = DataFrame
else:
    GeohashSeries = Series
    LatitudeSeries = Series
    LongitudeSeries = Series
    GeohashDataFrame = DataFrame

__all__ = [
    # Core types
    "LatLong",
    "ExactLatLong",
    "BoundingBox",
    # Type variables
    "T",
    # Validation types
    "Geohash",
    "Latitude",
    "Longitude",
    # Validation functions
    "is_valid_geohash",
    "is_valid_latitude",
    "is_valid_longitude",
    "assert_valid_geohash",
    "assert_valid_latitude",
    "assert_valid_longitude",
    # Literals and unions
    "Direction",
    "GeohashPrecision",
    # Constants
    "EARTH_RADIUS",
    "PRECISION_TO_ERROR",
    # Collection types
    "GeohashCollection",
    "GeohashList",
    # NumPy and Pandas types
    "GeohashArray",
    "LatitudeArray",
    "LongitudeArray",
    "GeohashSeries",
    "LatitudeSeries",
    "LongitudeSeries",
    "GeohashDataFrame",
]
