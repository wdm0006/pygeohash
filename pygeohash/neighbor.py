"""Geohash neighbor calculation functionality.

This module provides functionality for calculating adjacent geohashes
in different directions (right, left, top, bottom).
"""

from __future__ import annotations

from typing import Dict, Final, Literal

from pygeohash.geohash import __base32
from pygeohash.types import Direction
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
    logger.debug("Finding adjacent geohash for %s in direction %s", geohash, direction)

    if len(geohash) == 0:
        logger.error("Cannot find adjacent geohash: input geohash length is 0")
        raise ValueError("The geohash length cannot be 0. Possible when close to poles")

    source_hash = geohash.lower()
    last_char = source_hash[-1]
    base = source_hash[:-1]
    logger.debug("Processing: base=%s, last_char=%s", base, last_char)

    split_direction: Literal["even", "odd"] = "even" if len(source_hash) % 2 == 0 else "odd"
    logger.debug("Using %s lookup tables based on hash length", split_direction)

    if last_char in BORDERS[direction][split_direction]:
        logger.debug("Last character %s is on border, recursively finding parent neighbor", last_char)
        base = get_adjacent(base, direction)
    else:
        logger.debug("Last character %s is not on border, using direct neighbor lookup", last_char)

    neighbor_str = NEIGHBORS[direction][split_direction]
    idx = neighbor_str.index(last_char)
    base32_char = __base32[idx]
    result = base + base32_char
    logger.debug("Found adjacent geohash: %s", result)
    return result
