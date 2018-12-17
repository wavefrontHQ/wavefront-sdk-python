# Application Tags

Many Wavefront SDKs require you to specify _application tags_ that describe the architecture of your application as it is deployed. These tags are associated with the metrics and trace data sent from the instrumented microservices in your application. You specify a separate set of application tags for each microservice you instrument. Wavefront uses these tags to aggregate and filter data at different levels of granularity.

**Required tags** enable you to drill down into the data for a particular service:
* `application` - Name that identifies your Java application, for example: `OrderingApp`. All microservices in the same application should share the same application name.
* `service` - Name that identifies the microservice within your application, for example: `inventory`. Each microservice should have its own service name.

**Optional tags** enable you to use the physical topology of your application to further filter your data:
* `cluster` - Name of a group of related hosts that serves as a cluster or region in which the application will run, for example: `us-west-2`.
* `shard` - Name of a subgroup of hosts within a cluster that serve as a partition, replica, shard, or mirror, for example: `secondary`.

You can also optionally add custom tags specific to your application (see snippet below).

Application tags and their values are encapsulated in an `ApplicationTags` object in your microservice’s code. 
To create an `ApplicationTags` instance:

```python
from wavefront_sdk.common import ApplicationTags

application_tags = ApplicationTags(application="OrderingApp",
                                   service="inventory",
                                   cluster="us-west-2",
                                   shard="secondary",
                                   custom_tags=[("location", "Oregon")])
```
