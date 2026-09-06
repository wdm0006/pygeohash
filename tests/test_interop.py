"""Property, boundary, and golden-vector tests for pygeohash.interop.

The property tests re-derive the two grid geometries independently of the
module under test: the Web Mercator row/centre formulas, the Bing quadkey
digit algorithm, and the interleaved-bit longitude column are all implemented
here from their specifications, so an error shared with ``pygeohash.interop``
cannot hide. Golden vectors in ``tests/fixtures/interop_vectors.json`` were
generated once against mercantile and the Bing spec's worked examples (see
``tests/fixtures/generate_interop_vectors.py``).

Two documented geometric facts shape the assertions (module docstring of
``pygeohash.interop`` has the full story):

- Longitude is bit-exact between the grids; latitude is not. Equirectangular
  geohash latitude bands and real Web Mercator rows are different partitions
  of the axis, so latitude round trips are lossy by nature.
- Geohash cells cover +/-90 degrees but slippy rows only cover
  +/-85.05112878 degrees; ``clip=True`` is the only sanctioned bridging.
"""

from __future__ import annotations

import json
import math
import random
from pathlib import Path

import pytest

import pygeohash
from pygeohash import Tile, interop

FIXTURE = Path(__file__).parent / "fixtures" / "interop_vectors.json"
BASE32 = "0123456789bcdefghjkmnpqrstuvwxyz"
WEB_MERCATOR_LAT_LIMIT = 85.05112878

# Fixed seed: property tests must be reproducible; a failure reported by CI
# has to fail identically locally. Not security-sensitive (S311 is expected).
RNG = random.Random(20260906)  # noqa: S311


def _random_cell(precision: int) -> str:
    return "".join(RNG.choice(BASE32) for _ in range(precision))


def _random_tile(zoom: int) -> tuple[int, int, int]:
    side = 1 << zoom
    return RNG.randrange(side), RNG.randrange(side), zoom


# --- independent implementations of the two grid geometries -----------------


def _mercator_edge_lat(row_boundary: int, zoom: int) -> float:
    """Latitude of a tile-row boundary (mercantile formula), degrees."""
    mercator_y = 1.0 - 2.0 * row_boundary / (1 << zoom)
    return math.degrees(math.atan(math.sinh(math.pi * mercator_y)))


def _mercator_centre_lat(y: int, zoom: int) -> float:
    """Latitude of the centre of tile row ``y`` (true Mercator midpoint).

    Evaluated at the midpoint of the row in Mercator space, NOT averaged in
    latitude - the two differ away from the equator and only the true
    Mercator midpoint is the centre the containment law speaks of.
    """
    mercator_top = 1.0 - 2.0 * y / (1 << zoom)
    mercator_bottom = 1.0 - 2.0 * (y + 1) / (1 << zoom)
    return math.degrees(math.atan(math.sinh(math.pi * (mercator_top + mercator_bottom) / 2.0)))


def _tile_contains_point(x: int, y: int, zoom: int, lat: float, lon: float) -> bool:
    """True when the point lies inside the tile's lat/lon bounds (edges inclusive)."""
    lat_top = _mercator_edge_lat(y, zoom)
    lat_bottom = _mercator_edge_lat(y + 1, zoom)
    span = 360.0 / (1 << zoom)
    lon_west = x * span - 180.0
    lon_east = (x + 1) * span - 180.0
    return lat_bottom <= lat <= lat_top and lon_west <= lon <= lon_east


def _bing_quadkey(x: int, y: int, zoom: int) -> str:
    """Quadkey per the Bing Maps Tile System spec: digit = x_bit + 2*y_bit."""
    digits = []
    for level in range(zoom, 0, -1):
        bitmask = 1 << (level - 1)
        digits.append(str(int(bool(x & bitmask)) + 2 * int(bool(y & bitmask))))
    return "".join(digits)


def _longitude_column(geohash: str, zoom: int) -> int:
    """Column of a geohash cell at ``zoom`` from its interleaved bit stream."""
    bits = 0
    for character in geohash.lower():
        bits = (bits << 5) | BASE32.index(character)
    column = 0
    lon_bits = math.ceil(5 * len(geohash) / 2)
    for position in range(lon_bits):
        bit = (bits >> (5 * len(geohash) - 1 - 2 * position)) & 1
        column = (column << 1) | bit
    return column >> (lon_bits - zoom) if lon_bits >= zoom else column << (zoom - lon_bits)


