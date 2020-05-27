"""Unit Tests for Wavefront Python SDK - Histogram Impl.

@author Hao Song (songhao@vmware.com)
"""

import threading
import time
import unittest

from wavefront_sdk.common import utils
from wavefront_sdk.entities import WavefrontHistogramImpl


class TestHistogramImpl(unittest.TestCase):
    """Unit Tests of WavefrontHistogramImpl."""

    @classmethod
    def setUpClass(cls):
        """Initialize for tests."""
        # Delta for error
        cls._DELTA = 1e-1

        # Atomic clock
        cls._clock = utils.AtomicCounter(time.time() * 1000)

        # WavefrontHistogramImpl with values that are powers of 10
        cls._pow_10 = cls.create_pow_10_histogram(cls._clock.get)

        # WavefrontHistogramImpl with a value for each integer from 1 to 100
        cls._inc_100 = WavefrontHistogramImpl(cls._clock.get)
        for i in range(1, 101):
            cls._inc_100.update(i)

        # WavefrontHistogramImpl with a value for each integer from 1 to 1000
        cls._inc_1000 = WavefrontHistogramImpl(cls._clock.get)
        for i in range(1, 1001):
            cls._inc_1000.update(i)

        # Empty Wavefront Histogram
        cls._empty_hist = WavefrontHistogramImpl(cls._clock.get)

        # Simulate that 1 min has passed so that values prior to the
        # current min are ready to be read
        cls._clock.increment(60000 + 1)

    @staticmethod
    def create_pow_10_histogram(clock_millis):
        """Create WavefrontHistogramImpl with values that are powers of 10."""
        w_h = WavefrontHistogramImpl(clock_millis)
        w_h.update(0.1)
        w_h.update(1.0)
        w_h.update(1e1)
        w_h.update(1e1)
        w_h.update(1e2)
        w_h.update(1e3)
        w_h.update(1e4)
        w_h.update(1e4)
        w_h.update(1e5)
        return w_h

    @staticmethod
    def distribution_to_map(distributions):
        """Return Distributions in map format.

        @return: Distributions in map format.
        @rtype: dict
        """
        dist_map = {}
        for distribution in distributions:
            for centroid in distribution.centroids:
                dist_map.update(
                    {centroid[0]: dist_map.get(centroid[0], 0) + centroid[1]})
        return dist_map

    @staticmethod
    def thread_bulk_update(wavefront_histogram, means, counts):
        """Act as a helper func for multi-thread bulk updating."""
        while True:
            wavefront_histogram.bulk_update(means, counts)
            time.sleep(60)

    def test_distribution(self):
        """Test distribution."""
        w_h = self.create_pow_10_histogram(self._clock.get)
        self._clock.increment(60000 + 1)

        distributions = w_h.flush_distributions()
        dist_map = self.distribution_to_map(distributions)
        self.assertEqual(7, len(dist_map))
        self.assertTrue(dist_map.get(0.1) == 1)
        self.assertTrue(dist_map.get(1.0) == 1)
        self.assertTrue(dist_map.get(1e1) == 2)
        self.assertTrue(dist_map.get(1e2) == 1)
        self.assertTrue(dist_map.get(1e3) == 1)
        self.assertTrue(dist_map.get(1e4) == 2)
        self.assertTrue(dist_map.get(1e5) == 1)

        self.assertEqual(0, w_h.get_count())
        self.assertAlmostEqual(None, w_h.get_max(), delta=self._DELTA)
        self.assertAlmostEqual(None, w_h.get_min(), delta=self._DELTA)
        self.assertAlmostEqual(None, w_h.get_mean(), delta=self._DELTA)
        self.assertAlmostEqual(0, w_h.get_sum(), delta=self._DELTA)

        snapshot = w_h.get_snapshot()
        self.assertEqual(0, snapshot.get_count())
        self.assertAlmostEqual(None, snapshot.get_max(), delta=self._DELTA)
        self.assertAlmostEqual(None, snapshot.get_min(), delta=self._DELTA)
        self.assertAlmostEqual(0, snapshot.get_mean(), delta=self._DELTA)
        self.assertAlmostEqual(0, snapshot.get_sum(), delta=self._DELTA)
        self.assertAlmostEqual(None, snapshot.get_value(0.5),
                               delta=self._DELTA)

    def test_bulk_update(self):
        """Test bulk update."""
        w_h = WavefrontHistogramImpl(self._clock.get)
        w_h.bulk_update([24.2, 84.35, 1002.0], [80, 1, 9])
        self._clock.increment(60000 + 1)
        distributions = w_h.flush_distributions()
        dist_map = self.distribution_to_map(distributions)

        self.assertEqual(3, len(dist_map))
        self.assertTrue(dist_map.get(24.2) == 80)
        self.assertTrue(dist_map.get(84.35) == 1)
        self.assertTrue(dist_map.get(1002.0) == 9)

    def test_count(self):
        """Test get count of distribution."""
        self.assertEqual(9, self._pow_10.get_count())
        self.assertEqual(9, self._pow_10.get_snapshot().get_count())

    def test_max(self):
        """Test get max of distribution."""
        self.assertAlmostEqual(1e5, self._pow_10.get_max(), delta=self._DELTA)
        self.assertAlmostEqual(1e5, self._pow_10.get_snapshot().get_max(),
                               delta=self._DELTA)

    def test_min(self):
        """Test get min of distribution."""
        self.assertAlmostEqual(1.0, self._inc_100.get_min(), delta=self._DELTA)
        self.assertAlmostEqual(1.0, self._inc_100.get_snapshot().get_min(),
                               delta=self._DELTA)

    def test_mean(self):
        """Test get mean of distribution."""
        self.assertAlmostEqual(13457.9, self._pow_10.get_mean(),
                               delta=self._DELTA)
        self.assertAlmostEqual(13457.9, self._pow_10.get_snapshot().get_mean(),
                               delta=self._DELTA)

    def test_sum(self):
        """Test get sum of distribution."""
        self.assertAlmostEqual(121121.1, self._pow_10.get_sum(),
                               delta=self._DELTA)
        self.assertAlmostEqual(121121.1, self._pow_10.get_snapshot().get_sum(),
                               delta=self._DELTA)

    def test_std_dev(self):
        """Test get std dev of distribution."""
        self.assertAlmostEqual(30859.85, self._pow_10.std_dev(),
                               delta=self._DELTA)
        self.assertAlmostEqual(28.87, self._inc_100.std_dev(),
                               delta=self._DELTA)
        self.assertAlmostEqual(288.67, self._inc_1000.std_dev(),
                               delta=self._DELTA)
        self.assertEqual(0.0, self._empty_hist.std_dev())

    def test_size(self):
        """Test get size of distribution."""
        self.assertEqual(9, self._pow_10.get_snapshot().get_size())
        self.assertEqual(100, self._inc_100.get_snapshot().get_size())
        self.assertEqual(1000, self._inc_1000.get_snapshot().get_size())

    def test_multi_thread(self):
        """Test of multi-threading case."""
        w_h = WavefrontHistogramImpl(self._clock.get)
        w_h.bulk_update([21.2, 82.35, 1042.0], [70, 2, 6])
        thread_1 = threading.Thread(
            target=self.thread_bulk_update,
            args=(w_h, [24.2, 84.35, 1002.0], [80, 1, 9]))
        thread_2 = threading.Thread(
            target=self.thread_bulk_update,
            args=(w_h, [21.2, 84.35, 1052.0], [60, 12, 8]))
        thread_1.setDaemon(True)
        thread_2.setDaemon(True)
        thread_1.start()
        thread_2.start()
        time.sleep(1)
        self._clock.increment(60000 + 1)
        distributions = w_h.flush_distributions()
        dist_map = self.distribution_to_map(distributions)
        thread_1.join(2)
        thread_2.join(2)

        self.assertEqual(7, len(dist_map))
        self.assertTrue(dist_map.get(21.2) == 130)
        self.assertTrue(dist_map.get(24.2) == 80)
        self.assertTrue(dist_map.get(82.35) == 2)
        self.assertTrue(dist_map.get(84.35) == 13)
        self.assertTrue(dist_map.get(1002.0) == 9)
        self.assertTrue(dist_map.get(1042.0) == 6)
        self.assertTrue(dist_map.get(1052.0) == 8)


if __name__ == '__main__':
    # run 'python -m unittest discover' from top-level to run tests
    unittest.main()
