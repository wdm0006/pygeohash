Grid systems
============

pygeohash works with geohashes. Two other grids show up constantly in the
same codebases - Bing/OSM map tiles (and their quadkey string form) and,
less often, H3 and S2. The :mod:`pygeohash.interop` module converts
between geohashes, slippy tiles, quadkeys, and an integer form of the
geohash, with no new dependencies. This page says what each grid is for,
what the conversions guarantee, and what they cost.

Choosing a grid
---------------

**Geohash** encodes a latitude/longitude rectangle as a base32 string.
The string sorts approximately by location, prefixes share prefixes of
space, and the codec here is a C extension measured at hundreds of
nanoseconds (see the :doc:`benchmarks` page). It is a good default for
storage, sharding keys, and bounding queries, and the library around it
in this package - neighbors, bounding boxes, statistics - needs nothing
else installed.

**Slippy tiles** (``z``/``x``/``y``) and **quadkeys** are the grid of
every major web map. Tiles nest by construction: a tile's children are
the four tiles of the next zoom inside it, and a quadkey is exactly that
nesting path as a string of base-4 digits, so a quadkey prefix test
replaces a bounding-box test in tile caches. Rows use Web Mercator
latitude, which cuts the poles at about +/-85.05112878 degrees.

**H3** (hexagons) and **S2** (spherical cells) are separate ecosystems
with their own indexes, indexes of indexes, and native libraries. They
solve problems geohash does not try to: hexagon neighbourhood geometry,
spherical region covering, cell hierarchy with controlled shapes. This
library does not reimplement them and does not convert to them; if your
problem is hexagons or spherical covering, use those libraries directly.
Converting geohash to H3 through lat/lon floats would silently promise
grid alignment that no conversion can deliver.

What pygeohash.interop provides
-------------------------------

Seven public names, re-exported at the package root:

- ``Tile(x, y, zoom)`` - a slippy tile, row counted southward from the
  north pole.
- ``geohash_to_tile`` / ``tile_to_geohash`` - geohash cell to the tile
  containing its centre and back.
- ``geohash_to_quadkey`` / ``quadkey_to_geohash`` - the same through the
  quadkey string form.
- ``geohash_to_int`` / ``geohash_from_int`` - the geohash as an integer,
  5 bits per base32 character.

Conversion semantics
--------------------

Both grids are interleaved latitude/longitude bit streams, so longitude
is exact between them: an even-precision geohash at zoom ``5 * precision
/ 2`` maps cell-for-cell to a tile column and back, losslessly. Precision
``p`` maps to zoom ``floor(5 * p / 2)``.

Latitude is the honest caveat. Geohash latitude bands are equirectangular;
tile rows are Web Mercator, a different partition of the axis. A round
trip through a non-aligned zoom or precision therefore lands in the cell
containing the tile centre, which can be a neighbouring geohash cell in
latitude. The docstrings state plainly which directions are lossy, and
boundary centres resolve deterministically to the lower-x, lower-y cell.

The poles: geohashes cover +/-90 degrees and tiles do not exist beyond
about +/-85.05112878 degrees. Converting a cell whose centre is outside
the band raises ``ValueError``; ``clip=True`` maps it to the nearest
in-band tile row instead. Nothing is silently clamped by default.

Measured cost
-------------

Median of medians from the committed comparison-session protocol
(pygeohash 3.6.x development tree, all-Python conversions, shared input
``ezs42e44y``; the codec's C-backed encode/decode figures are on the
:doc:`benchmarks` page):

===================  ============
to-quadkey           ~14.5 us
from-quadkey         ~16.2 us
tile round trip      ~21.9 us
===================  ============

The conversions are pure Python by design: they are one-shot adapters at
tile-cache boundaries, not hot loops, and they add zero dependencies to
the package. If you need millions of conversions per second, that work
belongs in the systems this module talks to.

When to reach for H3 or S2
--------------------------

Reach for them when your problem is theirs - hexagonal indexing, spherical
covering, cell hierarchies with shapes geohash's rectangles cannot take.
Use :mod:`pygeohash.interop` when your problem is moving data between
geohash storage and the map-tile ecosystem without adding a dependency.
