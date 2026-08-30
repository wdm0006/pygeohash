"""Static typing fixture for the directly importable native decoder API."""

from pygeohash.cgeohash import geohash_module

decoded = geohash_module.decode("u4pruyd")
latitude: float = decoded.latitude
longitude: float = decoded.longitude

decoded_exactly = geohash_module.decode_exactly("u4pruyd")
exact_latitude: float = decoded_exactly.latitude
exact_longitude: float = decoded_exactly.longitude
latitude_error: float = decoded_exactly.latitude_error
longitude_error: float = decoded_exactly.longitude_error
