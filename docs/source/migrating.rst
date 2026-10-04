Migrating from python-geohash to PyGeoHash
==========================================

Apache Superset merged this migration on March 4, 2026 (`PR
#37524 <https://github.com/apache/superset/pull/37524>`__). Its description
gave the motivation as running the container without compiling a C++ extension
for ``python-geohash``, named ``.bbox()`` as the one API difference, and added
that the new library was "slower than the status quo". That last point was a
fair objection then. On the project's published benchmark it no longer holds
for encode and decode, and still holds, narrowly, for bounding boxes (see
:ref:`Performance <performance>`).

This is an API migration guide, not a claim that every current
``python-geohash`` installation compiles anything: ``python-geohash`` 0.9.2
publishes a manylinux x86-64 wheel.

Install and import
------------------

.. code:: console

   uv remove python-geohash
   uv add pygeohash

``python-geohash`` installs as ``python-geohash`` but imports as ``geohash``;
PyGeoHash installs and imports as ``pygeohash``.

.. code:: python

   # Before
   import geohash

   # After
   import pygeohash as pgh

Symbol-by-symbol changes
------------------------

Checked against PyGeoHash 3.5.1 and ``python-geohash`` 0.9.2, both installed
from PyPI into a clean environment.

+-----------------------------------------+-----------------------------------------------+------------------------+
| ``python-geohash``                      | PyGeoHash                                     | Migration note         |
+=========================================+===============================================+========================+
| ``geohash.encode(lat, lon, precision)`` | ``pgh.encode(lat, lon, precision=precision)`` | Same                   |
|                                         |                                               | latitude/longitude     |
|                                         |                                               | order. Both default to |
|                                         |                                               | 12 characters; pass    |
|                                         |                                               | the precision          |
|                                         |                                               | explicitly anyway.     |
+-----------------------------------------+-----------------------------------------------+------------------------+
| ``geohash.decode(code)``                | ``pgh.decode(code)``                          | Both return the cell   |
|                                         |                                               | center as a            |
|                                         |                                               | latitude/longitude     |
|                                         |                                               | pair; PyGeoHash        |
|                                         |                                               | returns a named tuple, |
|                                         |                                               | which still unpacks    |
|                                         |                                               | the same way.          |
+-----------------------------------------+-----------------------------------------------+------------------------+
| ``geohash.decode_exactly(code)``        | ``pgh.decode_exactly(code)``                  | Both return latitude,  |
|                                         |                                               | longitude, and the     |
|                                         |                                               | latitude and longitude |
|                                         |                                               | error margins.         |
+-----------------------------------------+-----------------------------------------------+------------------------+
| ``geohash.neighbors(code)``             | ``pgh.get_adjacent(code, direction)``         | Not drop-in.           |
|                                         |                                               | ``python-geohash``     |
|                                         |                                               | returns all eight      |
|                                         |                                               | neighbors as a list;   |
|                                         |                                               | PyGeoHash returns one  |
|                                         |                                               | ``"top"``,             |
|                                         |                                               | ``"right"``,           |
|                                         |                                               | ``"bottom"``, or       |
|                                         |                                               | ``"left"`` neighbor    |
|                                         |                                               | per call.              |
+-----------------------------------------+-----------------------------------------------+------------------------+
| ``geohash.expand(code)``                | compose ``pgh.get_adjacent`` calls            | Not drop-in.           |
|                                         |                                               | ``expand()`` returns   |
|                                         |                                               | nine codes: the cell   |
|                                         |                                               | and its eight          |
|                                         |                                               | neighbors. Diagonals   |
|                                         |                                               | need two chained       |
|                                         |                                               | ``get_adjacent``       |
|                                         |                                               | calls.                 |
+-----------------------------------------+-----------------------------------------------+------------------------+
| ``geohash.bbox(code)``                  | ``pgh.get_bounding_box(code)``                | Not drop-in: a         |
|                                         |                                               | dictionary with ``s``, |
|                                         |                                               | ``w``, ``n``, ``e``    |
|                                         |                                               | keys becomes a         |
|                                         |                                               | ``BoundingBox`` named  |
|                                         |                                               | tuple.                 |
+-----------------------------------------+-----------------------------------------------+------------------------+

