v3.2.0
======

 * Added input validation for latitude and longitude in encode functions to prevent invalid coordinates from being processed
 * Latitude values must now be between -90.0 and 90.0 degrees
 * Longitude values must now be between -180.0 and 180.0 degrees
 * Both encode() and encode_strictly() functions now raise ValueError with descriptive messages for invalid coordinates

v3.1.3
======

 * Updating pypi email to registered domain
 
v3.1.2
======

 * bugfix inadvertantly requiring numpy and pandas for type checks; they are now required for mypy but not at runtime.

v3.1.1
======

 * Added input validation to raise on invliad precisions and geohashes before sending to c lib
 
v3.1.0
======

 * Added comprehensive logging
 * Added type hints and a types module
 
v3.0.0
======

 * [meta] rewrote core logic from scratch in cpython for performance and to remove geohash.py dependency 
 * [meta] relicensed to MIT for more permissive use 
 * [meta] removed numba and numpy deps

v2.1.0
======

 * [bounding_box] added bounding box module 
 * [viz] added visualization module 
 * [docs] updated docstrings across the library 
 * [meta] added cursor rulesfiles 


v2.0.3
======

* [meta] restructured as pyproject.toml based project
* [meta] added ruff and tox configs 
* [meta] added gh actions workflows
* [docs] added proper sphinxdocs and background info 


v1.2.0
======

 * [stats] added variance
 * [stats] added standard deviation
 
v1.1.0
======

 * Added stats module
 * [stats] added mean geohash
 * [stats] added northernmost
 * [stats] added southernmost
 * [stats] added westernmost
 * [stats] added easternmost

v1.0.0
======

 * New repository created, based off of [geohash](https://github.com/vinsci/geohash)
 * Basic approximate distance added