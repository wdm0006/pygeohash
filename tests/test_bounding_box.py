"""Tests for the bounding box module."""

import pytest

from pygeohash.bounding_box import (
    BoundingBox,
    do_boxes_intersect,
    geohashes_in_box,
    get_bounding_box,
    is_point_in_box,
    is_point_in_geohash,
)
from pygeohash.geohash import encode

# Fixed boxes whose corner cells were dropped before the corner pre-filter was removed.
# Each one omits at least one intersecting cell at both precision 5 and precision 6
# under the old implementation.
CORNER_BOXES = [
    BoundingBox(-9.825261385772734, 87.4279160521848, -9.748421102977142, 87.67290863932223),
    BoundingBox(-59.406, -75.466, -59.325, -75.276),
    BoundingBox(37.875, -114.057, 38.101, -113.685),
    BoundingBox(34.365, 67.075, 34.641, 67.47),
]


def _brute_force_geohashes(bbox: BoundingBox, precision: int, samples: int = 100) -> set:
    """Encode a dense grid of points inside ``bbox``; every result must be enumerated."""
    lat_span = bbox.max_lat - bbox.min_lat
    lon_span = bbox.max_lon - bbox.min_lon
    return {
        encode(
            bbox.min_lat + lat_span * i / (samples - 1),
            bbox.min_lon + lon_span * j / (samples - 1),
            precision,
        )
        for i in range(samples)
        for j in range(samples)
    }


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

    @pytest.mark.parametrize(
        "bbox",
        [
            BoundingBox(-90.0, 0.0, -89.9, 0.1),
            BoundingBox(89.9, 0.0, 90.0, 0.1),
            BoundingBox(0.0, -180.0, 0.1, -179.9),
            BoundingBox(0.0, 179.9, 0.1, 180.0),
        ],
    )
    def test_geohashes_in_box_at_world_boundaries(self, bbox):
        """Test boxes touching geographic limits return intersecting geohashes."""
        result = geohashes_in_box(bbox, precision=4)

        assert result
        assert all(do_boxes_intersect(bbox, get_bounding_box(geohash)) for geohash in result)

    @pytest.mark.parametrize(
        "bbox",
        CORNER_BOXES,
    )
    @pytest.mark.parametrize("precision", [5, 6])
    def test_geohashes_in_box_includes_corner_cells(self, bbox, precision):
        """The cells containing the box's own four corners must be returned."""
        result = geohashes_in_box(bbox, precision=precision)

        corners = {
            encode(bbox.min_lat, bbox.min_lon, precision),
            encode(bbox.min_lat, bbox.max_lon, precision),
            encode(bbox.max_lat, bbox.min_lon, precision),
            encode(bbox.max_lat, bbox.max_lon, precision),
        }
        assert corners <= set(result)

    @pytest.mark.parametrize(
        "bbox",
        CORNER_BOXES,
    )
    @pytest.mark.parametrize("precision", [5, 6])
    def test_geohashes_in_box_covers_brute_force_sampling(self, bbox, precision):
        """Every cell found by densely sampling the box interior must be returned."""
        result = set(geohashes_in_box(bbox, precision=precision))

        assert _brute_force_geohashes(bbox, precision) <= result
        # The candidate set is widened, but each returned cell must still intersect.
        assert all(do_boxes_intersect(bbox, get_bounding_box(geohash)) for geohash in result)

    @pytest.mark.parametrize(
        ("fields", "expected_message"),
        [
            # Inverted latitude.
            ((51.0, 10.0, 50.0, 11.0), "min_lat (51.0) must not exceed max_lat (50.0)"),
            # Inverted longitude.
            ((50.0, 11.0, 51.0, 10.0), "min_lon (11.0) must not exceed max_lon (10.0)"),
            # The grouped-argument mistake: (min_lat, max_lat, min_lon, max_lon).
            ((50.0, 51.0, 10.0, 11.0), "min_lat (50.0) must not exceed max_lat (10.0)"),
            # A box written to span the antimeridian, which is not supported.
            ((50.0, 179.0, 51.0, -179.0), "min_lon (179.0) must not exceed max_lon (-179.0)"),
        ],
    )
    def test_inverted_box_is_rejected(self, fields, expected_message):
        """An inverted box raises instead of silently yielding empty/False results."""
        with pytest.raises(ValueError) as excinfo:
            BoundingBox(*fields)

        assert expected_message in str(excinfo.value)

    def test_inverted_latitude_message_names_the_field_order(self):
        """The latitude error spells out the interleaved field order."""
        with pytest.raises(ValueError, match=r"fields are \(min_lat, min_lon, max_lat, max_lon\)"):
            BoundingBox(51.0, 10.0, 50.0, 11.0)

    def test_inverted_longitude_message_names_the_antimeridian(self):
        """The longitude error explains that antimeridian-spanning boxes are unsupported."""
        with pytest.raises(ValueError, match="antimeridian"):
            BoundingBox(50.0, 179.0, 51.0, -179.0)

    @pytest.mark.parametrize(
        "fields",
        [
            (50.0, 10.0, 50.0, 11.0),  # Degenerate latitude.
            (50.0, 10.0, 51.0, 10.0),  # Degenerate longitude.
            (50.0, 10.0, 50.0, 10.0),  # Degenerate on both axes.
        ],
    )
    def test_degenerate_box_is_accepted(self, fields):
        """A box whose minimum equals its maximum on either axis stays legal."""
        bbox = BoundingBox(*fields)

        assert tuple(bbox) == fields

    @pytest.mark.parametrize("field_index", range(4))
    @pytest.mark.parametrize("value", [float("nan"), float("inf"), float("-inf")])
    def test_non_finite_coordinate_is_rejected(self, field_index, value):
        """Every bounding-box field requires a finite coordinate."""
        fields = [10.0, 20.0, 30.0, 40.0]
        fields[field_index] = value

        with pytest.raises(ValueError, match="finite"):
            BoundingBox(*fields)

    @pytest.mark.parametrize(
        ("fields", "field"),
        [
            ((-90.1, 20.0, 30.0, 40.0), "min_lat"),
            ((10.0, -180.1, 30.0, 40.0), "min_lon"),
            ((10.0, 20.0, 90.1, 40.0), "max_lat"),
            ((10.0, 20.0, 30.0, 180.1), "max_lon"),
        ],
    )
    def test_out_of_range_coordinate_is_rejected(self, fields, field):
        """Each field is constrained to the geographic bounds for its axis."""
        with pytest.raises(ValueError, match=field):
            BoundingBox(*fields)

    @pytest.mark.parametrize("field_index", range(4))
    @pytest.mark.parametrize("value", [True, False])
    def test_boolean_coordinate_is_rejected(self, field_index, value):
        """No field accepts a boolean, even though ``bool`` is a subclass of ``int``."""
        fields = [10.0, 20.0, 30.0, 40.0]
        fields[field_index] = value

        with pytest.raises(ValueError, match="not a bool"):
            BoundingBox(*fields)

    @pytest.mark.parametrize("field_index", range(4))
    @pytest.mark.parametrize("value", [True, False])
    def test_make_rejects_boolean_coordinate(self, field_index, value):
        """``_make`` routes through ``__new__`` and cannot smuggle a boolean in."""
        fields = [10.0, 20.0, 30.0, 40.0]
        fields[field_index] = value

        with pytest.raises(ValueError, match="not a bool"):
            BoundingBox._make(fields)

    @pytest.mark.parametrize("field", ["min_lat", "min_lon", "max_lat", "max_lon"])
    @pytest.mark.parametrize("value", [True, False])
    def test_replace_rejects_boolean_coordinate(self, field, value):
        """``_replace`` cannot swap a validated coordinate for a boolean."""
        bbox = BoundingBox(10.0, 20.0, 30.0, 40.0)

        with pytest.raises(ValueError, match="not a bool"):
            bbox._replace(**{field: value})

    @pytest.mark.parametrize(
        "fields",
        [
            (10, 20, 30, 40),
            (0, 0, 1, 1),
            (-90, -180, 90, 180),
        ],
    )
    def test_integer_coordinates_are_accepted(self, fields):
        """Ordinary integers stay valid and keep their values; only ``bool`` is rejected."""
        bbox = BoundingBox(*fields)

        assert tuple(bbox) == fields

    @pytest.mark.parametrize(
        "fields",
        [
            (-90.0, -180.0, 90.0, 180.0),
            (-90.0, -180.0, -90.0, -180.0),
            (90.0, 180.0, 90.0, 180.0),
        ],
    )
    def test_world_boundaries_are_accepted(self, fields):
        """Exact world limits, including degenerate corner boxes, remain valid."""
        assert tuple(BoundingBox(*fields)) == fields

    @pytest.mark.parametrize("geohash", ["s", "ezs42", "u4pruyd", "u4pruydqqvj8"])
    def test_geohashes_in_box_on_degenerate_box_returns_containing_cell(self, geohash):
        """A zero-area box still enumerates the cell that contains it."""
        center = get_bounding_box(geohash)
        point_lat = (center.min_lat + center.max_lat) / 2
        point_lon = (center.min_lon + center.max_lon) / 2
        precision = len(geohash)
        degenerate = BoundingBox(point_lat, point_lon, point_lat, point_lon)

        result = sorted(geohashes_in_box(degenerate, precision=precision))

        assert encode(point_lat, point_lon, precision) in result

    def test_replace_validates_ordering(self):
        """``_replace`` routes through ``__new__`` rather than bypassing validation."""
        bbox = BoundingBox(10.0, 20.0, 30.0, 40.0)

        assert bbox._replace(max_lat=35.0) == BoundingBox(10.0, 20.0, 35.0, 40.0)
        with pytest.raises(ValueError, match="min_lat"):
            bbox._replace(max_lat=5.0)

    @pytest.mark.parametrize(
        "operation",
        [
            lambda bbox: bbox._replace(max_lon=float("inf")),
            lambda bbox: bbox._replace(max_lon=181.0),
            lambda bbox: BoundingBox._make((10.0, 20.0, float("nan"), 40.0)),
            lambda bbox: BoundingBox._make((10.0, -181.0, 30.0, 40.0)),
        ],
    )
    def test_make_and_replace_validate_coordinates(self, operation):
        """Named-tuple construction helpers cannot bypass coordinate validation."""
        with pytest.raises(ValueError):
            operation(BoundingBox(10.0, 20.0, 30.0, 40.0))

    @pytest.mark.parametrize("precision", range(1, 13))
    def test_get_bounding_box_output_is_always_constructible(self, precision):
        """No box the library produces itself may be rejected by the new validation."""
        for lat, lon in [
            (0.0, 0.0),
            (57.64911, 10.40744),
            (-33.8688, 151.2093),
            (89.9999, 179.9999),
            (-89.9999, -179.9999),
            (90.0, 180.0),
            (-90.0, -180.0),
        ]:
            bbox = get_bounding_box(encode(lat, lon, precision))
            # Reconstructing exercises __new__ on values get_bounding_box just produced.
            assert BoundingBox(*bbox) == bbox
