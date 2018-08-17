from __future__ import absolute_import, division, print_function

from wavefront_python_sdk.common.connection_handler import IConnectionHandler
from wavefront_python_sdk.common.utils import metric_to_line_data, \
    histogram_to_line_data, tracing_span_to_line_data

import sys
import requests
from threading import Timer
from queue import Queue


class WavefrontDirectIngestionClient(IConnectionHandler):
    WAVEFRONT_METRIC_FORMAT = 'wavefront'
    WAVEFRONT_HISTOGRAM_FORMAT = 'histogram'
    WAVEFRONT_TRACING_SPAN_FORMAT = 'trace'

    def __init__(self, server, token, max_queue_size=50000, batch_size=10000, flush_interval_seconds=1):
        IConnectionHandler.__init__(self)
        self.server = server
        self._token = token
        self._max_queue_size = max_queue_size
        self._batch_size = batch_size
        self._flush_interval_seconds = flush_interval_seconds
        self._default_source = "wavefrontDirectSender"
        self._metrics_buffer = Queue(max_queue_size)
        self._histograms_buffer = Queue(max_queue_size)
        self._tracing_spans_buffer = Queue(max_queue_size)
        self._headers = {'Content-Type': 'text/plain', 'Authorization': 'Bearer ' + token}
        self._flush()

    def _report(self, points, data_format):
        try:
            params = {'f': data_format}
            r = requests.post(self.server + '/report', params=params, headers=self._headers, data=points)
            r.raise_for_status()
        except Exception as e:
            self.increment_failure_count()
            print(e, file=sys.stderr)

    def _internal_flush(self, data_buffer, data_format):
        buffer_len = data_buffer.qsize()
        while buffer_len > 0 and not data_buffer.empty():
            line_data = data_buffer.get()
            self._report(line_data, data_format)
            buffer_len -= 1

    def _flush(self):
        self.flush_now()
        print("flushing")
        # Flush every 5 secs
        Timer(5, self._flush).start()

    def flush_now(self):
        self._internal_flush(self._metrics_buffer, self.WAVEFRONT_METRIC_FORMAT)
        self._internal_flush(self._histograms_buffer, self.WAVEFRONT_HISTOGRAM_FORMAT)
        self._internal_flush(self._tracing_spans_buffer, self.WAVEFRONT_TRACING_SPAN_FORMAT)

    def send_metric(self, name, value, timestamp, source, tags):
        try:
            line_data = metric_to_line_data(name, value, timestamp, source, tags, self._default_source)
            print(line_data)
            self._metrics_buffer.put(line_data)
        except Exception as e:
            print("error sending metric data via direct ingestion:", e, file=sys.stderr)

    def send_metric_now(self, lines):
        try:
            if len(lines) > self._builder.max_queue_size:
                raise Exception("Data amount exceed max queue size")
            self._internal_flush(self._metrics_buffer, self.WAVEFRONT_METRIC_FORMAT)
            _ = [self._metrics_buffer.put(line) for line in lines]
            self._internal_flush(self._metrics_buffer, self.WAVEFRONT_METRIC_FORMAT)
        except Exception as e:
            print("error sending metric data now via direct ingestion:", e, file=sys.stderr)

    def send_distribution(self, name, centroids, histogram_granularities, timestamp, source, tags):
        try:
            line_data = histogram_to_line_data(name, centroids, histogram_granularities, timestamp, source, tags,
                                               self._default_source)
            print(line_data)
            self._histograms_buffer.put(line_data)
        except Exception as e:
            print("error sending histogram data via direct ingestion:", e, file=sys.stderr)
            pass

    def send_distribution_now(self, lines):
        try:
            if len(lines) > self._builder.max_queue_size:
                raise Exception("Data amount exceed max queue size")
            self._internal_flush(self._histograms_buffer, self.WAVEFRONT_HISTOGRAM_FORMAT)
            _ = [self._histograms_buffer.put(line) for line in lines]
            self._internal_flush(self._histograms_buffer, self.WAVEFRONT_HISTOGRAM_FORMAT)
        except Exception as e:
            print("error sending histogram data now via direct ingestion:", e, file=sys.stderr)

    def send_span(self, name, start_millis, duration_millis, source, trace_id, span_id,
                  parents, follows_from, tags, span_logs):
        try:
            line_data = tracing_span_to_line_data(name, start_millis, duration_millis, source, trace_id, span_id,
                                                  parents, follows_from, tags, span_logs, self._default_source)
            print(line_data)
            self._tracing_spans_buffer.put(line_data)
        except Exception as e:
            print("error sending span tracing data via direct ingestion:", e, file=sys.stderr)

    def send_span_now(self, lines):
        try:
            if len(lines) > self._builder.max_queue_size:
                raise Exception("Data amount exceed max queue size")
            self._internal_flush(self._tracing_spans_buffer, self.WAVEFRONT_TRACING_SPAN_FORMAT)
            _ = [self._tracing_spans_buffer.put(line) for line in lines]
            self._internal_flush(self._tracing_spans_buffer, self.WAVEFRONT_TRACING_SPAN_FORMAT)
        except Exception as e:
            print("error sending span tracing data now via direct ingestion:", e, file=sys.stderr)
