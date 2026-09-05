/**
 * MIT License
 *
 * Copyright (c) 2024 Will McGinnis
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 */

#define PY_SSIZE_T_CLEAN
#include <Python.h>
#include <limits.h>
#include <math.h>
#include <string.h>

// Base32 alphabet used for geohash encoding
static const char BASE32[] = "0123456789bcdefghjkmnpqrstuvwxyz";

// Mapping from byte value to its 5-bit base32 index, -1 for every
// non-alphabet byte. 256 entries so any char value (including bytes >= 128
// from multibyte UTF-8) can index it without a separate range guard.
static int base32_decode_map[256] = {0};

// Initialize the base32 decode map. Called once from the module init function.
static void init_base32_decode_map(void) {
    for (int i = 0; i < 256; i++) {
        base32_decode_map[i] = -1;
    }
    for (int i = 0; i < 32; i++) {
        base32_decode_map[(unsigned char)BASE32[i]] = i;
    }
}

// Python wrapper to expose the base32 alphabet
static PyObject* geohash_get_base32(PyObject *self, PyObject *args) {
    return PyUnicode_FromString(BASE32);
}

// Cached LatLong / ExactLatLong named-tuple classes from pygeohash.geohash_types.
// Importing the module and looking up the class on every decode call was a large
// share of decode's cost, so we resolve them once and hold the references for the
// lifetime of the process.
static PyObject *LatLong_type = NULL;
static PyObject *ExactLatLong_type = NULL;

static int ensure_types(void) {
    if (LatLong_type != NULL) {
        return 0;
    }
    PyObject *module = PyImport_ImportModule("pygeohash.geohash_types");
    if (!module) {
        return -1;
    }
    LatLong_type = PyObject_GetAttrString(module, "LatLong");
    ExactLatLong_type = PyObject_GetAttrString(module, "ExactLatLong");
    Py_DECREF(module);
    if (!LatLong_type || !ExactLatLong_type) {
        Py_CLEAR(LatLong_type);
        Py_CLEAR(ExactLatLong_type);
        return -1;
    }
    return 0;
}

// Build a named-tuple instance (LatLong / ExactLatLong) from a values tuple.
//
// A typing.NamedTuple is a plain tuple subclass whose generated __new__ does
// `tuple.__new__(cls, (field0, field1, ...))`. Calling the type the normal way
// (PyObject_CallFunction) pays for that extra Python-level __new__ on every
// decode. We skip it by invoking tuple's tp_new directly, which is exactly the
// operation the generated __new__ performs. `values` is consumed (stolen).
static PyObject* make_named_tuple(PyObject *type, PyObject *values) {
    if (!values) {
        return NULL;
    }
    PyObject *call_args = PyTuple_Pack(1, values);  // tuple.__new__(type, values)
    Py_DECREF(values);
    if (!call_args) {
        return NULL;
    }
    PyObject *result = PyTuple_Type.tp_new((PyTypeObject *)type, call_args, NULL);
    Py_DECREF(call_args);
    return result;
}

