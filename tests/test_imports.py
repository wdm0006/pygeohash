from __future__ import annotations

import builtins
import importlib
import sys

import pytest

import pygeohash


def reject_imports(monkeypatch: pytest.MonkeyPatch, names: set[str]) -> None:
    original_import = builtins.__import__

    def guarded_import(name: str, *args: object, **kwargs: object) -> object:
        if name.split(".", 1)[0] in names:
            raise AssertionError("optional import attempted: " + name)
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", guarded_import)


@pytest.mark.parametrize("module_name", ("pygeohash", "pygeohash.geohash"))
def test_core_import_does_not_load_optional_modules(monkeypatch: pytest.MonkeyPatch, module_name: str) -> None:
    monkeypatch.delitem(sys.modules, "pygeohash", raising=False)
    if module_name != "pygeohash":
        monkeypatch.delitem(sys.modules, module_name, raising=False)

    reject_imports(monkeypatch, {"numpy", "pandas", "matplotlib", "folium", "typing_extensions"})
    module = importlib.import_module(module_name)

    assert module.encode(42.6, -5.6, precision=5) == "ezs42"
    if module_name == "pygeohash":
        assert set(module.__all__) <= set(dir(module))
        assert not set(module._LAZY_IMPORTS).intersection(module.__dict__)


def test_visualization_exports_keep_dependencies_optional(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delitem(sys.modules, "pygeohash", raising=False)
    monkeypatch.delitem(sys.modules, "pygeohash.viz", raising=False)
    reject_imports(monkeypatch, {"matplotlib", "folium", "typing_extensions"})
    package = importlib.import_module("pygeohash")

    for name in ("plot_geohash", "plot_geohashes", "folium_map"):
        assert callable(getattr(package, name))


def test_lazy_export_is_loaded_once_and_cached(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delitem(pygeohash.__dict__, "get_bounding_box", raising=False)
    imports: list[str] = []

    def import_and_record(name: str) -> object:
        imports.append(name)
        return importlib.import_module(name)

    monkeypatch.setattr(pygeohash, "import_module", import_and_record)

    get_bounding_box = pygeohash.get_bounding_box

    assert get_bounding_box("ezs42").min_lat < 42.6
    assert pygeohash.get_bounding_box is get_bounding_box
    assert imports == ["pygeohash.bounding_box"]


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
