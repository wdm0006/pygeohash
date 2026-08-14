"""Tests for the visualization module."""

import unittest
from unittest.mock import patch, MagicMock

import pytest


class TestViz(unittest.TestCase):
    """Test the visualization module."""

    def setUp(self):
        """Set up the test environment."""
        # Skip tests if matplotlib is not installed
        try:
            import matplotlib  # noqa: F401
        except ImportError:
            pytest.skip("Matplotlib not installed")

    @patch("pygeohash.viz._check_viz_dependencies")
    @patch("matplotlib.pyplot.subplots")
    @patch("pygeohash.viz.get_bounding_box")
    def test_plot_geohash(self, mock_get_bbox, mock_subplots, mock_check_deps):
        """Test the plot_geohash function."""
        # Mock dependencies check
        mock_check_deps.return_value = True

        # Mock matplotlib
        mock_fig = MagicMock()
        mock_ax = MagicMock()
        mock_subplots.return_value = (mock_fig, mock_ax)

        # Mock bounding box
        mock_bbox = MagicMock()
        mock_bbox.min_lat = 37.7
        mock_bbox.max_lat = 37.8
        mock_bbox.min_lon = -122.5
        mock_bbox.max_lon = -122.4
        mock_get_bbox.return_value = mock_bbox

        # Import the function
        from pygeohash.viz import plot_geohash

        # Call the function
        fig, ax = plot_geohash("9q8yyk")

        # Check that the function was called correctly
        mock_check_deps.assert_called_once()
        mock_subplots.assert_called_once()
        mock_get_bbox.assert_called_once_with("9q8yyk")

        # Check that the plot was created
        self.assertEqual(fig, mock_fig)
        self.assertEqual(ax, mock_ax)

        # Check that add_patch was called
        mock_ax.add_patch.assert_called_once()

        # Check that set_xlabel and set_ylabel were called
        mock_ax.set_xlabel.assert_called_once_with("Longitude")
        mock_ax.set_ylabel.assert_called_once_with("Latitude")

        # Check that set_title was called
        mock_ax.set_title.assert_called_once_with("Geohash: 9q8yyk")

        # Check that set_aspect was called
        mock_ax.set_aspect.assert_called_once_with("equal", "box")

    @patch("pygeohash.viz._check_viz_dependencies")
    @patch("matplotlib.pyplot.subplots")
    @patch("pygeohash.viz.get_bounding_box")
    def test_plot_geohashes(self, mock_get_bbox, mock_subplots, mock_check_deps):
        """Test the plot_geohashes function."""
        # Mock dependencies check
        mock_check_deps.return_value = True

        # Mock matplotlib
        mock_fig = MagicMock()
        mock_ax = MagicMock()
        mock_subplots.return_value = (mock_fig, mock_ax)

        # Mock bounding box
        mock_bbox = MagicMock()
        mock_bbox.min_lat = 37.7
        mock_bbox.max_lat = 37.8
        mock_bbox.min_lon = -122.5
        mock_bbox.max_lon = -122.4
        mock_get_bbox.return_value = mock_bbox

        # Import the function
        from pygeohash.viz import plot_geohashes

        # Call the function
        fig, ax = plot_geohashes(["9q8yyk", "9q8yym", "9q8yyj"])

        # Check that the function was called correctly
        mock_check_deps.assert_called_once()
        mock_subplots.assert_called_once()

        # Check that get_bounding_box was called for each geohash
        self.assertEqual(mock_get_bbox.call_count, 3)

        # Check that the plot was created
        self.assertEqual(fig, mock_fig)
        self.assertEqual(ax, mock_ax)

        # Check that add_patch was called for each geohash
        self.assertEqual(mock_ax.add_patch.call_count, 3)

        # Check that set_xlabel and set_ylabel were called
        mock_ax.set_xlabel.assert_called_once_with("Longitude")
        mock_ax.set_ylabel.assert_called_once_with("Latitude")

        # Check that set_title was called
        mock_ax.set_title.assert_called_once_with("Geohashes: 3")

        # Check that set_aspect was called
        mock_ax.set_aspect.assert_called_once_with("equal", "box")

    @patch("pygeohash.viz._check_folium_dependencies")
    @patch("pygeohash.viz.decode")
    @patch("folium.Map")
    def test_folium_map(self, mock_map, mock_decode, mock_check_deps):
        """Test the folium_map function."""
        # Skip test if folium is not installed
        try:
            import folium  # noqa: F401
        except ImportError:
            pytest.skip("Folium not installed")

        # Mock dependencies check
        mock_check_deps.return_value = True

        # Mock decode
        mock_decode.return_value = (37.7749, -122.4194)

        # Mock folium.Map
        mock_map_instance = MagicMock()
        mock_map.return_value = mock_map_instance

        # Import the function
        from pygeohash.viz import folium_map

        # Call the function with a geohash
        m = folium_map(center_geohash="9q8yyk")

        # Check that the function was called correctly
        mock_check_deps.assert_called_once()
        mock_decode.assert_called_once_with("9q8yyk")
        mock_map.assert_called_once()

        # Check that the map was created
        self.assertEqual(m, mock_map_instance)

        # Check that the map has the add_geohash method
        self.assertTrue(hasattr(m, "add_geohash"))

        # Check that the map has the add_geohashes method
        self.assertTrue(hasattr(m, "add_geohashes"))

        # Check that the map has the add_geohash_grid method
        self.assertTrue(hasattr(m, "add_geohash_grid"))

        # Call the function with coordinates
        mock_check_deps.reset_mock()
        mock_map.reset_mock()

        m = folium_map(center=(37.7749, -122.4194))

        # Check that the function was called correctly
        mock_check_deps.assert_called_once()
        mock_map.assert_called_once()

        # Check that decode was not called
        mock_decode.assert_called_once()  # Still just the one call from before

    def test_missing_dependencies(self):
        """Test behavior when dependencies are missing."""
        # Import the functions
        from pygeohash.viz import (
            plot_geohash,
            plot_geohashes,
            folium_map,
        )

        # Mock the dependency checks to return False
        with patch("pygeohash.viz._check_viz_dependencies", return_value=False):
            # Call the functions
            fig, ax = plot_geohash("9q8yyk")
            self.assertIsNone(fig)
            self.assertIsNone(ax)

            fig, ax = plot_geohashes(["9q8yyk", "9q8yym", "9q8yyj"])
            self.assertIsNone(fig)
            self.assertIsNone(ax)

        with patch("pygeohash.viz._check_folium_dependencies", return_value=False):
            # Call the function
            m = folium_map(center_geohash="9q8yyk")
            self.assertIsNone(m)


