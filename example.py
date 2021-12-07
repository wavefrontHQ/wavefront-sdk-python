"""Wavefront SDK Usage Example."""

import sys
import time
import uuid

from wavefront_sdk.client_factory import WavefrontClientFactory
from wavefront_sdk.entities.histogram import histogram_granularity


def send_metrics(wavefront_client):
    """Send a metric."""
    wavefront_client.send_metric(
        'python.proxy.new york.power.usage',
        42422.0, None, 'localhost', None)


def send_delta_counter(wavefront_client):
    """Send a delta counter."""
    wavefront_client.send_delta_counter(
        'python.delta.proxy.counter',
        1.0, 'localhost', None)


def send_histogram(wavefront_client):
    """Send a histogram."""
    wavefront_client.send_distribution(
        'python.proxy.request.latency',
        [(30, 20), (5.1, 10)], {histogram_granularity.DAY,
                                histogram_granularity.HOUR,
                                histogram_granularity.MINUTE},
        None, 'appServer1', {'region': 'us-west'})


def send_tracing_span(wavefront_client):
    """Send a tracing span."""
    wavefront_client.send_span(
        'getAllUsersFromPythonProxy', 1533529977, 343500, 'localhost',
        uuid.UUID('7b3bf470-9456-11e8-9eb6-529269fb1459'),
        uuid.UUID('0313bafe-9457-11e8-9eb6-529269fb1459'),
        [uuid.UUID('2f64e538-9457-11e8-9eb6-529269fb1459')], None,
        [('application', 'Wavefront'),
         ('http.method', 'GET')], None)


def send_event(wavefront_client):
    """Send an event."""
    wavefront_client.send_event(
        'event_via_proxy',
        1590650592,
        1590650692,
        "localhost",
        ["env:", "test"],
        {"severity": "info",
         "type": "backup",
         "details": "broker backup"})


if __name__ == '__main__':
    # Either "proxy://our.proxy.lb.com:2878"
    # Or "https://someToken@DOMAIN.wavefront.com"
    wavefront_proxy_url = sys.argv[1]

    client_factory = WavefrontClientFactory()
    client_factory.add_client(wavefront_proxy_url)
    wavefront_client = client_factory.get_client()

    try:
        while True:
            send_metrics(wavefront_client)
            send_histogram(wavefront_client)
            send_tracing_span(wavefront_client)
            send_delta_counter(wavefront_client)
            send_event(wavefront_client)

            time.sleep(15)
    finally:
        wavefront_client.close()
