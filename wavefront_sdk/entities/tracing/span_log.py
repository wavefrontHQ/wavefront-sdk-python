"""Span Log.

@author Hao Song (songhao@vmware.com)`
"""


# pylint: disable=E0012,R0205
class SpanLog(object):
    """Span Log including timestamp and fields."""

    # pylint: disable=too-few-public-methods
    def __init__(self, timestamp, fields):
        """
        Construct Span Log.

        @param timestamp: Timestamp of the span log.
        @param fields: Fields of the span log.
        """
        self.timestamp = timestamp
        self.fields = fields
