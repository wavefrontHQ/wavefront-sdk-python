"""
Unit Tests for Wavefront Python SDK - Histogram Impl.

@author Hao Song (songhao@vmware.com)
"""

import unittest
import time
from wavefront_python_sdk.common.utils import AtomicCounter
from wavefront_python_sdk.entities import WavefrontHistogramImpl


class TestHistogramImpl(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls._DELTA = 1e-1
        cls._clock = AtomicCounter(time.time() * 1000)
        cls._pow_10 = cls.create_pow_10_histogram(cls._clock.get)
        cls._inc_100 = WavefrontHistogramImpl(cls._clock.get)
        for i in range(1, 101):
            cls._inc_100.update(i)
        cls._inc_1000 = WavefrontHistogramImpl(cls._clock.get)
        for i in range(1, 1001):
            cls._inc_1000.update(i)
        cls._clock.increment(60000 + 1)

    @staticmethod
    def create_pow_10_histogram(clock_millis):
        wh = WavefrontHistogramImpl(clock_millis)
        wh.update(0.1)
        wh.update(1.0)
        wh.update(1e1)
        wh.update(1e1)
        wh.update(1e2)
        wh.update(1e3)
        wh.update(1e4)
        wh.update(1e4)
        wh.update(1e5)
        return wh

    @staticmethod
    def distribution_to_map(distributions):
        dist_map = {}
        for distribution in distributions:
            for centroid in distribution.centroids:
                dist_map.update({centroid[0]:
                                     dist_map.get(centroid[0], 0) + centroid[
                                         1]})
        return dist_map

    def test_distribution(self):
        wh = self.create_pow_10_histogram(self._clock.get)
        self._clock.increment(60000 + 1)

        distributions = wh.flush_distributions()
        dist_map = self.distribution_to_map(distributions)
        self.assertEqual(7, len(dist_map))
        self.assertTrue(dist_map.get(0.1) == 1)
        self.assertTrue(dist_map.get(1.0) == 1)
        self.assertTrue(dist_map.get(1e1) == 2)
        self.assertTrue(dist_map.get(1e2) == 1)
        self.assertTrue(dist_map.get(1e3) == 1)
        self.assertTrue(dist_map.get(1e4) == 2)
        self.assertTrue(dist_map.get(1e5) == 1)

        self.assertEqual(0, wh.get_count())
        self.assertAlmostEqual(None, wh.get_max(), delta=self._DELTA)
        self.assertAlmostEqual(None, wh.get_min(), delta=self._DELTA)
        self.assertAlmostEqual(None, wh.get_mean(), delta=self._DELTA)
        self.assertAlmostEqual(0, wh.get_sum(), delta=self._DELTA)

        snapshot = wh.get_snapshot()
        self.assertEqual(0, snapshot.get_count())
        self.assertAlmostEqual(None, snapshot.get_max(), delta=self._DELTA)
        self.assertAlmostEqual(None, snapshot.get_min(), delta=self._DELTA)
        self.assertAlmostEqual(None, snapshot.get_mean(), delta=self._DELTA)
        self.assertAlmostEqual(0, snapshot.get_sum(), delta=self._DELTA)
        self.assertAlmostEqual(None, snapshot.get_value(0.5),
                               delta=self._DELTA)

    def test_bulk_update(self):
        wh = WavefrontHistogramImpl(self._clock.get)
        wh.bulk_update([24.2, 84.35, 1002.0], [80, 1, 9])
        self._clock.increment(60000 + 1)
        distributions = wh.flush_distributions()
        dist_map = self.distribution_to_map(distributions)

        self.assertEqual(3, len(dist_map))
        self.assertTrue(dist_map.get(24.2) == 80)
        self.assertTrue(dist_map.get(84.35) == 1)
        self.assertTrue(dist_map.get(1002.0) == 9)

    def test_count(self):
        self.assertEqual(9, self._pow_10.get_count())
        self.assertEqual(9, self._pow_10.get_snapshot().get_count())

    def test_max(self):
        self.assertAlmostEqual(1e5, self._pow_10.get_max(), delta=self._DELTA)
        self.assertAlmostEqual(1e5, self._pow_10.get_snapshot().get_max(),
                               delta=self._DELTA)

    def test_min(self):
        self.assertAlmostEqual(1.0, self._inc_100.get_min(), delta=self._DELTA)
        self.assertAlmostEqual(1.0, self._inc_100.get_snapshot().get_min(),
                               delta=self._DELTA)

    def test_mean(self):
        self.assertAlmostEqual(13457.9, self._pow_10.get_mean(),
                               delta=self._DELTA)
        self.assertAlmostEqual(13457.9, self._pow_10.get_snapshot().get_mean(),
                               delta=self._DELTA)

    def test_sum(self):
        self.assertAlmostEqual(121121.1, self._pow_10.get_sum(),
                               delta=self._DELTA)
        self.assertAlmostEqual(121121.1, self._pow_10.get_snapshot().get_sum(),
                               delta=self._DELTA)

    def test_size(self):
        self.assertEqual(9, self._pow_10.get_snapshot().get_size())
        self.assertEqual(100, self._inc_100.get_snapshot().get_size())
        self.assertEqual(1000, self._inc_1000.get_snapshot().get_size())


if __name__ == '__main__':
    # run 'python -m unittest discover' from top-level to run tests
    unittest.main()
