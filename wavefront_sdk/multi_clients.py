"""Wavefront Client to support sending data to multiple clients.

@author Yogesh Prasad Kurmi (ykurmi@vmware.com)
"""
from . import entities


class WavefrontMultiClient(entities.WavefrontMetricSender,
                           entities.WavefrontHistogramSender,
                           entities.WavefrontTracingSpanSender,
                           entities.WavefrontEventSender):
    """Wavefront multi client.

    Sends data to multiple clients.
    """

    senders = {}

    def with_wavefront_sender(self, client):
        """Add clients to wavefront multi client.

        @param client: Wavefront client
        @type: WavefrontClient
        @return:
        """
        self.senders[client.server] = client

    # pylint: disable=too-many-arguments
    def send_metric(self, name, value, timestamp, source, tags):
        """Send Metric Data via direct ingestion client.

        Wavefront Metrics Data format
        <metricName> <metricValue> [<timestamp>] source=<source> [pointTags]
        Example: "new-york.power.usage 42422 1533531013 source=localhost
                  datacenter=dc1"

        @param name: Metric Name
        @type name: str
        @param value: Metric Value
        @type value: float
        @param timestamp: Timestamp
        @type timestamp: long
        @param source: Source
        @type source: str
        @param tags: Tags
        @type tags: dict
        """
        for client in self.senders.values():
            client.send_metric(name, value, timestamp, source, tags)

    def send_metric_now(self, metrics):
        """Send a list of metrics immediately.

        Have to construct the data manually by calling
        common.utils.metric_to_line_data()

        @param metrics: List of string spans data
        @type metrics: list[str]
        """
        for client in self.senders.values():
            client.send_metric_now(metrics)

    # pylint: disable=too-many-arguments
    def send_distribution(self, name, centroids, histogram_granularities,
                          timestamp, source, tags):
        """Send Distribution Data via direct ingestion client.

        Wavefront Histogram Data format
        {!M | !H | !D} [<timestamp>] #<count> <mean> [centroids]
        <histogramName> source=<source> [pointTags]
        Example: "!M 1533531013 #20 30.0 #10 5.1 request.latency
                  source=appServer1 region=us-west"

        @param name: Histogram Name
        @type name: str
        @param centroids: List of centroids(pairs)
        @type centroids: list
        @param histogram_granularities: Histogram Granularities
        @type histogram_granularities: set
        @param timestamp: Timestamp
        @type timestamp: long
        @param source: Source
        @type source: str
        @param tags: Tags
        @type tags: dict
        """
        for client in self.senders.values():
            client.send_distribution(name, centroids, histogram_granularities,
                                     timestamp, source, tags)

    def send_distribution_now(self, distributions):
        """Send a list of distribution immediately.

        Have to construct the data manually by calling
        common.utils.histogram_to_line_data()

        @param distributions: List of string spans data
        @type distributions: list[str]
        """
        for client in self.senders.values():
            client.send_distribution_now(distributions)

    # pylint: disable=too-many-arguments
    def send_span(self, name, start_millis, duration_millis, source, trace_id,
                  span_id, parents, follows_from, tags, span_logs):
        """Send span data via direct ingestion client.

        Wavefront Tracing Span Data format
        <tracingSpanName> source=<source> [pointTags] <start_millis>
        <duration_milli_seconds>
        Example: "getAllUsers source=localhost
                  traceId=7b3bf470-9456-11e8-9eb6-529269fb1459
                  spanId=0313bafe-9457-11e8-9eb6-529269fb1459
                  parent=2f64e538-9457-11e8-9eb6-529269fb1459
                  application=Wavefront http.method=GET
                  1533531013 343500"

        @param name: Span Name
        @type name: str
        @param start_millis: Start time
        @type start_millis: long
        @param duration_millis: Duration time
        @type duration_millis: long
        @param source: Source
        @type source: str
        @param trace_id: Trace ID
        @type trace_id: UUID
        @param span_id: Span ID
        @type span_id: UUID
        @param parents: Parents Span ID
        @type parents: List of UUID
        @param follows_from: Follows Span ID
        @type follows_from: List of UUID
        @param tags: Tags
        @type tags: list
        @param span_logs: Span Log
        """
        for client in self.senders.values():
            client.send_span(name, start_millis, duration_millis, source,
                             trace_id, span_id, parents, follows_from,
                             tags, span_logs)

    def send_span_now(self, spans):
        """
        Send a list of spans immediately.

        Have to construct the data manually by calling
        common.utils.tracing_span_to_line_data()

        @param spans: List of string spans data
        @type spans: list[str]
        """
        for client in self.senders.values():
            client.send_span_now(spans)

    def send_span_log_now(self, span_logs):
        """
        Send a list of spans logs immediately.

        Have to construct the data manually by calling
        common.utils.span_log_to_line_data()

        @param span_logs: List of string span logs data
        @type span_logs: list[str]
        """
        for client in self.senders.values():
            client.send_span_log_now(span_logs)

    def send_event(self, name, start_time, end_time, source, tags,
                   annotations):
        """Send Event Data via direct ingestion client.

        Wavefront Event Data format
        {"name": <Event Name>, "annotations": <Annotations>,
         "hosts": <Host Name>,"startTime": <Start Time>,
          "endTime": <End Time>, "tags": <Tags>}
        Example: {"name": event_via_direct_ingestion, "annotations": {
        "severity": "severe", "type": "backup", "details": "broker backup"},
         "hosts": "localhost", "startTime": 1590678089, "endTime": 1590679089,
         "tags": ["env:", "test"]}

        @param name: Event Name
        @type name: str
        @param start_time: Event Start Time
        @type start_time: long
        @param end_time: Event End Time
        @type end_time: long
        @param source: Source
        @type source: str
        @param tags: Tags
        @type tags: list[str]
        @param annotations: Annotations
        @type annotations: dict
        """
        for client in self.senders.values():
            client.send_event(name, start_time, end_time, source, tags,
                              annotations)

    def send_event_now(self, events):
        """Send a list of events immediately.

        Have to construct the data manually by calling
        common.utils.event_to_json()

        @param events: List of string events data
        @type events: list[str]
        """
        for client in self.senders.values():
            client.send_event_now(events)

    def get_failure_count(self):
        """Get failure count for all connections."""
        count = 0
        for client in self.senders.values():
            count = count + client.get_failure_count()

        return count

    def flush_now(self):
        """Flush all the clients."""
        for client in self.senders.values():
            client.flush_now()

    def close(self):
        """Close all the clients."""
        for client in self.senders.values():
            client.close()
