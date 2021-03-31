"""Wavefront SDK Gauge.

@author Hao Song (songhao@vmware.com)
"""

from wavefront_sdk.common.metrics import metrics


# pylint: disable=too-few-public-methods
class WavefrontSdkGauge(metrics.WavefrontSdkMetric):
    """Wavefront SDK Gauge."""

    def __init__(self, supplier):
        """Construct Wavefront SDK Gauge."""
        self.supplier = supplier

    def get_value(self):
        """Get value of the gauge."""
        if callable(self.supplier):
            return self.supplier()
        return None
