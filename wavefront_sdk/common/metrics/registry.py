"""Wavefront SDK Metrics Registry.

@author Hao Song (songhao@vmware.com)
"""
import logging
import threading
import time

from wavefront_sdk.common.metrics import counter, deltacounter, gauge

LOGGER = logging.getLogger('wavefront_sdk.WavefrontSdkMetricsRegistry')


# pylint: disable=too-many-instance-attributes,E0012,R0205
class WavefrontSdkMetricsRegistry(object):
    """Wavefront SDK Metrics Registry."""

    # pylint: disable=too-many-arguments
    def __init__(self, wf_metric_sender, source=None, tags=None, prefix=None,
                 reporting_interval_secs=60):
        """Construct Wavefront SDK Metrics Registry."""
        self.wf_metric_sender = wf_metric_sender
        self.source = source
        self.tags = tags
        self.prefix = '' if not prefix else prefix + '.'
        self.reporting_interval_secs = reporting_interval_secs
        self.metrics = {}
        self._closed = False
        self._schedule_lock = threading.RLock()
        self._timer = None
        if wf_metric_sender:
            self._schedule_timer()

    def _schedule_timer(self):
        if not self._closed:
            self._timer = threading.Timer(self.reporting_interval_secs,
                                          self._run)
            self._timer.daemon = True
            self._timer.start()

    # pylint: disable=broad-except
    def _report(self, timeout_secs=None):
        timestamp = time.time()

        # Copying the dict prevents concurrent modification while iterating
        for key, val in self.metrics.copy().items():
            if timeout_secs and time.time() - timestamp > timeout_secs:
                break
            name = self.prefix + key
            try:
                if isinstance(val, gauge.WavefrontSdkGauge):
                    gauge_value = val.get_value()
                    if gauge_value:
                        self.wf_metric_sender.send_metric(
                            name, gauge_value, timestamp, self.source,
                            self.tags)
                elif isinstance(val, deltacounter.WavefrontSdkDeltaCounter):
                    delta_count = val.count()
                    self.wf_metric_sender.send_delta_counter(
                        name + '.count', delta_count,
                        self.source, self.tags, timestamp)
                    val.dec(delta_count)
                elif isinstance(val, counter.WavefrontSdkCounter):
                    self.wf_metric_sender.send_metric(
                        name + '.count', val.count(), timestamp,
                        self.source, self.tags)
            except Exception:
                LOGGER.warning('Unable to send internal SDK metric.')

    def _run(self):
        try:
            self._report()
        finally:
            with self._schedule_lock:
                if not self._closed:
                    self._schedule_timer()

    def close(self, timeout_secs=None):
        """Close Wavefront SDK Metrics Registry."""
        try:
            if self.wf_metric_sender:
                self._report(timeout_secs)
        finally:
            with self._schedule_lock:
                self._closed = True
                if self._timer is not None:
                    self._timer.cancel()

    def new_counter(self, name):
        """Get or create a counter from the registry."""
        return self._get_or_add(name, counter.WavefrontSdkCounter())

    def new_delta_counter(self, name):
        """Get or create a delta counter from the registry."""
        return self._get_or_add(name, deltacounter.WavefrontSdkDeltaCounter())

    def new_gauge(self, name, supplier):
        """Get or create a gauge from the registry."""
        return self._get_or_add(name, gauge.WavefrontSdkGauge(supplier))

    def _get_or_add(self, name, metric):
        existing_metric = self.metrics.get(name)
        if existing_metric:
            return existing_metric
        self.metrics.update({name: metric})
        return metric
