"""Interface of Metric Sender for both clients.

@author Hao Song (songhao@vmware.com)
"""
from __future__ import unicode_literals


# pylint: disable=E0012,R0205
class WavefrontMetricSender(object):
    """Interface of Metric Sender for both clients."""

    # ∆: INCREMENT
    DELTA_PREFIX = '∆'  # '\u2206'

    # Δ: GREEK CAPITAL LETTER DELTA
    DELTA_PREFIX_2 = 'Δ'  # '\u0394'

    # pylint: disable=too-many-arguments
    def send_metric(self, name, value, timestamp, source, tags):
        """Send Metric Data.

        Wavefront Metrics Data format
        <metricName> <metricValue> [<timestamp>] source=<source> [pointTags]
        Example: "new-york.power.usage 42422 1533531013 source=localhost
                  datacenter=dc1"

        @param name: Metric Name
        @type name: str
        @param value: Metric Value
        @type value: float
        @param timestamp: Timestamp
        @type timestamp: long
        @param source: Source
        @type source: str
        @param tags: Tags
        @type tags: dict
        """
        raise NotImplementedError

    def send_formatted_metric(self, point):
        """Send a formatted metric immediately.

        @param point: Formatted metric point
        @type: str
        """
        self.send_metric_now([point])

    def send_metric_now(self, metrics):
        """Send a list of metrics immediately.

        Have to construct the data manually by calling
        common.utils.metric_to_line_data()

        @param metrics: List of string spans data
        @type metrics: list[str]
        """
        raise NotImplementedError

    def send_delta_counter(self, name, value, source, tags, timestamp=None):
        """Send Delta Counter Data.

        @param name: Metric Name
        @type name: str
        @param value: Metric Value
        @type value: float
        @param source: Source
        @type source: str
        @param tags: Tags
        @param tags: dict
        :param timestamp: Timestamp
        """
        if not (name.startswith(self.DELTA_PREFIX) or
                name.startswith(self.DELTA_PREFIX_2)):
            name = self.DELTA_PREFIX + name
        if value > 0:
            self.send_metric(name, value, timestamp, source, tags)
