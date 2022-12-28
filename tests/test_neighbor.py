import unittest
import pygeohash as pgh


__author__ = 'willmcginnis'


class TestGeohash(unittest.TestCase):
    """
    Thest neightboring - test case created using https://www.movable-type.co.uk/scripts/geohash.html
    """
    def test_north_hemisphere_simple_odd(self):
        self.assertEqual(pgh.get_adjacent("gbsuv", "right"), 'gbsuy')
        self.assertEqual(pgh.get_adjacent("gbsuv", "left"), 'gbsuu')
        self.assertEqual(pgh.get_adjacent("gbsuv", "top"), 'gbsvj')
        self.assertEqual(pgh.get_adjacent("gbsuv", "bottom"), 'gbsut')

    def test_north_hemisphere_border_even(self):
        self.assertEqual(pgh.get_adjacent("u00000", "right"), 'u00002')
        self.assertEqual(pgh.get_adjacent("u00000", "left"), 'gbpbpb')
        self.assertEqual(pgh.get_adjacent("u00000", "top"), 'u00001') 
        self.assertEqual(pgh.get_adjacent("u00000", "bottom"), 'spbpbp')

    def test_south_hemisphere_simple_odd(self):
        self.assertEqual(pgh.get_adjacent("kd3ybyu", "right"), 'kd3ybyv')
        self.assertEqual(pgh.get_adjacent("kd3ybyu", "left"), 'kd3ybyg')
        self.assertEqual(pgh.get_adjacent("kd3ybyu", "top"), 'kd3ybzh')
        self.assertEqual(pgh.get_adjacent("kd3ybyu", "bottom"), 'kd3ybys')

    def test_south_hemisphere_border_even(self):
        self.assertEqual(pgh.get_adjacent("k0000000", "right"), 'k0000002')
        self.assertEqual(pgh.get_adjacent("k0000000", "left"), '7bpbpbpb')
        self.assertEqual(pgh.get_adjacent("k0000000", "top"), 'k0000001') 
        self.assertEqual(pgh.get_adjacent("k0000000", "bottom"), 'hpbpbpbp')

    def test_north_pole_even(self):
        self.assertEqual(pgh.get_adjacent("gzzzzz", "right"), 'upbpbp')
        self.assertEqual(pgh.get_adjacent("gzzzzz", "left"), 'gzzzzx')
        self.assertEqual(pgh.get_adjacent("gzzzzz", "bottom"), 'gzzzzy')
        with self.assertRaises(ValueError):
            pgh.get_adjacent("gzzzzz", "top")

    def test_south_pole_odd(self):
        self.assertEqual(pgh.get_adjacent("5bpbpbh", "right"), '5bpbpbj')
        self.assertEqual(pgh.get_adjacent("5bpbpbh", "left"), '5bpbpb5')
        self.assertEqual(pgh.get_adjacent("5bpbpbh", "top"), '5bpbpbk') 
        with self.assertRaises(ValueError):
            pgh.get_adjacent("5bpbpbh", "bottom")
