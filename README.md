# PyGeoHash

[![PyPI version](https://badge.fury.io/py/pygeohash.svg)](https://badge.fury.io/py/pygeohash)
[![Python Versions](https://img.shields.io/pypi/pyversions/pygeohash.svg)](https://pypi.org/project/pygeohash/)

A simple, lightweight, and dependency-free Python library for working with geohashes.

## What is PyGeoHash?

PyGeoHash is a Python module that provides functions for encoding and decoding geohashes to and from latitude and longitude coordinates, along with utilities for performing calculations and approximations with them.

It was originally based on Leonard Norrgård's [geohash](https://github.com/vinsci/geohash) module, but now adds more functionality while supporting Python 3, and is optimized for performance.

## Why PyGeoHash?

- **Zero Dependencies**: Works with just the Python standard library
- **Simple API**: Clean, intuitive functions that are easy to understand
- **Lightweight**: Minimal overhead for your projects
- **Python 3 Support**: Fully compatible with modern Python
- **Robust Implementation**: Reliable geohash operations
- **Optional Visualization**: Visualize geohashes with matplotlib and folium
- **Extensively Tested**: Comprehensive test suite validated against geohash.org

## Installation

```bash
# Basic installation
pip install pygeohash

# With visualization support
pip install pygeohash[viz]
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

## Visualization

PyGeoHash includes optional visualization capabilities:

```python
# Plot a single geohash
from pygeohash.viz import plot_geohash
import matplotlib.pyplot as plt

fig, ax = plot_geohash("9q8yyk", color="red")
plt.show()

# Plot multiple geohashes
from pygeohash.viz import plot_geohashes

geohashes = ["9q8yyk", "9q8yym", "9q8yyj"]
fig, ax = plot_geohashes(geohashes, colors="viridis")
plt.show()

# Create interactive maps with Folium
from pygeohash.viz import folium_map

m = folium_map(center_geohash="9q8yyk")
m.add_geohash("9q8yyk", color="red")
m.add_geohash_grid(precision=6)
m.save("geohash_map.html")
```

### Generating Example Visualizations

To generate example visualizations for the documentation, you can use the provided Makefile command:

```bash
# Install visualization dependencies
make install-viz

# Generate visualization examples
make viz-examples
```

This will create static images and interactive maps in the `docs/source/_static/images` directory.

## Features

- Encode coordinates to geohash strings
- Decode geohash strings back to coordinates
- Calculate approximate distances between geohashes
- Find adjacent geohashes in any direction
- Control precision of geohash encoding
- Bounding box calculations
- Visualize geohashes on static and interactive maps

## Testing and Accuracy

PyGeoHash is extensively tested to ensure accuracy in geohash encoding and decoding:

- **Comprehensive Test Suite**: Includes over 200 test cases covering various precision levels and geographic regions
- **Validated Against geohash.org**: All test cases are validated against the reference implementation at geohash.org
- **Edge Case Coverage**: Special attention to edge cases like poles, equator, date line, and precision boundaries
- **Roundtrip Consistency**: Ensures encode->decode->encode operations produce consistent results
- **Regional Coverage**: Test cases span all continents and major geographic features

To run the tests:

```bash
# Run the standard test suite
make test

# Run tests with coverage
make test-cov
```

## Use Cases

- Location-based services
- Spatial indexing
- Proximity searches
- Geographic data clustering
- Location encoding with privacy considerations
- Geospatial data visualization

## Contributing

Contributions are welcome! Feel free to submit a Pull Request.

## License

This project is licensed under the MIT license. See the LICENSE file for details. Prior to version 3.0.0's rewrite the project was licensed under the GPL-3.0 license.

## Acknowledgments

- Originally based on Leonard Norrgård's [geohash](https://github.com/vinsci/geohash) module (since re-written)
   
# Benchmarks

We did a rewrite of the core logic into cpython in v3.0.0 to improve performance and remove the dependency on geohash.py. Here is the performance part:

## Version 3.0.0

| Name (time in ns)                     | Min                  | Max                  | Mean                | StdDev              | Median              | IQR              | Outliers  | OPS (Kops/s)       | Rounds | Iterations |
|---------------------------------------|----------------------|----------------------|---------------------|---------------------|---------------------|------------------|-----------|--------------------|--------|------------|
| test_encode_benchmark                 | 614.0035 (1.0)       | 1,170,750.9984 (1.34)| 1,119.5566 (1.0)    | 6,011.2433 (1.35)   | 714.0043 (1.0)      | 664.4987 (7.30)  | 370;1371  | 893.2107 (1.0)     | 117772 | 1          |
| test_approximate_distance_benchmark   | 901.9859 (1.47)      | 872,125.0051 (1.0)   | 1,346.1119 (1.20)   | 4,467.1457 (1.0)    | 1,031.0032 (1.44)   | 90.9786 (1.0)    | 463;13144 | 742.8803 (0.83)    | 71891  | 1          |
| test_decode_benchmark                 | 2,791.9887 (4.55)    | 3,266,092.0115 (3.74)| 4,683.3561 (4.18)   | 22,447.8219 (5.03)  | 3,102.9922 (4.35)   | 2,965.2583 (32.59)| 103;302  | 213.5221 (0.24)    | 26769  | 1          |
| test_haversine_distance_benchmark     | 3,989.0001 (6.50)    | 1,066,400.9897 (1.22)| 5,441.2395 (4.86)   | 10,068.4850 (2.25)  | 4,475.0050 (6.27)   | 330.0083 (3.63)  | 429;3534  | 183.7817 (0.21)    | 28312  | 1          |


## Version 2.1.0
| Name (time in ns)                     | Min                  | Max                  | Mean                | StdDev              | Median              | IQR              | Outliers  | OPS (Kops/s)       | Rounds | Iterations |
|---------------------------------------|----------------------|----------------------|---------------------|---------------------|---------------------|------------------|-----------|--------------------|--------|------------|
| test_approximate_distance_benchmark   | 903.0045 (1.0)        | 2,239,810.0118 (145.76)| 1,242.2962 (1.0)     | 8,910.5317 (2.45)    | 1,034.0009 (1.0)     | 83.0041 (1.0)    | 411;12404  | 804,960.9836 (1.0) | 126872 | 1          |
| test_numba_point_decode_benchmark     | 5,554.9899 (6.15)     | 28,678.0123 (1.87)    | 11,125.8007 (8.96)   | 9,922.0335 (2.73)    | 6,597.9839 (6.38)    | 8,462.7463 (101.96)| 1;1       | 89,881.1717 (0.11) | 5      | 1          |
| test_numba_point_encode_benchmark     | 6,829.9996 (7.56)     | 15,366.0076 (1.0)     | 8,949.4046 (7.20)    | 3,633.1020 (1.0)     | 7,203.9838 (6.97)    | 3,100.7585 (37.36)| 1;1       | 111,739.2773 (0.14)| 5      | 1          |
| test_decode_benchmark                 | 9,094.0157 (10.07)    | 564,207.9923 (36.72)  | 23,505.3902 (18.92)  | 47,847.8575 (13.17)  | 19,235.4928 (18.60)  | 10,221.4981 (123.14)| 4;9     | 42,543.4333 (0.05) | 156    | 1          |
| test_encode_benchmark                 | 16,131.9913 (17.86)   | 6,522,867.0137 (424.50)| 43,962.7989 (35.39)  | 204,118.7023 (56.18) | 30,353.0251 (29.35)  | 5,316.5204 (64.05)| 12;160   | 22,746.5044 (0.03) | 1081   | 1          |
| test_haversine_distance_benchmark     | 19,751.9839 (21.87)   | 2,229,443.9841 (145.09)| 24,979.8646 (20.11)  | 27,057.9632 (7.45)   | 21,632.0041 (20.92)  | 1,626.0019 (19.59)| 453;3700 | 40,032.2426 (0.05) | 24647  | 1          |
| test_numba_vector_decode_benchmark    | 887,114.0017 (982.40) | 1,070,945.9893 (69.70)| 974,148.7971 (784.15)| 72,131.5386 (19.85)  | 977,645.9774 (945.50)| 111,056.4845 (>1000.0)| 2;0   | 1,026.5372 (0.00)  | 5      | 1          |
| test_numba_vector_encode_benchmark    | 6,603,729.9985 (>1000.0)| 9,492,440.0037 (617.76)| 8,344,232.0058 (>1000.0)| 1,069,465.9606 (294.37)| 8,602,735.0044 (>1000.0)| 1,065,492.2444 (>1000.0)| 2;0 | 119.8433 (0.00)    | 5      | 1          |