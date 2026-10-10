"""Static signature fixture for spherical radius coverage."""

from typing import Callable, List

import pygeohash as pgh

coverage: Callable[[float, float, float, int], List[str]] = pgh.geohashes_in_radius
cells: List[str] = pgh.geohashes_in_radius(latitude=42.6, longitude=-5.6, radius_m=1000.0, precision=5)
default_cells: List[str] = pgh.geohashes_in_radius(42.6, -5.6, 1000.0)
