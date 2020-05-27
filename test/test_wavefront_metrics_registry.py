"""Unit Tests for Wavefront SDK Metrics Registry.

@author Hao Song (songhao@vmware.com)
"""

import unittest

try:
    import queue
except ImportError:
    import Queue as queue  # noqa

from wavefront_sdk.common.metrics.registry import WavefrontSdkMetricsRegistry
from wavefront_sdk.direct import remaining_capacity_getter


class TestUtils(unittest.TestCase):
    """Test Functions of wavefront_sdk.common.utils."""

    def test_gauge(self):
        """Test WavefrontSdkGauge of WavefrontSdkMetricsRegistry."""
        registry = WavefrontSdkMetricsRegistry(None)
        capacity = 5
        buffer = queue.Queue(capacity)
        size = registry.new_gauge('gauge', buffer.qsize)
        remaining_capacity = registry.new_gauge(
            'remaining', remaining_capacity_getter(buffer))
        self.assertEqual(size.get_value(), 0)
        self.assertEqual(remaining_capacity.get_value(), capacity)
        buffer.put(0)
        self.assertEqual(size.get_value(), 1)
        self.assertEqual(registry.new_gauge('gauge', None).get_value(), 1)
        self.assertEqual(remaining_capacity.get_value(), capacity - 1)

    def test_counter(self):
        """Test WavefrontSdkCounter of WavefrontSdkMetricsRegistry."""
        registry = WavefrontSdkMetricsRegistry(None)
        counter = registry.new_counter('counter')
        self.assertEqual(counter.count(), 0)
        counter.inc()
        self.assertEqual(counter.count(), 1)
        counter.inc(2)
        self.assertEqual(counter.count(), 3)
        self.assertEqual(registry.new_counter('counter').count(), 3)
        self.assertEqual(registry.new_counter('counter_2').count(), 0)


if __name__ == '__main__':
    # run 'python -m unittest discover' from top-level to run tests
    unittest.main()