# --- golden vectors ----------------------------------------------------------


def test_fixture_replays_geohash_to_tile():
    for i, vector in enumerate(_load_fixture()["to_tile"]):
        assert interop.geohash_to_tile(vector["g"]) == Tile(vector["x"], vector["y"], vector["z"]), i


def test_fixture_replays_geohash_to_quadkey():
    for i, vector in enumerate(_load_fixture()["to_quadkey"]):
        assert interop.geohash_to_quadkey(vector["g"]) == vector["qk"], i


def test_fixture_replays_quadkey_to_geohash():
    for i, vector in enumerate(_load_fixture()["from_quadkey"]):
        if vector["p"] is None:
            assert interop.quadkey_to_geohash(vector["q"]) == vector["g"], i
        else:
            assert interop.quadkey_to_geohash(vector["q"], vector["p"]) == vector["g"], i


def test_fixture_replays_tile_to_geohash():
    for i, vector in enumerate(_load_fixture()["from_tile"]):
        if vector["p"] is None:
            assert interop.tile_to_geohash(vector["x"], vector["y"], vector["z"]) == vector["g"], i
        else:
            assert interop.tile_to_geohash(vector["x"], vector["y"], vector["z"], vector["p"]) == vector["g"], i


def test_fixture_replays_polar_raise_and_clip():
    for i, vector in enumerate(_load_fixture()["polar_raises"]):
        with pytest.raises(ValueError, match="85.05112878"):
            interop.geohash_to_tile(vector["g"])
        tile = interop.geohash_to_tile(vector["g"], clip=True)
        assert tile == Tile(vector["clip_x"], vector["clip_y"], vector["clip_z"]), i


def test_fixture_replays_integer_form():
    vectors = _load_fixture()
    for i, vector in enumerate(vectors["to_int"]):
        assert interop.geohash_to_int(vector["g"]) == vector["v"], i
    for i, vector in enumerate(vectors["from_int"]):
        assert interop.geohash_from_int(vector["v"], vector["p"]) == vector["g"], i


def test_fixture_bing_worked_example_quadkey():
    """Bing Maps Tile System spec: tile (3, 5, 3) has quadkey '213'."""
    vectors = _load_fixture()
    match = [v for v in vectors["from_quadkey"] if v["q"] == "213"]
    assert match and match[0]["g"] == interop.quadkey_to_geohash("213")


# --- alignment law: zoom mapping (exact, every precision and zoom) -----------


@pytest.mark.parametrize("precision", range(1, 13))
def test_geohash_to_tile_zoom_is_floor_5p_over_2(precision):
    zoom = (5 * precision) // 2
    for _ in range(24):
        cell = _random_cell(precision)
        if abs(pygeohash.decode(cell)[0]) > WEB_MERCATOR_LAT_LIMIT:
            continue  # polar cells are covered by the dedicated raise/clip tests
        assert interop.geohash_to_tile(cell).zoom == zoom, cell


@pytest.mark.parametrize("zoom", range(0, 31))
def test_default_precision_is_ceil_2z_over_5(zoom):
    expected = max(1, math.ceil(2 * zoom / 5))
    assert len(interop.tile_to_geohash(0, 0, zoom)) == expected
    assert len(interop.quadkey_to_geohash("0" * zoom)) == expected


# --- alignment law: longitude bit-exactness (identity in longitude) ----------


@pytest.mark.parametrize("precision", range(1, 13))
def test_geohash_to_tile_column_matches_bit_model(precision):
    zoom = (5 * precision) // 2
    for _ in range(24):
        cell = _random_cell(precision)
        centre = pygeohash.decode(cell)
        if abs(centre[0]) > WEB_MERCATOR_LAT_LIMIT:
            continue
        tile = interop.geohash_to_tile(cell)
        assert tile.x == _longitude_column(cell, zoom), cell


