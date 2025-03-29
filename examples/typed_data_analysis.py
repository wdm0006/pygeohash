"""Example demonstrating pygeohash's type system with Pandas and NumPy.

This example shows how to use pygeohash's type system to work with geospatial
data in a type-safe way using Pandas and NumPy. It demonstrates:

1. Creating and validating typed DataFrames
2. Working with NumPy arrays of coordinates
3. Converting between different data formats
4. Using type hints for better IDE support
"""

from typing import Union

import numpy as np
import pandas as pd

from pygeohash import (
    # Core types
    Latitude,
    Longitude,
    # Validation functions
    assert_valid_geohash,
    assert_valid_latitude,
    assert_valid_longitude,
    # Array types
    LatitudeArray,
    LongitudeArray,
    # Pandas types
    GeohashDataFrame,
    GeohashSeries,
    LatitudeSeries,
    LongitudeSeries,
    # Core functions
    encode,
)


def create_sample_data() -> GeohashDataFrame:
    """Create a sample GeohashDataFrame with San Francisco locations."""
    # Create raw data
    data = {
        "name": [
            "Golden Gate Bridge",
            "Alcatraz Island",
            "Fisherman's Wharf",
            "Oracle Park",
        ],
        "latitude": [
            37.8199,
            37.8270,
            37.8080,
            37.7786,
        ],
        "longitude": [
            -122.4783,
            -122.4230,
            -122.4177,
            -122.3893,
        ],
    }

    # Create DataFrame and validate coordinates
    df = pd.DataFrame(data)
    df["latitude"] = df["latitude"].apply(assert_valid_latitude)
    df["longitude"] = df["longitude"].apply(assert_valid_longitude)

    # Add geohash column
    df["geohash"] = df.apply(
        lambda row: assert_valid_geohash(encode(row["latitude"], row["longitude"], precision=7)), axis=1
    )

    # Convert to typed DataFrame
    return GeohashDataFrame(df)


def calculate_center_point(
    lats: Union[LatitudeArray, list[float]], lons: Union[LongitudeArray, list[float]]
) -> tuple[Latitude, Longitude]:
    """Calculate the center point of a set of coordinates.

    Args:
        lats: Array of latitudes
        lons: Array of longitudes

    Returns:
        tuple: (center_lat, center_lon)
    """
    # Convert to numpy arrays if needed
    lat_array = np.array(lats)
    lon_array = np.array(lons)

    # Calculate center (simple average for this example)
    center_lat = assert_valid_latitude(float(np.mean(lat_array)))
    center_lon = assert_valid_longitude(float(np.mean(lon_array)))

    return center_lat, center_lon


def main() -> None:
    """Run the example."""
    # Create sample data
    print("Creating sample data...")
    df = create_sample_data()

    # Demonstrate type safety
    print("\nAccessing typed columns:")
    geohashes: GeohashSeries = df.geohash
    latitudes: LatitudeSeries = df.latitude
    longitudes: LongitudeSeries = df.longitude

    print(f"First geohash: {geohashes.iloc[0]}")
    print(f"First coordinate: ({latitudes.iloc[0]}, {longitudes.iloc[0]})")

    # Convert to NumPy arrays
    print("\nConverting to NumPy arrays...")
    lat_array: LatitudeArray = latitudes.to_numpy()
    lon_array: LongitudeArray = longitudes.to_numpy()

    # Calculate center
    print("\nCalculating center point...")
    center_lat, center_lon = calculate_center_point(lat_array, lon_array)
    center_geohash = assert_valid_geohash(encode(center_lat, center_lon, precision=7))

    print(f"Center coordinate: ({center_lat}, {center_lon})")
    print(f"Center geohash: {center_geohash}")

    # Demonstrate error handling
    print("\nDemonstrating error handling...")
    try:
        # This will raise ValueError (invalid latitude)
        invalid_lat = assert_valid_latitude(91.0)
    except ValueError as e:
        print(f"Caught error: {e}")

    try:
        # This will raise ValueError (invalid geohash)
        invalid_geohash = assert_valid_geohash("invalid!")
    except ValueError as e:
        print(f"Caught error: {e}")


if __name__ == "__main__":
    main()
