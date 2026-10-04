Geohash precision to meters: derivation, latitude and privacy
=============================================================

**Geohash precision is the number of characters in the code. Each character
adds five bits, so cell width and height shrink by alternating factors of 8
and 4. At the equator, precision 5 is about 4.9 km × 4.9 km, precision 7 is
about 153 m × 153 m, and precision 9 is about 4.77 m × 4.77 m.** PyGeoHash
accepts precisions 1 through 12. (`PyGeoHash precision
validation <https://github.com/wdm0006/pygeohash/blob/6ba72196af6061652c14f4d8194b0f4f0b0d0541/pygeohash/geohash.py>`__)

The full 12-row table
---------------------

The complete table, from precision 1 (about 5,000 km) to precision 12 (about
3.7 cm by 1.9 cm), is in :doc:`Geohash concepts <concepts>`. This page does
not repeat it. It exists for what that table does not give you: where the
numbers come from, how width changes with latitude, and what truncating a code
does and does not do for privacy.

These are **cell dimensions, not error radii or source-coordinate accuracy**.
A decoded center is at most half the cell width and half the cell height from
a point encoded inside it, before considering the accuracy of the original
coordinates.

Where every number comes from
-----------------------------

The table is calculated, not copied. A code of length ``n`` contains ``5n``
bits. Geohash assigns the first bit to longitude and then alternates, so:

.. code:: text

   longitude_bits = ceil(5n / 2)
   latitude_bits  = floor(5n / 2)
   longitude_span = 360° / 2^longitude_bits
   latitude_span  = 180° / 2^latitude_bits

The linear dimensions use the International Union of Geodesy and Geophysics
mean Earth radius, ``R = 6,371,008.8 m``, and spherical arc length
``distance = R × angle in radians``. Thus:

.. code:: text

   equatorial_width = R × radians(longitude_span)
   height            = R × radians(latitude_span)

The radius is the documented IUGG mean-radius formula
``(2a + b) / 3 = 6,371,008.771... m``, rounded to one decimal place. (`geopy distance
documentation <https://geopy.readthedocs.io/en/stable/#module-geopy.distance>`__)
The bit allocation follows directly from conventional geohash's five-bit
Base32 characters and alternating longitude/latitude subdivisions. (`PyGeoHash
encoder <https://github.com/wdm0006/pygeohash/blob/6ba72196af6061652c14f4d8194b0f4f0b0d0541/pygeohash/cgeohash/geohash_module.c>`__)

To reproduce every row:

.. code:: python

   import math
   R = 6_371_008.8

   for n in range(1, 13):
       lon_bits, lat_bits = (5 * n + 1) // 2, (5 * n) // 2
       width = R * math.radians(360 / 2**lon_bits)
       height = R * math.radians(180 / 2**lat_bits)
       print(n, width, height)

Width changes with latitude
---------------------------

The table reports maximum east-west width at the equator. On the spherical
model, multiply that width by ``cos(latitude)`` for the cell's approximate
width elsewhere:

.. code:: text

   width_at_latitude ≈ equatorial_width × cos(latitude)

For example, a precision-7 cell is about 152.7 m wide at the equator, about
108.0 m wide at 45°, and about 76.4 m wide at 60°. Its north-south height
remains about 152.7 m in this model. Real ellipsoidal distances differ
slightly, so calculate the actual bounding box when the distinction matters.

Encode at an explicit precision:

.. code:: python

   import pygeohash as pgh
   code = pgh.encode(40.6892, -74.0445, precision=7)

Read the exact bounds of that particular cell:

.. code:: python

   box = pgh.get_bounding_box(code)
   print(box.min_lat, box.min_lon, box.max_lat, box.max_lon)

Privacy: what truncating a geohash does and does not buy you
------------------------------------------------------------

Truncation replaces a precise cell with an ancestor cell. If a 9-character
code is shortened to 6 characters, a roughly 4.8 m × 4.8 m equatorial cell
becomes a roughly 1.2 km × 611 m cell. That is useful data minimization: the
released string no longer identifies the original fine-grained cell.

.. code:: python

   coarse_code = precise_code[:6]
   coarse_bounds = pgh.get_bounding_box(coarse_code)

It is not anonymity. The cell may contain one home in a rural area, an office
campus, a hospital, or a sparse event. Repeated coarse observations can reveal
movement, and outside information can narrow the possibilities. A geohash also
reveals the cell directly; it is an encoding, not encryption.

Choose privacy precision from the harm model, local population density,
sampling frequency, retention period, and whether records can be linked.
Useful defaults to evaluate—not universal safe levels—are:

+--------------------+---------------------------+---------------------------+
| Released precision | Equatorial cell           | Privacy question to ask   |
+====================+===========================+===========================+
| 4                  | 39.1 km × 19.5 km         | Is metro-level location   |
|                    |                           | sufficient?               |
+--------------------+---------------------------+---------------------------+
| 5                  | 4.89 km × 4.89 km         | Could this cell still     |
|                    |                           | isolate a small town or   |
|                    |                           | sensitive site?           |
+--------------------+---------------------------+---------------------------+
| 6                  | 1.22 km × 611 m           | Can repeated records      |
|                    |                           | reconstruct a routine?    |
+--------------------+---------------------------+---------------------------+
| 7                  | 153 m × 153 m             | Could this identify a     |
|                    |                           | block, building cluster,  |
|                    |                           | or workplace?             |
+--------------------+---------------------------+---------------------------+
| 8+                 | 38.2 m × 19.1 m or        | Why is building- or       |
|                    | smaller                   | person-scale location     |
|                    |                           | necessary at all?         |
+--------------------+---------------------------+---------------------------+

If the product promise requires a minimum number of people per released area,
geohash length alone cannot enforce it. Measure population or cohort size and
suppress cells that do not meet the threshold.

Picking a precision for an index
--------------------------------

Pick a cell near the scale of candidate retrieval, then query neighboring
cells and apply an exact geometry or distance test. A precision-6 cell does
not mean “within 1 km,” and a precision-7 match does not mean two points are
within 153 m. Points at opposite cell corners can be farther apart, while
points separated by a cell boundary can be centimeters apart and have
different prefixes.

To see a real point at every precision before fixing a production bucket size,
loop ``pgh.encode`` over ``range(1, 13)`` and call ``pgh.get_bounding_box`` on
each prefix.
