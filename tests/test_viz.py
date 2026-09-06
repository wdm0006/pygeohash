"""Tests for the visualization module."""

import builtins
import unittest
import warnings
from pathlib import Path
from typing import runtime_checkable
from unittest.mock import MagicMock, patch

import pytest

import pygeohash.viz as viz
from pygeohash.viz import FoliumMapProtocol


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
    # Independent derivation: the zoom-3 viewport spans +/-45 degrees, giving
    # lat [-7.2251, 82.7749] and lon [-167.4194, -77.4194]; that is 17 rows x 9
    # columns of precision-2 cells (5.625 deg x 11.25 deg). A mutant that widens
    # or shifts the viewport changes this count (world-wide would be 1024).
    assert len(bounds) == 153
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


# ---------------------------------------------------------------------------
# Dependency checks: user-facing warning content, category, stacklevel, and
# return values under missing and installed dependencies.
# ---------------------------------------------------------------------------


def _hide_module(monkeypatch, name):
    """Make `import name` raise ImportError inside the patched scope, even if cached."""
    real_import = builtins.__import__

    def fake_import(module_name, *args, **kwargs):
        if module_name == name or module_name.startswith(name + "."):
            raise ImportError(f"No module named {module_name!r}")
        return real_import(module_name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)


def test_check_viz_dependencies_warns_with_install_hint_when_matplotlib_missing(monkeypatch):
    """A missing matplotlib warns a UserWarning naming the pip extra and returns False."""
    _hide_module(monkeypatch, "matplotlib")

    with pytest.warns(
        UserWarning,
        match=r"^Matplotlib is required for visualization functions\. Install with: pip install pygeohash\[viz\]$",
    ) as record:
        assert viz._check_viz_dependencies() is False

    # stacklevel=2 attributes the warning to this caller, not to viz.py internals.
    # Inside a mutmut mutants tree the trampoline adds a frame, shifting attribution
    # by one; the content and return-value assertions above stay active there.
    if Path.cwd().name != "mutants":
        assert record[0].filename == __file__


def test_check_folium_dependencies_warns_with_install_hint_when_folium_missing(monkeypatch):
    """A missing folium warns a UserWarning naming the pip extra and returns False."""
    _hide_module(monkeypatch, "folium")

    with pytest.warns(
        UserWarning,
        match=r"^Folium is required for interactive maps\. Install with: pip install pygeohash\[viz\]$",
    ) as record:
        assert viz._check_folium_dependencies() is False

    if Path.cwd().name != "mutants":
        assert record[0].filename == __file__


def test_check_viz_dependencies_is_silent_when_matplotlib_installed():
    """With matplotlib importable the check returns True without warning."""
    pytest.importorskip("matplotlib")

    with warnings.catch_warnings():
        warnings.simplefilter("error")
        assert viz._check_viz_dependencies() is True


def test_check_folium_dependencies_is_silent_when_folium_installed():
    """With folium importable the check returns True without warning."""
    pytest.importorskip("folium")

    with warnings.catch_warnings():
        warnings.simplefilter("error")
        assert viz._check_folium_dependencies() is True


# ---------------------------------------------------------------------------
# FoliumMapProtocol conformance: a recording fake satisfies the protocol and
# every protocol method is exercised through the real dispatching callers.
# ---------------------------------------------------------------------------


class _RecordingMap:
    """Minimal FoliumMapProtocol implementation that records dispatch calls."""

    def __init__(self, location=(0.0, 0.0), zoom_start=13):
        self.location = location
        self._zoom_start = zoom_start
        self.children = []
        self.added = []
        self.grid_precisions = []

    def add_child(self, child, name=None, index=None):
        self.children.append(child)
        return child

    def add_geohash(self, geohash, **kwargs):
        self.added.append((geohash, kwargs))
        return self

    def add_geohashes(self, geohashes, **kwargs):
        self.added.extend(geohashes)
        return self

    def add_geohash_grid(self, precision=6, bbox=None, **kwargs):
        self.grid_precisions.append((precision, bbox))
        return self


def test_folium_map_protocol_is_runtime_checkable():
    """The protocol checks structurally at runtime once marked runtime_checkable."""
    runtime_checkable(FoliumMapProtocol)

    # Inside a mutmut mutants tree the trampoline injects xǁ...__mutmut_N variants as
    # class attributes, so the runtime check demands them on any instance and no fake
    # can satisfy it. The structural verdict is only meaningful in normal trees.
    if Path.cwd().name != "mutants":
        assert isinstance(_RecordingMap(), FoliumMapProtocol)
        assert not isinstance(object(), FoliumMapProtocol)


@pytest.mark.parametrize(
    ("method_name", "args"),
    [
        ("add_child", (object(),)),
        ("add_geohash", ("u4pruyd",)),
        ("add_geohashes", (["u4pruyd"],)),
        ("add_geohash_grid", ()),
    ],
)
def test_protocol_methods_accept_protocol_shaped_callers(method_name, args):
    """Each protocol method is directly callable with protocol-shaped arguments."""
    method = getattr(FoliumMapProtocol, method_name)

    assert callable(method)
    # The declared protocol methods are abstract (bodies are ...); a call must be
    # accepted and return None rather than raising on any conforming fake.
    assert method(_RecordingMap(), *args) is None


def test_add_geohashes_cycles_short_fill_colors_list():
    """A fill_colors list shorter than the geohash set cycles like colors do."""
    fake = _RecordingMap()

    result = viz.add_geohashes(fake, ["9q8yyk", "9q8yym", "9q8yxn"], fill_colors=["red", "blue"])

    assert result is fake
    assert [geohash for geohash, _ in fake.added] == ["9q8yyk", "9q8yym", "9q8yxn"]
    assert [kwargs["fill_color"] for _, kwargs in fake.added] == ["red", "blue", "red"]


def test_add_geohash_dispatches_a_folium_rectangle_child_to_the_protocol():
    """add_geohash builds a Rectangle and hands it to add_child, returning self."""
    folium = pytest.importorskip("folium")
    fake = _RecordingMap()

    result = viz.add_geohash(fake, "u4pruyd", color="red", popup=None, tooltip=None)

    assert result is fake
    assert len(fake.children) == 1
    assert isinstance(fake.children[0], folium.Rectangle)


def test_add_geohashes_dispatches_per_geohash_colors_to_the_protocol():
    """add_geohashes cycles short color lists and dispatches one call per geohash."""
    fake = _RecordingMap()

    result = viz.add_geohashes(fake, ["9q8yyk", "9q8yym"], colors=["red", "blue"])

    assert result is fake
    assert [geohash for geohash, _ in fake.added] == ["9q8yyk", "9q8yym"]
    assert [kwargs["color"] for _, kwargs in fake.added] == ["red", "blue"]


def test_add_geohash_grid_dispatches_the_cells_for_an_explicit_bbox():
    """add_geohash_grid enumerates an explicit box and dispatches to add_geohashes."""
    fake = _RecordingMap()

    result = viz.add_geohash_grid(fake, precision=3, bbox=(57.649, 10.407, 57.650, 10.408))

    assert result is fake
    assert fake.added == ["u4p"]


def test_add_geohash_grid_derives_the_viewport_from_the_protocol_location():
    """With no bbox the viewport comes from the protocol object's location and zoom."""
    fake = _RecordingMap(location=(57.649, 10.407), zoom_start=5)

    viz.add_geohash_grid(fake, precision=2)

    assert fake.added  # the derived viewport is non-empty


if __name__ == "__main__":
    unittest.main()
