from typing import List

import pygeohash as pgh

neighbors: List[str] = pgh.get_neighbors("u4pruyd")
with_self: List[str] = pgh.get_neighbors("u4pruyd", include_self=True)
