"""Static signature fixture for spherical radius coverage."""

from typing import Callable, List

import pygeohash as pgh

coverage: Callable[[float, float, float, int], List[str]] = pgh.geohashes_in_radius
cells: List[str] = pgh.geohashes_in_radius(latitude=42.6, longitude=-5.6, radius_m=1000.0, precision=5)
default_cells: List[str] = pgh.geohashes_in_radius(42.6, -5.6, 1000.0)
capped: List[str] = pgh.geohashes_in_radius(42.6, -5.6, 1000.0, 5, max_cells=1_000)
uncapped: List[str] = pgh.geohashes_in_radius(42.6, -5.6, 1000.0, max_cells=None)
box_capped: List[str] = pgh.geohashes_in_box(pgh.BoundingBox(0.0, 0.0, 1.0, 1.0), 4, max_cells=None)
