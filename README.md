# PyGeoHash

[![PyPI version](https://badge.fury.io/py/pygeohash.svg)](https://badge.fury.io/py/pygeohash)
[![Python Versions](https://img.shields.io/pypi/pyversions/pygeohash.svg)](https://pypi.org/project/pygeohash/)

A simple, lightweight, and dependency-free Python library for working with geohashes.

## What is PyGeoHash?

PyGeoHash is a Python module that provides functions for encoding and decoding geohashes to and from latitude and 
longitude coordinates, along with utilities for performing calculations and approximations with them.

It is based on Leonard Norrgård's [geohash](https://github.com/vinsci/geohash) module, but adds more 
functionality while supporting Python 3.

## Why PyGeoHash?

- **Zero Dependencies**: Works with just the Python standard library
- **Simple API**: Clean, intuitive functions that are easy to understand
- **Lightweight**: Minimal overhead for your projects
- **Python 3 Support**: Fully compatible with modern Python
- **Robust Implementation**: Reliable geohash operations

## Installation

```bash
pip install pygeohash
```

## Quick Start

```python
import pygeohash as pgh

# Encode coordinates to geohash
geohash = pgh.encode(latitude=42.6, longitude=-5.6)
print(geohash)  # 'ezs42e44yx96'

# Control precision
short_geohash = pgh.encode(latitude=42.6, longitude=-5.6, precision=5)
print(short_geohash)  # 'ezs42'

# Decode geohash to coordinates
lat, lng = pgh.decode(geohash='ezs42')
print(lat, lng)  # '42.6', '-5.6'

# Calculate approximate distance between geohashes (in meters)
distance = pgh.geohash_approximate_distance(geohash_1='bcd3u', geohash_2='bc83n')
print(distance)  # 625441

# Get adjacent geohash
adjacent = pgh.get_adjacent(geohash='kd3ybyu', direction='right')
print(adjacent)  # 'kd3ybyv'
```

## Features

- Encode coordinates to geohash strings
- Decode geohash strings back to coordinates
- Calculate approximate distances between geohashes
- Find adjacent geohashes in any direction
- Control precision of geohash encoding
- Bounding box calculations

## Use Cases

- Location-based services
- Spatial indexing
- Proximity searches
- Geographic data clustering
- Location encoding with privacy considerations

## Contributing

Contributions are welcome! Feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Based on Leonard Norrgård's [geohash](https://github.com/vinsci/geohash) module
   