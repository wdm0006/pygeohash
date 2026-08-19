"""Bounding box operations for geohashes.

This module provides functions for working with geohash bounding boxes,
including calculating the bounding box for a geohash and operations
related to geospatial regions.
"""

from __future__ import annotations

import math
from typing import Any, Iterable, List, NamedTuple, Set, Iterator, Type, TypeVar

from pygeohash.geohash import decode_exactly, encode
from pygeohash.logging import get_logger

logger = get_logger(__name__)

_FIELD_ORDER = "BoundingBox fields are (min_lat, min_lon, max_lat, max_lon)"


class _BoundingBoxFields(NamedTuple):
    """Field layout for :class:`BoundingBox`; ``typing.NamedTuple`` forbids overriding ``__new__``."""

    min_lat: float
    min_lon: float
    max_lat: float
    max_lon: float


_BoundingBoxT = TypeVar("_BoundingBoxT", bound=_BoundingBoxFields)


class BoundingBox(_BoundingBoxFields):
    """Named tuple representing a geospatial bounding box.

    The fields interleave latitude and longitude, so the order is
    ``(min_lat, min_lon, max_lat, max_lon)`` rather than the grouped
    ``(min_lat, max_lat, min_lon, max_lon)``. Coordinates must be finite numbers within
    the geographic bounds for their axis; booleans are rejected even though ``bool`` is a
    subclass of ``int``. Construction also rejects an inverted box
    (``min_lat > max_lat`` or ``min_lon > max_lon``) with a ``ValueError``, which is
    what a grouped argument list produces. A degenerate box whose minimum equals its
    maximum on either axis is valid. Boxes spanning the antimeridian, which would need
    ``min_lon > max_lon``, are not supported.

    Attributes:
        min_lat (float): The minimum (southern) latitude of the box in decimal degrees.
            Must be between -90 and 90 and not exceed ``max_lat``.
        min_lon (float): The minimum (western) longitude of the box in decimal degrees.
            Must be between -180 and 180 and not exceed ``max_lon``.
        max_lat (float): The maximum (northern) latitude of the box in decimal degrees,
            between -90 and 90.
        max_lon (float): The maximum (eastern) longitude of the box in decimal degrees,
            between -180 and 180.

    Raises:
        ValueError: If a coordinate is a boolean, non-finite, outside its geographic
            bounds, or the box has ``min_lat > max_lat`` or ``min_lon > max_lon``.
    """

    __slots__ = ()

    def __new__(cls, min_lat: float, min_lon: float, max_lat: float, max_lon: float) -> "BoundingBox":
        for field, value, lower, upper in (
            ("min_lat", min_lat, -90.0, 90.0),
            ("min_lon", min_lon, -180.0, 180.0),
            ("max_lat", max_lat, -90.0, 90.0),
            ("max_lon", max_lon, -180.0, 180.0),
        ):
            # bool is a subclass of int, so it has to be rejected explicitly.
            if isinstance(value, bool):
                raise ValueError(f"{field} ({value}) must be a number, not a bool")
            try:
                is_finite = math.isfinite(value)
            except TypeError:
                is_finite = False
            if not is_finite:
                raise ValueError(f"{field} ({value}) must be a finite number")
            if not lower <= value <= upper:
                raise ValueError(f"{field} ({value}) must be between {lower:g} and {upper:g}")

        if min_lat > max_lat:
            raise ValueError(f"min_lat ({min_lat}) must not exceed max_lat ({max_lat}); {_FIELD_ORDER}")
        if min_lon > max_lon:
            raise ValueError(
                f"min_lon ({min_lon}) must not exceed max_lon ({max_lon}); "
                "boxes spanning the antimeridian are not supported"
            )
        return super().__new__(cls, min_lat, min_lon, max_lat, max_lon)

    # mypy rejects the narrowed self-type against the synthesized namedtuple signature.
    @classmethod
    def _make(cls: Type[_BoundingBoxT], iterable: Iterable[Any]) -> _BoundingBoxT:  # type: ignore[override]
        """Build a box from an iterable of field values, validating the ordering.

        Overridden so that ``_make`` and ``_replace`` route through ``__new__`` instead of
        ``tuple.__new__``, which would bypass validation.
        """
        return cls(*iterable)


def get_bounding_box(geohash: str) -> BoundingBox:
    """Calculate the bounding box for a geohash.

    Args:
        geohash (str): The geohash string to calculate the bounding box for.

    Returns:
        BoundingBox: A named tuple containing the minimum and maximum latitude and longitude
            values that define the bounding box of the geohash.

    Example:
        >>> tuple(round(value, 6) for value in get_bounding_box("u4pruyd"))
        (57.64801, 10.406799, 57.649384, 10.408173)

    Note:
        The precision of the coordinates in the bounding box depends on the length
        of the geohash. Longer geohashes result in smaller bounding boxes with more
        precise coordinates.
    """
    # Get the center point and error margins
    lat, lon, lat_err, lon_err = decode_exactly(geohash)
    return BoundingBox(lat - lat_err, lon - lon_err, lat + lat_err, lon + lon_err)