The ``bbox()`` gap
------------------

This is the gap Superset handled explicitly. ``pgh.get_bounding_box()``
returns a ``BoundingBox`` named tuple with ``min_lat``, ``min_lon``,
``max_lat``, and ``max_lon`` fields. If downstream code expects the old
dictionary, wrap it:

.. code:: python

   import pygeohash as pgh


   def bbox(code: str) -> dict[str, float]:
       box = pgh.get_bounding_box(code)
       return {
           "s": box.min_lat,
           "w": box.min_lon,
           "n": box.max_lat,
           "e": box.max_lon,
       }

For ``ezs42e44y`` the wrapper returns the same four values as
``geohash.bbox("ezs42e44y")``.

The eight-neighbor and expand gap
---------------------------------

If you used ``neighbors()`` or ``expand()``, compose the four cardinal calls.
A diagonal neighbor is a horizontal step followed by a vertical one:

.. code:: python

   import pygeohash as pgh


   def neighbors(code: str) -> list[str]:
       top = pgh.get_adjacent(code, "top")
       bottom = pgh.get_adjacent(code, "bottom")
       return [
           top,
           pgh.get_adjacent(top, "right"),
           pgh.get_adjacent(code, "right"),
           pgh.get_adjacent(bottom, "right"),
           bottom,
           pgh.get_adjacent(bottom, "left"),
           pgh.get_adjacent(code, "left"),
           pgh.get_adjacent(top, "left"),
       ]

The order differs from ``geohash.neighbors()``; compare as sets, and
``[code, *neighbors(code)]`` stands in for ``expand()``. For cells in the top
or bottom row, ``pgh.get_adjacent`` raises ``ValueError`` for a step beyond
the pole, where ``python-geohash`` returns the neighbors that exist, so catch
it if your data reaches the poles.


.. _performance:

Performance
-----------

The published benchmark (run 2026-09-06 on a Linux x86-64 Xeon, CPython
3.13.14, PyGeoHash 3.5.1 against ``python-geohash`` 0.9.2, median of three
timed runs) reports:

+--------------------+-----------+--------------------+--------------------+
| Operation          | PyGeoHash | ``python-geohash`` | Result             |
+====================+===========+====================+====================+
| Encode, precision  | 571 ns    | 627 ns             | PyGeoHash 1.10x    |
| 9                  |           |                    | faster             |
+--------------------+-----------+--------------------+--------------------+
| Decode             | 556 ns    | 814 ns             | PyGeoHash 1.46x    |
|                    |           |                    | faster             |
+--------------------+-----------+--------------------+--------------------+
| Bounding box       | 1,078 ns  | 939 ns             | ``python-geohash`` |
|                    |           |                    | 1.15x faster       |
+--------------------+-----------+--------------------+--------------------+

The two libraries' encode ranges do not overlap (PyGeoHash 476 to 580 ns,
``python-geohash`` 588 to 652 ns), but the margin is small, and this is one
machine. Rerun the suite where your workload runs before relying on it. Full
tables, method and the reproduction command are on the :doc:`benchmarks
page <benchmarks>`.

Container installs
------------------

PyGeoHash 3.5.1 publishes wheels for Windows, macOS, manylinux x86-64, and
manylinux ARM64 across supported CPython versions, so a matching wheel avoids
compiling the C extension at install time.

PyGeoHash publishes no musllinux wheels. Alpine and other musl environments
fall back to the source distribution and need build tooling. Check the files
for the release and platform you deploy before treating installation as
compiler-free.

Verify the migration
--------------------

Run the existing tests first, then add a parity check around the coordinates
and precisions your application uses:

.. code:: python

   import geohash
   import pygeohash as pgh

   samples = [(42.6, -5.6, 9), (57.64911, 10.40744, 7)]

   for lat, lon, precision in samples:
       assert pgh.encode(lat, lon, precision=precision) == geohash.encode(
           lat, lon, precision
       )

The project's comparison suite applies the same principle and asserts the
result of every measured call before reporting a timing.
