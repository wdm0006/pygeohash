pygeohash
=========

Pygeohash is a Python module that provides functions for decoding and encoding geohashes to and from latitude and 
longitude coordinates, and doing basic calculations and approximations with them.

It is based off of Leonard Norrgård's [geohash](https://github.com/vinsci/geohash) module, but aims to add more 
functionality while supporting python 3 as well.


Usage
=====

To use pygeohash:

```py
import pygeohash as pgh

pgh.encode(latitude=42.6, longitude=-5.6)
# >>> 'ezs42e44yx96'

pgh.encode(latitude=42.6, longitude=-5.6, precision=5)
# >>> 'ezs42'

pgh.decode(geohash='ezs42')
# >>> ('42.6', '-5.6')

pgh.geohash_approximate_distance(geohash_1='bcd3u', geohash_2='bc83n')
# >>> 625441

pgh.get_adjacent(geohash='kd3ybyu', direction='right')
# >>> kd3ybyv
```

Installation
============

Pygeohash has no requirements outside of the python stdlib, and aims to keep it that way if at all possible. To install:

    pip install pygeohash
   