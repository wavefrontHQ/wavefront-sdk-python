# Set Up a Wavefront Sender
You can choose to send metrics, histograms, or trace data from your application to the Wavefront service using one of the following techniques:
* Use [direct ingestion](https://docs.wavefront.com/direct_ingestion.html) to send the data directly to the Wavefront service. This is the simplest way to get up and running quickly.
* Use a [Wavefront proxy](https://docs.wavefront.com/proxies.html), which then forwards the data to the Wavefront service. This is the recommended choice for a large-scale deployment that needs resilience to internet outages, control over data queuing and filtering, and more. 

You instantiate an object that corresponds to your choice:
* Option 1: [Create a `WavefrontDirectClient`](#option-1-create-a-wavefrontdirectclient) to send data directly to a Wavefront service.
* Option 2: [Create a `WavefrontProxyClient`](#option-2-create-a-wavefrontproxyclient) to send data to a Wavefront proxy.

## Option 1: Create a WavefrontDirectClient
To create a `WavefrontDirectClient`, you initialize it with the information it needs to send data directly to Wavefront.

### Step 1. Obtain Wavefront Access Information
Gather the following access information:

* Identify the URL of your Wavefront instance. This is the URL you connect to when you log in to Wavefront, typically something like `https://<domain>.wavefront.com`.
* In Wavefront, verify that you have Direct Data Ingestion permission, and [obtain an API token](http://docs.wavefront.com/wavefront_api.html#generating-an-api-token).

### Step 2. Initialize the WavefrontDirectClient
You initialize a `WavefrontDirectClient` by building it with the access information you obtained in Step 1.

```python
from wavefront_sdk import WavefrontDirectClient

# Create a sender with:
   # the Wavefront URL 
   # a Wavefront API token that was created with direct ingestion permission
wavefront_sender = WavefrontDirectClient(
    server="<SERVER_ADDR>",
    token="<TOKEN>"
)
```

## Option 2: Create a WavefrontProxyClient

**Note:** Before your application can use a `WavefrontProxyClient`, you must [set up and start a Wavefront proxy](https://github.com/wavefrontHQ/java/tree/master/proxy#set-up-a-wavefront-proxy).

To create a `WavefrontProxyClient`, you build it with the information it needs to send data to a Wavefront proxy, including:

* The name of the host that will run the Wavefront proxy.
* One or more proxy listening ports to send data to. The ports you specify depend on the kinds of data you want to send (metrics, histograms, and/or trace data). You must specify at least one listener port. 
* Optional setting for tuning communication with the proxy.


```python
from wavefront_sdk import WavefrontProxyClient

# Create a sender with:
   # the proxy hostname or address
   # the recommended listener port (30000) for sending trace data to 
   # the recommended listener port (40000) for sending histograms to 
   # the default listener port (2878) for sending metrics to 
   # a nondefault interval (2 seconds) for flushing data from the sender to the proxy. Default: 5 seconds
wavefront_sender = WavefrontProxyClient(
   host="<PROXY_HOST>",
   tracing_port=30000,
   distribution_port=40000,
   metrics_port=2878,
   internal_flush=2
)
```
 
**Note:** When you [set up a Wavefront proxy](https://github.com/wavefrontHQ/java/tree/master/proxy#set-up-a-wavefront-proxy) on the specified proxy host, you specify the port it will listen to for each type of data to be sent. The `WavefrontProxyClient` must send data to the same ports that the Wavefront proxy listens to. Consequently, the port-related parameters must specify the same port numbers as the corresponding proxy configuration properties: 

| `WavefrontProxyClient()` parameter | Corresponding property in `wavefront.conf` |
| ----- | -------- |
| `metrics_port` | `pushListenerPorts=` |
| `distribution_port` | `histogramDistListenerPorts=` |
| `tracing_port` | `traceListenerPorts=` |
 
# Share a Wavefront Sender

Various Wavefront SDKs for Python use the `wavefront-sdk-python` library and require a Wavefront sender object.

If you are using multiple Wavefront Python SDKs within the same process, you can create a single Wavefront sender, and share it among the SDKs. 
 
<!--- 
For example, the following snippet shows how to use the same `WavefrontSender` when setting up the 
[wavefront-opentracing-sdk-python](https://github.com/wavefrontHQ/wavefront-opentracing-sdk-python) and 
XXX SDKs.
--->
