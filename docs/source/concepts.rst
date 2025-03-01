Geohash Concepts
===============

What is a Geohash?
-----------------

A geohash is a public domain geocoding system that encodes geographic coordinates (latitude and longitude) into a short string of letters and digits. It was invented by Gustavo Niemeyer in 2008.

Geohashes offer a way to represent a location with a single string, where:

- Similar locations share similar prefixes (hierarchical property)
- The longer the geohash, the more precise the location
- Geohashes can be used for indexing and searching geographic data

How Geohashing Works
-------------------

Geohashing uses a base-32 encoding system with the following characters:
``0123456789bcdefghjkmnpqrstuvwxyz`` (note the omission of a, i, l, and o to avoid confusion with numbers).

The encoding process works by recursively dividing the world into smaller and smaller grid cells:

1. Start with the entire world as a grid
2. Divide it into 32 cells (4 rows × 8 columns for longitude, 8 rows × 4 columns for latitude)
3. Determine which cell contains the target coordinates
4. Assign the corresponding character from the base-32 alphabet
5. Subdivide that cell into 32 smaller cells
6. Repeat the process until the desired precision is reached

.. code-block:: none

    World → "e" → "ez" → "ezs" → "ezs4" → "ezs42" → ...

Visual Representation
--------------------

Consider the following visualization of how geohashing divides the world:

.. code-block:: none

    First division (1st character):
    
    +---+---+---+---+---+---+---+---+
    | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 |
    +---+---+---+---+---+---+---+---+
    | 8 | 9 | b | c | d | e | f | g |
    +---+---+---+---+---+---+---+---+
    | h | j | k | m | n | p | q | r |
    +---+---+---+---+---+---+---+---+
    | s | t | u | v | w | x | y | z |
    +---+---+---+---+---+---+---+---+
    
    Second division (2nd character) of cell "e":
    
    +---+---+---+---+---+---+---+---+
    | e0 | e1 | e2 | e3 | e4 | e5 | e6 | e7 |
    +---+---+---+---+---+---+---+---+
    | e8 | e9 | eb | ec | ed | ee | ef | eg |
    +---+---+---+---+---+---+---+---+
    | eh | ej | ek | em | en | ep | eq | er |
    +---+---+---+---+---+---+---+---+
    | es | et | eu | ev | ew | ex | ey | ez |
    +---+---+---+---+---+---+---+---+

Precision and Cell Size
----------------------

The precision of a geohash depends on its length:

.. list-table::
   :header-rows: 1
   :widths: 15 25 25 35

   * - Geohash Length
     - Lat Precision
     - Lng Precision
     - Cell Dimensions
   * - 1
     - ±23 km
     - ±23 km
     - 5,000 km × 5,000 km
   * - 2
     - ±2.8 km
     - ±5.6 km
     - 1,250 km × 625 km
   * - 3
     - ±700 m
     - ±700 m
     - 156 km × 156 km
   * - 4
     - ±88 m
     - ±175 m
     - 39 km × 19.5 km
   * - 5
     - ±22 m
     - ±22 m
     - 4.9 km × 4.9 km
   * - 6
     - ±2.7 m
     - ±5.5 m
     - 1.2 km × 0.61 km
   * - 7
     - ±0.67 m
     - ±0.67 m
     - 153 m × 153 m
   * - 8
     - ±0.084 m
     - ±0.17 m
     - 38 m × 19 m
   * - 9
     - ±0.021 m
     - ±0.021 m
     - 4.8 m × 4.8 m
   * - 10
     - ±0.0026 m
     - ±0.0053 m
     - 1.2 m × 0.6 m
   * - 11
     - ±0.00065 m
     - ±0.00065 m
     - 15 cm × 15 cm
   * - 12
     - ±0.000082 m
     - ±0.000163 m
     - 3.7 cm × 1.9 cm

Properties of Geohashes
----------------------

Geohashes have several important properties:

1. **Hierarchical**: Geohashes with the same prefix are close to each other (but the reverse is not always true)
2. **Arbitrary Precision**: Can be as precise as needed by adjusting the length
3. **Compact**: Efficient storage of geographic coordinates
4. **Human-Readable**: Can be easily shared and communicated

Edge Cases and Limitations
-------------------------

While geohashes are powerful, they have some limitations:

1. **Edge Effects**: Points that are close but on opposite sides of a grid boundary may have completely different geohashes
2. **Longitude Wrapping**: Points near the 180° meridian may have very different geohashes despite being close
3. **Pole Proximity**: Precision decreases near the poles
4. **Non-Uniform Area**: Cells have different physical areas at different latitudes

To address the edge effect issue, when searching for nearby locations, it's often necessary to check adjacent geohash cells as well.

Geohash Bounding Boxes
---------------------

Every geohash represents a rectangular area on the Earth's surface, which can be described by a bounding box. A bounding box is defined by four coordinates:

- Minimum latitude (southern edge)
- Minimum longitude (western edge)
- Maximum latitude (northern edge)
- Maximum longitude (eastern edge)

Bounding boxes are useful for:

1. **Spatial Queries**: Finding all points within a geographic region
2. **Geofencing**: Determining if a point is inside or outside a defined area
3. **Spatial Indexing**: Efficiently organizing and querying spatial data
4. **Visualization**: Rendering geographic data on maps

When working with geohashes, bounding boxes provide a way to:

- Determine the exact area covered by a geohash
- Find all geohashes that intersect with a given area
- Check if two geographic regions overlap
- Identify if a point falls within a specific region

The precision of a bounding box derived from a geohash depends on the geohash length. Longer geohashes result in smaller, more precise bounding boxes.

Geohash vs. Other Geocoding Systems
----------------------------------

Compared to other geocoding systems:

- **What3Words**: Assigns three random words to each 3m×3m square; not hierarchical
- **Plus Codes**: Google's open location system; works without country or city references
- **Maidenhead Locator System**: Used by amateur radio operators; less precise
- **Military Grid Reference System (MGRS)**: Used by NATO militaries; more complex

Geohashes are particularly well-suited for computer systems due to their hierarchical nature and simple implementation. 