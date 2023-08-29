#! /usr/bin/env python3
"""Wavefront SDK Usage Example."""

import platform
import logging
import sys
import time
import uuid

from wavefront_sdk.client_factory import WavefrontClientFactory
from wavefront_sdk.entities.histogram import histogram_granularity

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG, datefmt='%r',
                    format='%(asctime)-12s %(levelname)-6s [%(threadName)s] (%(name)s) "%(message)s"')


def send_metrics(wavefront_client):
    """Send a metric."""
    wavefront_client.send_metric(
        'python.sdk.example.new_york.power.usage',  # metric name (str)
        time.time() % 3600,  # metric value (float)
        None,  # metric timestamp (int)
        platform.node(),  # metric source (str)
        {})  # metric tags (dict)


def send_delta_counter(wavefront_client):
    """Send a delta counter."""
    wavefront_client.send_delta_counter(
        'python.sdk.example.delta.proxy.counter',  # counter name (str)
        1.0,  # counter value (float)
        platform.node(),  # source name (str)
        None)  # counter tags (dict)


def send_histogram(wavefront_client):
    """Send a histogram."""
    wavefront_client.send_distribution(
        'python.sdk.example.request.latency',  # histogram name (str)
        [(30, 20), (5.1, 10)],  # histogram centroids (list)
        {histogram_granularity.DAY,
         histogram_granularity.HOUR,
         histogram_granularity.MINUTE},  # granularities (set)
        None,  # histogram timestamp (int)
        platform.node(),  # histogram source (str)
        {'region': 'us-west'})  # histogram tags (dict)


def send_tracing_span(wavefront_client):
    """Send a tracing span."""
    wavefront_client.send_span(
        'getAllUsersFromPythonProxy',  # span name (str)
        1533529977,  # start milliseconds (int)
        343500,  # duration milliseconds (int)
        platform.node(),  # span source (str)
        uuid.UUID('7b3bf470-9456-11e8-9eb6-529269fb1459'),  # trace ID (UUID)
        uuid.UUID('0313bafe-9457-11e8-9eb6-529269fb1459'),  # span ID (UUID)
        [
            uuid.UUID('2f64e538-9457-11e8-9eb6-529269fb1459')
        ],  # parents (list[UUID])
        None,  # follows from (list[UUID])
        [
            ('application', 'Wavefront'),
            ('http.method', 'GET')
        ],  # span tags (list[tuple])
        None  # span log
        )


def send_event(wavefront_client):
    """Send an event."""
    wavefront_client.send_event(
        'python_sdk_example_event',  # event name (str)
        1590650592,  # event start milliseconds (int)
        1590650692,  # event end milliseconds (int)
        platform.node(),  # event source (str)
        ["env:", "test"],  # event tags (list[str] or tuple[str])
        {
            "severity": "info",
            "type": "backup",
            "details": "broker backup"
            }  # event annotations (dict)
        )


def main():
    """Send sample metrics in a loop."""
    wavefront_proxy_url = sys.argv[1]
    csp_base_url, csp_api_token, csp_app_id, csp_app_secret, csp_org_id = None, None, None, None, None

    if len(sys.argv) == 4:
        csp_base_url = sys.argv[2]
        csp_api_token = sys.argv[3]
    elif len(sys.argv) > 4:
        csp_base_url = sys.argv[2]
        csp_app_id = sys.argv[3]
        csp_app_secret = sys.argv[4]
        if len(sys.argv) > 5:
            csp_org_id = sys.argv[5]

    client_factory = WavefrontClientFactory()
    client_factory.add_client(wavefront_proxy_url, csp_base_url=csp_base_url, csp_api_token=csp_api_token,
                              csp_app_id=csp_app_id, csp_app_secret=csp_app_secret, csp_org_id=csp_org_id)
    wfront_client = client_factory.get_client()

    try:
        while True:
            send_metrics(wfront_client)
            send_histogram(wfront_client)
            send_tracing_span(wfront_client)
            send_delta_counter(wfront_client)
            send_event(wfront_client)

            time.sleep(15)
    finally:
        wfront_client.close()


if __name__ == '__main__':
    # Either "proxy://our.proxy.lb.com:2878"
    #     Or "https://someToken@DOMAIN.wavefront.com"
    #     should be passed as an input in sys.argv[1]
    # Or "https://DOMAIN.wavefront.com" "https://CSP_ENDPOINT.cloud.vmware.com" "CSP_API_TOKEN"
    #     should be passed as an input in sys.argv[1], sys.argv[2], and sys.argv[3]
    # Or "https://DOMAIN.wavefront.com" "https://CSP_ENDPOINT.cloud.vmware.com" "CSP_APP_ID" "CSP_APP_SECRET"
    #     should be passed as an input in sys.argv[1], sys.argv[2], sys.argv[3], and sys.argv[4]
    # Or "https://DOMAIN.wavefront.com" "https://CSP_ENDPOINT.cloud.vmware.com" "CSP_APP_ID" "CSP_APP_SECRET" "ORG_ID"
    #     should be passed as an input in sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], and sys.argv[5]
    main()
