# -*- coding: utf-8 -*-

"""
Wavefront Direct Ingestion Client.

@author Hao Song (songhao@vmware.com)
"""

from __future__ import absolute_import

from threading import Timer, Lock
import logging
import requests

try:
    import Queue as queue
except ImportError:
    import queue

from wavefront_sdk.common.connection_handler import ConnectionHandler
from wavefront_sdk.common.utils import metric_to_line_data, \
    histogram_to_line_data, tracing_span_to_line_data, gzip_compress, chunks
from wavefront_sdk.entities import WavefrontTracingSpanSender, \
    WavefrontMetricSender, WavefrontHistogramSender
LOGGER = logging.getLogger('wavefront_sdk.WavefrontDirectClient')


# pylint: disable=too-many-instance-attributes

class WavefrontDirectClient(ConnectionHandler,
                            WavefrontMetricSender,
                            WavefrontHistogramSender,
                            WavefrontTracingSpanSender):
    """
    Wavefront direct ingestion client.

    Sends data directly to Wavefront cluster via the direct ingestion API.
    """

    WAVEFRONT_METRIC_FORMAT = 'wavefront'
    WAVEFRONT_HISTOGRAM_FORMAT = 'histogram'
    WAVEFRONT_TRACING_SPAN_FORMAT = 'trace'

    # pylint: disable=too-many-arguments
    def __init__(self, server, token, max_queue_size=50000, batch_size=10000,
                 flush_interval_seconds=5):
        """
        Construct Direct Client.

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
        ConnectionHandler.__init__(self)
        self.server = server
        self._token = token
        self._max_queue_size = max_queue_size
        self._batch_size = batch_size
        self._flush_interval_seconds = flush_interval_seconds
        self._default_source = "wavefrontDirectSender"
        self._metrics_buffer = queue.Queue(max_queue_size)
        self._histograms_buffer = queue.Queue(max_queue_size)
        self._tracing_spans_buffer = queue.Queue(max_queue_size)
        self._headers = {'Content-Type': 'application/octet-stream',
                         'Content-Encoding': 'gzip',
                         'Authorization': 'Bearer ' + token}
        self._closed = False
        self._schedule_lock = Lock()
        self._timer = None
        self._schedule_timer()

    def _report(self, points, data_format):
        r"""
        One api call sending one given string data.

        @param points: List of data in string format, concat by '\n'
        @type points: str
        @param data_format: Type of data to be sent
        @type data_format: str
        """
        try:
            params = {'f': data_format}
            compressed_data = gzip_compress(points.encode('utf-8'))
            response = requests.post(self.server + '/report', params=params,
                                     headers=self._headers,
                                     data=compressed_data)
            response.raise_for_status()
        except Exception as error:
            self.increment_failure_count()
            raise error

    def _batch_report(self, batch_line_data, data_format):
        """
        One api call sending one given list of data.

        @param batch_line_data: List of data to be sent
        @type batch_line_data: list
        @param data_format: Type of data to be sent
        @type data_format: str
        """
        # Split data into chunks, each with the size of given batch_size
        for batch in chunks(batch_line_data, self._batch_size):
            # report once per batch
            try:
                self._report('\n'.join(batch) + '\n', data_format)
            except Exception as error:
                LOGGER.error("Failed to report %s data points to wavefront %s",
                             data_format, error)

    def _internal_flush(self, data_buffer, data_format):
        """
        Get all data from one data buffer to a list, and report that list.

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
        self._batch_report(data, data_format)

    def _schedule_timer(self):
        # Flush every 5 secs by default
        if not self._closed:
            self._timer = Timer(self._flush_interval_seconds, self._flush)
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
                             self.WAVEFRONT_METRIC_FORMAT)
        self._internal_flush(self._histograms_buffer,
                             self.WAVEFRONT_HISTOGRAM_FORMAT)
        self._internal_flush(self._tracing_spans_buffer,
                             self.WAVEFRONT_TRACING_SPAN_FORMAT)

    def close(self):
        """Flush all buffer before close the client."""
        self.flush_now()
        with self._schedule_lock:
            self._closed = True
            if self._timer is not None:
                self._timer.cancel()

    # pylint: disable=too-many-arguments

    def send_metric(self, name, value, timestamp, source, tags):
        """
        Send Metric Data via proxy.

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
        line_data = metric_to_line_data(name, value, timestamp, source, tags,
                                        self._default_source)
        self._metrics_buffer.put(line_data)

    def send_metric_now(self, metrics):
        """
        Send a list of metrics immediately.

        Have to construct the data manually by calling
        common.utils.metric_to_line_data()

        @param metrics: List of string spans data
        @type metrics: list[str]
        """
        self._batch_report(metrics, self.WAVEFRONT_METRIC_FORMAT)

    # pylint: disable=too-many-arguments

    def send_distribution(self, name, centroids, histogram_granularities,
                          timestamp, source, tags):
        """
        Send Distribution Data via proxy.

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
        line_data = histogram_to_line_data(
            name, centroids, histogram_granularities, timestamp, source, tags,
            self._default_source)
        self._histograms_buffer.put(line_data)

    def send_distribution_now(self, distributions):
        """
        Send a list of distribution immediately.

        Have to construct the data manually by calling
        common.utils.metric_to_line_data()

        @param distributions: List of string spans data
        @type distributions: list[str]
        """
        self._batch_report(distributions, self.WAVEFRONT_HISTOGRAM_FORMAT)

    # pylint: disable=too-many-arguments

    def send_span(self, name, start_millis, duration_millis, source, trace_id,
                  span_id, parents, follows_from, tags, span_logs):
        """
        Send span data via proxy.

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
        line_data = tracing_span_to_line_data(
            name, start_millis, duration_millis, source, trace_id, span_id,
            parents, follows_from, tags, span_logs, self._default_source)
        self._tracing_spans_buffer.put(line_data)

    def send_span_now(self, spans):
        """
        Send a list of spans immediately.

        Have to construct the data manually by calling
        common.utils.metric_to_line_data()

        @param spans: List of string spans data
        @type spans: list[str]
        """
        self._batch_report(spans, self.WAVEFRONT_TRACING_SPAN_FORMAT)
