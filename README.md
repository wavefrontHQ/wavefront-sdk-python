# VMware Aria Operations™ for Applications Python SDK

[![Build Status](https://github.com/wavefrontHQ/wavefront-sdk-python/actions/workflows/main.yml/badge.svg)](https://github.com/wavefrontHQ/wavefront-sdk-python/actions)
[![image](https://img.shields.io/pypi/v/wavefront-sdk-python.svg)](https://pypi.org/project/wavefront-sdk-python/)
[![image](https://img.shields.io/pypi/l/wavefront-sdk-python.svg)](https://pypi.org/project/wavefront-sdk-python/)
[![image](https://img.shields.io/pypi/pyversions/wavefront-sdk-python.svg)](https://pypi.org/project/wavefront-sdk-python/)
![PyPI - Downloads](https://img.shields.io/pypi/dm/wavefront-sdk-python)

## Table of Content

* [Overview](#overview)
* [Prerequisites](#prerequisites)
* [Set Up a Sender](#set-up-a-sender)
* [Send Data](#send-data)
* [Close the Sender](#close-the-sender)
* [License](#license)
* [Contribute](#contribute)

## Overview

VMware Aria Operations for Applications (formerly known as Tanzu Observability by Wavefront) Python SDK lets you send raw data from your Python application to Operations for Applications using a wavefront_sender interface. The data is then stored as metrics, histograms, and trace data. This SDK is also referred to as the Wavefront Sender SDK for Python.

Although this library is mostly used by the other Operations for Applications Python SDKs to send data to Operations for Applications, you can also use this SDK directly. For example, you can send data directly from a data store or CSV file to Operations for Applications.

Note: We're in the process of updating the product name to Operations for Applications, but in many places we still refer to it as Wavefront.

## Prerequisites

* Python versions 3.8 - 3.11 are supported.
* Install `wavefront-sdk-python`:

    ```python
    pip install wavefront-sdk-python
    ```

## Set Up a Sender

You can send metrics, histograms, or trace data from your application to the service using a Wavefront Proxy or direct ingestions.

* Use [**direct ingestion**](https://docs.wavefront.com/direct_ingestion.html) to send the data directly to the service. This is the simplest way for POC environment to get it running quickly.
* Use a [**Wavefront Proxy**](https://docs.wavefront.com/proxies.html), which forwards the data to the service. This is the recommended way for a production environment and large-scale deployment that needs resilience to internet outages, control over data queuing and filtering, and more.

Let's [create a `WavefrontClient`](#create-a-wavefrontclient) to send data to Operations for Applications either through the Wavefront Proxy or directly over HTTP.

> **Deprecated implementations**: *`WavefrontDirectClient` and `WavefrontProxyClient` are deprecated starting with Wavefront proxy version 7.0. We recommend all new applications to use the `WavefrontClient`.*

### Create a WavefrontClient

Use `WavefrontClientFactory` to create a `WavefrontClient` instance, which can send data directly to the service or send data using a Wavefront proxy.

The `WavefrontClientFactory` supports multiple client bindings. If more than one client configuration is specified, you can create a `WavefrontMultiClient` instance, which can send data to multiple services.

#### Initialize the WavefrontClient (Wavefront Proxy/Direct Ingestion)

##### Prerequisites (Wavefront Proxy/Direct Ingestion)

* Sending data by using the Wavefront proxy?
  Before your application can use a `WavefrontClient` you must [install a Wavefront proxy](https://docs.wavefront.com/proxies_installing.html).
* Sending data by using direct ingestion?
  * Verify that you have the Direct Data Ingestion permission. For details, see [Operations for Applications Permissions](https://docs.wavefront.com/users_account_managing.html#examine-groups-roles-and-permissions).
  * The HTTP URL of your cluster. This is the URL you connect to when you log in to the service, typically something like `http://<domain>.wavefront.com`. You can also use HTTP client with Wavefront proxy version 7.0 or later. Example: `http://proxy.acme.corp:2878`.
  * [Obtain the Operations for Applications API token](https://docs.wavefront.com/api_tokens.html#generate-and-manage-the-api-tokens-for-your-user-account).

**Example**: Use a factory class to create a WavefrontClient and send data to Operations for Applications through a Wavefront proxy or using direct ingestion.

```python
from wavefront_sdk.client_factory import WavefrontClientFactory

# Create a sender with:
   # Required Parameter
   #   URL format to send data via proxy: "proxy://<your.proxy.load.balancer.com>:<somePort>"
   #   URL format to send data via direct ingestion: "https://TOKEN@DOMAIN.wavefront.com"
   # Optional Parameter
   #   max queue size (in data points). Default: 50000
   #   batch size (in data points). Default: 10000
   #   flush interval (in seconds). Default: 1 second

client_factory = WavefrontClientFactory()
client_factory.add_client(
    url="<URL for proxy or direct ingestions>",
    max_queue_size=50000,
    batch_size=10000,
    flush_interval_seconds=5)
wavefront_sender = client_factory.get_client()
```

#### Initialize the WavefrontClient with a VMware Cloud Services API Token

##### Prerequisites (VMware Cloud Services API Token)

* The HTTP URL of your cluster. This is the URL you connect to when you log in to the service, typically something like `http://<domain>.wavefront.com`.
* The base HTTP URL of your VMware Cloud Services Console. This is the URL you connect to when you log in to the VMware Cloud Services Console, typically something like `http://console.cloud.vmware.com`.
* Verify that you have access to the VMware Cloud Services Console. For details, see [Operations for Applications Permissions](https://docs.wavefront.com/csp_permissions_overview.html#operations-for-applications-permissions).
* [Generating an API token](https://developer.vmware.com/apis/csp/).

**Example**: Use a factory class to create a WavefrontClient and send data to Operations for Applications via VMware Cloud Services API Token.

```python
from wavefront_sdk.client_factory import WavefrontClientFactory

# Create a sender with:
   # Required Parameter
   #   URL format to send data via direct ingestion: "https://<DOMAIN>.wavefront.com"
   #   URL format to get tokens via VMware Cloud Services authentication: "https://<CSP_ENDPOINT>.cloud.vmware.com"
   #   VMware Cloud Services API Token for VMware Cloud Services authentication: "<CSP_API_TOKEN>"
   # Optional Parameter
   #   max queue size (in data points). Default: 50000
   #   batch size (in data points). Default: 10000
   #   flush interval (in seconds). Default: 1 second

client_factory = WavefrontClientFactory()
client_factory.add_client(
    url="<URL for direct ingestions>",
    csp_base_url='<URL for csp authentication>',
    csp_api_token="<Token for csp api>",
    max_queue_size=50000,
    batch_size=10000,
    flush_interval_seconds=5)
wavefront_sender = client_factory.get_client()
```

#### Initialize the WavefrontClient with a Server to Server OAuth App

##### Prerequisites (Server to Server OAuth App)

* The HTTP URL of your cluster. This is the URL you connect to when you log in to the service, typically something like `http://<domain>.wavefront.com`.
* The base HTTP URL of your VMware Cloud Services Console. This is the URL you connect to when you log in to the VMware Cloud Services Console, typically something like `http://console.cloud.vmware.com`.
* Verify that you have the required permissions for adding and managing OAuth apps in this Organization. For details, see [Organization roles and permissions](https://docs.vmware.com/en/VMware-Cloud-services/services/Using-VMware-Cloud-Services/GUID-C11D3AAC-267C-4F16-A0E3-3EDF286EBE53.html#organization-roles-and-permissions-0).
* [Create a server to server app](https://docs.vmware.com/en/VMware-Cloud-services/services/Using-VMware-Cloud-Services/GUID-327AE12A-85DB-474B-89B2-86651DF91C77.html).

**Example**: Use a factory class to create a WavefrontClient and send data to Operations for Applications by using the server to server OAuth app.

```python
from wavefront_sdk.client_factory import WavefrontClientFactory

# Create a sender with:
   # Required Parameter
   #   URL format to send data via direct ingestion: "https://<DOMAIN>.wavefront.com"
   #   URL format to get tokens via csp authentication: "https://<CSP_ENDPOINT>.cloud.vmware.com"
   #   VMware Cloud services OAuth App ID for csp authentication: "<CSP_APP_ID>"
   #   VMware Cloud services OAuth App secret for csp authentication: "<CSP_APP_SECRET>"
   # Optional Parameter
   #   VMware Cloud services Organization ID for csp authentication. Default: None
   #   max queue size (in data points). Default: 50000
   #   batch size (in data points). Default: 10000
   #   flush interval (in seconds). Default: 1 second

client_factory = WavefrontClientFactory()
client_factory.add_client(
    url="<URL for direct ingestions>",
    csp_base_url='<URL for csp authentication>',
    csp_app_id="<ID for csp oauth app>",
    csp_app_secret="<Secret for csp oauth app>",
    csp_org_id="<ID for csp organization>",
    max_queue_size=50000,
    batch_size=10000,
    flush_interval_seconds=5)
wavefront_sender = client_factory.get_client()
```

#### Add multiple clients to client factory to send data to multiple services

**Example**: Creating a `WavefrontMultiClient` to send data to multiple Operations for Applications services.

```python
from wavefront_sdk.client_factory import WavefrontClientFactory

client_factory = WavefrontClientFactory()
client_factory.add_client("proxy://our.proxy.lb.com:2878")
client_factory.add_client("https://someToken@DOMAIN.wavefront.com")

# Send traces and spans to the tracing port. If you are directly using the sender SDK to send spans without using any other SDK, use the same port as the customTracingListenerPorts configured in the wavefront proxy. Assume you have installed and started the proxy on <proxy_hostname>.
client_factory.add_client("http://<proxy_hostname>:30000")

wavefront_sender = client_factory.get_client()
```

## Send Data

Operations for Applications supports different metric types, such as gauges, counters, delta counters, histograms, traces, and spans. See [Metrics](https://docs.wavefront.com/metric_types.html) for details. To send data to Operations for Applications using the `wavefront_sender` you need to instantiate the following:

* [Single Metric or Delta Counter](#single-metric-or-delta-counter)
* [Single Histogram Distribution](#single-histogram-distribution)
* [Single Span](#single-span)
* [Single Event](#single-event)

### Send a Single Data Point

The following examples show how to send a single data point to the service. You use the Wavefront Sender you created above.

#### Single Metric or Delta Counter

```python
from uuid import UUID

# Wavefront metrics data format:
# <metricName> <metricValue> [<timestamp>] source=<source> [pointTags]
wavefront_sender.send_metric(
    name="new_york.power.usage",
    value=42422.0,
    timestamp=1533529977,
    source="localhost",
    tags={"datacenter": "dc1"})

# Wavefront delta counter data format:
# <metricName> <metricValue> source=<source> [pointTags]
wavefront_sender.send_delta_counter(
    name="delta.counter",
    value=1.0,
    source="localhost",
    tags={"datacenter": "dc1"})
```

***Note***: If your metric name has a bad character, that character is replaced with a `-`.

#### Single Histogram Distribution

```python
from uuid import UUID
from wavefront_sdk.entities.histogram import histogram_granularity

# Wavefront histogram data format:
# {!M | !H | !D} [<timestamp>] #<count> <mean> [centroids] <histogramName> source=<source> [pointTags]
# Example: You can choose to send to at most 3 bins: Minute, Hour, Day
# "!M 1533529977 #20 30.0 #10 5.1 request.latency source=appServer1 region=us-west"
# "!H 1533529977 #20 30.0 #10 5.1 request.latency source=appServer1 region=us-west"
# "!D 1533529977 #20 30.0 #10 5.1 request.latency source=appServer1 region=us-west"
wavefront_sender.send_distribution(
    name="request.latency",
    centroids=[(30, 20), (5.1, 10)],
    histogram_granularities={histogram_granularity.DAY,
                             histogram_granularity.HOUR,
                             histogram_granularity.MINUTE},
    timestamp=1533529977,
    source="appServer1",
    tags={"region": "us-west"})
```

#### Single Span

If you are directly using the Sender SDK to send data to the service, you won’t see span-level RED metrics by default unless you use the Wavefront proxy and define a custom tracing port (`tracing_port`). See [Instrument Your Application with the Sender SDKs](https://docs.wavefront.com/tracing_instrumenting_frameworks.html#instrument-your-application-with-wavefront-sender-sdks) for details.

```python
from uuid import UUID

# Wavefront trace and span data format:
# <tracingSpanName> source=<source> [pointTags] <start_millis> <duration_milliseconds>
# Example: "getAllUsers source=localhost
#           traceId=7b3bf470-9456-11e8-9eb6-529269fb1459
#           spanId=0313bafe-9457-11e8-9eb6-529269fb1459
#           parent=2f64e538-9457-11e8-9eb6-529269fb1459
#           application=Wavefront http.method=GET
#           1533529977 343500"
wavefront_sender.send_span(
    name="getAllUsers",
    start_millis=1533529977,
    duration_millis=343500,
    source="localhost",
    trace_id=UUID("7b3bf470-9456-11e8-9eb6-529269fb1459"),
    span_id=UUID("0313bafe-9457-11e8-9eb6-529269fb1459"),
    parents=[UUID("2f64e538-9457-11e8-9eb6-529269fb1459")],
    follows_from=None,
    tags=[("application", "Wavefront"),
          ("service", "istio"),
          ("http.method", "GET")],
    span_logs=None)
```

#### Single Event

```python
# Wavefront event format:
# @Event <StartTime> <EndTime> "<EventName>"  severity="<Severity>"
# type="<Type>" details="<EventDetail>" host="<Source>" tag="<Tags>"
wavefront_sender.send_event('event name',
                            1592200048,
                            1592201048,
                            "localhost",
                            ["env:", "dev"],
                            {"severity": "info",
                             "type": "backup",
                             "details": "broker backup"})
```

### Send Batch Data

The following examples show how to generate data points manually and send them as a batch to Operations for Applications.

#### Batch Metrics

```python
from uuid import UUID
from wavefront_sdk.common import metric_to_line_data

# Generate string data in Wavefront metric format
one_metric_data = metric_to_line_data(
    name="new-york.power.usage",
    value=42422,
    timestamp=1493773500,
    source="localhost",
    tags={"datacenter": "dc1"},
    default_source="defaultSource")

# Result of one_metric_data:
  # '"new-york.power.usage" 42422.0 1493773500 source="localhost" "datacenter"="dc1"\n'

# List of data
batch_metric_data = [one_metric_data, one_metric_data]

# Send list of data immediately
wavefront_sender.send_metric_now(batch_metric_data)
```

***Note***: If your metric name has a bad character, that character is replaced with a `-`.

#### Batch Histograms

```python
from uuid import UUID
from wavefront_sdk.entities.histogram import histogram_granularity
from wavefront_sdk.common import histogram_to_line_data

# Generate string data in Wavefront histogram format
one_histogram_data = histogram_to_line_data(
    name="request.latency",
    centroids=[(30.0, 20), (5.1, 10)],
    histogram_granularities={histogram_granularity.MINUTE,
                             histogram_granularity.HOUR,
                             histogram_granularity.DAY},
    timestamp=1493773500,
    source="appServer1",
    tags={"region": "us-west"},
    default_source ="defaultSource")

# Result of one_histogram_data:
  # '!D 1493773500 #20 30.0 #10 5.1 "request.latency" source="appServer1" "region"="us-west"\n
  # !H 1493773500 #20 30.0 #10 5.1 "request.latency" source="appServer1" "region"="us-west"\n
  # !M 1493773500 #20 30.0 #10 5.1 "request.latency" source="appServer1" "region"="us-west"\n'

# List of data
batch_histogram_data = [one_histogram_data, one_histogram_data]

# Send list of data immediately
wavefront_sender.send_distribution_now(batch_histogram_data)
```

#### Batch Trace Data

If you are directly using the Sender SDK to send data to the service, you won’t see span-level RED metrics by default unless you use the Wavefront proxy and define a custom tracing port (`tracing_port`). See [Instrument Your Application with Wavefront Sender SDKs](https://docs.wavefront.com/tracing_instrumenting_frameworks.html#instrument-your-application-with-wavefront-sender-sdks) for details.

```python
from uuid import UUID
from wavefront_sdk.common import tracing_span_to_line_data

# Generate string data in Wavefront tracing span format
one_tracing_span_data = tracing_span_to_line_data(
    name="getAllUsers",
    start_millis=1552949776000,
    duration_millis=343,
    source="localhost",
    trace_id=UUID("7b3bf470-9456-11e8-9eb6-529269fb1459"),
    span_id=UUID("0313bafe-9457-11e8-9eb6-529269fb1459"),
    parents=[UUID("2f64e538-9457-11e8-9eb6-529269fb1459")],
    follows_from=[UUID("5f64e538-9457-11e8-9eb6-529269fb1459")],
    tags=[("application", "Wavefront"), ("http.method", "GET")],
    span_logs=None,
    default_source="defaultSource")

# Result of one_tracing_span_data:
  # '"getAllUsers" source="localhost" traceId=7b3bf470-9456-11e8-9eb6-529269fb1459 spanId=0313bafe-
  # 9457-11e8-9eb6-529269fb1459 parent=2f64e538-9457-11e8-9eb6-529269fb1459 followsFrom=5f64e538-
  # 9457-11e8-9eb6-529269fb1459 "application"="Wavefront" "http.method"="GET" 1552949776000 343\n'

# List of data
batch_span_data = [one_tracing_span_data, one_tracing_span_data]

# Send list of data immediately
wavefront_sender.send_span_now(batch_span_data)
```

#### Batch Events

```python
from wavefront_sdk.common import event_to_line_data

# Generate string data in Wavefront event format
one_event_data = event_to_line_data(
    name="event name",
    start_time=1592200048,
    end_time=1592201048,
    source="localhost",
    tags=["env", "dev"],
    annotations={"severity": "info",
                 "type": "backup",
                 "details": "broker backup"})

# Result of one_event_data:
# '@Event 1592200048 1592201048 "event name" severity="info" type="backup" details="broker backup"
# host="localhost" tag="env" tag="dev"\n'

# List of events
batch_event_data = [one_event_data, one_event_data]

# Send list of events immediately
wavefront_sender.send_event_now(batch_event_data)
```

## Close the Sender

Remember to flush the buffer and close the sender before shutting down the application.

```python
# To shut down a sender from a WavefrontClientFactory
wavefront_sender = client_factory.get_client()

# If the application failed to send metrics/histograms/tracing-spans,
# you can get the total failure count as follows:
total_failures = wavefront_sender.get_failure_count()

# On-demand buffer flush
wavefront_sender.flush_now()

# Close the sender connection
wavefront_sender.close()
```

## License

[Apache 2.0 License](LICENSE).

## Contribute

To get support with our project and contribute, follow the instructions in [CONTRIBUTING.md](CONTRIBUTING.md).

To create a new release, follow the instructions in [RELEASING.md](RELEASING.md)
