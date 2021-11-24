"""
.. module:: nbgeohash
   :platform: Unix, Windows
   :synopsis: A module for encoding to and decoding from the geohash system

.. moduleauthor:: ilyas Moutawwakil <moutawwakil.ilyas.tsi@gmail.com>


"""


from math import log10

__base32 = '0123456789bcdefghjkmnpqrstuvwxyz'
#  Note: the alphabet in geohash differs from the common base32 alphabet described in IETF's RFC 4648
# (http://tools.ietf.org/html/rfc4648)

try:
    # Soft dependency
    import numpy as np
    from numba import njit, types
except ImportError:
    print('Numpy and Numba are soft dependencies to use this feature.')
    raise ImportError(
        "Couldn't import numpy or numba, make sure they are installed properly.")

__author__ = 'Ilyas Moutawwakil'


@njit(cache=True, fastmath=True)
def base32_to_int(s: types.char) -> types.uint8:
    """
    Returns the equivalent value of a base 32 character.
    Surprisingly, on Numba this approach is faster than all the others.
    More specifically, because the numba hashtable (dictionary) is slower.
    """
    res = ord(s) - 48
    if res > 9:
        res -= 40
    if res > 16:
        res -= 1
    if res > 18:
        res -= 1
    if res > 20:
        res -= 1
    return res


@njit(fastmath=True)
def nb_decode_exactly(geohash: types.string) -> types.Tuple:
    """
    Decode the geohash to its exact values, including the error
    margins of the result.  Returns four float values: latitude,
    longitude, the plus/minus error for latitude (as a positive
    number) and the plus/minus error for longitude (as a positive
    number).
    """

    lat_interval_neg, lat_interval_pos, lon_interval_neg, lon_interval_pos = -90, 90, -180, 180
    lat_err, lon_err = 90, 180
    masks = np.array([16, 8, 4, 2, 1])
    is_even = True
    for c in geohash:
        cd = base32_to_int(c)
        for mask in masks:
            if is_even:  # adds longitude info
                lon_err /= 2
                if cd & mask:
                    lon_interval_neg = (lon_interval_neg +
                                        lon_interval_pos) / 2
                else:
                    lon_interval_pos = (lon_interval_neg +
                                        lon_interval_pos) / 2
            else:  # adds latitude info
                lat_err /= 2
                if cd & mask:
                    lat_interval_neg = (lat_interval_neg +
                                        lat_interval_pos) / 2
                else:
                    lat_interval_pos = (lat_interval_neg +
                                        lat_interval_pos) / 2
            is_even = not is_even
    lat = (lat_interval_neg + lat_interval_pos) / 2
    lon = (lon_interval_neg + lon_interval_pos) / 2
    return lat, lon, lat_err, lon_err


@njit(fastmath=True)
def nb_point_decode(geohash: types.string) -> types.Tuple:
    """
    Decode geohash, returning two float with latitude and longitude containing only relevant digits.
    """

    lat, lon, lat_err, lon_err = nb_decode_exactly(geohash)
    # Format to the number of decimals that are known
    lat_dec = max(1, round(-log10(lat_err))) - 1
    lon_dec = max(1, round(-log10(lon_err))) - 1
    lat = round(lat, lat_dec)
    lon = round(lon, lon_dec)

    return lat, lon


@njit(fastmath=True, parallel=True)
def nb_vector_decode(geohashes: types.Array) -> types.Tuple:
    """
    Decode geohashes, returning two Arrays of floats with latitudes and longitudes containing only relevant digits.
    This is not exactly a vectorized version of nb_point_decode, but it is way faster and gets faster as the number of geohashes increase.
    """

    n = len(geohashes)
    lats = np.empty(n)
    lons = np.empty(n)
    for i, geohash in enumerate(geohashes):
        lat, lon, lat_err, lon_err = nb_decode_exactly(str(geohash))
        # Format to the number of decimals that are known
        lat_dec = max(1, round(-log10(lat_err))) - 1
        lon_dec = max(1, round(-log10(lon_err))) - 1
        lats[i] = round(lat, lat_dec)
        lons[i] = round(lon, lon_dec)

    return lats, lons


@njit(fastmath=True)
def nb_point_encode(latitude: types.float64, longitude: types.float64, precision: types.int8 = 12) -> types.string:
    """
    Encode a point given by latitude and longitude to a geohash of the specified precision.
    """
    lat_interval_neg, lat_interval_pos, lon_interval_neg, lon_interval_pos = -90, 90, -180, 180
    geohash = np.zeros(precision, dtype='<U1')
    bits = np.array([16, 8, 4, 2, 1])
    bit = 0
    ch = 0
    n = 0
    even = True
    while n < precision:
        if even:
            mid = (lon_interval_neg + lon_interval_pos) / 2
            if longitude > mid:
                ch |= bits[bit]
                lon_interval_neg = mid
            else:
                lon_interval_pos = mid
        else:
            mid = (lat_interval_neg + lat_interval_pos) / 2
            if latitude > mid:
                ch |= bits[bit]
                lat_interval_neg = mid
            else:
                lat_interval_pos = mid
        even = not even

        if bit < 4:
            bit += 1
        else:
            geohash[n] = __base32[ch]
            bit = 0
            ch = 0
            n += 1

    return ''.join(geohash)


@njit(fastmath=True, parallel=True)
def nb_vector_encode(latitudes: types.Array, longitudes: types.Array, precision: types.int8 = 12) -> types.Array:
    """
    Encode a vector of points given by latitudes and longitudes to a vector of geohashes of the specified precision.
    This is not exactly a vectorized version of nb_point_encode, but it is way faster and gets faster as the number of points increase.
    """
    n = len(latitudes)
    geohashes = np.empty(n, dtype='<U12')
    for i in range(n):
        geohashes[i] = nb_point_encode(latitudes[i], longitudes[i], precision)
    return geohashes
