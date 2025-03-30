Type System
===========

The ``pygeohash`` library provides a comprehensive type system to help users write type-safe code and get better IDE support. This includes both basic types for working with geohashes and specialized types for NumPy and Pandas integration.

Core Types
---------

These are the fundamental types used throughout the library:

``LatLong``
    A named tuple representing a latitude/longitude coordinate pair:

    .. code-block:: python

        from pygeohash import LatLong

        location: LatLong = LatLong(latitude=37.7749, longitude=-122.4194)
        print(f"Latitude: {location.latitude}, Longitude: {location.longitude}")

``ExactLatLong``
    A named tuple that includes error margins for latitude and longitude:

    .. code-block:: python

        from pygeohash import ExactLatLong, decode_exactly

        exact_location: ExactLatLong = decode_exactly("9q9hwg")
        print(f"Lat: {exact_location.latitude} ± {exact_location.latitude_error}")
        print(f"Lon: {exact_location.longitude} ± {exact_location.longitude_error}")

``BoundingBox``
    A named tuple representing a geographical bounding box:

    .. code-block:: python

        from pygeohash import BoundingBox, get_bounding_box

        bbox: BoundingBox = get_bounding_box("9q9hwg")
        print(f"Min Lat: {bbox.min_lat}, Max Lat: {bbox.max_lat}")
        print(f"Min Lon: {bbox.min_lon}, Max Lon: {bbox.max_lon}")

Validation Types
--------------

The library provides special types and validation functions for geohashes and coordinates. These help catch errors early and make code more maintainable.

Validation Functions
~~~~~~~~~~~~~~~~~~

The library provides three pairs of validation functions:

1. Check functions that return boolean:
   - ``is_valid_geohash(value: str) -> bool``
   - ``is_valid_latitude(value: float) -> bool``
   - ``is_valid_longitude(value: float) -> bool``

2. Assertion functions that return validated types:
   - ``assert_valid_geohash(value: str) -> Geohash``
   - ``assert_valid_latitude(value: float) -> Latitude``
   - ``assert_valid_longitude(value: float) -> Longitude``

Basic Usage
~~~~~~~~~~

Here's how to use the validation functions:

.. code-block:: python

    from pygeohash import (
        Geohash, Latitude, Longitude,
        assert_valid_geohash, assert_valid_latitude, assert_valid_longitude,
        is_valid_geohash, is_valid_latitude, is_valid_longitude,
    )

    # Using check functions (returns bool)
    if is_valid_geohash("9q9hwg"):
        print("Valid geohash!")

    if is_valid_latitude(37.7749) and is_valid_longitude(-122.4194):
        print("Valid coordinates!")

    # Using assertion functions (returns validated type)
    try:
        geohash: Geohash = assert_valid_geohash("9q9hwg")
        lat: Latitude = assert_valid_latitude(37.7749)
        lon: Longitude = assert_valid_longitude(-122.4194)
    except ValueError as e:
        print(f"Validation failed: {e}")

Validation Rules
~~~~~~~~~~~~~~

The validation functions enforce the following rules:

1. Geohash validation:
   - Must contain only base32 characters (0-9, b-h, j-k, m-n, p-z)
   - Must be between 1 and 12 characters long
   - Cannot be empty or None

2. Latitude validation:
   - Must be between -90 and 90 degrees inclusive
   - Must be a valid float number

3. Longitude validation:
   - Must be between -180 and 180 degrees inclusive
   - Must be a valid float number

Best Practices
~~~~~~~~~~~~

Here are some recommended patterns for using the validation types:

1. Validate early:

.. code-block:: python

    from pygeohash import assert_valid_geohash, assert_valid_latitude, assert_valid_longitude

    def process_location(geohash: str, lat: float, lon: float) -> None:
        # Validate all inputs immediately at function start
        validated_geohash = assert_valid_geohash(geohash)
        validated_lat = assert_valid_latitude(lat)
        validated_lon = assert_valid_longitude(lon)
        
        # Rest of the function can assume valid data
        ...

2. Use type hints with validated types:

.. code-block:: python

    from pygeohash import Geohash, Latitude, Longitude

    def calculate_distance(
        geohash1: Geohash,
        lat: Latitude,
        lon: Longitude,
    ) -> float:
        # Function can assume inputs are already validated
        ...

3. Handle validation errors appropriately:

.. code-block:: python

    from pygeohash import assert_valid_geohash, is_valid_latitude, is_valid_longitude

    def safe_process_location(geohash: str, lat: float, lon: float) -> None:
        # Check without raising for coordinates
        if not is_valid_latitude(lat) or not is_valid_longitude(lon):
            print(f"Warning: Invalid coordinates ({lat}, {lon})")
            return

        try:
            # Assert for geohash (will raise if invalid)
            validated_geohash = assert_valid_geohash(geohash)
        except ValueError as e:
            print(f"Error: {e}")
            return

        # Process validated data
        ...

4. Use with NumPy and Pandas:

.. code-block:: python

    import numpy as np
    import pandas as pd
    from pygeohash import (
        assert_valid_geohash,
        assert_valid_latitude,
        assert_valid_longitude,
    )

    # Validate NumPy arrays
    def validate_coordinate_arrays(
        lats: np.ndarray,
        lons: np.ndarray,
    ) -> tuple[np.ndarray, np.ndarray]:
        # Vectorized validation
        valid_lats = np.logical_and(lats >= -90, lats <= 90)
        valid_lons = np.logical_and(lons >= -180, lons <= 180)
        
        if not np.all(valid_lats):
            raise ValueError("Invalid latitudes found")
        if not np.all(valid_lons):
            raise ValueError("Invalid longitudes found")
            
        return lats, lons

    # Validate Pandas Series
    def validate_geohash_series(s: pd.Series) -> pd.Series:
        # Apply validation to each element
        return s.apply(assert_valid_geohash)

