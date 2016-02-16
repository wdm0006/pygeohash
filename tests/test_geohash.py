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
        self.assertEqual(pgh.decode('ezs42'), (42.6, -5.6))

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
        self.assertAlmostEqual(pgh.geohash_haversine_distance('testxyz', 'testwxy'), 6339.483649071294, places=4)

    def test_stats(self):
        data = [(50, 0), (-50, 0), (0, -50), (0, 50)]
        data = [pgh.encode(lat, lon) for lat, lon in data]

        # mean
        mean = pgh.mean(data)
        self.assertEqual(mean, '7zzzzzzzzzzz')

        # north
        north = pgh.northern(data)
        self.assertEqual(north, 'gbzurypzpgxc')

        # south
        south = pgh.southern(data)
        self.assertEqual(south, '5zpgxczbzury')

        # east
        east = pgh.eastern(data)
        self.assertEqual(east, 'mpgxczbzuryp')

        # west
        west = pgh.western(data)
        self.assertEqual(west, '6zurypzpgxcz')

        var = pgh.variance(data)
        self.assertAlmostEqual(var, 30910779278721.996, places=2)

        std = pgh.std(data)
        self.assertAlmostEqual(std, 5559746.332227937, places=4)
