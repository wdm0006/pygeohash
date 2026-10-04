.. meta::
   :description: Convert geohash to slippy z/x/y tiles and Bing quadkeys in Python, with zoom derivation, latitude-loss rules and explicit polar clipping.

Geohash to map tiles and Bing quadkeys in Python
================================================

**Tile conversion is generally lossy in latitude.** It maps cell
centres, not whole cell footprints. Centres outside ±85.05112878° raise
``ValueError`` unless you explicitly choose ``clip=True``. Keep the
original geohash as your storage key when converting for a map layer or
tile cache.

.. code:: python

   import pygeohash as pgh
   tile, quadkey = pgh.geohash_to_tile("ezs42"), pgh.geohash_to_quadkey("ezs42")

Here ``tile`` is ``Tile(x=1984, y=1511, zoom=12)`` and ``quadkey`` is
``"031333200222"``. Use ``tile.zoom``, ``tile.x``, and ``tile.y`` for a
slippy ``z/x/y`` address; the tuple itself is ordered **x, y, zoom**. No
visualization extra or new runtime dependency is needed.

As verified on 2026-10-04, interop is in the development source and is
absent from the published 3.5.1 release. To run these examples now,
install this pinned source revision (a compiler is needed for the
package's C core):

.. code:: bash

   pip install "pygeohash @ git+https://github.com/wdm0006/pygeohash.git@b0c06ed723a58bab372ac6fbfe8bda953448d637"

Derive the zoom before building cache keys
------------------------------------------

A precision-p geohash contains 5p bits, alternating longitude first,
then latitude. It has ``ceil(5p/2)`` longitude bits and ``floor(5p/2)``
latitude bits. ``geohash_to_tile`` chooses ``zoom = floor(5p/2)``:
precision 5 gives zoom 12, precision 6 gives zoom 15. This API does not
accept an arbitrary target zoom. At even precision, every longitude bit
maps to the tile column; at odd precision, the final longitude bit is
discarded and two geohash columns share one tile x. The tile row comes
from projecting the geohash cell centre into Web Mercator.

What round-trips, and what does not
-----------------------------------

+----------------------+----------------------+----------------------+
| Conversion           | Preserved            | Limitation           |
+======================+======================+======================+
| Geohash → tile →     | Longitude column     | Latitude can shift;  |
| geohash, even p at   |                      | original string can  |
| z=5p/2               |                      | change               |
+----------------------+----------------------+----------------------+
| Geohash → tile →     | Longitude prefix at  | One longitude bit is |
| geohash, odd p       | tile zoom            | lost; latitude can   |
|                      |                      | shift                |
+----------------------+----------------------+----------------------+
| Tile/quadkey →       | Centre-based mapping | Tile row can change; |
| geohash →            |                      | arbitrary            |
| tile/quadkey         |                      | zoom/precision       |
|                      |                      | alignment can lose   |
|                      |                      | column detail        |
+----------------------+----------------------+----------------------+
| Geohash → integer →  | Entire lowercase     | Integer does not     |
| geohash, original p  | string               | carry length; this   |
| retained             |                      | is storage encoding, |
|                      |                      | not grid conversion  |
+----------------------+----------------------+----------------------+

Reverse conversion defaults to ``max(1, ceil(2*zoom/5))`` characters.
You can supply precision 1–12; tile zoom accepts 0–30. Do not use a
successful example as proof of a universal round trip:

.. code:: python

   import pygeohash as pgh
   original = "ezs42e"
   tile = pgh.geohash_to_tile(original)
   restored = pgh.tile_to_geohash(tile.x, tile.y, tile.zoom)
   assert restored == "ezs42s"  # latitude changed at even precision 6
   assert pgh.quadkey_to_geohash(pgh.geohash_to_quadkey(original)) == restored

Decide the polar policy explicitly
----------------------------------

The guard tests the geohash **centre**, not whether the whole rectangle
fits in the band. For polar data, handle the error or deliberately
choose the nearest renderable tile row. Clipping does not preserve the
polar location:

.. code:: python

   import pygeohash as pgh
   try:
       pgh.geohash_to_tile("zzzz")
   except ValueError:
       clipped = pgh.geohash_to_tile("zzzz", clip=True)
       assert clipped == pgh.Tile(x=1023, y=0, zoom=10)
   assert pgh.geohash_to_quadkey("zzzz", clip=True) == "1111111111"

The same policy applies to quadkeys. Valid tile inputs already have
in-band centres. Keeping the original geohash lets your application
distinguish a polar record from its display adapter.

Geohash vs quadkey: keep the key your system needs
--------------------------------------------------

Use the geohash for your existing rows and convert at the tile-cache
boundary. A quadkey addresses a map tile; it is not a lossless
replacement for a geohash cell. For grid selection and the conceptual
explanation, see `Grid systems <grid_systems.html>`__. For lossless
database encoding, see `Geohash integer
storage <geohash-integer-storage.html>`__.

**ASSUMPTION: no other Python geohash library ships this tile/quadkey
conversion.** The `published benchmark
page <https://pygeohash.mcginniscommawill.com/benchmarks.html>`__
reports no measured competitor ships it. That supports the measured
field, not a verified claim about every current Python library.
