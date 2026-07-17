v3.3.1
======

 * [bugfix] `encode`/`encode_strictly` in the C extension now reject a precision outside 1-12 with a ValueError. Calling `pygeohash.cgeohash.geohash_module.encode` directly with a larger precision previously overran a fixed-size buffer.
 * [bugfix] the C encoders now reject NaN and infinite coordinates with a ValueError. Passing an infinite longitude previously hung the call.
 * [bugfix] `geohash_approximate_distance` now returns 0.0 for two identical geohashes instead of the precision-table value for their shared prefix.
 * [bugfix] `geohashes_in_box` now clamps its sampling range to latitude +/-90 and longitude +/-180, so boxes touching the world limits enumerate correctly.
 * [bugfix] `plot_geohashes` works again with matplotlib >= 3.9, which removed `matplotlib.cm.get_cmap`.
 * [packaging] the `py.typed` marker is now shipped in the wheel and sdist, so type checkers finally see pygeohash's inline type hints. The "Typing :: Typed" classifier is now accurate.
 * [docs] `encode_strictly` no longer claims to perform extra validation. It is identical to `encode` and is kept only as a back-compatible alias.

v3.3.0
======

 * [perf] reworked the C decode path: cache the LatLong/ExactLatLong types instead of importing them per call, decode straight into a LatLong without building and discarding an intermediate ExactLatLong, and construct the result tuple directly (decode ~3x faster, bounding box ~1.5x faster)
 * [perf] trimmed the Python wrappers: dropped redundant per-character validation (the C extension already validates) and per-call debug logging from the encode/decode/bounding-box hot paths
 * [bugfix] fixed a latent out-of-bounds read in the C decoder for input bytes >= 128 (e.g. multibyte UTF-8); these are now cleanly rejected as invalid characters
 * [tests] added a cross-library benchmark suite comparing pygeohash against other geohash libraries, behind an optional 'benchmark' extra

v3.2.2
======

 * Fresh release for more wheels
 
v3.2.1
======
 
 * bugfix

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