# (center, attribute of the world edge the clipped grid should reach, its value)
GRID_EDGE_CASES = [
    ((89.9, 0.0), "max_lat", 90.0),
    ((-89.9, 0.0), "min_lat", -90.0),
    ((0.0, 179.9), "max_lon", 180.0),
    ((0.0, -179.9), "min_lon", -180.0),
]

INVALID_GRID_BOXES = [
    (-100.0, -10.0, -95.0, 10.0),
    (-10.0, -200.0, 10.0, -190.0),
    (50.0, 179.0, 51.0, -179.0),
]


def _grid_rectangle_bounds(folium_module, geohash_map):
    """Collect ``(min_lat, min_lon, max_lat, max_lon)`` for every rectangle on the map."""
    return [
        (child.locations[0][0], child.locations[0][1], child.locations[1][0], child.locations[1][1])
        for child in geohash_map._children.values()
        if isinstance(child, folium_module.Rectangle)
    ]


@pytest.mark.parametrize("center, edge, edge_value", GRID_EDGE_CASES)
def test_add_geohash_grid_clips_generated_viewport(center, edge, edge_value):
    """A viewport derived near a world edge is clipped instead of raising."""
    folium = pytest.importorskip("folium")
    from pygeohash.viz import folium_map

    geohash_map = folium_map(center=center, zoom_start=3)
    geohash_map.add_geohash_grid(precision=2)

    bounds = _grid_rectangle_bounds(folium, geohash_map)
    assert len(bounds) > 0
    assert all(-90.0 <= min_lat <= max_lat <= 90.0 for min_lat, _, max_lat, _ in bounds)
    assert all(-180.0 <= min_lon <= max_lon <= 180.0 for _, min_lon, _, max_lon in bounds)

    reached = {
        "min_lat": min(bound[0] for bound in bounds),
        "min_lon": min(bound[1] for bound in bounds),
        "max_lat": max(bound[2] for bound in bounds),
        "max_lon": max(bound[3] for bound in bounds),
    }
    assert reached[edge] == edge_value


