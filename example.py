# -*- coding: utf-8 -*-
"""Wavefront SDK Usage Example."""

import sys
import time
import uuid

from wavefront_sdk.direct import WavefrontDirectClient
from wavefront_sdk.entities.histogram import histogram_granularity
from wavefront_sdk.proxy import WavefrontProxyClient


def send_metrics_via_proxy(proxy_client):
    """Send a distribution using proxy client."""
    proxy_client.send_metric(
        'python' + str(sys.version_info[0]) + '.proxy.new york.power.usage',
        42422.0, None, 'localhost', None)


def send_delta_counter_via_proxy(proxy_client):
    """Send a delta counter using proxy client."""
    proxy_client.send_delta_counter(
        'python' + str(sys.version_info[0]) + '.delta.proxy.counter',
        1.0, 'localhost', None)


def send_histogram_via_proxy(proxy_client):
    """Send a histogram using proxy client."""
    proxy_client.send_distribution(
        'python' + str(sys.version_info[0]) + '.proxy.request.latency',
        [(30, 20), (5.1, 10)], {histogram_granularity.DAY,
                                histogram_granularity.HOUR,
                                histogram_granularity.MINUTE},
        None, 'appServer1', {'region': 'us-west'})


def send_tracing_span_via_proxy(proxy_client):
    """Send a tracing span using proxy client."""
    proxy_client.send_span(
        'getAllUsersFromPythonProxy', 1533529977, 343500, 'localhost',
        uuid.UUID('7b3bf470-9456-11e8-9eb6-529269fb1459'),
        uuid.UUID('0313bafe-9457-11e8-9eb6-529269fb1459'),
        [uuid.UUID('2f64e538-9457-11e8-9eb6-529269fb1459')], None,
        [('application', 'Wavefront'),
         ('http.method', 'GET')], None)


def send_metrics_via_direct_ingestion(direct_ingestion_client):
    """Send a metric through direct ingestion."""
    direct_ingestion_client.send_metric(
        'python' + str(sys.version_info[0]) + '.direct.new york.power.usage',
        42422.0, None, 'localhost', None)


def send_delta_counter_via_direct_ingestion(direct_ingestion_client):
    """Send a delta counter through direct ingestion."""
    direct_ingestion_client.send_delta_counter(
        'python' + str(sys.version_info[0]) + '.delta.direct.counter',
        1.0, 'localhost', None)


def send_histogram_via_direct_ingestion(direct_ingestion_client):
    """Send a histogram through direct ingestion."""
    direct_ingestion_client.send_distribution(
        'python' + str(sys.version_info[0]) + '.direct.request.latency',
        [(30, 20), (5.1, 10)], {histogram_granularity.DAY,
                                histogram_granularity.HOUR,
                                histogram_granularity.MINUTE},
        None, 'appServer1',
        {'region': 'us-west'})


def send_tracing_span_via_direct_ingestion(direct_ingestion_client):
    """Send a tracing span through direct ingestion."""
    direct_ingestion_client.send_span(
        'getAllUsersFromPythonDirect', 1533529977, 343500, 'localhost',
        uuid.UUID('7b3bf470-9456-11e8-9eb6-529269fb1459'),
        uuid.UUID('0313bafe-9457-11e8-9eb6-529269fb1459'),
        [uuid.UUID('2f64e538-9457-11e8-9eb6-529269fb1459')],
        None, [('application', 'Wavefront'), ('http.method', 'GET')], None)


def send_event_via_proxy(wavefront_proxy_client):
    """Send an event via proxy."""
    wavefront_proxy_client.send_event(
        'event_via_proxy',
        1590650592,
        1590650692,
        'localhost',
        ["env:", "test"],
        {"severity": "info",
         "type": "backup",
         "details": "broker backup"})


def send_event_via_direct_ingestion(direct_ingestion_client):
    """Send an event through direct ingestion."""
    direct_ingestion_client.send_event(
        'event_via_direct',
        1590730937,
        1590731037,
        'localhost',
        ["env:", "test"],
        {"severity": "severe",
         "type": "backup",
         "details": "broker backup"})


if __name__ == '__main__':
    wavefront_server = sys.argv[1]
    token = sys.argv[2]
    proxy_host = None if len(sys.argv) <= 3 else sys.argv[3]
    metrics_port = None if len(sys.argv) <= 4 else sys.argv[4]
    distribution_port = None if len(sys.argv) <= 5 else sys.argv[5]
    tracing_port = None if len(sys.argv) <= 6 else sys.argv[6]
    event_port = None if len(sys.argv) <= 7 else sys.argv[7]

    wavefront_proxy_client = WavefrontProxyClient(
        host=proxy_host,
        metrics_port=metrics_port,
        distribution_port=distribution_port,
        tracing_port=tracing_port,
        event_port=event_port)

    wavefront_direct_client = WavefrontDirectClient(wavefront_server, token)

    try:
        while True:
            send_metrics_via_proxy(wavefront_proxy_client)
            send_histogram_via_proxy(wavefront_proxy_client)
            send_tracing_span_via_proxy(wavefront_proxy_client)
            send_delta_counter_via_proxy(wavefront_proxy_client)
            send_event_via_proxy(wavefront_proxy_client)

            send_metrics_via_direct_ingestion(wavefront_direct_client)
            send_histogram_via_direct_ingestion(wavefront_direct_client)
            send_tracing_span_via_direct_ingestion(wavefront_direct_client)
            send_delta_counter_via_direct_ingestion(wavefront_direct_client)
            send_event_via_direct_ingestion(wavefront_direct_client)

            time.sleep(1)
    finally:
        wavefront_proxy_client.close()
        wavefront_direct_client.close()
