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

// Decode a geohash string to exact latitude/longitude with error margins
static PyObject* geohash_decode_exactly(PyObject *self, PyObject *args) {
    const char *geohash;
    
    if (!PyArg_ParseTuple(args, "s", &geohash)) {
        return NULL;
    }
    
    double lat_interval[2] = {-90.0, 90.0};
    double lon_interval[2] = {-180.0, 180.0};
    double lat_err = 90.0;
    double lon_err = 180.0;
    int is_even = 1;
    int len = strlen(geohash);
    
    init_base32_decode_map();
    
    for (int i = 0; i < len; i++) {
        int cd = base32_decode_map[(int)geohash[i]];
        if (cd == -1) {
            PyErr_SetString(PyExc_ValueError, "Invalid character in geohash");
            return NULL;
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
    
    double lat = (lat_interval[0] + lat_interval[1]) / 2.0;
    double lon = (lon_interval[0] + lon_interval[1]) / 2.0;
    
    // Get the ExactLatLong named tuple class from the geohash_types module
    PyObject *module = PyImport_ImportModule("pygeohash.geohash_types");
    if (!module) {
        return NULL;
    }
    
    PyObject *exactlatlongClass = PyObject_GetAttrString(module, "ExactLatLong");
    Py_DECREF(module);
    if (!exactlatlongClass) {
        return NULL;
    }
    
    // Create a new ExactLatLong instance
    PyObject *args_tuple = Py_BuildValue("dddd", lat, lon, lat_err, lon_err);
    PyObject *exactlatlongInstance = PyObject_CallObject(exactlatlongClass, args_tuple);
    
    Py_DECREF(exactlatlongClass);
    Py_DECREF(args_tuple);
    
    return exactlatlongInstance;
}

// Python wrapper for decode function
static PyObject* geohash_decode(PyObject *self, PyObject *args) {
    const char *geohash;
    
    if (!PyArg_ParseTuple(args, "s", &geohash)) {
        return NULL;
    }
    
    // Call decode_exactly to get the coordinates and error margins
    PyObject *exact_result = geohash_decode_exactly(self, args);
    if (!exact_result) {
        return NULL;
    }
    
    // Extract values from the ExactLatLong tuple
    PyObject *lat_obj = PyObject_GetAttrString(exact_result, "latitude");
    PyObject *lon_obj = PyObject_GetAttrString(exact_result, "longitude");
    
    if (!lat_obj || !lon_obj) {
        Py_XDECREF(lat_obj);
        Py_XDECREF(lon_obj);
        Py_DECREF(exact_result);
        return NULL;
    }
    
    double lat = PyFloat_AsDouble(lat_obj);
    double lon = PyFloat_AsDouble(lon_obj);
    
    Py_DECREF(lat_obj);
    Py_DECREF(lon_obj);
    Py_DECREF(exact_result);
    
    // Get the LatLong named tuple class from the geohash_types module
    PyObject *module = PyImport_ImportModule("pygeohash.geohash_types");
    if (!module) {
        return NULL;
    }
    
    PyObject *latlongClass = PyObject_GetAttrString(module, "LatLong");
    Py_DECREF(module);
    if (!latlongClass) {
        return NULL;
    }
    
    // Create a new LatLong instance
    PyObject *args_tuple = Py_BuildValue("dd", lat, lon);
    PyObject *latlongInstance = PyObject_CallObject(latlongClass, args_tuple);
    
    Py_DECREF(latlongClass);
    Py_DECREF(args_tuple);
    
    return latlongInstance;
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

// Encode coordinates to a geohash string with strict midpoint handling
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