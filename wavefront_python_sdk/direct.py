from __future__ import absolute_import, division, print_function

from wavefront_python_sdk.common.connection_handler import ConnectionHandler
from wavefront_python_sdk.common.utils import metric_to_line_data, \
    histogram_to_line_data, tracing_span_to_line_data, gzip_compress, chunks

import requests
from threading import Timer

try:
    import Queue as queue
except ImportError:
    import queue


class WavefrontDirectClient(ConnectionHandler):
    WAVEFRONT_METRIC_FORMAT = 'wavefront'
    WAVEFRONT_HISTOGRAM_FORMAT = 'histogram'
    WAVEFRONT_TRACING_SPAN_FORMAT = 'trace'

    def __init__(self, server, token, max_queue_size=50000, batch_size=10000, flush_interval_seconds=1):
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
        self._flush()

    def _report(self, points, data_format):
        try:
            params = {'f': data_format}
            compressed_data = gzip_compress(points.encode())
            r = requests.post(self.server + '/report', params=params, headers=self._headers, data=compressed_data)
            r.raise_for_status()
        except Exception as e:
            self.increment_failure_count()
            raise e

    def _batch_report(self, batch_line_data, data_format):
        chunk_data = list(chunks(batch_line_data, self._batch_size))
        for batch in chunk_data:
            self._report('\n'.join('{0}'.format(line) for line in batch) + "\n", data_format)

    def _internal_flush(self, data_buffer, data_format):
        data = []
        size = data_buffer.qsize()
        while size > 0 and not data_buffer.empty():
            data.append(data_buffer.get())
            size -= 1
        self._batch_report(data, data_format)

    def _flush(self):
        self.flush_now()
        # Flush every 5 secs
        Timer(5, self._flush).start()

    def flush_now(self):
        self._internal_flush(self._metrics_buffer, self.WAVEFRONT_METRIC_FORMAT)
        self._internal_flush(self._histograms_buffer, self.WAVEFRONT_HISTOGRAM_FORMAT)
        self._internal_flush(self._tracing_spans_buffer, self.WAVEFRONT_TRACING_SPAN_FORMAT)

    def send_metric(self, name, value, timestamp, source, tags):
        line_data = metric_to_line_data(name, value, timestamp, source, tags, self._default_source)
        self._metrics_buffer.put(line_data)

    def send_metric_now(self, lines):
        self._batch_report(lines, self.WAVEFRONT_METRIC_FORMAT)

    def send_distribution(self, name, centroids, histogram_granularities, timestamp, source, tags):
        line_data = histogram_to_line_data(name, centroids, histogram_granularities, timestamp, source, tags,
                                           self._default_source)
        self._histograms_buffer.put(line_data)

    def send_distribution_now(self, lines):
        self._batch_report(lines, self.WAVEFRONT_HISTOGRAM_FORMAT)

    def send_span(self, name, start_millis, duration_millis, source, trace_id, span_id,
                  parents, follows_from, tags, span_logs):
        line_data = tracing_span_to_line_data(name, start_millis, duration_millis, source, trace_id, span_id,
                                              parents, follows_from, tags, span_logs, self._default_source)
        self._tracing_spans_buffer.put(line_data)

    def send_span_now(self, lines):
        self._batch_report(lines, self.WAVEFRONT_TRACING_SPAN_FORMAT)
