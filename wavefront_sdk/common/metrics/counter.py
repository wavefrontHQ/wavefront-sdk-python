# -*- coding: utf-8 -*-
"""Wavefront SDK Counter.

@author Hao Song (songhao@vmware.com)
"""
import threading

from wavefront_sdk.common.metrics import metrics


class WavefrontSdkCounter(metrics.WavefrontSdkMetric):
    """Wavefront SDK Counter."""

    def __init__(self):
        """Construct Wavefront SDK Counter."""
        self._lock = threading.Lock()
        self._count = 0

    def inc(self, val=1):
        """Increase the value of the counter."""
        with self._lock:
            self._count += val

    def count(self):
        """Get the value of the counter."""
        with self._lock:
            return self._count

    def clear(self):
        """Reset the counter."""
        with self._lock:
            self._count = 0