// Core decode: walk the geohash bits into a center point and error margins.
// Returns 0 on success, -1 on an invalid character (with a Python exception set).
//
// The geohash bit stream strictly alternates longitude/latitude starting with
// longitude, and each character contributes 5 bits, so character parity
// alternates: even-index characters start on a longitude bit (L A L A L for
// masks 16, 8, 4, 2, 1), odd-index characters on a latitude bit (A L A L A).
// Characters are processed in pairs, which makes the parity of every unrolled
// step a compile-time constant, with one trailing character for odd lengths.
// The floating point operations per bit (error halving, midpoint
// (lo + hi) * 0.5, and which bound is replaced) run in the original order, so
// results are bit-identical to the previous loop (verified by
// tests/test_c_codec_bit_identity.py).
static int decode_to_doubles(const char *geohash, double *out_lat, double *out_lon,
                             double *out_lat_err, double *out_lon_err) {
    double lat_lo = -90.0, lat_hi = 90.0;
    double lon_lo = -180.0, lon_hi = 180.0;
    double lat_err = 90.0;
    double lon_err = 180.0;
    size_t len = strlen(geohash);

    if (len < 1 || len > 12) {
        PyErr_SetString(PyExc_ValueError, "Geohash must be between 1 and 12 characters long");
        return -1;
    }

    size_t i = 0;
    for (; i + 1 < len; i += 2) {
        // The table guards every byte: non-alphabet bytes (including >= 128)
        // map to -1. Whether an invalid character is detected here or after
        // bisecting the first of the pair is unobservable: the caller discards
        // all interval state when -1 is returned.
        int cd0 = base32_decode_map[(unsigned char)geohash[i]];
        int cd1 = base32_decode_map[(unsigned char)geohash[i + 1]];
        if (cd0 < 0 || cd1 < 0) {
            PyErr_SetString(PyExc_ValueError, "Invalid character in geohash");
            return -1;
        }

        double mid;

        // character i (even index): lon, lat, lon, lat, lon
        lon_err *= 0.5; mid = (lon_lo + lon_hi) * 0.5; if (cd0 & 16) { lon_lo = mid; } else { lon_hi = mid; }
        lat_err *= 0.5; mid = (lat_lo + lat_hi) * 0.5; if (cd0 &  8) { lat_lo = mid; } else { lat_hi = mid; }
        lon_err *= 0.5; mid = (lon_lo + lon_hi) * 0.5; if (cd0 &  4) { lon_lo = mid; } else { lon_hi = mid; }
        lat_err *= 0.5; mid = (lat_lo + lat_hi) * 0.5; if (cd0 &  2) { lat_lo = mid; } else { lat_hi = mid; }
        lon_err *= 0.5; mid = (lon_lo + lon_hi) * 0.5; if (cd0 &  1) { lon_lo = mid; } else { lon_hi = mid; }

        // character i + 1 (odd index): lat, lon, lat, lon, lat
        lat_err *= 0.5; mid = (lat_lo + lat_hi) * 0.5; if (cd1 & 16) { lat_lo = mid; } else { lat_hi = mid; }
        lon_err *= 0.5; mid = (lon_lo + lon_hi) * 0.5; if (cd1 &  8) { lon_lo = mid; } else { lon_hi = mid; }
        lat_err *= 0.5; mid = (lat_lo + lat_hi) * 0.5; if (cd1 &  4) { lat_lo = mid; } else { lat_hi = mid; }
        lon_err *= 0.5; mid = (lon_lo + lon_hi) * 0.5; if (cd1 &  2) { lon_lo = mid; } else { lon_hi = mid; }
        lat_err *= 0.5; mid = (lat_lo + lat_hi) * 0.5; if (cd1 &  1) { lat_lo = mid; } else { lat_hi = mid; }
    }
    if (i < len) {
        // odd length: final character, even index -> starts on a longitude bit
        int cd = base32_decode_map[(unsigned char)geohash[i]];
        if (cd < 0) {
            PyErr_SetString(PyExc_ValueError, "Invalid character in geohash");
            return -1;
        }

        double mid;

        lon_err *= 0.5; mid = (lon_lo + lon_hi) * 0.5; if (cd & 16) { lon_lo = mid; } else { lon_hi = mid; }
        lat_err *= 0.5; mid = (lat_lo + lat_hi) * 0.5; if (cd &  8) { lat_lo = mid; } else { lat_hi = mid; }
        lon_err *= 0.5; mid = (lon_lo + lon_hi) * 0.5; if (cd &  4) { lon_lo = mid; } else { lon_hi = mid; }
        lat_err *= 0.5; mid = (lat_lo + lat_hi) * 0.5; if (cd &  2) { lat_lo = mid; } else { lat_hi = mid; }
        lon_err *= 0.5; mid = (lon_lo + lon_hi) * 0.5; if (cd &  1) { lon_lo = mid; } else { lon_hi = mid; }
    }

    *out_lat = (lat_lo + lat_hi) * 0.5;
    *out_lon = (lon_lo + lon_hi) * 0.5;
    *out_lat_err = lat_err;
    *out_lon_err = lon_err;
    return 0;
}