Common Validation Errors
~~~~~~~~~~~~~~~~~~~~~

Here are the common validation errors you might encounter:

1. Invalid geohash format:

.. code-block:: python

    # These will raise ValueError
    assert_valid_geohash("")  # Empty string
    assert_valid_geohash("!")  # Invalid characters
    assert_valid_geohash("9q9hwg" * 3)  # Too long (>12 chars)

2. Invalid coordinate values:

.. code-block:: python

    # These will raise ValueError
    assert_valid_latitude(91)  # Above 90 degrees
    assert_valid_latitude(-91)  # Below -90 degrees
    assert_valid_longitude(181)  # Above 180 degrees
    assert_valid_longitude(-181)  # Below -180 degrees

Collection Types
--------------

The library provides type aliases for collections of geohashes:

``GeohashCollection``
    A generic iterable of geohash strings:

    .. code-block:: python

        from pygeohash import GeohashCollection, mean

        def calculate_center(geohashes: GeohashCollection) -> str:
            return mean(geohashes)

``GeohashList``
    A concrete list of geohash strings:

    .. code-block:: python

        from pygeohash import GeohashList

        geohashes: GeohashList = ["9q9hwg", "9q9hwy", "9q9hwv"]

NumPy Integration
---------------

For users working with NumPy arrays, the library provides specialized array types:

``GeohashArray``
    A NumPy array of geohash strings:

    .. code-block:: python

        import numpy as np
        from pygeohash import GeohashArray, encode

        # Create a grid of coordinates
        lats = np.array([37.7749, 37.7750, 37.7751])
        lons = np.array([-122.4194, -122.4195, -122.4196])
        
        # Convert to geohashes
        geohashes: GeohashArray = np.array([
            encode(lat, lon) for lat, lon in zip(lats, lons)
        ])

``LatitudeArray`` and ``LongitudeArray``
    NumPy arrays for latitude and longitude values:

    .. code-block:: python

        from pygeohash import LatitudeArray, LongitudeArray

        latitudes: LatitudeArray = np.array([37.7749, 37.7750, 37.7751])
        longitudes: LongitudeArray = np.array([-122.4194, -122.4195, -122.4196])

Pandas Integration
----------------

For users working with Pandas, the library provides specialized Series and DataFrame types:

``GeohashSeries``, ``LatitudeSeries``, and ``LongitudeSeries``
    Pandas Series for geohash strings and coordinates:

    .. code-block:: python

        import pandas as pd
        from pygeohash import GeohashSeries, LatitudeSeries, LongitudeSeries

        geohashes: GeohashSeries = pd.Series(["9q9hwg", "9q9hwy", "9q9hwv"])
        latitudes: LatitudeSeries = pd.Series([37.7749, 37.7750, 37.7751])
        longitudes: LongitudeSeries = pd.Series([-122.4194, -122.4195, -122.4196])

``GeohashDataFrame``
    A typed DataFrame with geohash-related columns:

    .. code-block:: python

        from pygeohash import GeohashDataFrame

        # Create a DataFrame with typed columns
        df = GeohashDataFrame({
            'geohash': ["9q9hwg", "9q9hwy", "9q9hwv"],
            'latitude': [37.7749, 37.7750, 37.7751],
            'longitude': [-122.4194, -122.4195, -122.4196]
        })

        # Type checking will ensure these columns exist and have correct types
        print(df.geohash)  # GeohashSeries
        print(df.latitude)  # LatitudeSeries
        print(df.longitude)  # LongitudeSeries

Utility Types
-----------

The library also includes utility types for specific purposes:

``Direction``
    A literal type for cardinal directions:

    .. code-block:: python

        from pygeohash import Direction, get_adjacent

        def get_neighbor(geohash: str, dir: Direction) -> str:
            return get_adjacent(geohash, dir)  # dir must be "right", "left", "top", or "bottom"

``GeohashPrecision``
    A type representing valid geohash precision values:

    .. code-block:: python

        from pygeohash import GeohashPrecision, encode

        def create_geohash(lat: float, lon: float, prec: GeohashPrecision = 6) -> str:
            return encode(lat, lon, prec)  # prec must be between 1 and 12

Type Safety and Fallbacks
-----------------------

The library's type system is designed to be both helpful and unobtrusive:

1. During development and type checking:
   - Full type information is available for IDE support
   - Type checkers will catch type-related errors

2. At runtime:
   - If NumPy/Pandas are not available, types fall back to standard Python types
   - No runtime overhead or dependencies are added

Example: Type-Safe Function
-------------------------

Here's an example of how to write a type-safe function that works with different input types:

.. code-block:: python

    from typing import Union
    from pygeohash import (
        GeohashCollection, GeohashArray, GeohashSeries,
        LatitudeArray, LongitudeArray,
        encode
    )

    def process_coordinates(
        lats: Union[LatitudeArray, list[float]],
        lons: Union[LongitudeArray, list[float]],
        precision: GeohashPrecision = 6
    ) -> GeohashCollection:
        """Process coordinates and return geohashes.
        
        Works with both NumPy arrays and Python lists.
        """
        return [encode(lat, lon, precision) for lat, lon in zip(lats, lons)]

This type system helps catch errors early, provides better IDE support, and makes the code more maintainable while remaining flexible for different use cases. 