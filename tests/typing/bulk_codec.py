"""Static typing fixture for the bulk encode/decode API."""

import array

import pygeohash as pgh

hashes: list[str] = pgh.encode_many([42.6, 57.6], (-5.6, 10.4), precision=5)
hashes_from_array: list[str] = pgh.encode_many(array.array("d", [42.6]), array.array("d", [-5.6]))
points: list[pgh.LatLong] = pgh.decode_many(hashes)
first_latitude: float = points[0].latitude
points_from_generator: list[pgh.LatLong] = pgh.decode_many(h for h in hashes)
