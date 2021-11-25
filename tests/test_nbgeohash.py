import unittest
import pygeohash as pgh

try:
    import numpy as np

except ImportError:
    print("Numpy is a soft dependency to use this feature.")
    raise ImportError("Couldn't import numpy, make sure it is installed properly.")

__author__ = "Ilyas Moutawwakil"


class TestNumbaPointGeohash(unittest.TestCase):
    """ """

    def test_encode(self):
        self.assertEqual(pgh.nb_point_encode(42.6, -5.6), "ezs42e44yx96")
        self.assertEqual(pgh.nb_point_encode(42.6, -5.6, precision=5), "ezs42")

    def test_decode(self):
        self.assertEqual(pgh.nb_point_decode("ezs42"), (42.6, -5.6))


class TestNumbaVectorGeohash(unittest.TestCase):
    """ """

    def test_encode(self):
        x = np.array([42.6, 2.6732])
        y = np.array([-5.6, -92.1736])
        geohashes_12 = np.array(["ezs42e44yx96", "9bqrnw9hx2w7"])
        geohashes_5 = np.array(["ezs42", "9bqrn"])

        self.assertListEqual(pgh.nb_vector_encode(x, y).tolist(), geohashes_12.tolist())
        self.assertListEqual(
            pgh.nb_vector_encode(x, y, precision=5).tolist(), geohashes_5.tolist()
        )

    def test_decode(self):
        latitudes = np.array([-10.299737, -42.279401, 2.673264])
        longitudes = np.array([-0.996014, -127.773821, -92.173682])
        geohashes = np.array(["7ypm3kfxxjvf", "30mpkrmbwhmk", "9bqrnw9hvs8b"])
        results = pgh.nb_vector_decode(geohashes)

        self.assertListEqual(results[0].tolist(), latitudes.tolist())
        self.assertListEqual(results[1].tolist(), longitudes.tolist())


if __name__ == "__main__":
    unittest.main()