@pytest.mark.parametrize("zoom", [2, 4, 5, 7, 10, 12, 15, 20, 25, 30])
def test_tile_to_geohash_to_tile_preserves_column_exactly(zoom):
    for _ in range(40):
        x, y, _ = _random_tile(zoom)
        cell = interop.tile_to_geohash(x, y, zoom)
        if abs(pygeohash.decode(cell)[0]) > WEB_MERCATOR_LAT_LIMIT:
            # The containing cell can straddle the Mercator band even when the
            # tile centre is in-band; the back conversion then raises by the
            # polar policy, which the dedicated polar tests cover.
            continue
        back = interop.geohash_to_tile(cell)
        # The back conversion may be at a finer default zoom; expand its exact
        # column to the original zoom. A west-half cell (tie rule) still
        # expands to the source column: (2 * x) >> 1 == x.
        assert back.x >> (back.zoom - zoom) == x, (x, y, zoom, cell)


# --- alignment law: containment (exact, both directions) ---------------------


@pytest.mark.parametrize("precision", range(1, 13))
def test_geohash_to_tile_contains_cell_centre(precision):
    for _ in range(24):
        cell = _random_cell(precision)
        lat, lon = pygeohash.decode(cell)
        if abs(lat) > WEB_MERCATOR_LAT_LIMIT:
            continue
        tile = interop.geohash_to_tile(cell)
        assert _tile_contains_point(tile.x, tile.y, tile.zoom, lat, lon), cell


@pytest.mark.parametrize("zoom", range(0, 31, 2))
def test_tile_to_geohash_contains_tile_centre(zoom):
    for _ in range(20):
        x, y, _ = _random_tile(zoom)
        cell = interop.tile_to_geohash(x, y, zoom)
        box = pygeohash.get_bounding_box(cell)
        centre_lat = _mercator_centre_lat(y, zoom)
        centre_lon = (2 * x + 1) * 180.0 / (1 << zoom) - 180.0
        assert box.min_lat <= centre_lat <= box.max_lat, (x, y, zoom, cell)
        assert box.min_lon <= centre_lon <= box.max_lon, (x, y, zoom, cell)


def test_quadkey_to_geohash_contains_tile_centre():
    for _ in range(60):
        x, y, zoom = _random_tile(RNG.randrange(0, 16))
        cell = interop.quadkey_to_geohash(_bing_quadkey(x, y, zoom))
        box = pygeohash.get_bounding_box(cell)
        centre_lat = _mercator_centre_lat(y, zoom)
        centre_lon = (2 * x + 1) * 180.0 / (1 << zoom) - 180.0
        assert box.min_lat <= centre_lat <= box.max_lat, (x, y, zoom, cell)
        assert box.min_lon <= centre_lon <= box.max_lon, (x, y, zoom, cell)


# --- alignment law: ties resolve west and north (lower x, lower y) -----------


@pytest.mark.parametrize(
    ("x", "y", "zoom", "expected"),
    [
        (1, 1, 2, "d"),  # Bing spec example tile, quadkey "03": centre on a boundary
        (0, 0, 0, "e"),  # root tile centres on (0, 0)
    ],
)
def test_tie_resolves_to_lower_x_lower_y_cell(x, y, zoom, expected):
    assert interop.tile_to_geohash(x, y, zoom) == expected


def test_tie_quadkey_agrees_with_tile():
    assert interop.quadkey_to_geohash("03") == "d"
    assert interop.quadkey_to_geohash("") == "e"


# --- documented latitude lossiness (spec contradiction, pinned) --------------


def test_latitude_round_trip_is_documented_lossy():
    """'wj' -> tile (24, 13, 5) -> 'wh': the Mercator midpoint of the row that
    contains 'wj's centre lies in the adjacent equirectangular cell.

    This is the Web Mercator/equirectangular grid mismatch documented in the
    module docstring - pinned here so a change gets reviewed, not sneaked in.
    """
    tile = interop.geohash_to_tile("wj")
    assert tile == Tile(x=24, y=13, zoom=5)
    assert interop.tile_to_geohash(tile.x, tile.y, tile.zoom) == "wh"
    # The longitude column is still exact through the round trip.
    assert interop.geohash_to_tile(interop.tile_to_geohash(tile.x, tile.y, tile.zoom)).x == tile.x


# --- quadkey <-> tile agreement (Bing digit algorithm, test-local) -----------


