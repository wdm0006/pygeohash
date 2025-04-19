"""Tests for type validation functions in pygeohash.types."""

import pytest
import pygeohash as pgh
from pygeohash.types import is_valid_latitude, is_valid_longitude, is_valid_geohash

# Test cases for is_valid_latitude
# Format: (latitude, expected_result)
valid_latitude_cases = [
    (0.0, True),
    (45.0, True),
    (-45.0, True),
    (90.0, True),         # Upper boundary
    (-90.0, True),        # Lower boundary
    (90.000001, False),   # Just above upper boundary
    (-90.000001, False),  # Just below lower boundary
    (100.0, False),
    (-100.0, False),
    ("not a number", False),
    (None, False),
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
    ("EZS42", True), # Case-insensitivity

    # Invalid characters
    ("gbsua", False), # Contains 'a'
    ("gbsui", False), # Contains 'i'
    ("gbsul", False), # Contains 'l'
    ("gbsuo", False), # Contains 'o'
    ("gbsuv ", False), # Contains space
    ("gbsuv-", False), # Contains hyphen
    ("", True),       # Empty string is technically valid by this check

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
    (180.0, True),        # Upper boundary
    (-180.0, True),       # Lower boundary
    (180.000001, False),  # Just above upper boundary
    (-180.000001, False), # Just below lower boundary
    (200.0, False),
    (-200.0, False),
    ("not a number", False),
    (None, False),
]

@pytest.mark.parametrize("longitude, expected", valid_longitude_cases)
def test_is_valid_longitude(longitude, expected):
    """Test the is_valid_longitude function with various inputs."""
    assert is_valid_longitude(longitude) == expected

# TODO: Add similar tests for is_valid_longitude and is_valid_geohash
# (Longitude boundaries: -180 to 180)
# (Geohash validation: check valid characters, maybe length constraints if applicable) 