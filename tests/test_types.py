"""Tests for type validation functions in pygeohash.types."""

import pandas as pd
import pytest
from pygeohash.types import (
    assert_valid_latitude,
    assert_valid_longitude,
    is_geohash_dataframe,
    is_geohash_series,
    is_valid_geohash,
    is_valid_latitude,
    is_valid_longitude,
)

# Test cases for is_valid_latitude
# Format: (latitude, expected_result)
valid_latitude_cases = [
    (0.0, True),
    (45.0, True),
    (-45.0, True),
    (90.0, True),  # Upper boundary
    (-90.0, True),  # Lower boundary
    (90.000001, False),  # Just above upper boundary
    (-90.000001, False),  # Just below lower boundary
    (100.0, False),
    (-100.0, False),
    (45, True),  # Plain integers stay valid
    (-45, True),
    ("not a number", False),
    (None, False),
    (True, False),  # bool is a subclass of int but is not a coordinate
    (False, False),
]


@pytest.mark.parametrize("latitude, expected", valid_latitude_cases)
def test_is_valid_latitude(latitude, expected):
    """Test the is_valid_latitude function with various inputs."""
    assert is_valid_latitude(latitude) == expected


# Test cases for is_valid_geohash
# Format: (geohash_value, expected_result)
valid_geohash_cases = [
    # Valid geohashes
    ("gbsuv", True),
    ("u00000", True),
    ("000000000000", True),
    ("ezs42", True),
    ("EZS42", True),  # Case-insensitivity
    # Invalid characters
    ("gbsua", False),  # Contains 'a'
    ("gbsui", False),  # Contains 'i'
    ("gbsul", False),  # Contains 'l'
    ("gbsuo", False),  # Contains 'o'
    ("gbsuv ", False),  # Contains space
    ("gbsuv-", False),  # Contains hyphen
    ("", False),  # Empty string is invalid (length must be 1-12)
    ("a" * 13, False),  # Too long (>12 characters)
    # Invalid types
    (123, False),
    (0.0, False),
    (99.9, False),
    ([], False),
    ({}, False),
    (None, False),
    (True, False),
    (False, False),
]


@pytest.mark.parametrize("geohash_value, expected", valid_geohash_cases)
def test_is_valid_geohash(geohash_value, expected):
    """Test the is_valid_geohash function with various inputs."""
    assert is_valid_geohash(geohash_value) == expected


# Test cases for is_valid_longitude
# Format: (longitude, expected_result)
valid_longitude_cases = [
    (0.0, True),
    (90.0, True),
    (-90.0, True),
    (180.0, True),  # Upper boundary
    (-180.0, True),  # Lower boundary
    (180.000001, False),  # Just above upper boundary
    (-180.000001, False),  # Just below lower boundary
    (200.0, False),
    (-200.0, False),
    (90, True),  # Plain integers stay valid
    (-90, True),
    ("not a number", False),
    (None, False),
    (True, False),  # bool is a subclass of int but is not a coordinate
    (False, False),
]


@pytest.mark.parametrize("longitude, expected", valid_longitude_cases)
def test_is_valid_longitude(longitude, expected):
    """Test the is_valid_longitude function with various inputs."""
    assert is_valid_longitude(longitude) == expected


@pytest.mark.parametrize("value", [True, False])
def test_assert_valid_latitude_rejects_booleans(value):
    """assert_valid_latitude must not silently convert a bool into 1.0/0.0."""
    with pytest.raises(ValueError, match="Invalid latitude"):
        assert_valid_latitude(value)


@pytest.mark.parametrize("value", [True, False])
def test_assert_valid_longitude_rejects_booleans(value):
    """assert_valid_longitude must not silently convert a bool into 1.0/0.0."""
    with pytest.raises(ValueError, match="Invalid longitude"):
        assert_valid_longitude(value)


def test_assert_valid_coordinates_accept_integers():
    """Ordinary integer coordinates keep working and come back as floats."""
    assert assert_valid_latitude(45) == 45.0
    assert assert_valid_longitude(-120) == -120.0


def test_is_geohash_series_accepts_valid_strings():
    """A Series containing only geohash strings is valid."""
    assert is_geohash_series(pd.Series(["gbsuv", "u00000", "EZS42"])) is True


@pytest.mark.parametrize(
    "values",
    [
        [123],
        [1, 2, 3],
        [True],
        [False],
        ["gbsuv", 123],
        ["u00000", True],
    ],
)
def test_is_geohash_series_rejects_non_string_values(values):
    """Non-string values are not geohashes, even when their text would be valid."""
    assert is_geohash_series(pd.Series(values)) is False


@pytest.mark.parametrize("values", [[123], [1, 2, 3], [True], [False]])
def test_is_geohash_dataframe_rejects_non_string_columns(values):
    """Numeric-only and boolean-only DataFrames have no geohash column."""
    assert is_geohash_dataframe(pd.DataFrame({"id": values})) is False


def test_is_geohash_dataframe_accepts_valid_geohash_column():
    """A valid geohash string column is detected alongside non-geohash data."""
    dataframe = pd.DataFrame({"id": [123, 456], "geohash": ["gbsuv", "u00000"]})

    assert is_geohash_dataframe(dataframe) is True


# TODO: Add similar tests for is_valid_longitude and is_valid_geohash
# (Longitude boundaries: -180 to 180)
# (Geohash validation: check valid characters, maybe length constraints if applicable)