@pytest.mark.parametrize("zoom", range(0, 13))
def test_geohash_to_quadkey_matches_bing_algorithm(zoom):
    for _ in range(20):
        cell = _random_cell(max(1, math.ceil(2 * zoom / 5) if zoom else 1))
        lat, lon = pygeohash.decode(cell)
        if abs(lat) > WEB_MERCATOR_LAT_LIMIT:
            continue
        tile = interop.geohash_to_tile(cell)
        assert interop.geohash_to_quadkey(cell) == _bing_quadkey(tile.x, tile.y, tile.zoom), cell


# --- polar boundary sweep ----------------------------------------------------


def _all_cells(precision):
    return [a + b for a in BASE32 for b in BASE32] if precision == 2 else None


def test_precision_2_polar_classification_is_exhaustive():
    """Every precision-2 cell: raises iff its centre is outside the band."""
    polar = in_band = 0
    for cell in _all_cells(2):
        lat, _ = pygeohash.decode(cell)
        if abs(lat) > WEB_MERCATOR_LAT_LIMIT:
            polar += 1
            with pytest.raises(ValueError, match="85.05112878"):
                interop.geohash_to_tile(cell)
        else:
            in_band += 1
            interop.geohash_to_tile(cell)  # must not raise
    assert polar == 64 and in_band == 960


def test_precision_2_clip_rows_are_exhaustive():
    """Clipping a polar cell maps to the nearest edge row: north -> 0, south -> last."""
    for cell in _all_cells(2):
        lat, _ = pygeohash.decode(cell)
        if abs(lat) <= WEB_MERCATOR_LAT_LIMIT:
            continue
        tile = interop.geohash_to_tile(cell, clip=True)
        assert tile.y == (0 if lat > 0 else (1 << tile.zoom) - 1), cell


@pytest.mark.parametrize(
    "latitude",
    [85.05112878, 85.051128780001, 85.05112878 - 1e-9, -85.05112878, -85.051128780001, -(85.05112878 - 1e-9)],
)
@pytest.mark.parametrize("precision", [2, 5, 9, 12])
def test_mercator_boundary_classification_follows_cell_centre(latitude, precision):
    """Points at/next to the band edge: raise iff the CELL centre is outside."""
    cell = pygeohash.encode(latitude, 10.0, precision=precision)
    centre_lat, _ = pygeohash.decode(cell)
    outside = abs(centre_lat) > WEB_MERCATOR_LAT_LIMIT
    if outside:
        with pytest.raises(ValueError):
            interop.geohash_to_tile(cell)
        tile = interop.geohash_to_tile(cell, clip=True)
        assert 0 <= tile.y < (1 << tile.zoom)
    else:
        tile = interop.geohash_to_tile(cell)
        assert 0 <= tile.y < (1 << tile.zoom)


def test_clip_never_raises_for_polar_reasons_and_stays_in_band():
    for _ in range(40):
        cell = _random_cell(9)
        tile = interop.geohash_to_tile(cell, clip=True)
        assert 0 <= tile.y < (1 << tile.zoom)


# --- caps and invalid input (error messages are part of the contract) --------


@pytest.mark.parametrize("bad", [0, 13, -1, 1.5, "3", True])
def test_precision_out_of_caps_rejected(bad):
    # None is deliberately absent from the bad list: precision=None means
    # "use the default", which must keep working.
    with pytest.raises(ValueError, match="[Pp]recision"):
        interop.tile_to_geohash(0, 0, 5, precision=bad)
    with pytest.raises(ValueError, match="[Pp]recision"):
        interop.quadkey_to_geohash("03", precision=bad)


@pytest.mark.parametrize("bad", [-1, 31, 100, 1.5, "5", True])
def test_zoom_out_of_caps_rejected(bad):
    # Same validator serves both entry points; quadkey length caps are
    # covered separately in test_invalid_quadkey_rejected.
    with pytest.raises(ValueError, match="[Zz]oom"):
        interop.tile_to_geohash(0, 0, bad)


@pytest.mark.parametrize("bad_x", [-1, 32, 1000])
def test_tile_x_out_of_range_rejected(bad_x):
    with pytest.raises(ValueError, match="x"):
        interop.tile_to_geohash(bad_x, 0, 5)


