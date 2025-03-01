"""Tests for the bounding box module."""

import pytest

from pygeohash import (
    BoundingBox,
    do_boxes_intersect,
    geohashes_in_box,
    get_bounding_box,
    is_point_in_box,
    is_point_in_geohash,
)
from pygeohash.geohash import encode


class TestBoundingBox:
    """Test class for bounding box operations."""

    def test_get_bounding_box(self):
        """Test the get_bounding_box function with various geohashes."""
        # Test with a precision 1 geohash
        bbox = get_bounding_box("u")
        assert isinstance(bbox, BoundingBox)
        assert bbox.min_lat < bbox.max_lat
        assert bbox.min_lon < bbox.max_lon
        assert -90 <= bbox.min_lat <= 90
        assert -180 <= bbox.min_lon <= 180
        assert -90 <= bbox.max_lat <= 90
        assert -180 <= bbox.max_lon <= 180

        # Test with a precision 6 geohash
        bbox = get_bounding_box("u4pruy")
        assert isinstance(bbox, BoundingBox)
        assert bbox.min_lat < bbox.max_lat
        assert bbox.min_lon < bbox.max_lon
        assert pytest.approx(bbox.min_lat, 0.001) == 57.649
        assert pytest.approx(bbox.min_lon, 0.001) == 10.407
        assert pytest.approx(bbox.max_lat, 0.001) == 57.649
        assert pytest.approx(bbox.max_lon, 0.001) == 10.407

        # Test with a precision 9 geohash (higher precision)
        bbox = get_bounding_box("u4pruydqq")
        assert isinstance(bbox, BoundingBox)
        assert bbox.min_lat < bbox.max_lat
        assert bbox.min_lon < bbox.max_lon

    def test_bounding_box_properties(self):
        """Test the properties of the BoundingBox named tuple."""
        bbox = BoundingBox(10.0, 20.0, 30.0, 40.0)
        assert bbox.min_lat == 10.0
        assert bbox.min_lon == 20.0
        assert bbox.max_lat == 30.0
        assert bbox.max_lon == 40.0

    def test_is_point_in_box(self):
        """Test the is_point_in_box function."""
        bbox = BoundingBox(10.0, 20.0, 30.0, 40.0)

        # Test point inside the box
        assert is_point_in_box(20.0, 30.0, bbox) is True

        # Test points on the edges
        assert is_point_in_box(10.0, 30.0, bbox) is True  # Min latitude
        assert is_point_in_box(30.0, 30.0, bbox) is True  # Max latitude
        assert is_point_in_box(20.0, 20.0, bbox) is True  # Min longitude
        assert is_point_in_box(20.0, 40.0, bbox) is True  # Max longitude

        # Test points outside the box
        assert is_point_in_box(9.9, 30.0, bbox) is False  # Below min latitude
        assert is_point_in_box(30.1, 30.0, bbox) is False  # Above max latitude
        assert is_point_in_box(20.0, 19.9, bbox) is False  # Below min longitude
        assert is_point_in_box(20.0, 40.1, bbox) is False  # Above max longitude

    def test_is_point_in_geohash(self):
        """Test the is_point_in_geohash function."""
        # Use a known geohash for testing
        geohash = "u4pruy"  # Somewhere in Denmark

        # Get the bounding box for reference
        bbox = get_bounding_box(geohash)

        # Test point inside the geohash
        center_lat = (bbox.min_lat + bbox.max_lat) / 2
        center_lon = (bbox.min_lon + bbox.max_lon) / 2
        assert is_point_in_geohash(center_lat, center_lon, geohash) is True

        # Test points outside the geohash
        assert is_point_in_geohash(bbox.min_lat - 1.0, center_lon, geohash) is False
        assert is_point_in_geohash(bbox.max_lat + 1.0, center_lon, geohash) is False
        assert is_point_in_geohash(center_lat, bbox.min_lon - 1.0, geohash) is False
        assert is_point_in_geohash(center_lat, bbox.max_lon + 1.0, geohash) is False

    def test_do_boxes_intersect(self):
        """Test the do_boxes_intersect function."""
        # Test boxes that intersect
        box1 = BoundingBox(10.0, 20.0, 30.0, 40.0)
        box2 = BoundingBox(20.0, 30.0, 40.0, 50.0)
        assert do_boxes_intersect(box1, box2) is True

        # Test boxes that touch at a corner
        box3 = BoundingBox(30.0, 40.0, 50.0, 60.0)
        assert do_boxes_intersect(box1, box3) is True

        # Test boxes that don't intersect
        box4 = BoundingBox(50.0, 60.0, 70.0, 80.0)
        assert do_boxes_intersect(box1, box4) is False

        # Test boxes where one is inside the other
        box5 = BoundingBox(15.0, 25.0, 25.0, 35.0)
        assert do_boxes_intersect(box1, box5) is True

    def test_geohashes_in_box(self):
        """Test the geohashes_in_box function."""
        # Create a small bounding box
        small_box = BoundingBox(57.649, 10.407, 57.650, 10.408)

        # Test with precision 5
        result_5 = geohashes_in_box(small_box, precision=5)
        assert isinstance(result_5, list)
        assert all(isinstance(gh, str) for gh in result_5)
        assert all(len(gh) == 5 for gh in result_5)

        # Test with precision 6
        result_6 = geohashes_in_box(small_box, precision=6)
        assert isinstance(result_6, list)
        assert all(isinstance(gh, str) for gh in result_6)
        assert all(len(gh) == 6 for gh in result_6)

        # Test that higher precision gives more geohashes
        # This might not always be true for very small boxes, but should be for most cases
        if len(set(result_5)) > 1:  # Only if the small box spans multiple precision 5 geohashes
            assert len(result_6) >= len(result_5)

        # Create a larger bounding box
        large_box = BoundingBox(57.0, 10.0, 58.0, 11.0)

        # Test with precision 3
        result_large = geohashes_in_box(large_box, precision=3)
        assert isinstance(result_large, list)
        assert all(isinstance(gh, str) for gh in result_large)
        assert all(len(gh) == 3 for gh in result_large)
        assert len(result_large) > 1  # Should span multiple geohashes

        # Test for interior geohashes
        # Create a box that's large enough to contain geohashes that don't touch the edges
        very_large_box = BoundingBox(40.0, -75.0, 42.0, -72.0)  # Roughly covers parts of NY, CT, NJ
        result_interior = geohashes_in_box(very_large_box, precision=3)

        # Get geohashes for the corners
        corner_geohashes = [
            encode(very_large_box.min_lat, very_large_box.min_lon, 3),  # Southwest
            encode(very_large_box.min_lat, very_large_box.max_lon, 3),  # Southeast
            encode(very_large_box.max_lat, very_large_box.min_lon, 3),  # Northwest
            encode(very_large_box.max_lat, very_large_box.max_lon, 3),  # Northeast
        ]

        # Verify that we have more geohashes than just the corners and edges
        # This is a simple heuristic to check that interior geohashes are included
        assert len(result_interior) > len(set(corner_geohashes))

        # Verify that at least one geohash is not on the edge
        # Get a point in the middle of the box
        mid_lat = (very_large_box.min_lat + very_large_box.max_lat) / 2
        mid_lon = (very_large_box.min_lon + very_large_box.max_lon) / 2
        mid_geohash = encode(mid_lat, mid_lon, 3)

        assert mid_geohash in result_interior
