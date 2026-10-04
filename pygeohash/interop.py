"""Bridges between geohash and the tile/integer systems it shares geometry with.

Geohash and the Bing/OSM slippy-tile system (zoom / x / y, quadkey) describe the
same world in two encodings, and this module converts between them exactly where
geometry allows and honestly where it does not:

- **Longitude agrees bit for bit.** Both systems split longitude into
  ``2**zoom`` equal columns at zoom ``z``; a geohash cell of precision ``p``
  occupies ``ceil(5p/2)`` longitude bits and a tile at zoom ``floor(5p/2)``
  shares that prefix. Column mapping is pure bit arithmetic — exact in both
  directions, and lossless at even precision ``p`` against zoom ``5p/2``.
- **Latitude does not, and cannot.** Geohash splits latitude evenly
  (equirectangular); slippy rows follow the Web Mercator projection, which has
  no representation poleward of ±85.05112878°. The two latitude grids agree
  only at the equator and diverge away from it, so row mapping goes through
  the projection and round trips are generally lossy in latitude. Any converter
  that claims bit-exact geohash/tile latitude cells is quietly returning tiles
  that do not render on real maps.

Conversion semantics pinned by this module:

1. **Longitude identity**: for even precision ``p``, ``geohash → tile →
   geohash`` preserves the tile column exactly, and the cell column equals the
   tile column at zoom ``5p/2`` — a true bijection in longitude.
2. **Containment**: ``geohash_to_tile`` returns the tile containing the cell
   centre (for odd precision the cell is half a tile column wide with the same
   latitude extent, so its centre decides); ``tile_to_geohash`` and
   ``quadkey_to_geohash`` return the geohash cell containing the tile centre at
   default precision ``ceil(2·zoom/5)``. Round trips through non-aligned zooms
   or odd precisions are lossy in latitude — this is a property of the grids,
   not of these functions, and the docstrings say so plainly.
3. **Ties**: a centre exactly on a cell boundary resolves deterministically to
   the lower-x, lower-y cell (west, north). Longitude centres are exact dyadic
   values and can land on boundaries; Web Mercator latitudes cannot.
4. **Polar policy**: geohashes cover ±90° but tiles only ±85.05112878°.
   ``geohash_to_tile`` and ``geohash_to_quadkey`` raise :class:`ValueError`
   when the cell centre lies outside that band; ``clip=True`` maps the cell to
   the nearest in-band tile row instead. The tile→geohash direction never
   raises for polar reasons — a valid slippy ``y`` is always in-band by
   construction. Nothing is ever clamped silently.

Caps: precision 1–12, zoom 0–30. Inputs follow the package codec conventions
(case-insensitive geohash strings, :class:`ValueError` with a specific message
on invalid input). All functions are pure, deterministic, and thread-safe; the
row arithmetic mirrors the reference ``mercantile`` formulas bit for bit.
"""

from __future__ import annotations

from math import atan, floor, log, pi, radians, sin, sinh
from typing import NamedTuple

from pygeohash.geohash import MAX_PRECISION, MIN_PRECISION, __base32

__all__ = [
    "Tile",
    "geohash_to_quadkey",
    "quadkey_to_geohash",
    "geohash_to_tile",
    "tile_to_geohash",
    "geohash_to_int",
    "geohash_from_int",
]

# Slippy tiles cover the Web Mercator square only: latitudes poleward of
# ±85.05112878 degrees (atan(sinh(pi)) in radians, per the Bing Maps Tile
# System specification) have no tile row. The value is the standard published
# constant, not derived here.
WEB_MERCATOR_LAT_LIMIT = 85.05112878

MIN_ZOOM = 0
MAX_ZOOM = 30

# mercantile counts points within this distance of a tile's right/bottom edge
# as belonging to the next tile over, to absorb float dust when round-tripping
# tile edges through lng/lat. Mirrored so both tools agree row for row.
_MERCATOR_EPSILON = 1e-14

_BASE32_MAP = {char: index for index, char in enumerate(__base32)}


class Tile(NamedTuple):
    """A slippy-map tile index (the ``z/x/y`` of Bing/OSM tile caches).

    ``x`` and ``y`` index the ``2**zoom × 2**zoom`` tile grid; ``y`` is counted
    southward from the north pole (the slippy convention), so ``(0, 0)`` is the
    north-west tile of the grid.

    Example:
        >>> Tile(x=1984, y=1511, zoom=12)
        Tile(x=1984, y=1511, zoom=12)
    """

    x: int
    y: int
    zoom: int


