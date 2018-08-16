from wavefront_python_sdk.proxy.wavefront_proxy_client import WavefrontProxyClient
from wavefront_python_sdk.direct_ingestion.wavefront_direct_ingestion_client import WavefrontDirectIngestionClient
from wavefront_python_sdk.entities.histogram import HistogramGranularity

import sys
import time
from uuid import UUID


def send_metrics_via_proxy(proxy_client):
    proxy_client.send_metric("python.proxy.new york.power.usage", 42422.0, None, "localhost", None)


def send_histogram_via_proxy(proxy_client):
    proxy_client.send_distribution("python.proxy.request.latency", [(30, 20), (5.1, 10)],
                                   {HistogramGranularity(HistogramGranularity.DAY),
                                    HistogramGranularity(HistogramGranularity.HOUR),
                                    HistogramGranularity(HistogramGranularity.MINUTE)},
                                   None, "appServer1", {"region": "us-west"})


def send_tracing_span_via_proxy(proxy_client):
    proxy_client.send_span("getAllUsersFromPythonProxy", 1533529977, 343500, "localhost",
                           UUID("7b3bf470-9456-11e8-9eb6-529269fb1459"),
                           UUID("0313bafe-9457-11e8-9eb6-529269fb1459"),
                           [UUID("2f64e538-9457-11e8-9eb6-529269fb1459")], None,
                           [("application", "Wavefront"), ("http.method", "GET")], None)


def send_metrics_via_direct_ingestion(direct_ingestion_client):
    direct_ingestion_client.send_metric("python.direct.new york.power.usage", 42422.0, None, "localhost", None)


def send_histogram_via_direct_ingestion(direct_ingestion_client):
    direct_ingestion_client.send_distribution("python.direct.request.latency", [(30, 20), (5.1, 10)],
                                              {HistogramGranularity(HistogramGranularity.DAY),
                                               HistogramGranularity(HistogramGranularity.HOUR),
                                               HistogramGranularity(HistogramGranularity.MINUTE)},
                                              None, "appServer1", {"region": "us-west"})


def send_tracing_span_via_direct_ingestion(direct_ingestion_client):
    direct_ingestion_client.send_span("getAllUsersFromPythonDirect", 1533529977, 343500, "localhost",
                                      UUID("7b3bf470-9456-11e8-9eb6-529269fb1459"),
                                      UUID("0313bafe-9457-11e8-9eb6-529269fb1459"),
                                      [UUID("2f64e538-9457-11e8-9eb6-529269fb1459")], None,
                                      [("application", "Wavefront"), ("http.method", "GET")], None)


if __name__ == "__main__":
    wavefront_server = sys.argv[1]
    token = sys.argv[2]
    proxy_host = None if len(sys.argv) <= 3 else sys.argv[3]
    metrics_port = None if len(sys.argv) <= 4 else sys.argv[4]
    distribution_port = None if len(sys.argv) <= 5 else sys.argv[5]
    tracing_port = None if len(sys.argv) <= 6 else sys.argv[6]
    print(wavefront_server, token, proxy_host, metrics_port, distribution_port, tracing_port)

    proxy_client_builder = WavefrontProxyClient.Builder(proxy_host, metrics_port, distribution_port, tracing_port)
    wavefront_proxy_client = proxy_client_builder.build()

    direct_ingestion_client_builder = WavefrontDirectIngestionClient.Builder(wavefront_server, token)
    wavefront_direct_ingestion_client = direct_ingestion_client_builder.build()

    while True:
        send_metrics_via_proxy(wavefront_proxy_client)
        send_histogram_via_proxy(wavefront_proxy_client)
        send_tracing_span_via_proxy(wavefront_proxy_client)

        send_metrics_via_direct_ingestion(wavefront_direct_ingestion_client)
        send_histogram_via_direct_ingestion(wavefront_direct_ingestion_client)
        send_tracing_span_via_direct_ingestion(wavefront_direct_ingestion_client)

        time.sleep(1)
