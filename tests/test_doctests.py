"""Run the examples in dependency-free package modules as doctests."""

import doctest
from pathlib import Path
from types import ModuleType
from typing import Tuple

import pytest

from pygeohash import bounding_box, distances, geohash, geohash_types, neighbor, stats, types


def test_docstring_examples() -> None:
    # In a mutmut mutants tree every function exists as x_*__mutmut_N copies carrying the
    # same docstrings, which inflates the example count and kills mutmut's stats phase.
    # The exact-count inventory is only meaningful in a normal tree.
    if Path.cwd().name == "mutants":
        pytest.skip("doctest inventory is not meaningful in a mutmut mutants tree")

    modules: Tuple[ModuleType, ...] = (geohash, distances, neighbor, bounding_box, stats, types, geohash_types)
    results = {module.__name__: doctest.testmod(module, raise_on_error=False) for module in modules}
    failures = {name: result.failed for name, result in results.items() if result.failed}

    assert failures == {}
    assert sum(result.attempted for result in results.values()) == 21
    for module in (distances, bounding_box, stats, neighbor):
        assert results[module.__name__].attempted > 0