def is_point_in_box(lat: float, lon: float, bbox: BoundingBox) -> bool:
    """Check if a point is within a bounding box.

    Args:
        lat (float): The latitude of the point to check.
        lon (float): The longitude of the point to check.
        bbox (BoundingBox): The bounding box to check against.

    Returns:
        bool: True if the point is within the bounding box, False otherwise.

    Example:
        >>> bbox = get_bounding_box("u4pruyd")
        >>> is_point_in_box(57.649, 10.407, bbox)
        True
        >>> is_point_in_box(40.0, 10.0, bbox)
        False
    """
    logger.debug("Checking if point (lat=%f, lon=%f) is in box: %s", lat, lon, bbox)
    result = bbox.min_lat <= lat <= bbox.max_lat and bbox.min_lon <= lon <= bbox.max_lon
    logger.debug("Point is %s the box", "inside" if result else "outside")
    return result


def is_point_in_geohash(lat: float, lon: float, geohash: str) -> bool:
    """Check if a point is within a geohash's bounding box.

    Args:
        lat (float): The latitude of the point to check.
        lon (float): The longitude of the point to check.
        geohash (str): The geohash to check against.

    Returns:
        bool: True if the point is within the geohash's bounding box, False otherwise.

    Example:
        >>> is_point_in_geohash(57.649, 10.407, "u4pruyd")
        True
        >>> is_point_in_geohash(40.0, 10.0, "u4pruyd")
        False
    """
    logger.debug("Checking if point (lat=%f, lon=%f) is in geohash: %s", lat, lon, geohash)
    bbox: BoundingBox = get_bounding_box(geohash)
    return is_point_in_box(lat, lon, bbox)


def do_boxes_intersect(bbox1: BoundingBox, bbox2: BoundingBox) -> bool:
    """Check if two bounding boxes intersect.

    Args:
        bbox1 (BoundingBox): The first bounding box.
        bbox2 (BoundingBox): The second bounding box.

    Returns:
        bool: True if the bounding boxes intersect, False otherwise.

    Example:
        >>> box1 = BoundingBox(10.0, 20.0, 30.0, 40.0)
        >>> box2 = BoundingBox(20.0, 30.0, 40.0, 50.0)
        >>> do_boxes_intersect(box1, box2)
        True
    """
    logger.debug("Checking intersection between boxes: %s and %s", bbox1, bbox2)
    result = not (
        bbox1.max_lat < bbox2.min_lat
        or bbox1.min_lat > bbox2.max_lat
        or bbox1.max_lon < bbox2.min_lon
        or bbox1.min_lon > bbox2.max_lon
    )
    logger.debug("Boxes %s intersect", "do" if result else "do not")
    return result


def geohashes_in_box(bbox: BoundingBox, precision: int = 6) -> List[str]:
    """Find geohashes that intersect with a given bounding box.

    Args:
        bbox (BoundingBox): The bounding box to find geohashes for.
        precision (int, optional): The precision of the geohashes to return. Defaults to 6.

    Returns:
        List[str]: A list of geohashes that intersect with the bounding box.

    Example:
        >>> box = BoundingBox(57.64, 10.40, 57.65, 10.41)
        >>> sorted(geohashes_in_box(box, precision=5))
        ['u4pru']

    Note:
        The number of geohashes returned depends on the size of the bounding box
        and the precision requested. Higher precision values will result in more
        geohashes for the same bounding box.
    """
    logger.debug("Finding geohashes in box %s with precision %d", bbox, precision)

    # Find a geohash at the center of the bounding box
    center_lat: float = (bbox.min_lat + bbox.max_lat) / 2
    center_lon: float = (bbox.min_lon + bbox.max_lon) / 2
    center_geohash: str = encode(center_lat, center_lon, precision)
    logger.debug("Center geohash: %s at (lat=%f, lon=%f)", center_geohash, center_lat, center_lon)

    # Get the size of a geohash at this precision
    center_bbox: BoundingBox = get_bounding_box(center_geohash)
    lat_step: float = center_bbox.max_lat - center_bbox.min_lat
    lon_step: float = center_bbox.max_lon - center_bbox.min_lon
    logger.debug("Geohash size at precision %d: lat_step=%f, lon_step=%f", precision, lat_step, lon_step)

    # Create a set to store unique geohashes
    result: Set[str] = set()

    # Calculate the starting points slightly outside the bounding box
    # to ensure we cover the entire area
    start_lat: float = max(bbox.min_lat - lat_step, -90.0)
    end_lat: float = min(bbox.max_lat + lat_step, 90.0)
    start_lon: float = max(bbox.min_lon - lon_step, -180.0)
    end_lon: float = min(bbox.max_lon + lon_step, 180.0)
    logger.debug("Search area: lat=[%f, %f], lon=[%f, %f]", start_lat, end_lat, start_lon, end_lon)

    # Sample points in a grid pattern with spacing based on geohash size
    # This ensures we get all geohashes that intersect with the bounding box
    for lat in _float_range(start_lat, end_lat, lat_step / 2):
        for lon in _float_range(start_lon, end_lon, lon_step / 2):
            gh: str = encode(lat, lon, precision)
            gh_bbox: BoundingBox = get_bounding_box(gh)
            # Only add geohashes that actually intersect with our bounding box
            if do_boxes_intersect(bbox, gh_bbox):
                result.add(gh)

    logger.debug("Found %d intersecting geohashes", len(result))
    return list(result)


def _float_range(start: float, stop: float, step: float) -> Iterator[float]:
    """Helper function to create a range of float values.

    Args:
        start (float): The start value.
        stop (float): The stop value (inclusive).
        step (float): The step size.

    Returns:
        Iterator[float]: An iterator of float values from start to stop with the given step size.
    """
    current: float = start
    while current <= stop:
        yield current
        current += step
