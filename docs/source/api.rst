API Reference
=============

This section provides detailed documentation for all functions available in the PyGeoHash library.

Core Functions
--------------

These core functions are implemented using a high-performance C extension for maximum efficiency.

.. autofunction:: pygeohash.encode
.. autofunction:: pygeohash.encode_strictly
.. autofunction:: pygeohash.decode
.. autofunction:: pygeohash.decode_exactly

Data Types
----------

.. autoclass:: pygeohash.LatLong
   :members:
   :undoc-members:
   :show-inheritance:
   :noindex:

.. autoclass:: pygeohash.ExactLatLong
   :members:
   :undoc-members:
   :show-inheritance:
   :noindex:

.. autoclass:: pygeohash.BoundingBox
   :members:
   :undoc-members:
   :show-inheritance:
   :noindex:

Distance Calculations
---------------------

.. autofunction:: pygeohash.geohash_approximate_distance
.. autofunction:: pygeohash.geohash_haversine_distance

Geohash Navigation
------------------

.. autofunction:: pygeohash.get_adjacent

Bounding Box Operations
-----------------------

.. autofunction:: pygeohash.get_bounding_box
.. autofunction:: pygeohash.is_point_in_box
.. autofunction:: pygeohash.is_point_in_geohash
.. autofunction:: pygeohash.do_boxes_intersect
.. autofunction:: pygeohash.geohashes_in_box

Statistical Functions
---------------------

.. autofunction:: pygeohash.mean
.. autofunction:: pygeohash.northern
.. autofunction:: pygeohash.southern
.. autofunction:: pygeohash.eastern
.. autofunction:: pygeohash.western
.. autofunction:: pygeohash.variance
.. autofunction:: pygeohash.std

Visualization Functions
-----------------------

These functions require additional dependencies that can be installed with:
``pip install pygeohash[viz]``

The visualization module provides tools for creating static plots with Matplotlib and interactive maps with Folium:

.. autofunction:: pygeohash.plot_geohash
.. autofunction:: pygeohash.plot_geohashes
.. autofunction:: pygeohash.folium_map

For detailed examples of how to use these functions, see the :doc:`examples` section. 
