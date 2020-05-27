# -*- coding: utf-8 -*-
"""Wavefront Proxy Client.

@author Hao Song (songhao@vmware.com).
"""

from __future__ import absolute_import

import logging
from socket import gethostname

from . import entities
from .common import constants, utils
from .common.metrics import registry
from .common.proxy_connection_handler import ProxyConnectionHandler

LOGGER = logging.getLogger('wavefront_sdk.WavefrontDirectClient')


# pylint: disable=too-many-instance-attributes
class WavefrontProxyClient(entities.WavefrontMetricSender,
                           entities.WavefrontHistogramSender,
                           entities.WavefrontTracingSpanSender):
    """WavefrontProxyClient that sends data directly via TCP.

    User should probably attempt to reconnect
    when exceptions are thrown from any methods.
    """

    # pylint: disable=too-many-arguments
    def __init__(self, host, metrics_port, distribution_port, tracing_port,
                 timeout=None, enable_internal_metrics=True):
        """Construct Proxy Client.

        @param host: Hostname of the Wavefront proxy, 2878 by default
        @param metrics_port:
        Metrics Port on which the Wavefront proxy is listening on
        @param distribution_port:
        Distribution Port on which the Wavefront proxy is listening on
        @param tracing_port:
        Tracing Port on which the Wavefront proxy is listening on
        @param timeout:
        Timeout to set on socket connecting to proxy
        """
        self.proxy_host = host
        self.metrics_port = metrics_port
        self.distribution_port = distribution_port
        self.tracing_port = tracing_port

        if enable_internal_metrics:
            self._sdk_metrics_registry = registry.WavefrontSdkMetricsRegistry(
                wf_metric_sender=self,
                prefix='{}.core.sender.proxy'.format(
                    constants.SDK_METRIC_PREFIX))
        else:
            self._sdk_metrics_registry = registry.WavefrontSdkMetricsRegistry(
                wf_metric_sender=None)

        self._metrics_proxy_connection_handler = (
            None if metrics_port is None
            else ProxyConnectionHandler(host, metrics_port,
                                        self._sdk_metrics_registry,
                                        'metricHandler',
                                        timeout=timeout))
        self._histogram_proxy_connection_handler = (
            None if distribution_port is None
            else ProxyConnectionHandler(host, distribution_port,
                                        self._sdk_metrics_registry,
                                        'histogramHandler',
                                        timeout=timeout))
        self._tracing_proxy_connection_handler = (
            None if tracing_port is None
            else ProxyConnectionHandler(host, tracing_port,
                                        self._sdk_metrics_registry,
                                        'tracingHandler',
                                        timeout=timeout))
        self._default_source = gethostname()

        self._points_discarded = self._sdk_metrics_registry.new_counter(
            'points.discarded')
        self._points_dropped = self._sdk_metrics_registry.new_counter(
            'points.dropped')
        self._points_valid = self._sdk_metrics_registry.new_counter(
            'points.valid')
        self._points_invalid = self._sdk_metrics_registry.new_counter(
            'points.invalid')

        self._histograms_dropped = self._sdk_metrics_registry.new_counter(
            'histograms.dropped')
        self._histograms_discarded = self._sdk_metrics_registry.new_counter(
            'histograms.discarded')
        self._histograms_valid = self._sdk_metrics_registry.new_counter(
            'histograms.valid')
        self._histograms_invalid = self._sdk_metrics_registry.new_counter(
            'histograms.invalid')

        self._spans_dropped = self._sdk_metrics_registry.new_counter(
            'spans.dropped')
        self._spans_discarded = self._sdk_metrics_registry.new_counter(
            'spans.discarded')
        self._spans_valid = self._sdk_metrics_registry.new_counter(
            'spans.valid')
        self._spans_invalid = self._sdk_metrics_registry.new_counter(
            'spans.invalid')

        self._span_logs_dropped = self._sdk_metrics_registry.new_counter(
            'span_logs.dropped')
        self._span_logs_discarded = self._sdk_metrics_registry.new_counter(
            'span_logs.discarded')
        self._span_logs_valid = self._sdk_metrics_registry.new_counter(
            'span_logs.valid')
        self._span_logs_invalid = self._sdk_metrics_registry.new_counter(
            'span_logs.invalid')

    def close(self):
        """Close all proxy connections."""
        if self._metrics_proxy_connection_handler:
            self._metrics_proxy_connection_handler.close()
        if self._histogram_proxy_connection_handler:
            self._histogram_proxy_connection_handler.close()
        if self._tracing_proxy_connection_handler:
            self._tracing_proxy_connection_handler.close()
        self._sdk_metrics_registry.close(timeout_secs=1)

    def get_failure_count(self):
        """Get Total Failure Count for all connections.

        @return: Failure Count
        """
        failure_count = 0
        if self._metrics_proxy_connection_handler:
            failure_count += (
                self._metrics_proxy_connection_handler.get_failure_count())
        if self._histogram_proxy_connection_handler:
            failure_count += (
                self._histogram_proxy_connection_handler.get_failure_count())
        if self._tracing_proxy_connection_handler:
            failure_count += (
                self._tracing_proxy_connection_handler.get_failure_count())
        return failure_count

    # pylint: disable=too-many-arguments
    def send_metric(self, name, value, timestamp, source, tags):
        """Send Metric Data via proxy.

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
        if not self._metrics_proxy_connection_handler:
            self._points_discarded.inc()
            LOGGER.warning("Can't send data to Wavefront. Please configure "
                           "metrics port for Wavefront proxy.")
        try:
            line_data = utils.metric_to_line_data(
                name, value, timestamp, source, tags, self._default_source)
            self._points_valid.inc()
            self._metrics_proxy_connection_handler.send_data(line_data)
        except ValueError:
            self._points_invalid.inc()
        except Exception as error:
            self._points_dropped.inc()
            self._metrics_proxy_connection_handler.increment_failure_count()
            raise error

    def send_metric_now(self, metrics):
        """Send a list of metrics immediately.

        Have to construct the data manually by calling
        common.utils.metric_to_line_data()

        @param metrics: List of string spans data
        @type metrics: list[str]
        """
        if not self._metrics_proxy_connection_handler:
            self._points_discarded.inc()
            LOGGER.warning("Can't send data to Wavefront. Please configure "
                           "metrics port for Wavefront proxy.")
        for metric in metrics:
            try:
                self._metrics_proxy_connection_handler.send_data(metric)
            except Exception as error:
                self._points_dropped.inc()
                self._metrics_proxy_connection_handler.increment_failure_count(
                )
                raise error

    # pylint: disable=too-many-arguments
    def send_distribution(self, name, centroids, histogram_granularities,
                          timestamp, source, tags):
        """Send Distribution Data via proxy.

        Wavefront Histogram Data format
        {!M | !H | !D} [<timestamp>] #<count> <mean> [centroids]
        <histogramName> source=<source> [pointTags]
        Example: "!M 1533531013 #20 30.0 #10 5.1 request.latency
                  source=appServer1 region=us-west"

        @param name: Histogram Name
        @type name: str
        @param centroids: List of centroids(pairs)
        @type centroids: list
        @param histogram_granularities: Histogram Granularities
        @type histogram_granularities: set
        @param timestamp: Timestamp
        @type timestamp: long
        @param source: Source
        @type source: str
        @param tags: Tags
        @type tags: dict
        """
        if not self._histogram_proxy_connection_handler:
            self._histograms_discarded.inc()
            LOGGER.warning("Can't send data to Wavefront. Please configure "
                           "histogram distribution port for Wavefront proxy.")
        try:
            line_data = utils.histogram_to_line_data(
                name, centroids, histogram_granularities, timestamp, source,
                tags, self._default_source)
            self._histograms_valid.inc()
            self._histogram_proxy_connection_handler.send_data(line_data)
        except ValueError:
            self._histograms_invalid.inc()
        except Exception as error:
            self._histograms_dropped.inc()
            self._histogram_proxy_connection_handler.increment_failure_count()
            raise error

    def send_distribution_now(self, distributions):
        """Send a list of distributions immediately.

        Have to construct the data manually by calling
        common.utils.histogram_to_line_data()

        @param distributions: List of string distribution data
        @type distributions: list[str]
        """
        if not self._histogram_proxy_connection_handler:
            self._histograms_discarded.inc()
            LOGGER.warning("Can't send data to Wavefront. Please configure "
                           "histogram distribution port for Wavefront proxy.")
        for distribution in distributions:
            try:
                self._histogram_proxy_connection_handler.send_data(
                    distribution)
            except Exception as error:
                self._histograms_dropped.inc()
                (self._histogram_proxy_connection_handler
                 .increment_failure_count())
                raise error

    # pylint: disable=too-many-arguments
    def send_span(self, name, start_millis, duration_millis, source, trace_id,
                  span_id, parents, follows_from, tags, span_logs):
        """Send span data via proxy.

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
        @type tags: list
        @param span_logs: Span Log
        """
        if not self._tracing_proxy_connection_handler:
            self._spans_discarded.inc()
            if span_logs:
                self._span_logs_discarded.inc()
            LOGGER.warning("Can't send data to Wavefront. Please configure "
                           "tracing port for Wavefront proxy.")
        try:
            line_data = utils.tracing_span_to_line_data(
                name, start_millis, duration_millis, source, trace_id,
                span_id, parents, follows_from, tags, span_logs,
                self._default_source)
            self._spans_valid.inc()
            self._tracing_proxy_connection_handler.send_data(line_data)
        except ValueError:
            self._spans_invalid.inc()
        except Exception as error:
            self._spans_dropped.inc()
            self._tracing_proxy_connection_handler.increment_failure_count()
            raise error
        if span_logs:
            try:
                span_log_line_data = utils.span_log_to_line_data(
                    trace_id, span_id, span_logs)
                self._span_logs_valid.inc()
                self._tracing_proxy_connection_handler.send_data(
                    span_log_line_data)
            except ValueError:
                self._span_logs_invalid.inc()
            except Exception as error:
                self._span_logs_dropped.inc()
                (self._tracing_proxy_connection_handler.
                 increment_failure_count())
                raise error

    def send_span_now(self, spans):
        """Send a list of spans immediately.

        Have to construct the data manually by calling
        common.utils.tracing_span_to_line_data()

        @param spans: List of string tracing span data
        @type spans: list[str]
        """
        if not self._tracing_proxy_connection_handler:
            self._spans_discarded.inc()
            LOGGER.warning("Can't send data to Wavefront. Please configure "
                           "tracing port for Wavefront proxy.")
        for span in spans:
            try:
                self._tracing_proxy_connection_handler.send_data(span)
            except Exception as error:
                self._spans_dropped.inc()
                self._tracing_proxy_connection_handler.increment_failure_count(
                    )
                raise error

    def send_span_log_now(self, span_logs):
        """Send a list of span logs immediately.

        Have to construct the data manually by calling
        common.utils.tracing_span_to_line_data()

        @param span_logs: List of string span log data
        @type span_logs: list[str]
        """
        if not self._tracing_proxy_connection_handler:
            self._span_logs_discarded.inc()
            LOGGER.warning("Can't send data to Wavefront. Please configure "
                           "tracing port for Wavefront proxy.")
        for span_log in span_logs:
            try:
                self._tracing_proxy_connection_handler.send_data(span_log)
            except Exception as error:
                self._span_logs_dropped.inc()
                self._tracing_proxy_connection_handler.increment_failure_count(
                )
                raise error
