"""Geohash neighbor calculation functionality.

This module provides functionality for calculating adjacent geohashes
in different directions (right, left, top, bottom).
"""

from __future__ import annotations

from typing import Dict, Final, Literal, cast

from pygeohash.geohash import __base32
from pygeohash.types import Direction

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


def get_adjacent(geohash: str, direction: Direction) -> str:
    """Calculate the adjacent geohash in the specified direction.

    Args:
        geohash (str): The input geohash string.
        direction (Direction): The direction to find the adjacent geohash.
            Must be one of: "right", "left", "top", "bottom".

    Returns:
        str: The adjacent geohash in the specified direction.

    Raises:
        ValueError: If the geohash length is 0 (possible when close to poles).

    Example:
        >>> get_adjacent("u4pruyd", "top")
        'u4pruyf'
    """
    if len(geohash) == 0:
        raise ValueError("The geohash length cannot be 0. Possible when close to poles")
    source_hash = geohash.lower()
    last_char = source_hash[-1]
    base = source_hash[:-1]

    split_direction: Literal["even", "odd"] = "even" if len(source_hash) % 2 == 0 else "odd"

    if last_char in BORDERS[direction][split_direction]:
        base = get_adjacent(base, direction)

    neighbor_str = NEIGHBORS[direction][split_direction]
    idx = neighbor_str.index(last_char)
    base32_char = __base32[idx]
    return base + cast(str, base32_char)
