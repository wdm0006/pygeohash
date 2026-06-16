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
#include <math.h>
#include <string.h>

// Base32 alphabet used for geohash encoding
static const char BASE32[] = "0123456789bcdefghjkmnpqrstuvwxyz";

// Mapping from base32 character to its index value
static int base32_decode_map[128] = {0};

// Initialize the base32 decode map
static void init_base32_decode_map() {
    static int initialized = 0;
    if (!initialized) {
        // Initialize all to -1 (invalid)
        for (int i = 0; i < 128; i++) {
            base32_decode_map[i] = -1;
        }
        // Set valid values
        for (int i = 0; i < 32; i++) {
            base32_decode_map[(int)BASE32[i]] = i;
        }
        initialized = 1;
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
static int decode_to_doubles(const char *geohash, double *out_lat, double *out_lon,
                             double *out_lat_err, double *out_lon_err) {
    double lat_interval[2] = {-90.0, 90.0};
    double lon_interval[2] = {-180.0, 180.0};
    double lat_err = 90.0;
    double lon_err = 180.0;
    int is_even = 1;
    size_t len = strlen(geohash);

    init_base32_decode_map();

    for (size_t i = 0; i < len; i++) {
        unsigned char c = (unsigned char)geohash[i];
        // Guard the table lookup: bytes >= 128 (e.g. multibyte UTF-8) must not
        // index past base32_decode_map, they are simply invalid.
        int cd = (c < 128) ? base32_decode_map[c] : -1;
        if (cd == -1) {
            PyErr_SetString(PyExc_ValueError, "Invalid character in geohash");
            return -1;
        }

        // Process each bit of the base32 character
        for (int mask = 16; mask > 0; mask >>= 1) {
            if (is_even) {  // longitude
                lon_err /= 2.0;
                if (cd & mask) {
                    lon_interval[0] = (lon_interval[0] + lon_interval[1]) / 2.0;
                } else {
                    lon_interval[1] = (lon_interval[0] + lon_interval[1]) / 2.0;
                }
            } else {  // latitude
                lat_err /= 2.0;
                if (cd & mask) {
                    lat_interval[0] = (lat_interval[0] + lat_interval[1]) / 2.0;
                } else {
                    lat_interval[1] = (lat_interval[0] + lat_interval[1]) / 2.0;
                }
            }
            is_even = !is_even;
        }
    }

    *out_lat = (lat_interval[0] + lat_interval[1]) / 2.0;
    *out_lon = (lon_interval[0] + lon_interval[1]) / 2.0;
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

// Encode coordinates to a geohash string
static PyObject* geohash_encode(PyObject *self, PyObject *args, PyObject *kwargs) {
    double latitude, longitude;
    int precision = 12;
    
    static char *kwlist[] = {"latitude", "longitude", "precision", NULL};
    
    if (!PyArg_ParseTupleAndKeywords(args, kwargs, "dd|i", kwlist, 
                                    &latitude, &longitude, &precision)) {
        return NULL;
    }
    
    // Ensure latitude is between -90 and 90
    if (latitude < -90.0) latitude = -90.0;
    if (latitude > 90.0) latitude = 90.0;
    
    // Ensure longitude is between -180 and 180
    while (longitude < -180.0) longitude += 360.0;
    while (longitude > 180.0) longitude -= 360.0;
    
    double lat_interval[2] = {-90.0, 90.0};
    double lon_interval[2] = {-180.0, 180.0};
    char geohash[13] = {0};  // Maximum precision is 12 + null terminator
    int bits[] = {16, 8, 4, 2, 1};
    int bit = 0;
    int ch = 0;
    int is_even = 1;
    int hash_index = 0;
    
    while (hash_index < precision) {
        if (is_even) {  // longitude
            double mid = (lon_interval[0] + lon_interval[1]) / 2.0;
            if (longitude >= mid) {
                ch |= bits[bit];
                lon_interval[0] = mid;
            } else {
                lon_interval[1] = mid;
            }
        } else {  // latitude
            double mid = (lat_interval[0] + lat_interval[1]) / 2.0;
            if (latitude >= mid) {
                ch |= bits[bit];
                lat_interval[0] = mid;
            } else {
                lat_interval[1] = mid;
            }
        }
        
        is_even = !is_even;
        
        if (bit < 4) {
            bit++;
        } else {
            geohash[hash_index++] = BASE32[ch];
            bit = 0;
            ch = 0;
        }
    }
    
    geohash[hash_index] = '\0';
    return PyUnicode_FromString(geohash);
}

// Encode coordinates to a geohash string.
//
// NOTE: This is intentionally identical to geohash_encode above. Despite the
// "strictly" name, it performs the same interval-bisection encoding with the
// same midpoint handling and produces the same output for every input. It is
// kept as a separate entry point only for API/back-compatibility.
static PyObject* geohash_encode_strictly(PyObject *self, PyObject *args, PyObject *kwargs) {
    double latitude, longitude;
    int precision = 12;
    
    static char *kwlist[] = {"latitude", "longitude", "precision", NULL};
    
    if (!PyArg_ParseTupleAndKeywords(args, kwargs, "dd|i", kwlist, 
                                    &latitude, &longitude, &precision)) {
        return NULL;
    }
    
    // Ensure latitude is between -90 and 90
    if (latitude < -90.0) latitude = -90.0;
    if (latitude > 90.0) latitude = 90.0;
    
    // Ensure longitude is between -180 and 180
    while (longitude < -180.0) longitude += 360.0;
    while (longitude > 180.0) longitude -= 360.0;
    
    double lat_interval[2] = {-90.0, 90.0};
    double lon_interval[2] = {-180.0, 180.0};
    char geohash[13] = {0};  // Maximum precision is 12 + null terminator
    int bits[] = {16, 8, 4, 2, 1};
    int bit = 0;
    int ch = 0;
    int is_even = 1;
    int hash_index = 0;
    
    while (hash_index < precision) {
        if (is_even) {  // longitude
            double mid = (lon_interval[0] + lon_interval[1]) / 2.0;
            if (longitude >= mid) {
                ch |= bits[bit];
                lon_interval[0] = mid;
            } else {
                lon_interval[1] = mid;
            }
        } else {  // latitude
            double mid = (lat_interval[0] + lat_interval[1]) / 2.0;
            if (latitude >= mid) {
                ch |= bits[bit];
                lat_interval[0] = mid;
            } else {
                lat_interval[1] = mid;
            }
        }
        
        is_even = !is_even;
        
        if (bit < 4) {
            bit++;
        } else {
            geohash[hash_index++] = BASE32[ch];
            bit = 0;
            ch = 0;
        }
    }
    
    geohash[hash_index] = '\0';
    return PyUnicode_FromString(geohash);
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
    return PyModule_Create(&geohashmodule);
} 