from setuptools import setup, find_packages
from codecs import open
from os import path

VERSION = '1.2.0'

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='pygeohash',
    version=VERSION,
    description='Python module for interacting with geohashes',
    long_description=long_description,
    url='https://github.com/wdm0006/pygeohash',
    download_url='https://github.com/wdm0006/pygeohash/tarball/' + VERSION,
    license='GPL3',
    classifiers=[
      'Development Status :: 3 - Alpha',
      'Intended Audience :: Developers',
      'Programming Language :: Python :: 3',
    ],
    keywords='geohash gis',
    packages=find_packages(exclude=['tests*']),
    include_package_data=True,
    author='Will McGinnis',
    install_requires=[],
    author_email='will@pedalwrencher.com'
)