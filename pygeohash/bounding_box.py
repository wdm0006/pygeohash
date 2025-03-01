"""Bounding box operations for geohashes.

This module provides functions for working with geohash bounding boxes,
including calculating the bounding box for a geohash and operations
related to geospatial regions.
"""

from typing import List, NamedTuple

from pygeohash.geohash import decode_exactly, encode


class BoundingBox(NamedTuple):
    """Named tuple representing a geospatial bounding box.

    Attributes:
        min_lat (float): The minimum (southern) latitude of the box in decimal degrees.
        min_lon (float): The minimum (western) longitude of the box in decimal degrees.
        max_lat (float): The maximum (northern) latitude of the box in decimal degrees.
        max_lon (float): The maximum (eastern) longitude of the box in decimal degrees.
    """

    min_lat: float
    min_lon: float
    max_lat: float
    max_lon: float


def get_bounding_box(geohash: str) -> BoundingBox:
    """Calculate the bounding box for a geohash.

    Args:
        geohash (str): The geohash string to calculate the bounding box for.

    Returns:
        BoundingBox: A named tuple containing the minimum and maximum latitude and longitude
            values that define the bounding box of the geohash.

    Example:
        >>> get_bounding_box("u4pruyd")
        BoundingBox(min_lat=57.649, min_lon=10.407, max_lat=57.649, max_lon=10.407)

    Note:
        The precision of the coordinates in the bounding box depends on the length
        of the geohash. Longer geohashes result in smaller bounding boxes with more
        precise coordinates.
    """
    # Get the center point and error margins
    lat, lon, lat_err, lon_err = decode_exactly(geohash)

    # Calculate the bounding box coordinates
    min_lat = lat - lat_err
    min_lon = lon - lon_err
    max_lat = lat + lat_err
    max_lon = lon + lon_err

    return BoundingBox(min_lat, min_lon, max_lat, max_lon)


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
    return bbox.min_lat <= lat <= bbox.max_lat and bbox.min_lon <= lon <= bbox.max_lon


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
    bbox = get_bounding_box(geohash)
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
    return not (
        bbox1.max_lat < bbox2.min_lat
        or bbox1.min_lat > bbox2.max_lat
        or bbox1.max_lon < bbox2.min_lon
        or bbox1.min_lon > bbox2.max_lon
    )


def geohashes_in_box(bbox: BoundingBox, precision: int = 6) -> List[str]:
    """Find geohashes that intersect with a given bounding box.

    Args:
        bbox (BoundingBox): The bounding box to find geohashes for.
        precision (int, optional): The precision of the geohashes to return. Defaults to 6.

    Returns:
        List[str]: A list of geohashes that intersect with the bounding box.

    Example:
        >>> box = BoundingBox(57.64, 10.40, 57.65, 10.41)
        >>> geohashes_in_box(box, precision=5)
        ['u4pru', 'u4prv']

    Note:
        The number of geohashes returned depends on the size of the bounding box
        and the precision requested. Higher precision values will result in more
        geohashes for the same bounding box.
    """
    # Calculate step size based on precision (approximate)
    lat_step = 180.0 / (2 ** (5 * precision / 2))
    lon_step = 360.0 / (2 ** (5 * precision / 2))

    # Create a set to store unique geohashes
    result = set()

    # Sample points along the edges
    # Top and bottom edges (constant latitude)
    for lon in _float_range(bbox.min_lon, bbox.max_lon, lon_step):
        result.add(encode(bbox.min_lat, lon, precision))
        result.add(encode(bbox.max_lat, lon, precision))

    # Left and right edges (constant longitude)
    for lat in _float_range(bbox.min_lat, bbox.max_lat, lat_step):
        result.add(encode(lat, bbox.min_lon, precision))
        result.add(encode(lat, bbox.max_lon, precision))

    # Sample interior points in a grid pattern to catch geohashes completely within the box
    # Use a smaller step size for the interior to ensure we catch all geohashes
    interior_lat_step = lat_step / 2
    interior_lon_step = lon_step / 2

    # Calculate the number of steps to take in each direction
    lat_range = bbox.max_lat - bbox.min_lat
    lon_range = bbox.max_lon - bbox.min_lon

    # Only sample interior points if the box is large enough
    if lat_range > interior_lat_step * 3 and lon_range > interior_lon_step * 3:
        # Start slightly inside the box to avoid edge points
        start_lat = bbox.min_lat + interior_lat_step
        end_lat = bbox.max_lat - interior_lat_step
        start_lon = bbox.min_lon + interior_lon_step
        end_lon = bbox.max_lon - interior_lon_step

        for lat in _float_range(start_lat, end_lat, interior_lat_step):
            for lon in _float_range(start_lon, end_lon, interior_lon_step):
                result.add(encode(lat, lon, precision))

    return list(result)


def _float_range(start: float, stop: float, step: float) -> List[float]:
    """Helper function to create a range of float values.

    Args:
        start (float): The start value.
        stop (float): The stop value (inclusive).
        step (float): The step size.

    Returns:
        List[float]: A list of float values from start to stop with the given step size.
    """
    result = []
    current = start
    while current <= stop:
        result.append(current)
        current += step
    return result
