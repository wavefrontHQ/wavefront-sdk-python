# wavefront-sdk-python

[![travis build status](https://travis-ci.com/wavefrontHQ/wavefront-sdk-python.svg?branch=master)](https://travis-ci.com/wavefrontHQ/wavefront-sdk-python)
[![image](https://img.shields.io/pypi/v/wavefront-sdk-python.svg)](https://pypi.org/project/wavefront-sdk-python/)
[![image](https://img.shields.io/pypi/l/wavefront-sdk-python.svg)](https://pypi.org/project/wavefront-sdk-python/)
[![image](https://img.shields.io/pypi/pyversions/wavefront-sdk-python.svg)](https://pypi.org/project/wavefront-sdk-python/)


Wavefront by VMware SDK for Python is the core library for sending metrics, histograms and trace data from your Python application to Wavefront using via proxy or direct ingestion.

## Requirements and Installation
Python 2.7+ and Python 3.x are supported.

```
pip install wavefront-sdk-python
```

## Set Up a Wavefront Sender

You can choose to send metrics, histograms, or trace data from your application to the Wavefront service using one of the following techniques:
* Use [direct ingestion](https://docs.wavefront.com/direct_ingestion.html) to send the data directly to the Wavefront service. This is the simplest way to get up and running quickly.
* Use a [Wavefront proxy](https://docs.wavefront.com/proxies.html), which then forwards the data to the Wavefront service. This is the recommended choice for a large-scale deployment that needs resilience to internet outages, control over data queuing and filtering, and more.

You instantiate an object that corresponds to your choice:
* Option 1: [Create a `WavefrontDirectClient`](#option-1-create-a-wavefrontdirectclient) to send data directly to a Wavefront service.
* Option 2: [Create a `WavefrontProxyClient`](#option-2-create-a-wavefrontproxyclient) to send data to a Wavefront proxy.

### Option 1: Create a WavefrontDirectClient
To create a `WavefrontDirectClient`, you initialize it with the information it needs to send data directly to Wavefront.

#### Step 1. Obtain Wavefront Access Information
Gather the following access information:

* Identify the URL of your Wavefront instance. This is the URL you connect to when you log in to Wavefront, typically something like `https://mydomain.wavefront.com`.
* In Wavefront, verify that you have Direct Data Ingestion permission, and [obtain an API token](http://docs.wavefront.com/wavefront_api.html#generating-an-api-token).

#### Step 2. Initialize the WavefrontDirectClient
You initialize a `WavefrontDirectClient` by providing the access information you obtained in Step 1.

You can optionally specify parameters to tune the following ingestion properties:

* Max queue size - Internal buffer capacity of the Wavefront sender. Any data in excess of this size is dropped.
* Flush interval - Interval for flushing data from the Wavefront sender directly to Wavefront.
* Batch size - Amount of data to send to Wavefront in each flush interval.

Together, the batch size and flush interval control the maximum theoretical throughput of the Wavefront sender. You should override the defaults _only_ to set higher values.


```python
from wavefront_sdk import WavefrontDirectClient

# Create a sender with:
   # your Wavefront URL
   # a Wavefront API token that was created with direct ingestion permission
   # max queue size (in data points). Default: 50,000
   # batch size (in data points). Default: 10,000
   # flush interval  (in seconds). Default: 1 second
wavefront_sender = WavefrontDirectClient(
    server="<SERVER_ADDR>",
    token="<TOKEN>",
    max_queue_size=50000,
    batch_size=10000,
    flush_interval_seconds=5
)
```

### Option 2: Create a WavefrontProxyClient

**Note:** Before your application can use a `WavefrontProxyClient`, you must [set up and start a Wavefront proxy](https://github.com/wavefrontHQ/java/tree/master/proxy#set-up-a-wavefront-proxy).

To create a `WavefrontProxyClient`, you instantiate it with the information it needs to send data to a Wavefront proxy, including:

* The name of the host that will run the Wavefront proxy.
* One or more proxy listening ports to send data to. The ports you specify depend on the kinds of data you want to send (metrics, histograms, and/or trace data). You must specify at least one listener port.
* Optional setting for tuning communication with the proxy.

```python
from wavefront_sdk import WavefrontProxyClient

# Create a sender with:
   # the proxy hostname or address
   # the default listener port (2878) for sending metrics to
   # the recommended listener port (2878) for sending histograms to
   # the recommended listener port (30000) for sending trace data to
   # a nondefault interval (2 seconds) for flushing data from the sender to the proxy. Default: 5 seconds
wavefront_sender = WavefrontProxyClient(
   host="<PROXY_HOST>",
   metrics_port=2878,
   distribution_port=2878,
   tracing_port=30000,
   internal_flush=2
)
```

**Note:** When you [set up a Wavefront proxy](https://github.com/wavefrontHQ/java/tree/master/proxy#set-up-a-wavefront-proxy) on the specified proxy host, you specify the port it will listen to for each type of data to be sent. The `WavefrontProxyClient` must send data to the same ports that the Wavefront proxy listens to. Consequently, the port-related parameters must specify the same port numbers as the corresponding proxy configuration properties:

| `WavefrontProxyClient()` parameter | Corresponding property in `wavefront.conf` |
| ----- | -------- |
| `metrics_port` | `pushListenerPorts=` |
| `distribution_port` | `histogramDistListenerPorts=` |
| `tracing_port` | `traceListenerPorts=` |



## Send a Single Data Point to Wavefront

The following examples show how to send a single data point to Wavefront. You use the Wavefront sender you created above.


### Single Metric or  Delta Counter

```python
from uuid import UUID

# Wavefront metrics data format:
# <metricName> <metricValue> [<timestamp>] source=<source> [pointTags]
wavefront_sender.send_metric(
    name="new york.power.usage", value=42422.0, timestamp=1533529977,
    source="localhost", tags={"datacenter": "dc1"})

# Wavefront delta counter data format:
# <metricName> <metricValue> source=<source> [pointTags]
wavefront_sender.send_delta_counter(
    name="delta.counter", value=1.0,
    source="localhost", tags={"datacenter": "dc1"})
```
### Single Histogram Distribution

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
    name="request.latency", centroids=[(30, 20), (5.1, 10)],
    histogram_granularities={histogram_granularity.DAY,
                             histogram_granularity.HOUR,
                             histogram_granularity.MINUTE},
    timestamp=1533529977, source="appServer1", tags={"region": "us-west"})
```

### Single Span
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
    name="getAllUsers", start_millis=1533529977, duration_millis=343500,
    source="localhost", trace_id=UUID("7b3bf470-9456-11e8-9eb6-529269fb1459"),
    span_id=UUID("0313bafe-9457-11e8-9eb6-529269fb1459"),
    parents=[UUID("2f64e538-9457-11e8-9eb6-529269fb1459")],
    follows_from=None, tags=[("application", "Wavefront"),
                             ("http.method", "GET")],
    span_logs=None)
```

## Send Batch Data

The following examples show how to generate data points manually and send them as a batch to Wavefront.

### Batch Metrics

```python
from uuid import UUID
from wavefront_sdk.common import metric_to_line_data

# Generate string data in Wavefront metric format
one_metric_data = metric_to_line_data(
    name="new-york.power.usage", value=42422, timestamp=1493773500,
    source="localhost", tags={"datacenter": "dc1"},
    default_source="defaultSource")

# Result of one_metric_data:
  # '"new-york.power.usage" 42422.0 1493773500 source="localhost" "datacenter"="dc1"\n'

# List of data
batch_metric_data = [one_metric_data, one_metric_data]

# Send list of data immediately
wavefront_sender.send_metric_now(batch_metric_data)
```
### Batch Histograms

```python
from uuid import UUID
from wavefront_sdk.entities.histogram import histogram_granularity
from wavefront_sdk.common import histogram_to_line_data

# Generate string data in Wavefront histogram format
one_histogram_data = histogram_to_line_data(
    name="request.latency", centroids=[(30.0, 20), (5.1, 10)],
    histogram_granularities={histogram_granularity.MINUTE,
                             histogram_granularity.HOUR,
                             histogram_granularity.DAY},
    timestamp=1493773500, source="appServer1", tags={"region": "us-west"},
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
### Batch Trace Data

```python
from uuid import UUID
from wavefront_sdk.common import tracing_span_to_line_data

# Generate string data in Wavefront tracing span format
one_tracing_span_data = tracing_span_to_line_data(
    name="getAllUsers", start_millis=1552949776000, duration_millis=343,
    source="localhost", trace_id=UUID("7b3bf470-9456-11e8-9eb6-529269fb1459"),
    span_id=UUID("0313bafe-9457-11e8-9eb6-529269fb1459"),
    parents=[UUID("2f64e538-9457-11e8-9eb6-529269fb1459")],
    follows_from=[UUID("5f64e538-9457-11e8-9eb6-529269fb1459")],
    tags=[("application", "Wavefront"), ("http.method", "GET")],
    span_logs=None, default_source="defaultSource")

# Result of one_tracing_span_data:
  # '"getAllUsers" source="localhost" traceId=7b3bf470-9456-11e8-9eb6-529269fb1459 spanId=0313bafe-
  # 9457-11e8-9eb6-529269fb1459 parent=2f64e538-9457-11e8-9eb6-529269fb1459 followsFrom=5f64e538-
  # 9457-11e8-9eb6-529269fb1459 "application"="Wavefront" "http.method"="GET" 1552949776000 343\n'

# List of data
batch_span_data = [one_tracing_span_data, one_tracing_span_data]

# Send list of data immediately
wavefront_sender.send_span_now(batch_span_data)
```

## Get a Failure Count

If there are any failures observed while sending metrics, histograms, or trace data, you can get the total failure count.

```python
# Get the total failure count
total_failures = wavefront_sender.get_failure_count()
```
## Close the Connection

If the Wavefront sender is a `WavefrontDirectClient`, flush all buffers and then close the connection before shutting down the application.

```python
# To shut down a WavefrontDirectClient
# Flush all buffers.
wavefront_sender.flush_now()

# Close the sender connection
wavefront_sender.close()
```
If the Wavefront sender is a `WavefrontProxyClient`, close the connection before shutting down the application.

```python
# To shut down a WavefrontProxyClient

# Close the sender connection
wavefront_sender.close()
```
