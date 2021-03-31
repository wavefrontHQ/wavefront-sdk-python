"""Tracing Span Sender Interface for both Clients.

@author Hao Song (songhao@vmware.com)`
"""


# pylint: disable=E0012,R0205
class WavefrontTracingSpanSender(object):
    """Tracing Span Sender Interface for both Clients."""

    # pylint: disable=too-many-arguments
    def send_span(self, name, start_millis, duration_millis, source, trace_id,
                  span_id, parents, follows_from, tags, span_logs):
        """Send span data via proxy.

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
        raise NotImplementedError

    def send_formatted_span(self, span):
        """Send a formatted span immediately.

        @param span: Formatted span
        @type: str
        """
        self.send_span_now([span])

    def send_span_now(self, spans):
        """Send a list of spans immediately.

        Have to construct the data manually by calling
        common.utils.metric_to_line_data()

        @param spans: List of string spans data
        @type spans: list[str]
        """
        raise NotImplementedError

    def send_span_log_now(self, span_logs):
        """Send a list of span logs immediately.

        Have to construct the data manually by calling
        common.utils.span_log_to_line_data()

        @param span_logs: List of string span logs data
        @type span_logs: list[str]
        """
        raise NotImplementedError