def test_add_geohash_grid_ordinary_viewport():
    """An ordinary central viewport still adds geohash rectangles."""
    folium = pytest.importorskip("folium")
    from pygeohash.viz import folium_map

    geohash_map = folium_map(center=(37.7749, -122.4194), zoom_start=3)
    geohash_map.add_geohash_grid(precision=2)

    bounds = _grid_rectangle_bounds(folium, geohash_map)
    assert len(bounds) > 0
    assert any(min_lat <= 37.7749 <= max_lat for min_lat, _, max_lat, _ in bounds)
    assert any(min_lon <= -122.4194 <= max_lon for _, min_lon, _, max_lon in bounds)


@pytest.mark.parametrize("bbox", INVALID_GRID_BOXES)
def test_add_geohash_grid_rejects_explicit_invalid_bbox(bbox):
    """An explicit caller-supplied box is still validated by BoundingBox."""
    pytest.importorskip("folium")
    from pygeohash.viz import folium_map

    geohash_map = folium_map(center=(0.0, 0.0), zoom_start=3)

    with pytest.raises(ValueError):
        geohash_map.add_geohash_grid(precision=2, bbox=bbox)


def test_plot_geohashes_rejects_empty_collection():
    """An empty geohash collection is rejected before matplotlib sees infinite axis limits."""
    pytest.importorskip("matplotlib")
    from pygeohash.viz import plot_geohashes

    with pytest.raises(ValueError, match="at least one geohash"):
        plot_geohashes([])


def test_plot_geohashes_rejects_empty_colors():
    """An empty color list is rejected instead of dividing by zero while cycling."""
    pytest.importorskip("matplotlib")
    from pygeohash.viz import plot_geohashes

    with pytest.raises(ValueError, match="non-empty list of colors"):
        plot_geohashes(["9q8yyk"], colors=[])


def test_plot_geohashes_cycles_short_color_list():
    """A short non-empty color list still cycles across a longer geohash list."""
    matplotlib = pytest.importorskip("matplotlib")
    matplotlib.use("Agg")
    from matplotlib.patches import Rectangle

    from pygeohash.viz import plot_geohashes

    fig, ax = plot_geohashes(["9q8yyk", "9q8yym", "9q8yyj"], colors=["red", "blue"])
    try:
        patches = [child for child in ax.get_children() if isinstance(child, Rectangle) and child.get_label()]
        assert [patch.get_edgecolor() for patch in patches] == [
            matplotlib.colors.to_rgba("red", 0.5),
            matplotlib.colors.to_rgba("blue", 0.5),
            matplotlib.colors.to_rgba("red", 0.5),
        ]
    finally:
        matplotlib.pyplot.close(fig)


@pytest.mark.parametrize("kwargs", [{"colors": []}, {"fill_colors": []}])
def test_add_geohashes_rejects_empty_style_lists(kwargs):
    """Empty color/fill-color lists are rejected instead of dividing by zero while cycling."""
    pytest.importorskip("folium")
    from pygeohash.viz import folium_map

    geohash_map = folium_map(center=(0.0, 0.0), zoom_start=3)

    with pytest.raises(ValueError, match="non-empty list of colors"):
        geohash_map.add_geohashes(["9q8yyk"], **kwargs)


def test_add_geohashes_cycles_short_color_list():
    """A short non-empty color list still cycles across a longer geohash list."""
    folium = pytest.importorskip("folium")
    from pygeohash.viz import folium_map

    geohash_map = folium_map(center=(0.0, 0.0), zoom_start=3)
    geohash_map.add_geohashes(["9q8yyk", "9q8yym", "9q8yyj"], colors=["red", "blue"])

    rectangles = [child for child in geohash_map._children.values() if isinstance(child, folium.Rectangle)]
    assert [rectangle.options["color"] for rectangle in rectangles] == ["red", "blue", "red"]


if __name__ == "__main__":
    unittest.main()
