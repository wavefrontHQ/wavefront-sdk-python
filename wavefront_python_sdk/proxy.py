"""
Wavefront Proxy Client
@author Hao Song (songhao@vmware.com).
"""

from __future__ import absolute_import, division, print_function

from socket import gethostname
from wavefront_python_sdk.common.proxy_connection_handler import \
    ProxyConnectionHandler
from wavefront_python_sdk.common.utils import metric_to_line_data, \
    histogram_to_line_data, tracing_span_to_line_data


class WavefrontProxyClient(object):
    """
    WavefrontProxyClient that sends data directly via TCP
    to the Wavefront Proxy Agent.

    User should probably attempt to reconnect
    when exceptions are thrown from any methods.
    """

    def __init__(self, host, metrics_port, distribution_port, tracing_port):
        """
        Constructor of Direct Ingestion Client
        @param host: Hostname of the Wavefront proxy, 2878 by default
        @param metrics_port:
        Metrics Port on which the Wavefront proxy is listening on
        @param distribution_port:
        Distribution Port on which the Wavefront proxy is listening on
        @param tracing_port:
        Tracing Port on which the Wavefront proxy is listening on
        """
        self.proxy_host = host
        self.metrics_port = metrics_port
        self.distribution_port = distribution_port
        self.tracing_port = tracing_port
        self._metrics_proxy_connection_handler = None if metrics_port is None \
            else ProxyConnectionHandler(host, metrics_port)
        self._histogram_proxy_connection_handler = None if distribution_port is None \
            else ProxyConnectionHandler(host, distribution_port)
        self._tracing_proxy_connection_handler = None if tracing_port is None \
            else ProxyConnectionHandler(host, tracing_port)
        self._default_source = gethostname()

    def send_metric(self, name, value, timestamp, source, tags):
        """
        Send Metric Data via proxy
        Wavefront Metrics Data format
        <metricName> <metricValue> [<timestamp>] source=<source> [pointTags]
        Example: "new-york.power.usage 42422 1533531013 source=localhost
                  datacenter=dc1"
        @param name: Metric Name
        @type name: str
        @param value: Metric Value
        @type value: str
        @param timestamp: Timestamp
        @type timestamp: long
        @param source: Source
        @type source: str
        @param tags: Tags
        @type tags: dict
        """
        try:
            line_data = metric_to_line_data(name, value, timestamp, source,
                                            tags, self._default_source)
            self._metrics_proxy_connection_handler.send_data(line_data)
        except Exception as e:
            self._metrics_proxy_connection_handler.increment_failure_count()
            raise e

    def send_metric_now(self, spans):
        """
        Send a list of spans immediately. Have to constructor the data manually
        by calling common.utils.metric_to_line_data()
        @param spans: List of string spans data
        @type spans: list[str]
        """
        for span in spans:
            try:
                self._metrics_proxy_connection_handler.send_data(span)
            except Exception as e:
                self._metrics_proxy_connection_handler.increment_failure_count()
                raise e

    def send_distribution(self, name, centroids, histogram_granularities,
                          timestamp, source, tags):
        """
        Send Distribution Data via proxy
        Wavefront Histogram Data format
        {!M | !H | !D} [<timestamp>] #<count> <mean> [centroids] <histogramName>
        source=<source> [pointTags]
        Example: "!M 1533531013 #20 30.0 #10 5.1 request.latency source=appServer1
                  region=us-west"
        @param name: Histogram Name
        @type name: str
        @param centroids: List of centroids(pairs)
        @type centroids: list
        @param histogram_granularities: Histogram Granularities
        @type histogram_granularities: str
        @param timestamp: Timestamp
        @type timestamp: long
        @param source: Source
        @type source: str
        @param tags: Tags
        @type tags: dict
        """
        try:
            line_data = histogram_to_line_data(name, centroids,
                                               histogram_granularities,
                                               timestamp, source, tags,
                                               self._default_source)
            self._histogram_proxy_connection_handler.send_data(line_data)
        except Exception as e:
            self._histogram_proxy_connection_handler.increment_failure_count()
            raise e

    def send_distribution_now(self, distributions):
        """
        Send a list of distributions immediately. Have to constructor the data
        manually by calling common.utils.histogram_to_line_data()
        @param distributions: List of string distribution data
        @type distributions: list[str]
        """
        for distribution in distributions:
            try:
                self._histogram_proxy_connection_handler.send_data(distribution)
            except Exception as e:
                self._histogram_proxy_connection_handler.increment_failure_count()
                raise e

    def send_span(self, name, start_millis, duration_millis, source, trace_id,
                  span_id,
                  parents, follows_from, tags, span_logs):
        """
        Send span data via proxy
        Wavefront Tracing Span Data format
        <tracingSpanName> source=<source> [pointTags] <start_millis>
        <duration_milli_seconds>
        Example: "getAllUsers source=localhost
                  traceId=7b3bf470-9456-11e8-9eb6-529269fb1459
                  spanId=0313bafe-9457-11e8-9eb6-529269fb1459
                  parent=2f64e538-9457-11e8-9eb6-529269fb1459
                  application=Wavefront http.method=GET
                  1533531013 343500"
        @param name: Span Name
        @type name: str
        @param start_millis: Start time
        @type start_millis: long
        @param duration_millis: Duration time
        @type duration_millis: long
        @param source: Source
        @type source: str
        @param trace_id: Trace ID
        @type trace_id: UUID
        @param span_id: Span ID
        @type span_id: UUID
        @param parents: Parents Span ID
        @type parents: List of UUID
        @param follows_from: Follows Span ID
        @type follows_from: List of UUID
        @param tags: Tags
        @type tags: dict
        @param span_logs: Span Log
        """
        try:
            line_data = tracing_span_to_line_data(name, start_millis,
                                                  duration_millis, source,
                                                  trace_id, span_id,
                                                  parents, follows_from, tags,
                                                  span_logs,
                                                  self._default_source)
            self._tracing_proxy_connection_handler.send_data(line_data)
        except Exception as e:
            self._tracing_proxy_connection_handler.increment_failure_count()
            raise e

    def send_span_now(self, spans):
        """
        Send a list of spans immediately. Have to constructor the data manually
        by calling common.utils.tracing_span_to_line_data()
        @param spans: List of string tracing span data
        @type spans: list[str]
        """
        for span in spans:
            try:
                self._tracing_proxy_connection_handler.send_data(span)
            except Exception as e:
                self._tracing_proxy_connection_handler.increment_failure_count()
                raise e
