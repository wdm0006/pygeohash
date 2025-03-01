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


if __name__ == "__main__":
    unittest.main()
