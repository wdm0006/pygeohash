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
:ref:`geohash-vs-h3-vs-s2` below compares the three side by side.
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

.. _geohash-vs-h3-vs-s2:

Geohash vs H3 vs S2: which spatial index should you use?
--------------------------------------------------------

**Use geohash when you need a short, sortable string that an ordinary database
index, key-value store, log, or URL can handle. Use H3 when your application
is built around hex-cell traversal and aggregation. Use S2 when you need a
cell hierarchy on the sphere, spherical geometry, or coverings of complex
regions.** None is the universal winner, and proximity search often still
needs an exact distance check after the index produces candidates.

The short decision table
~~~~~~~~~~~~~~~~~~~~~~~~

+------------------------+------------------------+------------------------+
| Requirement            | Best starting point    | Why                    |
+========================+========================+========================+
| Store a location as a  | Geohash                | The code is a Base32   |
| readable string and    |                        | string whose prefixes  |
| group by prefix        |                        | represent coarser      |
|                        |                        | cells.                 |
+------------------------+------------------------+------------------------+
| Use an ordinary        | Geohash                | No spatial type or     |
| B-tree, sorted         |                        | matching geospatial    |
| key-value store, or    |                        | library is required on |
| prefix scan            |                        | the query side.        |
+------------------------+------------------------+------------------------+
| Aggregate and traverse | H3                     | H3 exposes             |
| a mostly hexagonal     |                        | grid-distance, disk,   |
| global grid            |                        | ring, and neighbor     |
|                        |                        | operations over        |
|                        |                        | hexagonal cells.       |
+------------------------+------------------------+------------------------+
| Model movement between | H3                     | A hexagon has six edge |
| adjacent cells         |                        | directions away from   |
|                        |                        | the twelve unavoidable |
|                        |                        | pentagons.             |
+------------------------+------------------------+------------------------+
| Cover spherical        | S2                     | S2 is a spherical      |
| polygons, polylines,   |                        | geometry library as    |
| caps, or other regions |                        | well as a hierarchical |
|                        |                        | cell index.            |
+------------------------+------------------------+------------------------+
| Preserve a 64-bit      | S2                     | ``S2CellId`` encodes a |
| hierarchical cell      |                        | cube face,             |
| identifier             |                        | Hilbert-curve          |
|                        |                        | position, and level.   |
+------------------------+------------------------+------------------------+
| Perform exact          | Spatial database or    | All three indexes are  |
| nearest-neighbor or    | geometry library       | candidate filters;     |
| radius search          |                        | cell membership alone  |
|                        |                        | is not exact distance. |
+------------------------+------------------------+------------------------+

H3 is sometimes described as “equal-area.” That shorthand is inaccurate: H3's
official statistics say cell area varies with position, and every resolution
has twelve pentagons because a sphere cannot be tiled entirely by hexagons.
Choose H3 for its grid topology and traversal API, not for a promise that
every cell has the same area or every neighboring center is the same metric
distance apart. (`H3 cell
statistics <https://h3geo.org/docs/core-library/restable/>`__) (`H3
overview <https://h3geo.org/docs/>`__)

What each system actually indexes
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Geohash: interleaved latitude and longitude bits
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

A conventional geohash repeatedly bisects longitude and latitude, interleaves
the resulting bits, and writes each five-bit group with a compact Base32
alphabet. Each added character selects a child rectangle, so truncating a code
selects its parent. The cells are rectangles in latitude/longitude
coordinates; their east-west size shrinks toward the poles.

That representation is operationally simple. A service can write ``dr5regw3``
into a text column, index it, sort it, group by ``LEFT(code, 5)``, or scan a
key prefix. Another service does not need H3 or S2 merely to recognize the
key. This is the clearest reason to choose geohash.

The tradeoff is geometry. Nearby points can fall on opposite sides of a prefix
boundary and share little of the string. Rectangular cells have eight
surrounding cells and diagonal centers are farther away than edge-adjacent
centers. A single prefix range is therefore not an exact proximity query.

H3: a hierarchical hexagonal grid
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

H3 is a discrete global grid built from an icosahedron. Most cells are
hexagons; twelve cells at every resolution are pentagons. Its API treats cells
as a graph and provides operations such as grid distance and disks around an
origin. (`H3
terminology <https://h3geo.org/docs/library/terminology/>`__) (`H3
grid traversal <https://h3geo.org/docs/api/traversal/>`__)

Choose H3 over geohash for hex-cell heat maps, k-ring-style candidate
expansion, or flow and adjacency analysis. Those use cases benefit from
six-way local connectivity and H3's traversal primitives. Do not choose it
merely because you heard “hexagons are equal-area”; the cells are not strictly
equal-area, and pentagon distortion is part of the model.

S2: spherical cells and geometry
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

S2 projects six cube faces onto the unit sphere and recursively subdivides
them. Its 64-bit cell IDs follow linked Hilbert curves, preserving useful
locality while encoding one of 31 levels. ``S2Cell`` represents a spherical
quadrilateral with geodesic edges, and the wider library supplies containment,
intersection, and region-covering operations. (`S2 cell
hierarchy <https://s2geometry.io/devguide/s2cell_hierarchy>`__)