def _decode_bits(geohash: str) -> tuple[int, int]:
    """Validate a geohash string and return its bit value and precision."""
    if not isinstance(geohash, str):
        raise ValueError(f"Geohash must be a string, but got {type(geohash).__name__}.")
    if not geohash:
        raise ValueError("Geohash cannot be empty.")
    if len(geohash) > MAX_PRECISION:
        raise ValueError(f"Geohash must be at most {MAX_PRECISION} characters long.")

    bits = 0
    for character in geohash.lower():
        digit = _BASE32_MAP.get(character)
        if digit is None:
            raise ValueError(
                f"Invalid character {character!r} in geohash {geohash!r}: characters must "
                f"come from the geohash base32 alphabet '{__base32}'"
            )
        bits = (bits << 5) | digit
    return bits, len(geohash)


def _validate_precision(precision: int) -> int:
    """Reject non-int and out-of-range precisions, matching the codec's messages."""
    if isinstance(precision, bool) or not isinstance(precision, int):
        raise ValueError(f"Precision must be an integer, but got {type(precision).__name__}.")
    if not (MIN_PRECISION <= precision <= MAX_PRECISION):
        raise ValueError(f"Precision must be between {MIN_PRECISION} and {MAX_PRECISION}, but got {precision}.")
    return precision


def _validate_zoom(zoom: int) -> int:
    """Reject non-int and out-of-range zooms."""
    if isinstance(zoom, bool) or not isinstance(zoom, int):
        raise ValueError(f"Zoom must be an integer, but got {type(zoom).__name__}.")
    if not (MIN_ZOOM <= zoom <= MAX_ZOOM):
        raise ValueError(f"Zoom must be between {MIN_ZOOM} and {MAX_ZOOM}, but got {zoom}.")
    return zoom


def _validate_tile_axis(value: int, axis: str, zoom: int) -> int:
    """Reject non-int and out-of-range tile coordinates at a validated zoom."""
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"Tile {axis} must be an integer, but got {type(value).__name__}.")
    limit = (1 << zoom) - 1
    if not (0 <= value <= limit):
        message = f"Tile {axis} must be between 0 and {limit} at zoom {zoom}, but got {value}."
        if axis == "y":
            message += " Tile y counts southward from the north pole (slippy convention)."
        raise ValueError(message)
    return value