// Decode a geohash string to exact latitude/longitude with error margins
static PyObject* geohash_decode_exactly(PyObject *self, PyObject *args) {
    const char *geohash;

    if (!PyArg_ParseTuple(args, "s", &geohash)) {
        return NULL;
    }

    double lat, lon, lat_err, lon_err;
    if (decode_to_doubles(geohash, &lat, &lon, &lat_err, &lon_err) != 0) {
        return NULL;
    }
    if (ensure_types() != 0) {
        return NULL;
    }
    return make_named_tuple(ExactLatLong_type, Py_BuildValue("dddd", lat, lon, lat_err, lon_err));
}

// Python wrapper for decode function
static PyObject* geohash_decode(PyObject *self, PyObject *args) {
    const char *geohash;

    if (!PyArg_ParseTuple(args, "s", &geohash)) {
        return NULL;
    }

    // Decode straight into a LatLong: no intermediate ExactLatLong, no second
    // module import, no attribute round-trip.
    double lat, lon, lat_err, lon_err;
    if (decode_to_doubles(geohash, &lat, &lon, &lat_err, &lon_err) != 0) {
        return NULL;
    }
    if (ensure_types() != 0) {
        return NULL;
    }
    return make_named_tuple(LatLong_type, Py_BuildValue("dd", lat, lon));
}

// Argument converters for the encoders. bool is a subclass of int, so the plain
// "d"/"i" format units coerce True/False to 1.0/0.0 before any check below can
// see them; these reject booleans up front so a direct extension call matches
// the package-root wrappers' contract.
static int convert_coordinate(PyObject *obj, void *addr) {
    if (PyBool_Check(obj)) {
        PyErr_SetString(PyExc_ValueError, "latitude and longitude must be numbers, not booleans");
        return 0;
    }
    double value = PyFloat_AsDouble(obj);
    if (value == -1.0 && PyErr_Occurred()) {
        return 0;
    }
    *(double *)addr = value;
    return 1;
}

static int convert_precision(PyObject *obj, void *addr) {
    if (PyBool_Check(obj)) {
        PyErr_SetString(PyExc_ValueError, "precision must be an integer, not a boolean");
        return 0;
    }
    PyObject *index = PyNumber_Index(obj);
    if (index == NULL) {
        return 0;
    }
    long value = PyLong_AsLong(index);
    Py_DECREF(index);
    if (value == -1 && PyErr_Occurred()) {
        return 0;
    }
    if (value < INT_MIN || value > INT_MAX) {
        PyErr_SetString(PyExc_OverflowError, "Python int too large to convert to C int");
        return 0;
    }
    *(int *)addr = (int)value;
    return 1;
}

// Shared validation + normalization for the encoders: rejects non-finite
// coordinates and out-of-range precision (same checks, same order, same
// exceptions as before), clamps latitude to [-90, 90] and wraps longitude
// into [-180, 180]. Returns 0 on success, -1 with an exception set.
static int prepare_encode(double *latitude, double *longitude, int precision) {
    if (!isfinite(*latitude) || !isfinite(*longitude)) {
        PyErr_SetString(PyExc_ValueError, "latitude and longitude must be finite");
        return -1;
    }

    if (precision < 1 || precision > 12) {
        PyErr_SetString(PyExc_ValueError, "precision must be between 1 and 12");
        return -1;
    }

    // Ensure latitude is between -90 and 90
    if (*latitude < -90.0) *latitude = -90.0;
    if (*latitude > 90.0) *latitude = 90.0;

    // Ensure longitude is between -180 and 180
    while (*longitude < -180.0) *longitude += 360.0;
    while (*longitude > 180.0) *longitude -= 360.0;

    return 0;
}

