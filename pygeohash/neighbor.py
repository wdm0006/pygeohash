"""Geohash neighbor calculation functionality.

This module provides functionality for calculating adjacent geohashes
in different directions (right, left, top, bottom).
"""

from __future__ import annotations

from typing import Dict, Final, FrozenSet, Literal, Tuple

from pygeohash.geohash import __base32
from pygeohash.types import Direction, is_valid_geohash
from pygeohash.logging import get_logger

logger = get_logger(__name__)

# Configuration  -- from https://github.com/davetroy/geohash-js/blob/master/geohash.js
NEIGHBORS: Final[Dict[Direction, Dict[Literal["even", "odd"], str]]] = {
    "right": {
        "even": "bc01fg45238967deuvhjyznpkmstqrwx",
        "odd": "p0r21436x8zb9dcf5h7kjnmqesgutwvy",  # = top-even
    },
    "left": {
        "even": "238967debc01fg45kmstqrwxuvhjyznp",
        "odd": "14365h7k9dcfesgujnmqp0r2twvyx8zb",  # = bottom-even
    },
    "top": {
        "even": "p0r21436x8zb9dcf5h7kjnmqesgutwvy",
        "odd": "bc01fg45238967deuvhjyznpkmstqrwx",  # = right-even
    },
    "bottom": {
        "even": "14365h7k9dcfesgujnmqp0r2twvyx8zb",
        "odd": "238967debc01fg45kmstqrwxuvhjyznp",  # = left-even
    },
}

# Used change of parent tile
BORDERS: Final[Dict[Direction, Dict[Literal["even", "odd"], str]]] = {
    "right": {
        "even": "bcfguvyz",
        "odd": "prxz",  # top-even
    },
    "left": {
        "even": "0145hjnp",
        "odd": "028b",  # bottom-even
    },
    "top": {
        "even": "prxz",
        "odd": "bcfguvyz",  # right-even
    },
    "bottom": {
        "even": "028b",
        "odd": "0145hjnp",  # left-even
    },
}

DIRECTIONS: Final[Tuple[Direction, ...]] = ("right", "left", "top", "bottom")

# Precomputed lookups so the hot path avoids per-call construction, str.index scans,
# and recursion on border characters. Indexed [direction][parity_bit] where bit 0 =
# even-length hash and bit 1 = odd-length hash (a prefix of length i + 1 has parity
# bit (i + 1) & 1).
_BORDER_SETS: Final[Dict[Direction, Tuple[FrozenSet[str], FrozenSet[str]]]] = {
    direction: (
        frozenset(BORDERS[direction]["even"]),
        frozenset(BORDERS[direction]["odd"]),
    )
    for direction in DIRECTIONS
}
_NEIGHBOR_MAPS: Final[Dict[Direction, Tuple[Dict[str, str], Dict[str, str]]]] = {
    direction: (
        {char: __base32[i] for i, char in enumerate(NEIGHBORS[direction]["even"])},
        {char: __base32[i] for i, char in enumerate(NEIGHBORS[direction]["odd"])},
    )
    for direction in DIRECTIONS
}


def get_adjacent(geohash: str, direction: Direction) -> str:
    """Calculate the adjacent geohash in the specified direction.

    Args:
        geohash (str): The input geohash string.
        direction (Direction): The direction to find the adjacent geohash.
        Must be one of: "right", "left", "top", "bottom".

    Returns:
        str: The adjacent geohash in the specified direction. Longitude is cyclic, so the
        "left"/"right" neighbors of a cell touching the antimeridian wrap around to the
        other side of the grid.

    Raises:
        ValueError: If the geohash is empty; if it is not a canonical geohash (1-12
        characters drawn from the geohash base32 alphabet, case-insensitive); if the
        direction is not one of "right", "left", "top" or "bottom"; or if the requested
        neighbor would lie beyond the north or south pole ("top" of the top row,
        "bottom" of the bottom row).

    Example:
        >>> get_adjacent("u4pruyd", "top")
        'u4pruyf'
    """
    if len(geohash) == 0:
        logger.error("Cannot find adjacent geohash: input geohash length is 0")
        raise ValueError("The geohash length cannot be 0. Possible when close to poles")

    if not is_valid_geohash(geohash):
        logger.error("Cannot find adjacent geohash: %r is not a valid geohash", geohash)
        raise ValueError(
            f"Invalid geohash: {geohash!r}. A geohash must be 1 to 12 characters "
            "from the base32 alphabet '0123456789bcdefghjkmnpqrstuvwxyz'"
        )

    if direction not in DIRECTIONS:
        logger.error("Cannot find adjacent geohash: %r is not a valid direction", direction)
        raise ValueError(f"Invalid direction: {direction!r}. Must be one of 'right', 'left', 'top', 'bottom'")

    source_hash = geohash.lower()
    border_sets = _BORDER_SETS[direction]
    neighbor_maps = _NEIGHBOR_MAPS[direction]

    # Walk right-to-left through border characters instead of recursing: position i
    # ends a substring of length i + 1, so its parity bit is (i + 1) & 1. Reaching
    # the first character on a border means the neighbor crosses into the parent tile.
    i = len(source_hash) - 1
    while source_hash[i] in border_sets[(i + 1) & 1]:
        if i == 0:
            if direction in ("top", "bottom"):
                pole = "north" if direction == "top" else "south"
                logger.error("Cannot find adjacent geohash: the %s neighbor lies beyond the %s pole", direction, pole)
                raise ValueError(f"No adjacent geohash to the {direction}: it would lie beyond the {pole} pole")
            # Longitude is cyclic, so the top-level tables already encode the antimeridian wrap.
            break
        i -= 1

    translated = neighbor_maps[(i + 1) & 1][source_hash[i]]
    if i == len(source_hash) - 1:
        # Common case: the last character is not on a border, no parent lookup needed.
        return source_hash[:-1] + translated

    parts = [source_hash[:i], translated]
    for j in range(i + 1, len(source_hash)):
        parts.append(neighbor_maps[(j + 1) & 1][source_hash[j]])
    return "".join(parts)
