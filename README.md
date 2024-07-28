pygeohash
=========

[![Coverage Status](https://coveralls.io/repos/wdm0006/pygeohash/badge.svg?branch=master&service=github)](https://coveralls.io/github/wdm0006/pygeohash?branch=master)  ![travis status](https://travis-ci.org/wdm0006/pygeohash.svg?branch=master) 

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
   
License
========

A portion of this codebase (geohash.py), is from Leonard Norrgard's module, which carries the following license:

Copyright (C) 2015 [Leonard Norrgard](leonard.norrgard@gmail.com)

Geohash is free software: you can redistribute it and/or modify it
under the terms of the GNU Affero General Public License as published
by the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Geohash is distributed in the hope that it will be useful, but WITHOUT
ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
FITNESS FOR A PARTICULAR PURPOSE.  See the GNU Affero General Public
License for more details.

You should have received a copy of the GNU Affero General Public
License along with Geohash.  If not, see
[gnu.org](http://www.gnu.org/licenses/).

This derivative work likewise carries the same license:

Copyright (C) 2015 [Will McGinnis](will@pedalwrencher.com)
