Usage Guide
===========

This guide covers common use cases and patterns for working with the PyGeoHash library.

Installation
-----------

PyGeoHash can be installed from PyPI using pip:

.. code-block:: bash

    pip install pygeohash

Basic Operations
--------------

Encoding Coordinates to Geohash
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To convert latitude and longitude coordinates to a geohash string:

.. code-block:: python

    import pygeohash as pgh
    
    # Default precision (12 characters)
    geohash = pgh.encode(latitude=42.6, longitude=-5.6)
    print(geohash)  # 'ezs42e44yx96'
    
    # Custom precision (5 characters)
    short_geohash = pgh.encode(latitude=42.6, longitude=-5.6, precision=5)
    print(short_geohash)  # 'ezs42'
    
    # Strict encoding (validates input coordinates)
    strict_geohash = pgh.encode_strictly(latitude=42.6, longitude=-5.6, precision=5)
    print(strict_geohash)  # 'ezs42'

Decoding Geohash to Coordinates
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To convert a geohash string back to latitude and longitude coordinates:

.. code-block:: python

    import pygeohash as pgh
    
    # Basic decoding
    location = pgh.decode(geohash='ezs42')
    print(location.latitude, location.longitude)
    
    # Decoding with error margins
    exact_location = pgh.decode_exactly(geohash='ezs42')
    print(exact_location.latitude, exact_location.longitude)
    print(exact_location.latitude_error, exact_location.longitude_error)  # Error margins

Working with Geohash Precision
-----------------------------

The precision of a geohash determines how accurately it represents a location. Each additional character in a geohash increases precision:

.. code-block:: python

    import pygeohash as pgh
    
    # Different precision levels for the same location
    location = (37.371392, -122.046208)  # Google headquarters
    
    for precision in range(1, 13):
        geohash = pgh.encode(location[0], location[1], precision=precision)
        decoded = pgh.decode(geohash)
        print(f"Precision {precision}: {geohash} -> ({decoded.latitude}, {decoded.longitude})")

Calculating Distances
-------------------

To calculate the distance between two geohashes:

.. code-block:: python

    import pygeohash as pgh
    
    # Approximate distance based on matching characters
    approx_distance = pgh.geohash_approximate_distance(
        geohash_1='bcd3u', 
        geohash_2='bc83n'
    )
    print(f"Approximate distance: {approx_distance} meters")
    
    # More accurate distance using Haversine formula
    haversine_distance = pgh.geohash_haversine_distance(
        geohash_1='bcd3u', 
        geohash_2='bc83n'
    )
    print(f"Haversine distance: {haversine_distance} meters")

Finding Adjacent Geohashes
------------------------

To find geohashes adjacent to a given geohash:

.. code-block:: python

    import pygeohash as pgh
    
    # Get adjacent geohash in a specific direction
    # Directions: 'top', 'right', 'bottom', 'left'
    adjacent_right = pgh.get_adjacent(geohash='kd3ybyu', direction='right')
    print(f"Right: {adjacent_right}")
    
    # Get adjacent geohashes in all four directions
    adjacent_top = pgh.get_adjacent(geohash='kd3ybyu', direction='top')
    adjacent_right = pgh.get_adjacent(geohash='kd3ybyu', direction='right')
    adjacent_bottom = pgh.get_adjacent(geohash='kd3ybyu', direction='bottom')
    adjacent_left = pgh.get_adjacent(geohash='kd3ybyu', direction='left')
    
    print(f"Top: {adjacent_top}")
    print(f"Right: {adjacent_right}")
    print(f"Bottom: {adjacent_bottom}")
    print(f"Left: {adjacent_left}")

Statistical Functions
-------------------

PyGeoHash provides several statistical functions for working with groups of geohashes:

.. code-block:: python

    import pygeohash as pgh
    
    # Sample geohashes
    geohashes = ['ezs42', 'ezs41', 'ezs43', 'ezs40']
    
    # Find the mean position
    mean_position = pgh.mean(geohashes)
    print(f"Mean position: {mean_position}")
    
    # Find cardinal extremes
    north = pgh.northern(geohashes)
    south = pgh.southern(geohashes)
    east = pgh.eastern(geohashes)
    west = pgh.western(geohashes)
    
    print(f"Northernmost: {north}")
    print(f"Southernmost: {south}")
    print(f"Easternmost: {east}")
    print(f"Westernmost: {west}")
    
    # Calculate statistical measures
    variance = pgh.variance(geohashes)
    std_dev = pgh.std(geohashes)
    
    print(f"Variance: {variance} meters²")
    print(f"Standard deviation: {std_dev} meters")

Practical Examples
----------------

Location-Based Search
^^^^^^^^^^^^^^^^^^^

Using geohashes for a simple location-based search:

.. code-block:: python

    import pygeohash as pgh
    
    # Define a database of points of interest with their geohashes
    pois = [
        {"name": "Eiffel Tower", "geohash": "u09tvw0f"},
        {"name": "Statue of Liberty", "geohash": "dr5regw3"},
        {"name": "Sydney Opera House", "geohash": "r3gx2u9b"},
        {"name": "Taj Mahal", "geohash": "ttmgrbh1"},
        {"name": "Great Wall of China", "geohash": "wx4g09c6"},
    ]
    
    # User's current location
    user_lat, user_lng = 48.8584, 2.2945  # Paris
    user_geohash = pgh.encode(user_lat, user_lng, precision=5)
    
    # Find nearby POIs (simplified approach)
    nearby_pois = []
    for poi in pois:
        # Compare the first 3 characters (city-level precision)
        if poi["geohash"][:3] == user_geohash[:3]:
            nearby_pois.append(poi)
    
    print(f"Nearby POIs: {nearby_pois}")
    
    # For more accurate results, calculate actual distances
    for poi in pois:
        location = pgh.decode(poi["geohash"])
        distance = pgh.geohash_haversine_distance(
            user_geohash,
            poi["geohash"]
        )
        poi["distance"] = distance
    
    # Sort by distance
    sorted_pois = sorted(pois, key=lambda x: x["distance"])
    print(f"Sorted POIs by distance: {sorted_pois}")

Geofencing
^^^^^^^^^

Using geohashes for simple geofencing:

.. code-block:: python

    import pygeohash as pgh
    
    # Define a geofence as a set of geohash prefixes
    geofence = {"u09t", "u09s", "u09w"}  # Area around Paris
    
    # Check if a location is within the geofence
    def is_in_geofence(lat, lng, geofence_prefixes, prefix_length=4):
        location_geohash = pgh.encode(lat, lng, precision=prefix_length)
        location_prefix = location_geohash[:4]
        return location_prefix in geofence_prefixes
    
    # Test locations
    test_locations = [
        {"name": "Eiffel Tower", "lat": 48.8584, "lng": 2.2945},
        {"name": "Notre-Dame", "lat": 48.8530, "lng": 2.3499},
        {"name": "London Eye", "lat": 51.5033, "lng": -0.1195},
    ]
    
    for location in test_locations:
        in_geofence = is_in_geofence(location["lat"], location["lng"], geofence)
        print(f"{location['name']} is {'inside' if in_geofence else 'outside'} the geofence")

Performance Considerations
------------------------

- Geohash operations are generally very fast
- For large datasets, consider using the Numba-accelerated functions (requires Numba and NumPy)
- When working with millions of geohashes, consider using a database with geospatial capabilities
- For high-precision applications, be aware of the limitations of geohashes near poles and the 180° meridian 