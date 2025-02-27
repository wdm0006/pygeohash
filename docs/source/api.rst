API Reference
============

This section provides detailed documentation for all functions available in the PyGeoHash library.

Core Functions
-------------

.. autofunction:: pygeohash.encode
.. autofunction:: pygeohash.encode_strictly
.. autofunction:: pygeohash.decode
.. autofunction:: pygeohash.decode_exactly

Data Types
---------

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

Distance Calculations
--------------------

.. autofunction:: pygeohash.geohash_approximate_distance
.. autofunction:: pygeohash.geohash_haversine_distance

Geohash Navigation
-----------------

.. autofunction:: pygeohash.get_adjacent

Statistical Functions
-------------------

.. autofunction:: pygeohash.mean
.. autofunction:: pygeohash.northern
.. autofunction:: pygeohash.southern
.. autofunction:: pygeohash.eastern
.. autofunction:: pygeohash.western
.. autofunction:: pygeohash.variance
.. autofunction:: pygeohash.std

Numba-accelerated Functions
-------------------------

These functions require Numba and NumPy to be installed and provide faster performance for large-scale operations.

.. autofunction:: pygeohash.nb_point_encode
.. autofunction:: pygeohash.nb_point_decode
.. autofunction:: pygeohash.nb_vector_encode
.. autofunction:: pygeohash.nb_vector_decode
.. autofunction:: pygeohash.nb_decode_exactly 