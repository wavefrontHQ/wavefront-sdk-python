# -*- coding: utf-8 -*-
"""Wavefront Direct Ingestion Client.

@author Hao Song (songhao@vmware.com)
"""

from __future__ import absolute_import

import logging
import socket
import threading

import requests

try:
    import queue
except ImportError:
    import Queue as queue  # noqa

from . import entities
from .common import connection_handler, constants, utils
from .common.metrics import registry


# pylint: disable=too-many-instance-attributes
class WavefrontDirectClient(connection_handler.ConnectionHandler,
                            entities.WavefrontMetricSender,
                            entities.WavefrontHistogramSender,
                            entities.WavefrontTracingSpanSender,
                            entities.WavefrontEventSender):
    """Wavefront direct ingestion client.

    Sends data directly to Wavefront cluster via the direct ingestion API.
    """

    WAVEFRONT_METRIC_FORMAT = 'wavefront'
    WAVEFRONT_HISTOGRAM_FORMAT = 'histogram'
    WAVEFRONT_TRACING_SPAN_FORMAT = 'trace'
    WAVEFRONT_SPAN_LOG_FORMAT = 'spanLogs'
    WAVEFRONT_EVENT_FORMAT = 'event'

    REPORT_END_POINT = '/report'
    EVENT_END_POINT = '/api/v2/event'

    # pylint: disable=too-many-arguments
    # pylint: disable=too-many-statements

    def __init__(self,
                 server,
                 token,
                 max_queue_size=50000,
                 batch_size=10000,
                 flush_interval_seconds=5,
                 enable_internal_metrics=True):
        """Construct Direct Client.

        @param server: Server address, Example: https://INSTANCE.wavefront.com
        @type server: str
        @param token: Token with Direct Data Ingestion permission granted
        @type token: str
        @param max_queue_size:
        @type max_queue_size: int
        Max Queue Size, size of internal data buffer for each data type.
        50000 by default
        @param batch_size:
        @type batch_size: int
        Batch Size, amount of data sent by one api call, 10000 by default
        @param flush_interval_seconds: Interval flush time, 5 secs by default
        @type flush_interval_seconds: int
        """
        super().__init__()
        self.server = server
        self._token = token
        self._max_queue_size = max_queue_size
        self._batch_size = batch_size
        self._flush_interval_seconds = flush_interval_seconds
        self._default_source = socket.gethostname() or 'unknown'
        self._metrics_buffer = queue.Queue(max_queue_size)
        self._histograms_buffer = queue.Queue(max_queue_size)
        self._tracing_spans_buffer = queue.Queue(max_queue_size)
        self._spans_log_buffer = queue.Queue(max_queue_size)
        self._events_buffer = queue.Queue(max_queue_size)
        self._headers = {'Content-Type': 'application/octet-stream',
                         'Content-Encoding': 'gzip',
                         'Authorization': 'Bearer ' + token}
        self._event_headers = {'Content-Type': 'application/json',
                               'Content-Encoding': 'gzip',
                               'Authorization': 'Bearer ' + token}
        self._closed = False
        self._schedule_lock = threading.Lock()
        self._timer = None
        self._schedule_timer()

        if enable_internal_metrics:
            self._sdk_metrics_registry = registry.WavefrontSdkMetricsRegistry(
                wf_metric_sender=self,
                prefix='{}.core.sender.direct'.format(
                    constants.SDK_METRIC_PREFIX))
        else:
            self._sdk_metrics_registry = registry.WavefrontSdkMetricsRegistry(
                wf_metric_sender=None)

        semver = utils.get_sem_ver(constants.WAVEFRONT_SDK_PYTHON)

        def version():
            return semver
        self._sdk_metrics_registry.new_gauge('version', version)
        self._sdk_metrics_registry.new_gauge(
            'points.queue.size', self._metrics_buffer.qsize)
        self._sdk_metrics_registry.new_gauge(
            'points.queue.remaining_capacity',
            remaining_capacity_getter(self._metrics_buffer))
        self._points_valid = self._sdk_metrics_registry.new_counter(
            'points.valid')
        self._points_invalid = self._sdk_metrics_registry.new_counter(
            'points.invalid')
        self._points_dropped = self._sdk_metrics_registry.new_counter(
            'points.dropped')
        self._points_report_errors = self._sdk_metrics_registry.new_counter(
            'points.report.errors')

        self._sdk_metrics_registry.new_gauge(
            'histograms.queue.size', self._histograms_buffer.qsize)
        self._sdk_metrics_registry.new_gauge(
            'histograms.queue.remaining_capacity',
            remaining_capacity_getter(self._histograms_buffer))
        self._histograms_valid = self._sdk_metrics_registry.new_counter(
            'histograms.valid')
        self._histograms_invalid = self._sdk_metrics_registry.new_counter(
            'histograms.invalid')
        self._histograms_dropped = self._sdk_metrics_registry.new_counter(
            'histograms.dropped')
        self._histograms_report_errors = (
            self._sdk_metrics_registry.new_counter('histograms.report.errors'))

        self._sdk_metrics_registry.new_gauge(
            'spans.queue.size', self._tracing_spans_buffer.qsize)
        self._sdk_metrics_registry.new_gauge(
            'spans.queue.remaining_capacity',
            remaining_capacity_getter(self._tracing_spans_buffer))
        self._spans_valid = self._sdk_metrics_registry.new_counter(
            'spans.valid')
        self._spans_invalid = self._sdk_metrics_registry.new_counter(
            'spans.invalid')
        self._spans_dropped = self._sdk_metrics_registry.new_counter(
            'spans.dropped')
        self._spans_report_errors = self._sdk_metrics_registry.new_counter(
            'spans.report.errors')

        self._sdk_metrics_registry.new_gauge(
            'span_logs.queue.size', self._spans_log_buffer.qsize)
        self._sdk_metrics_registry.new_gauge(
            'span_logs.queue.remaining_capacity',
            remaining_capacity_getter(self._spans_log_buffer))
        self._span_logs_valid = self._sdk_metrics_registry.new_counter(
            'span_logs.valid')
        self._span_logs_invalid = self._sdk_metrics_registry.new_counter(
            'span_logs.invalid')
        self._span_logs_dropped = self._sdk_metrics_registry.new_counter(
            'span_logs.dropped')
        self._span_logs_report_errors = self._sdk_metrics_registry.new_counter(
            'span_logs.report.errors')

        self._sdk_metrics_registry.new_gauge(
            'events.queue.size', self._events_buffer.qsize)
        self._sdk_metrics_registry.new_gauge(
            'events.queue.remaining_capacity',
            remaining_capacity_getter(self._events_buffer))
        self._events_valid = self._sdk_metrics_registry.new_counter(
            'events.valid')
        self._events_invalid = self._sdk_metrics_registry.new_counter(
            'events.invalid')
        self._events_dropped = self._sdk_metrics_registry.new_counter(
            'events.dropped')
        self._events_report_errors = self._sdk_metrics_registry.new_counter(
            'events.report.errors')

    def _report(self, points, data_format, entity_prefix, report_errors):
        r"""One api call sending one given string data.

        @param points: List of data in string format, concat by '\n'
        @type points: str
        @param data_format: Type of data to be sent
        @type data_format: str
        """
        try:
            if data_format == self.WAVEFRONT_EVENT_FORMAT:
                response = requests.post(self.server + self.EVENT_END_POINT,
                                         params=None,
                                         headers=self._event_headers,
                                         data=points)
            else:
                params = {'f': data_format}
                compressed_data = utils.gzip_compress(points.encode('utf-8'))
                response = requests.post(self.server + self.REPORT_END_POINT,
                                         params=params,
                                         headers=self._headers,
                                         data=compressed_data)

            self._sdk_metrics_registry.new_counter(
                '{}.report.{}'.format(entity_prefix,
                                      response.status_code)).inc()
            response.raise_for_status()
        except Exception as error:
            report_errors.inc()
            raise error

    def _batch_report(self, batch_line_data, data_format, entity_prefix,
                      report_errors):
        """One api call sending one given list of data.

        @param batch_line_data: List of data to be sent
        @type batch_line_data: list
        @param data_format: Type of data to be sent
        @type data_format: str
        """
        # Split data into chunks, each with the size of given batch_size
        for batch in utils.chunks(batch_line_data, self._batch_size):
            # report once per batch
            try:
                self._report('\n'.join(batch) + '\n', data_format,
                             entity_prefix, report_errors)
            # pylint: disable=broad-except,fixme
            # TODO: Please replace a generic Exception with a specific one.
            except Exception as error:
                logging.error(
                    'Failed to report %s data points to wavefront %s',
                    data_format, error)

    def _internal_flush(self, data_buffer, data_format, entity_prefix,
                        report_errors):
        """Get all data from one data buffer to a list, and report that list.

        @param data_buffer: Data buffer to be flush and sent
        @type: Queue
        @param data_format: Type of data to be sent
        @type: str
        """
        data = []
        size = data_buffer.qsize()
        while size > 0 and not data_buffer.empty():
            data.append(data_buffer.get())
            size -= 1
        self._batch_report(data, data_format, entity_prefix, report_errors)

    def _schedule_timer(self):
        # Flush every 5 secs by default
        if not self._closed:
            self._timer = threading.Timer(self._flush_interval_seconds,
                                          self._flush)
            self._timer.daemon = True
            self._timer.start()

    def _flush(self):
        """Use Timer to keep flushing each <flush_interval_seconds> secs."""
        try:
            self.flush_now()
        finally:
            with self._schedule_lock:
                if not self._closed:
                    self._schedule_timer()

    def flush_now(self):
        """Flush all the data buffer immediately."""
        self._internal_flush(self._metrics_buffer,
                             self.WAVEFRONT_METRIC_FORMAT, 'points',
                             self._points_report_errors)
        self._internal_flush(self._histograms_buffer,
                             self.WAVEFRONT_HISTOGRAM_FORMAT, 'histograms',
                             self._histograms_report_errors)
        self._internal_flush(self._tracing_spans_buffer,
                             self.WAVEFRONT_TRACING_SPAN_FORMAT, 'spans',
                             self._spans_report_errors)
        self._internal_flush(self._spans_log_buffer,
                             self.WAVEFRONT_SPAN_LOG_FORMAT, 'span_logs',
                             self._span_logs_report_errors)
        self._internal_flush(self._events_buffer,
                             self.WAVEFRONT_EVENT_FORMAT, 'events',
                             self._events_report_errors)

    def close(self):
        """Flush all buffer before close the client."""
        self.flush_now()
        with self._schedule_lock:
            self._closed = True
            if self._timer is not None:
                self._timer.cancel()
        self._sdk_metrics_registry.close(timeout_secs=1)

    def send_metric(self, name, value, timestamp, source, tags):
        """Send Metric Data via direct ingestion client.

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
        try:
            line_data = utils.metric_to_line_data(
                name, value, timestamp, source, tags, self._default_source)
            self._points_valid.inc()
        except ValueError as error:
            self._points_invalid.inc()
            raise error
        try:
            self._metrics_buffer.put(line_data)
        except queue.Full as error:
            self._points_dropped.inc()
            raise error

    def send_metric_now(self, metrics):
        """Send a list of metrics immediately.

        Have to construct the data manually by calling
        common.utils.metric_to_line_data()

        @param metrics: List of string spans data
        @type metrics: list[str]
        """
        self._batch_report(metrics, self.WAVEFRONT_METRIC_FORMAT, 'points',
                           self._points_report_errors)

    def send_distribution(self, name, centroids, histogram_granularities,
                          timestamp, source, tags):
        """Send Distribution Data via direct ingestion client.

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
        try:
            line_data = utils.histogram_to_line_data(
                name, centroids, histogram_granularities, timestamp,
                source, tags, self._default_source)
            self._histograms_valid.inc()
        except ValueError as error:
            self._histograms_invalid.inc()
            raise error
        try:
            self._histograms_buffer.put(line_data)
        except queue.Full as error:
            self._histograms_dropped.inc()
            raise error

    def send_distribution_now(self, distributions):
        """Send a list of distribution immediately.

        Have to construct the data manually by calling
        common.utils.histogram_to_line_data()

        @param distributions: List of string spans data
        @type distributions: list[str]
        """
        self._batch_report(distributions, self.WAVEFRONT_HISTOGRAM_FORMAT,
                           'histograms', self._histograms_report_errors)

    # pylint: disable=too-many-arguments

    def send_span(self, name, start_millis, duration_millis, source, trace_id,
                  span_id, parents, follows_from, tags, span_logs):
        """Send span data via direct ingestion client.

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
        try:
            line_data = utils.tracing_span_to_line_data(
                name, start_millis, duration_millis, source, trace_id, span_id,
                parents, follows_from, tags, span_logs, self._default_source)
            self._spans_valid.inc()
        except ValueError as error:
            self._spans_invalid.inc()
            raise error
        try:
            self._tracing_spans_buffer.put(line_data)
        except queue.Full as error:
            self._spans_dropped.inc()
            raise error
        if span_logs:
            try:
                line_data = utils.span_log_to_line_data(
                    trace_id, span_id, span_logs)
                self._span_logs_valid.inc()
            except ValueError as error:
                self._span_logs_invalid.inc()
                raise error
            try:
                self._spans_log_buffer.put(line_data)
            except queue.Full as error:
                self._span_logs_dropped.inc()
                raise error

    def send_span_now(self, spans):
        """
        Send a list of spans immediately.

        Have to construct the data manually by calling
        common.utils.tracing_span_to_line_data()

        @param spans: List of string spans data
        @type spans: list[str]
        """
        self._batch_report(spans, self.WAVEFRONT_TRACING_SPAN_FORMAT, 'spans',
                           self._spans_report_errors)

    def send_span_log_now(self, span_logs):
        """
        Send a list of spans logs immediately.

        Have to construct the data manually by calling
        common.utils.span_log_to_line_data()

        @param span_logs: List of string span logs data
        @type span_logs: list[str]
        """
        self._batch_report(span_logs, self.WAVEFRONT_SPAN_LOG_FORMAT,
                           'span_logs', self._span_logs_report_errors)

    def send_event(self, name, start_time, end_time, source, tags,
                   annotations):
        """Send Event Data via direct ingestion client.

        Wavefront Event Data format
        {"name": <Event Name>, "annotations": <Annotations>,
         "hosts": <Host Name>,"startTime": <Start Time>,
          "endTime": <End Time>, "tags": <Tags>}
        Example: {"name": event_via_direct_ingestion, "annotations": {
        "severity": "severe", "type": "backup", "details": "broker backup"},
         "hosts": ["localhost"], "startTime": 1590678089,
         "endTime": 1590679089, "tags": ["env:", "test"]}

        @param name: Event Name
        @type name: str
        @param start_time: Event Start Time
        @type start_time: long
        @param end_time: Event End Time
        @type end_time: long
        @param source: Source
        @type source: str
        @param tags: Tags
        @type tags: list[str]
        @param annotations: Annotations
        @type annotations: dict
        """
        try:
            line_data = utils.event_to_json(
                name, start_time, end_time, source, tags, annotations,
                self._default_source)
            self._events_valid.inc()
        except ValueError as error:
            self._events_invalid.inc()
            raise error
        try:
            self._events_buffer.put(line_data)
        except queue.Full as error:
            self._events_dropped.inc()
            raise error

    def send_event_now(self, events):
        """Send a list of events immediately.

        Have to construct the data manually by calling
        common.utils.event_to_json()

        @param events: List of string events data
        @type events: list[str]
        """
        self._batch_report(events, self.WAVEFRONT_EVENT_FORMAT, 'events',
                           self._events_report_errors)

    def get_failure_count(self):
        """Get failure count for one connection."""
        return (self._points_report_errors.count() +
                self._histograms_report_errors.count() +
                self._spans_report_errors.count() +
                self._span_logs_report_errors.count() +
                self._events_report_errors.count())


def remaining_capacity_getter(buf):
    """Get remaining capacity of given queue.

    @param buf: Input Buffer Queue.
    @type buf: queue.Queue
    @return: Remaining capacity of the queue.
    @rtype: int
    """
    return lambda: buf.maxsize - buf.qsize()
