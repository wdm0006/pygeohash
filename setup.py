"""
Setup script for building the pygeohash package with C extension.
"""

from setuptools import Extension, setup

geohash_module = Extension(
    "pygeohash.cgeohash.geohash_module",
    sources=["pygeohash/cgeohash/geohash_module.c"],
    extra_compile_args=["-O3"],  # Optimize for performance
)

if __name__ == "__main__":
    setup(ext_modules=[geohash_module])
