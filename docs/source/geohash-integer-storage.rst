.. meta::
   :description: Store geohashes as integers with exact precision-preserving round trips, BIGINT sizing caveats and numeric prefix-range examples.

Store a geohash as an integer in Python
=======================================

**Retain precision alongside the integer, or enforce one precision for
the whole column.** The value carries no length: ``"0"`` and ``"00"``
both encode as zero. Integer storage preserves the geohash exactly with
its original precision; it does not improve coordinate accuracy. Unlike
tile conversion, it has no latitude loss or Web Mercator polar
restriction.

.. code:: python

   import pygeohash as pgh
   value, precision = pgh.geohash_to_int("ezs42"), len("ezs42")
   assert pgh.geohash_from_int(value, precision) == "ezs42"

The integer is ``14672002``. All 1–12-character geohashes fit in at most
60 bits, within a signed SQL ``BIGINT``.

As verified on 2026-10-04, interop is in the development source and is
absent from the published 3.5.1 release. To run these examples now,
install this pinned source revision (a compiler is needed for the
package's C core):

.. code:: bash

   pip install "pygeohash @ git+https://github.com/wdm0006/pygeohash.git@b0c06ed723a58bab372ac6fbfe8bda953448d637"

Exact storage contract
----------------------

Each base32 character contributes five bits. For precision p the value
is in ``[0, 2**(5*p))``. ``geohash_from_int`` requires precision 1–12
and rejects negative values and values that overflow that precision.
Input strings are case-insensitive; restored strings are lowercase:

.. code:: python

   import pygeohash as pgh
   for code in ("EZS42", "00", "zzzzzzzzzzzz"):
       assert pgh.geohash_from_int(pgh.geohash_to_int(code), len(code)) == code.lower()
   assert pgh.geohash_from_int(0, 2) == "00"

No projection happens. Polar cells round-trip too. If you convert
through `map tiles or quadkeys <geohash-to-tiles-and-quadkeys.html>`__
first, latitude can shift and polar centres raise by default; integer
storage cannot undo that loss.

Smaller keys where the precision justifies them
-----------------------------------------------

In `PostgreSQL
18 <https://www.postgresql.org/docs/18/datatype-numeric.html>`__,
``BIGINT`` uses eight bytes. Its `character storage
rules <https://www.postgresql.org/docs/18/datatype-character.html>`__
use one byte of overhead for short strings: a 12-character ASCII geohash
takes 13 bytes of character storage. Eight bytes is a smaller key
payload at that precision, but a five-character string takes six bytes
and can be smaller. Row alignment, index overhead and a per-row
precision field also matter.

ASSUMPTION: smaller payloads at longer precision may reduce index size
and improve cache use. Measure your actual index and query plan; no
database speedup or percentage reduction is claimed here.
Fixed-precision integer keys give numeric range bounds without depending
on text collation. String prefix indexes remain a reasonable option.

Turn a prefix into an integer range
-----------------------------------

Choose one stored precision, here six characters. A prefix of length m
and integer value k covers all suffixes in the half-open range
``[k << (5*(p-m)), (k+1) << (5*(p-m)))``:

.. code:: python

   import pygeohash as pgh
   precision = 6
   prefix = "ezs"
   suffix_bits = 5 * (precision - len(prefix))
   k = pgh.geohash_to_int(prefix)
   lower, upper = k << suffix_bits, (k + 1) << suffix_bits
   assert lower <= pgh.geohash_to_int("ezs42e") < upper
   assert not lower <= pgh.geohash_to_int("ezt000") < upper

For a PostgreSQL column deliberately fixed at precision 6:

.. code:: sql

   CREATE TABLE locations (
       geohash_value BIGINT NOT NULL
           CHECK (geohash_value >= 0 AND geohash_value < 1073741824)
   );
   CREATE INDEX locations_geohash_idx ON locations (geohash_value);
   SELECT geohash_value FROM locations
   WHERE geohash_value >= 469499904 AND geohash_value < 469532672;

The range selects the ``ezs`` prefix at precision 6. Store the precision
in the schema contract. For mixed precisions, store it per row and
filter on it before using these bounds; identical integers can otherwise
represent different cells. Prefix retrieval selects encoded cells, not
an exact radius or nearest-neighbor result. Apply the appropriate
geometry filter for that application.

For choosing between storage and map grids, see `Grid
systems <grid_systems.html>`__.