// Shared encode core: bisect the lat/lon intervals, emitting `precision`
// base32 characters into `geohash` (must have room for precision + 1 bytes).
//
// The bit stream strictly alternates longitude/latitude starting with
// longitude and each character covers 5 bits, so character parity alternates:
// even-index characters bisect lon, lat, lon, lat, lon (masks 16, 8, 4, 2, 1),
// odd-index characters lat, lon, lat, lon, lat. Characters are emitted in
// pairs - always longitude-first - plus one trailing character for odd
// precision, which makes the parity of every unrolled step a compile-time
// constant. The midpoint arithmetic ((lo + hi) * 0.5), the >= midpoint
// comparisons, and the interval replacements run in the original order, so
// outputs are bit-identical to the previous loop (verified by
// tests/test_c_codec_bit_identity.py).
static void encode_core(double latitude, double longitude, int precision, char *geohash) {
    double lat_lo = -90.0, lat_hi = 90.0;
    double lon_lo = -180.0, lon_hi = 180.0;
    int hash_index = 0;

    while (hash_index + 1 < precision) {
        double mid;
        int ch;

        // even-index character: lon, lat, lon, lat, lon
        ch = 0;
        mid = (lon_lo + lon_hi) * 0.5;
        if (longitude >= mid) { ch |= 16; lon_lo = mid; } else { lon_hi = mid; }
        mid = (lat_lo + lat_hi) * 0.5;
        if (latitude >= mid) { ch |= 8; lat_lo = mid; } else { lat_hi = mid; }
        mid = (lon_lo + lon_hi) * 0.5;
        if (longitude >= mid) { ch |= 4; lon_lo = mid; } else { lon_hi = mid; }
        mid = (lat_lo + lat_hi) * 0.5;
        if (latitude >= mid) { ch |= 2; lat_lo = mid; } else { lat_hi = mid; }
        mid = (lon_lo + lon_hi) * 0.5;
        if (longitude >= mid) { ch |= 1; lon_lo = mid; } else { lon_hi = mid; }
        geohash[hash_index++] = BASE32[ch];

        // odd-index character: lat, lon, lat, lon, lat
        ch = 0;
        mid = (lat_lo + lat_hi) * 0.5;
        if (latitude >= mid) { ch |= 16; lat_lo = mid; } else { lat_hi = mid; }
        mid = (lon_lo + lon_hi) * 0.5;
        if (longitude >= mid) { ch |= 8; lon_lo = mid; } else { lon_hi = mid; }
        mid = (lat_lo + lat_hi) * 0.5;
        if (latitude >= mid) { ch |= 4; lat_lo = mid; } else { lat_hi = mid; }
        mid = (lon_lo + lon_hi) * 0.5;
        if (longitude >= mid) { ch |= 2; lon_lo = mid; } else { lon_hi = mid; }
        mid = (lat_lo + lat_hi) * 0.5;
        if (latitude >= mid) { ch |= 1; lat_lo = mid; } else { lat_hi = mid; }
        geohash[hash_index++] = BASE32[ch];
    }
    if (hash_index < precision) {
        // odd precision: final character, even index -> longitude first
        double mid;
        int ch = 0;

        mid = (lon_lo + lon_hi) * 0.5;
        if (longitude >= mid) { ch |= 16; lon_lo = mid; } else { lon_hi = mid; }
        mid = (lat_lo + lat_hi) * 0.5;
        if (latitude >= mid) { ch |= 8; lat_lo = mid; } else { lat_hi = mid; }
        mid = (lon_lo + lon_hi) * 0.5;
        if (longitude >= mid) { ch |= 4; lon_lo = mid; } else { lon_hi = mid; }
        mid = (lat_lo + lat_hi) * 0.5;
        if (latitude >= mid) { ch |= 2; lat_lo = mid; } else { lat_hi = mid; }
        mid = (lon_lo + lon_hi) * 0.5;
        if (longitude >= mid) { ch |= 1; lon_lo = mid; } else { lon_hi = mid; }
        geohash[hash_index++] = BASE32[ch];
    }

    geohash[hash_index] = '\0';
}
// Build the output string directly: the result is pure-ASCII base32 with a
// known length, so PyUnicode_New + copy skips the strlen and UTF-8 scanning
// that PyUnicode_FromString performs. maxchar 127 forces the compact 1-byte
// (ASCII) representation.
static PyObject* make_hash_string(const char *geohash, int precision) {
    PyObject *result = PyUnicode_New((Py_ssize_t)precision, 127);
    if (result == NULL) {
        return NULL;
    }
    memcpy((char *)PyUnicode_1BYTE_DATA(result), geohash, (size_t)precision);
    return result;
}

