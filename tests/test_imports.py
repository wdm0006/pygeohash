import importlib
import subprocess
import sys

import pytest

import pygeohash


@pytest.mark.parametrize("statement", ("import pygeohash", "from pygeohash.geohash import encode"))
def test_core_import_does_not_load_optional_modules(statement: str) -> None:
    script = f"""
import importlib.abc
import sys


class RejectOptional(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.split(".", 1)[0] in {{"numpy", "pandas", "matplotlib", "folium", "typing_extensions"}}:
            raise AssertionError("optional import attempted: " + fullname)


sys.meta_path.insert(0, RejectOptional())
sys.path.insert(0, ".")
{statement}
import pygeohash

assert pygeohash.encode(42.6, -5.6, precision=5) == "ezs42"
assert set(pygeohash.__all__) <= set(dir(pygeohash))
assert not {{
    "pygeohash.bounding_box",
    "pygeohash.distances",
    "pygeohash.neighbor",
    "pygeohash.stats",
    "pygeohash.types",
    "pygeohash.viz",
    "statistics",
}} & set(sys.modules)

get_bounding_box = pygeohash.get_bounding_box
assert get_bounding_box("ezs42").min_lat < 42.6
assert pygeohash.__dict__["get_bounding_box"] is get_bounding_box
assert "pygeohash.bounding_box" in sys.modules
assert not {{
    "pygeohash.distances",
    "pygeohash.neighbor",
    "pygeohash.stats",
    "pygeohash.types",
    "pygeohash.viz",
    "statistics",
}} & set(sys.modules)
"""
    subprocess.run((sys.executable, "-I", "-c", script), check=True)  # noqa: S603


def test_wildcard_import_keeps_visualization_dependencies_optional() -> None:
    script = """
import importlib.abc
import sys


class RejectVisualization(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.split(".", 1)[0] in {"matplotlib", "folium", "typing_extensions"}:
            raise AssertionError("visualization import attempted: " + fullname)


sys.meta_path.insert(0, RejectVisualization())
sys.path.insert(0, ".")
from pygeohash import *

assert callable(plot_geohash)
assert callable(plot_geohashes)
assert callable(folium_map)
"""
    subprocess.run((sys.executable, "-I", "-c", script), check=True)  # noqa: S603


def test_public_exports_match_their_implementations() -> None:
    exports = {
        "pygeohash.geohash": ("encode", "encode_strictly", "decode", "decode_exactly"),
        "pygeohash.geohash_types": ("LatLong", "ExactLatLong", "GeohashPrecision"),
        "pygeohash.bounding_box": (
            "BoundingBox",
            "get_bounding_box",
            "is_point_in_box",
            "is_point_in_geohash",
            "do_boxes_intersect",
            "geohashes_in_box",
        ),
        "pygeohash.distances": ("geohash_approximate_distance", "geohash_haversine_distance"),
        "pygeohash.neighbor": ("get_adjacent",),
        "pygeohash.stats": ("mean", "northern", "southern", "eastern", "western", "variance", "std"),
        "pygeohash.types": (
            "Direction",
            "GeohashCollection",
            "GeohashList",
            "Geohash",
            "Latitude",
            "Longitude",
            "LatitudeArray",
            "LongitudeArray",
            "GeohashArray",
            "GeohashSeries",
            "LatitudeSeries",
            "LongitudeSeries",
            "GeohashDataFrame",
            "EARTH_RADIUS",
            "PRECISION_TO_ERROR",
            "assert_valid_geohash",
            "assert_valid_latitude",
            "assert_valid_longitude",
            "is_valid_geohash",
            "is_valid_latitude",
            "is_valid_longitude",
        ),
        "pygeohash.logging": (
            "logger",
            "get_logger",
            "set_log_level",
            "add_stream_handler",
            "add_file_handler",
            "remove_all_handlers",
        ),
        "pygeohash.viz": ("plot_geohash", "plot_geohashes", "folium_map"),
    }

    assert set(pygeohash.__all__) == {name for names in exports.values() for name in names}
    assert len(pygeohash.__all__) == len(set(pygeohash.__all__))
    for module, names in exports.items():
        implementation = importlib.import_module(module)
        for name in names:
            assert getattr(pygeohash, name) is getattr(implementation, name)

    unknown = "not_an_export"
    with pytest.raises(AttributeError, match="has no attribute 'not_an_export'"):
        getattr(pygeohash, unknown)
