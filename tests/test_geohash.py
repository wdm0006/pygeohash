import unittest
import pygeohash as pgh

__author__ = 'willmcginnis'


class TestGeohash(unittest.TestCase):
    """
    """

    def test_encode(self):
        self.assertEqual(pgh.encode(42.6, -5.6), 'ezs42e44yx96')
        self.assertEqual(pgh.encode(42.6, -5.6, precision=5), 'ezs42')

    def test_decode(self):
        self.assertEqual(pgh.decode('ezs42'), pgh.LatLong(42.6, -5.6))

    def test_check_validity(self):
        exception_raised = False
        try:
            pgh.geohash_approximate_distance('shibu', 'shiba', check_validity=True)
        except ValueError:
            exception_raised = True

        self.assertTrue(exception_raised)

    def test_distance(self):
        # test the fast geohash distance approximations
        self.assertEqual(pgh.geohash_approximate_distance('bcd3u', 'bc83n'), 625441)
        self.assertEqual(pgh.geohash_approximate_distance('bcd3uasd', 'bcd3n'), 19545)
        self.assertEqual(pgh.geohash_approximate_distance('bcd3u', 'bcd3uasd'), 3803)
        self.assertEqual(pgh.geohash_approximate_distance('bcd3ua', 'bcd3uasdub'), 610)

        # test the haversine great circle distance calculations
        self.assertAlmostEqual(pgh.geohash_haversine_distance('testxyz', 'testwxy'), 5888.614420771857, places=4)

    def test_stats(self):
        coordinates = [pgh.LatLong(50, 0), pgh.LatLong(-50, 0), pgh.LatLong(0, -50), pgh.LatLong(0, 50)]
        coordinates = [pgh.encode(*coordinate) for coordinate in coordinates]

        # mean
        mean = pgh.mean(coordinates)
        self.assertEqual(mean, '7zzzzzzzzzzz')

        # north
        north = pgh.northern(coordinates)
        self.assertEqual(north, 'gbzurypzpgxc')

        # south
        south = pgh.southern(coordinates)
        self.assertEqual(south, '5zpgxczbzury')

        # east
        east = pgh.eastern(coordinates)
        self.assertEqual(east, 'mpgxczbzuryp')

        # west
        west = pgh.western(coordinates)
        self.assertEqual(west, '6zurypzpgxcz')

        var = pgh.variance(coordinates)
        self.assertAlmostEqual(var, 30910779169327.953, places=2)

        std = pgh.std(coordinates)
        self.assertAlmostEqual(std, 5559746.322389894, places=4)
