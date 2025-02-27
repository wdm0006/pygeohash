import importlib.util
import pytest

import pygeohash as pgh

# Check if numpy and numba are available
numpy_available = importlib.util.find_spec("numpy") is not None
numba_available = importlib.util.find_spec("numba") is not None

# Skip the entire module if numpy or numba are not available
pytestmark = pytest.mark.skipif(
    not (numpy_available and numba_available), reason="Numpy and Numba are required for these tests"
)

if numpy_available and numba_available:
    import numpy as np

__author__ = "ilyasmoutawwakil"


class TestNumbaPointGeohash:
    def test_encode(self):
        assert pgh.nb_point_encode(42.6, -5.6) == "ezs42e44yx96"
        assert pgh.nb_point_encode(42.6, -5.6, precision=5) == "ezs42"

    def test_decode(self):
        assert pgh.nb_point_decode("ezs42") == (42.6, -5.6)


class TestNumbaVectorGeohash:
    def test_encode(self):
        x = np.array([42.6, 2.6732])
        y = np.array([-5.6, -92.1736])
        geohashes_12 = np.array(["ezs42e44yx96", "9bqrnw9hx2w7"])
        geohashes_5 = np.array(["ezs42", "9bqrn"])

        assert pgh.nb_vector_encode(x, y).tolist() == geohashes_12.tolist()
        assert pgh.nb_vector_encode(x, y, precision=5).tolist() == geohashes_5.tolist()

    def test_decode(self):
        latitudes = np.array([-10.299737, -42.279401, 2.673264])
        longitudes = np.array([-0.996014, -127.773821, -92.173682])
        geohashes = np.array(["7ypm3kfxxjvf", "30mpkrmbwhmk", "9bqrnw9hvs8b"])
        results = pgh.nb_vector_decode(geohashes)

        assert results[0].tolist() == latitudes.tolist()
        assert results[1].tolist() == longitudes.tolist()