// Encode coordinates to a geohash string
static PyObject* geohash_encode(PyObject *self, PyObject *args, PyObject *kwargs) {
    double latitude, longitude;
    int precision = 12;

    static char *kwlist[] = {"latitude", "longitude", "precision", NULL};

    if (!PyArg_ParseTupleAndKeywords(args, kwargs, "O&O&|O&", kwlist,
                                    convert_coordinate, &latitude,
                                    convert_coordinate, &longitude,
                                    convert_precision, &precision)) {
        return NULL;
    }

    if (prepare_encode(&latitude, &longitude, precision) != 0) {
        return NULL;
    }

    char geohash[13] = {0};  // Maximum precision is 12 + null terminator
    encode_core(latitude, longitude, precision, geohash);
    return make_hash_string(geohash, precision);
}

// Encode coordinates to a geohash string.
//
// NOTE: This is intentionally identical to geohash_encode above. Despite the
// "strictly" name, it runs the same validation and the same interval-bisection
// core and produces the same output for every input. It is kept as a separate
// entry point only for API/back-compatibility.
static PyObject* geohash_encode_strictly(PyObject *self, PyObject *args, PyObject *kwargs) {
    double latitude, longitude;
    int precision = 12;

    static char *kwlist[] = {"latitude", "longitude", "precision", NULL};

    if (!PyArg_ParseTupleAndKeywords(args, kwargs, "O&O&|O&", kwlist,
                                    convert_coordinate, &latitude,
                                    convert_coordinate, &longitude,
                                    convert_precision, &precision)) {
        return NULL;
    }

    if (prepare_encode(&latitude, &longitude, precision) != 0) {
        return NULL;
    }

    char geohash[13] = {0};  // Maximum precision is 12 + null terminator
    encode_core(latitude, longitude, precision, geohash);
    return make_hash_string(geohash, precision);
}

// Module method definitions
static PyMethodDef GeohashMethods[] = {
    {"decode_exactly", geohash_decode_exactly, METH_VARARGS, 
     "Decode a geohash to its exact values, including error margins."},
    {"decode", geohash_decode, METH_VARARGS, 
     "Decode a geohash to latitude and longitude coordinates."},
    {"encode", (PyCFunction)geohash_encode, METH_VARARGS | METH_KEYWORDS, 
     "Encode coordinates to a geohash string."},
    {"encode_strictly", (PyCFunction)geohash_encode_strictly, METH_VARARGS | METH_KEYWORDS, 
     "Encode coordinates to a geohash string with strict midpoint handling."},
    {"get_base32", geohash_get_base32, METH_NOARGS, 
     "Get the base32 alphabet used for geohash encoding."},
    {NULL, NULL, 0, NULL}  // Sentinel
};

// Module definition
static struct PyModuleDef geohashmodule = {
    PyModuleDef_HEAD_INIT,
    "cgeohash.geohash_module",
    "C implementation of geohash encoding and decoding",
    -1,
    GeohashMethods
};

// Module initialization function
PyMODINIT_FUNC PyInit_geohash_module(void) {
    init_base32_decode_map();
    return PyModule_Create(&geohashmodule);
}