def _default_precision(zoom: int) -> int:
    """Default cell precision for a tile: ceil(2*zoom/5), never below 1.

    Zoom 0 would otherwise default to precision 0, but a precision-0 geohash
    does not exist; the root tile's centre lands in a precision-1 cell.
    """
    return max(1, (2 * zoom + 4) // 5)


def _centre_longitude_bits(value: int, zoom: int, n_bits: int) -> int:
    """Longitude bits of the geohash cell containing a tile centre.

    The centre's longitude expansion is the tile's ``zoom`` bits followed by a
    1 and then zeros (the centre sits at the odd dyadic ``[2*value, 2*value+2)
    midpoint``). Truncated below the centre depth it is plain bit slicing; at
    or beyond it the centre lies exactly on a cell boundary, and the tie rule
    resolves to the lower cell — west.
    """
    centre = (value << 1) | 1
    if n_bits <= zoom:
        return centre >> (zoom + 1 - n_bits)
    return (centre << (n_bits - zoom - 1)) - 1


def _tile_centre_equator_offset(y: int, zoom: int) -> float:
    """Signed equirectangular offset from the equator of tile row ``y`` at ``zoom``.

    The offset is ``latitude / 180`` — the quantity whose top
    ``latitude_bits`` binary digits above the equator cell are the geohash
    latitude bits. It is built directly in radians (``lat_rad / pi``) and
    never added to 0.5: at high zooms the tile centre sits within an ulp of
    ``0.5`` of an equirectangular cell boundary, and adding 0.5 first rounds
    the offset at ulp(0.5) — far too coarsely to decide which side of the
    boundary the centre is on.
    """
    return atan(sinh(pi * (1.0 - 2.0 * (y + 0.5) / (1 << zoom)))) / pi


def _mercator_row(latitude: float, zoom: int) -> int:
    """Tile row containing ``latitude`` at ``zoom`` (mercantile-parity formula).

    Latitude must already be inside the Web Mercator band; the ``<= 0`` and
    ``>= 1`` branches exist so the clip path (which sits exactly on the band
    edges) and float dust at those edges land on rows 0 and ``2**zoom - 1``.
    """
    sin_latitude = sin(radians(latitude))
    y_fraction = 0.5 - 0.25 * log((1.0 + sin_latitude) / (1.0 - sin_latitude)) / pi
    if y_fraction <= 0:
        return 0
    if y_fraction >= 1:
        return (1 << zoom) - 1
    return int(floor((y_fraction + _MERCATOR_EPSILON) * (1 << zoom)))


def _bits_to_geohash(bits: int, precision: int) -> str:
    """Render a ``5*precision``-bit value as a base32 geohash string."""
    characters = []
    for _ in range(precision):
        characters.append(__base32[(bits >> (5 * precision - 5)) & 31])
        bits <<= 5
    return "".join(characters)


def geohash_to_tile(geohash: str, clip: bool = False) -> Tile:
    """Return the slippy tile containing a geohash cell's centre.

    The zoom is ``floor(5 * precision / 2)``. The tile column is the cell's
    longitude-bit prefix — exact for every precision (an odd-precision cell is
    half a tile column wide and sits fully inside one column). The tile row
    contains the cell centre under the Web Mercator projection, so it is exact
    in longitude but generally lossless nowhere in latitude: geohash latitude
    bands are equirectangular and tile rows are not. Round-tripping cells
    through :func:`tile_to_geohash` therefore shifts latitude — see the
    containment notes there.

    Args:
        geohash (str): The geohash cell to map. Case-insensitive.
        clip (bool, optional): Behaviour when the cell centre lies poleward of
            the Web Mercator band (±85.05112878°), where tiles do not exist.
            ``False`` (the default) raises :class:`ValueError`; ``True`` maps
            the cell to the nearest in-band tile row (row 0 northward,
            ``2**zoom - 1`` southward).

    Returns:
        Tile: The containing tile ``(x, y, zoom)``.

    Raises:
        ValueError: If the geohash is not a valid 1-12 character base32 string,
            or (with ``clip=False``) if its centre lies outside the Web
            Mercator latitude band.

    Example:
        >>> geohash_to_tile("ezs42")
        Tile(x=1984, y=1511, zoom=12)
        >>> geohash_to_tile("ezs42").zoom  # floor(5 * 5 / 2)
        12
    """
    bits, precision = _decode_bits(geohash)
    total_bits = 5 * precision
    zoom = total_bits // 2

    # Split the interleaved stream: longitude bits at even positions, latitude
    # bits at odd positions. The cell's longitude depth is zoom or zoom + 1
    # bits, so its high bits are exactly the containing tile column.
    longitude_bits = 0
    latitude_bits = 0
    for position in range(total_bits):
        bit = (bits >> (total_bits - 1 - position)) & 1
        if position % 2 == 0:
            longitude_bits = (longitude_bits << 1) | bit
        else:
            latitude_bits = (latitude_bits << 1) | bit
    x = longitude_bits >> (total_bits // 2 + total_bits % 2 - zoom)

    # The cell's latitude depth equals the zoom, so its centre is the odd
    # dyadic (2*latitude_bits + 1) / 2**(zoom + 1) — exact in binary.
    centre_latitude = 180.0 * (2 * latitude_bits + 1) / (1 << (zoom + 1)) - 90.0
    if centre_latitude > WEB_MERCATOR_LAT_LIMIT or centre_latitude < -WEB_MERCATOR_LAT_LIMIT:
        if not clip:
            raise ValueError(
                f"Geohash {geohash!r} cell centre latitude {centre_latitude} degrees is outside "
                f"the Web Mercator band ±{WEB_MERCATOR_LAT_LIMIT} degrees. Slippy tiles and "
                "quadkeys do not exist for the polar caps; pass clip=True to map the cell to "
                "the nearest in-band tile row."
            )
        centre_latitude = min(max(centre_latitude, -WEB_MERCATOR_LAT_LIMIT), WEB_MERCATOR_LAT_LIMIT)

    return Tile(x, _mercator_row(centre_latitude, zoom), zoom)


def geohash_to_quadkey(geohash: str, clip: bool = False) -> str:
    """Return the Bing quadkey of the tile containing a geohash cell's centre.

    The quadkey has ``floor(5 * precision / 2)`` digits — one per tile level,
    each digit the tile's x-then-y bit pair. For even precision the quadkey
    addresses the column the cell lives in exactly; latitude rows follow the
    Web Mercator projection, so the mapping is lossy in latitude for every
    precision (see :func:`geohash_to_tile`).

    Args:
        geohash (str): The geohash cell to map. Case-insensitive.
        clip (bool, optional): Polar policy for the cell centre, exactly as in
            :func:`geohash_to_tile`: ``False`` raises outside the Web Mercator
            band, ``True`` maps to the nearest in-band row.

    Returns:
        str: The quadkey, one ``0``-``3`` digit per zoom level. Never empty for
        a valid geohash (precision 1 already maps to zoom 2).

    Raises:
        ValueError: If the geohash is invalid, or (with ``clip=False``) if its
            centre lies outside the Web Mercator latitude band.

    Example:
        >>> geohash_to_quadkey("ezs42")
        '031333200222'
    """
    tile = geohash_to_tile(geohash, clip=clip)
    digits = []
    for level in range(tile.zoom):
        shift = tile.zoom - 1 - level
        digits.append("0123"[((tile.y >> shift) & 1) << 1 | ((tile.x >> shift) & 1)])
    return "".join(digits)


def quadkey_to_geohash(quadkey: str, precision: int | None = None) -> str:
    """Return the geohash cell containing a quadkey's tile centre.

    The precision defaults to ``ceil(2 * zoom / 5)`` (one more bit pair than
    the tile has levels, rounded): the cell is finer than or equal to the tile
    in longitude and contains the tile centre in latitude. Cells returned this
    way are exact in longitude (the tile centre is a dyadic point there, with
    boundary cases resolved west) and approximate in latitude, because the
    tile centre's Web Mercator latitude rarely lands on an equirectangular
    geohash boundary. Round trips through :func:`geohash_to_quadkey` are
    therefore lossy in latitude for every precision.

    Args:
        quadkey (str): The quadkey to map, one ``0``-``3`` digit per zoom
            level. The empty string is the zoom-0 root tile.
        precision (int, optional): Precision of the returned cell, 1-12.
            Defaults to ``ceil(2 * zoom / 5)`` (precision 1 for the root tile).

    Returns:
        str: The geohash cell containing the tile centre, lowercase.

    Raises:
        ValueError: If the quadkey is not a string of at most 30 ``0``-``3``
            digits, or the precision is not an integer between 1 and 12.

    Example:
        >>> quadkey_to_geohash("031333200222")
        'ezs42'
        >>> quadkey_to_geohash("03")  # Bing's example tile (1, 1, 2): centre resolves west
        'd'
    """
    if not isinstance(quadkey, str):
        raise ValueError(f"Quadkey must be a string, but got {type(quadkey).__name__}.")
    if len(quadkey) > MAX_ZOOM:
        raise ValueError(
            f"Quadkey must be at most {MAX_ZOOM} characters long (zoom {MAX_ZOOM}), but got {len(quadkey)} characters."
        )

    x = 0
    y = 0
    for character in quadkey:
        if character not in "0123":
            raise ValueError(
                f"Invalid character {character!r} in quadkey {quadkey!r}: quadkeys use only the digits 0, 1, 2 and 3."
            )
        digit = ord(character) - 48
        x = (x << 1) | (digit & 1)
        y = (y << 1) | (digit >> 1)

    return _tile_to_geohash(x, y, len(quadkey), precision)


def tile_to_geohash(x: int, y: int, zoom: int, precision: int | None = None) -> str:
    """Return the geohash cell containing a slippy tile's centre.

    The precision defaults to ``ceil(2 * zoom / 5)`` (precision 1 for zoom 0):
    high enough that the cell's longitude depth reaches the tile centre's
    depth, so the longitude is pinned exactly, with boundary centres resolved
    to the lower-x, lower-y cell (west, north) per the tie rule. Latitude comes
    from the tile centre's Web Mercator latitude, so the cell containing it is
    approximate — tile centres rarely land on equirectangular cell boundaries.

    Round trips are lossy in latitude by the nature of the two grids: feed the
    result back through :func:`geohash_to_tile` and the row can move whenever
    the cell straddles a row boundary. Nothing is lost in longitude at even
    precision and zoom ``5 * precision / 2``, which map cell-for-cell.

    Args:
        x (int): Tile column, ``0`` to ``2**zoom - 1``.
        y (int): Tile row, ``0`` to ``2**zoom - 1``, counted southward from
            the north pole (slippy convention).
        zoom (int): Zoom level, 0-30.
        precision (int, optional): Precision of the returned cell, 1-12.
            Defaults to ``ceil(2 * zoom / 5)``.

    Returns:
        str: The geohash cell containing the tile centre, lowercase.

    Raises:
        ValueError: If ``zoom`` is not an integer between 0 and 30, if ``x``
            or ``y`` is not an integer within ``0..2**zoom - 1``, or the
            precision is not an integer between 1 and 12.

    Example:
        >>> tile_to_geohash(1984, 1511, 12)
        'ezs42'
        >>> tile_to_geohash(1, 1, 2)  # centre on a precision-1 boundary: resolves west
        'd'
    """
    return _tile_to_geohash(x, y, zoom, precision)


def _tile_to_geohash(x: int, y: int, zoom: int, precision: int | None) -> str:
    """Shared tile/quadkey → geohash body once the tile index is validated."""
    _validate_zoom(zoom)
    _validate_tile_axis(x, "x", zoom)
    _validate_tile_axis(y, "y", zoom)
    if precision is None:
        precision = _default_precision(zoom)
    else:
        _validate_precision(precision)

    longitude_bits = _centre_longitude_bits(x, zoom, (5 * precision + 1) // 2)

    # Latitude: the tile centre's Web Mercator latitude is never a dyadic
    # value, so it never lands exactly on an equirectangular cell boundary and
    # the containing band is a plain floor. The offset from the equator is
    # kept separate from the equator cell index: at high zooms the tile centre
    # sits within an ulp of a cell boundary, and forming the full fraction
    # (offset + 0.5) first would round the offset at ulp(0.5) — far too
    # coarsely to pick the correct side.
    latitude_cells = 1 << (5 * precision // 2)
    latitude_bits = (latitude_cells // 2) + floor(_tile_centre_equator_offset(y, zoom) * latitude_cells)

    # Re-interleave into 5*precision bits: longitude at even positions,
    # latitude at odd ones, MSB first.
    bits = 0
    for position in range(5 * precision):
        if position % 2 == 0:
            bit = (longitude_bits >> ((5 * precision + 1) // 2 - 1 - position // 2)) & 1
        else:
            bit = (latitude_bits >> (5 * precision // 2 - 1 - position // 2)) & 1
        bits = (bits << 1) | bit
    return _bits_to_geohash(bits, precision)


def geohash_to_int(geohash: str) -> int:
    """Return the integer form of a geohash: base32 digits, 5 bits each, MSB first.

    Lossless and exact for every valid geohash: the integer carries all
    ``5 * precision`` bits, and :func:`geohash_from_int` with the original
    precision recovers the string (lowercased) exactly. This is a pure
    re-encoding — no grid semantics involved.

    Args:
        geohash (str): The geohash to convert. Case-insensitive.

    Returns:
        int: The base32 bit value, ``0`` to ``2**(5 * precision) - 1``.

    Raises:
        ValueError: If the geohash is not a valid 1-12 character base32 string.

    Example:
        >>> geohash_to_int("ezs42")
        14672002
        >>> geohash_from_int(geohash_to_int("EZS42"), 5)
        'ezs42'
    """
    bits, _ = _decode_bits(geohash)
    return bits


def geohash_from_int(value: int, precision: int) -> str:
    """Return the geohash string encoded in an integer's low ``5 * precision`` bits.

    The inverse of :func:`geohash_to_int`. ``precision`` is required because
    the integer form carries no length: leading zero bits are indistinguishable
    from a shorter hash, so the caller must say how wide the value was.

    Args:
        value (int): The bit value, ``0`` (inclusive) to ``2**(5 * precision)``
            (exclusive). Negative values and values that overflow the requested
            precision are rejected.
        precision (int): Character count of the result, 1-12.

    Returns:
        str: The lowercase geohash string.

    Raises:
        ValueError: If ``precision`` is not an integer between 1 and 12, or
            ``value`` is not an integer in ``[0, 2**(5 * precision))``.

    Example:
        >>> geohash_from_int(14672002, 5)
        'ezs42'
        >>> geohash_from_int(0, 1)
        '0'
    """
    _validate_precision(precision)
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"Value must be an integer, but got {type(value).__name__}.")
    limit = 1 << (5 * precision)
    if value < 0:
        raise ValueError(f"Value must be non-negative, but got {value}.")
    if value >= limit:
        raise ValueError(f"Value must be less than 2**(5 * precision) = {limit}, but got {value}.")
    return _bits_to_geohash(value, precision)
