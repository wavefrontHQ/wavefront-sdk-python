from __future__ import absolute_import, division, print_function

from socket import gethostname
from wavefront_python_sdk.common.proxy_connection_handler import ProxyConnectionHandler
from wavefront_python_sdk.common.utils import metric_to_line_data, \
    histogram_to_line_data, tracing_span_to_line_data


class WavefrontProxyClient:

    def __init__(self, proxy_host, metrics_port=2878, distribution_port=40000, tracing_port=30000):
        self.proxy_host = proxy_host
        self.metrics_port = metrics_port
        self.distribution_port = distribution_port
        self.tracing_port = tracing_port
        self._metrics_proxy_connection_handler = None if metrics_port is None \
            else ProxyConnectionHandler(proxy_host, metrics_port)
        self._histogram_proxy_connection_handler = None if distribution_port is None \
            else ProxyConnectionHandler(proxy_host, distribution_port)
        self._tracing_proxy_connection_handler = None if tracing_port is None \
            else ProxyConnectionHandler(proxy_host, tracing_port)
        self._default_source = gethostname()

    def send_metric(self, name, value, timestamp, source, tags):
        try:
            line_data = metric_to_line_data(name, value, timestamp, source, tags, self._default_source)
            self._metrics_proxy_connection_handler.send_data(line_data)
        except Exception as e:
            self._metrics_proxy_connection_handler.increment_failure_count()
            raise e

    def send_metric_now(self, lines):
        for line in lines:
            try:
                self._metrics_proxy_connection_handler.send_data(line)
            except Exception as e:
                self._metrics_proxy_connection_handler.increment_failure_count()
                raise e

    def send_distribution(self, name, centroids, histogram_granularities, timestamp, source, tags):
        try:
            line_data = histogram_to_line_data(name, centroids, histogram_granularities, timestamp, source, tags,
                                               self._default_source)
            self._histogram_proxy_connection_handler.send_data(line_data)
        except Exception as e:
            self._histogram_proxy_connection_handler.increment_failure_count()
            raise e

    def send_distribution_now(self, lines):
        for line in lines:
            try:
                self._histogram_proxy_connection_handler.send_data(line)
            except Exception as e:
                self._histogram_proxy_connection_handler.increment_failure_count()
                raise e

    def send_span(self, name, start_millis, duration_millis, source, trace_id, span_id,
                  parents, follows_from, tags, span_logs):
        try:
            line_data = tracing_span_to_line_data(name, start_millis, duration_millis, source, trace_id, span_id,
                                                  parents, follows_from, tags, span_logs, self._default_source)
            self._tracing_proxy_connection_handler.send_data(line_data)
        except Exception as e:
            self._tracing_proxy_connection_handler.increment_failure_count()
            raise e

    def send_span_now(self, lines):
        for line in lines:
            try:
                self._tracing_proxy_connection_handler.send_data(line)
            except Exception as e:
                self._tracing_proxy_connection_handler.increment_failure_count()
                raise e