@pytest.mark.parametrize("bad_y", [-1, 32, 1000])
def test_tile_y_out_of_range_rejected(bad_y):
    with pytest.raises(ValueError, match="y"):
        interop.tile_to_geohash(0, bad_y, 5)


@pytest.mark.parametrize("bad", ["", "!", "a", "ezs42!", "ezs4!", "e" * 13])
def test_invalid_geohash_rejected(bad):
    with pytest.raises(ValueError):
        interop.geohash_to_tile(bad)
    with pytest.raises(ValueError):
        interop.geohash_to_quadkey(bad)
    with pytest.raises(ValueError):
        interop.geohash_to_int(bad)


@pytest.mark.parametrize("bad", ["0" * 31, "5", "4", "a", "03a"])
def test_invalid_quadkey_rejected(bad):
    with pytest.raises(ValueError):
        interop.quadkey_to_geohash(bad)


@pytest.mark.parametrize("bad", [-1, -(2**60), 2**5, 2**60, 1.5, True, None])
def test_integer_value_out_of_range_rejected(bad):
    with pytest.raises(ValueError):
        interop.geohash_from_int(bad, 1)


def test_integer_value_overflow_message_names_the_cap():
    with pytest.raises(ValueError, match="2\\*\\*\\(5 \\* precision\\)"):
        interop.geohash_from_int(32, 1)


def test_non_string_inputs_rejected():
    for bad in (None, 42, 3.14, b"ezs42", ["ezs42"]):
        with pytest.raises(ValueError):
            interop.geohash_to_tile(bad)
        with pytest.raises(ValueError):
            interop.quadkey_to_geohash(bad)


# --- case handling -----------------------------------------------------------


def test_geohash_inputs_are_case_insensitive():
    for variant in ("EZS42", "ezs42", "EzS42", "eZs42"):
        assert interop.geohash_to_tile(variant) == interop.geohash_to_tile("ezs42")
        assert interop.geohash_to_quadkey(variant) == interop.geohash_to_quadkey("ezs42")
        assert interop.geohash_to_int(variant) == interop.geohash_to_int("ezs42")


def test_geohash_outputs_are_lowercase():
    assert interop.tile_to_geohash(1984, 1511, 12) == "ezs42"
    assert interop.quadkey_to_geohash("031333200222") == "ezs42"


# --- integer form (exact, lossless with explicit precision) ------------------


@pytest.mark.parametrize("precision", range(1, 13))
def test_integer_round_trip_is_exact(precision):
    for _ in range(20):
        cell = _random_cell(precision)
        assert interop.geohash_from_int(interop.geohash_to_int(cell), precision) == cell


def test_integer_boundaries():
    assert interop.geohash_to_int("0") == 0
    assert interop.geohash_to_int("0" * 12) == 0
    assert interop.geohash_to_int("z" * 12) == 2**60 - 1
    assert interop.geohash_from_int(0, 1) == "0"
    assert interop.geohash_from_int(31, 1) == "z"
    assert interop.geohash_from_int(2**60 - 1, 12) == "z" * 12


# --- Tile NamedTuple behaviour ------------------------------------------------


def test_tile_is_a_plain_tuple():
    tile = Tile(x=1984, y=1511, zoom=12)
    assert tile == (1984, 1511, 12)
    x, y, zoom = tile
    assert (x, y, zoom) == (1984, 1511, 12)
    assert (tile.x, tile.y, tile.zoom) == (1984, 1511, 12)
    with pytest.raises((AttributeError, TypeError)):
        tile.zoom = 5


# --- purity and determinism ---------------------------------------------------


def test_repeated_calls_are_deterministic():
    for _ in range(10):
        cell = _random_cell(7)
        if abs(pygeohash.decode(cell)[0]) > WEB_MERCATOR_LAT_LIMIT:
            continue  # polar cells raise (by policy); that is tested separately
        assert interop.geohash_to_tile(cell) == interop.geohash_to_tile(cell)
        assert interop.geohash_to_quadkey(cell) == interop.geohash_to_quadkey(cell)
        tile = interop.geohash_to_tile(cell)
        assert interop.tile_to_geohash(tile.x, tile.y, tile.zoom) == interop.tile_to_geohash(tile.x, tile.y, tile.zoom)
        assert interop.geohash_to_int(cell) == interop.geohash_to_int(cell)


def _load_fixture():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))