Choose S2 over geohash when the application must cover a spherical polygon
with a controlled number of cells, test spherical regions, or work
consistently across the antimeridian and poles. This is more machinery than a
string-prefix index, but it is machinery geohash does not provide.

Database indexing
~~~~~~~~~~~~~~~~~

Geohash fits systems whose common denominator is a string key. Store a fixed
precision code in a text column, add a normal index, and derive coarser
buckets by prefix. This works well for partitioning, approximate aggregation,
cache keys, and candidate lookup where a small set of neighboring cells is
acceptable.

It does **not** turn ``LIKE 'dr5re%'`` into an exact radius query. A robust
proximity search usually:

1. chooses a cell precision near the search radius;
2. fetches the containing cell and enough adjacent cells to cross boundaries;
3. calculates exact distance for the candidates; and
4. applies the requested radius and ordering.

H3 follows the same candidate-then-filter pattern but supplies richer grid
traversal. S2 region coverings can produce candidates for more complex
spherical shapes. If the database already has a mature spatial index and exact
geometry operators, use those directly unless portable cell keys solve a
separate systems problem.

Proximity search
~~~~~~~~~~~~~~~~

Choose geohash when the query infrastructure can only perform string or prefix
operations, or when interoperability with existing geohash keys matters. Query
the current cell plus neighbors, then filter by exact distance.

Choose H3 when “within N cell steps,” rings, disks, or repeated neighborhood
aggregation are first-class operations. ``gridDistance`` is graph distance—the
minimum number of edges in a path—not meters. (`H3
terminology <https://h3geo.org/docs/library/terminology/>`__)

Choose S2 when the candidate region is a spherical cap, polygon, or polyline
buffer, or when one hierarchical covering must mix cell levels. S2 explicitly
supports approximating regions with collections of cells at different levels. (`S2 cell
hierarchy <https://s2geometry.io/devguide/s2cell_hierarchy>`__)

Operational tradeoffs
~~~~~~~~~~~~~~~~~~~~~

+------------------+--------------------+------------------+------------------+
| Question         | Geohash            | H3               | S2               |
+==================+====================+==================+==================+
| Identifier       | Short Base32       | 64-bit index,    | 64-bit           |
|                  | string             | commonly         | ``S2CellId``,    |
|                  |                    | rendered as      | commonly         |
|                  |                    | hexadecimal      | rendered as a    |
|                  |                    |                  | token            |
+------------------+--------------------+------------------+------------------+
| Cell shape       | Latitude/longitude | Hexagon except   | Spherical        |
|                  | rectangle          | twelve pentagons | quadrilateral    |
|                  |                    | per resolution   |                  |
+------------------+--------------------+------------------+------------------+
| Hierarchy        | String prefix      | Hierarchical     | 31-level         |
|                  |                    | resolutions,     | hierarchy        |
|                  |                    | with exact       |                  |
|                  |                    | parent/child     |                  |
|                  |                    | APIs             |                  |
+------------------+--------------------+------------------+------------------+
| Local traversal  | Compute adjacent   | Grid traversal   | Cell neighbors   |
|                  | rectangles         | is a core API    | and region       |
|                  |                    |                  | coverings        |
+------------------+--------------------+------------------+------------------+
| Geometry library | No                 | Primarily a grid | Yes: points,     |
|                  |                    | index            | polylines,       |
|                  |                    |                  | polygons, caps,  |
|                  |                    |                  | and regions      |
+------------------+--------------------+------------------+------------------+
| Plain            | Natural fit        | Possible after   | Possible after   |
| string-prefix    |                    | serialization,   | tokenization,    |
| storage          |                    | but prefixes are | but prefixes are |
|                  |                    | not the          | not the          |
|                  |                    | hierarchy API    | hierarchy API    |
+------------------+--------------------+------------------+------------------+
| Main distortion  | Longitude width    | Area varies;     | Projected cube   |
| to remember      | shrinks with       | pentagons and    | cells vary in    |
|                  | latitude; prefix   | local distortion | shape and size   |
|                  | discontinuities    | exist            |                  |
+------------------+--------------------+------------------+------------------+

Python: when geohash is the right choice
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

No installation is required to make the category decision. If a sortable
geohash string is the result you need, PyGeoHash encodes it directly:

.. code:: python

   import pygeohash as pgh
   code = pgh.encode(40.6892, -74.0445, precision=7)

The :doc:`precision reference <geohash-precision-reference>` shows how
those 7 characters translate into a cell size, and how truncation changes what
the code reveals.

When your problem is moving data between geohash storage and the map-tile
ecosystem, rather than choosing a different index, use :mod:`pygeohash.interop`
without adding a dependency.

Practical guides
----------------

Start with these standalone task pages for runnable code and operational
caveats; the sections above explain the grid choices.

.. toctree::
   :maxdepth: 1

   geohash-to-tiles-and-quadkeys
   geohash-integer-storage
