"""
Unit Tests for Wavefront Python SDK.

@author Hao Song (songhao@vmware.com)
"""

import unittest
from uuid import UUID

from wavefront_sdk.common.utils import sanitize, \
    metric_to_line_data, histogram_to_line_data, tracing_span_to_line_data
from wavefront_sdk.entities import histogram_granularity


class TestUtils(unittest.TestCase):
    """
    Test Functions of wavefront_sdk.common.utils.
    """

    def test_sanitize(self):
        """
        Test wavefront_sdk.common.utils.sanitize().
        """
        self.assertEqual('"hello"', sanitize("hello"))
        self.assertEqual('"hello-world"', sanitize("hello world"))
        self.assertEqual('"hello.world"', sanitize("hello.world"))
        self.assertEqual('"hello\\"world\\""', sanitize('hello"world"'))
        self.assertEqual('"hello\'world"', sanitize("hello'world"))

    def test_metric_to_line_data(self):
        """
        Test wavefront_sdk.common.utils.metric_to_line_data().
        """
        self.assertEqual(
            '"new-york.power.usage" 42422.0 1493773500 source="localhost"'
            ' "datacenter"="dc1"\n',
            metric_to_line_data(
                "new-york.power.usage", 42422, 1493773500, "localhost",
                {"datacenter": "dc1"}, "defaultSource"))

        # null timestamp
        self.assertEqual(
            '"new-york.power.usage" 42422.0 source="localhost" '
            '"datacenter"="dc1"\n',
            metric_to_line_data(
                "new-york.power.usage", 42422, None, "localhost",
                {"datacenter": "dc1"}, "defaultSource"))

        # null tags
        self.assertEqual(
            '"new-york.power.usage" 42422.0 1493773500 source="localhost"\n',
            metric_to_line_data(
                "new-york.power.usage", 42422, 1493773500, "localhost", None,
                "defaultSource"))

        # null tags and null timestamp
        self.assertEqual(
            '"new-york.power.usage" 42422.0 source="localhost"\n',
            metric_to_line_data(
                "new-york.power.usage", 42422, None, "localhost", None,
                "defaultSource"))

    def test_histogram_to_line_data(self):
        """
        Test wavefront_sdk.common.utils.histogram_to_line_data().
        """
        self.assertEqual(
            '!M 1493773500 #20 30.0 #10 5.1 "request.latency" '
            'source="appServer1" "region"="us-west"\n',
            histogram_to_line_data(
                "request.latency", [(30.0, 20), (5.1, 10)],
                {histogram_granularity.MINUTE}, 1493773500, "appServer1",
                {"region": "us-west"}, "defaultSource"))

        # null timestamp
        self.assertEqual(
            '!M #20 30.0 #10 5.1 "request.latency" source="appServer1" '
            '"region"="us-west"\n',
            histogram_to_line_data("request.latency", [(30.0, 20), (5.1, 10)],
                                   {histogram_granularity.MINUTE},
                                   None, "appServer1", {"region": "us-west"},
                                   "defaultSource"))

        # null tags
        self.assertEqual(
            '!M 1493773500 #20 30.0 #10 5.1 "request.latency" '
            'source="appServer1"\n',
            histogram_to_line_data(
                "request.latency", [(30.0, 20), (5.1, 10)],
                {histogram_granularity.MINUTE}, 1493773500, "appServer1", None,
                "defaultSource"))

        # empty centroids
        with self.assertRaises(ValueError):
            histogram_to_line_data(
                "request.latency", [], {histogram_granularity.MINUTE},
                1493773500, "appServer1", None, "defaultSource")

        # no histogram granularity specified
        with self.assertRaises(ValueError):
            histogram_to_line_data(
                "request.latency", [(30.0, 20), (5.1, 10)], {}, 1493773500,
                "appServer1", None, "defaultSource")

        # multiple granularities
        self.assertEqual(
            sorted([
                '!M 1493773500 #20 30.0 #10 5.1 "request.latency" '
                'source="appServer1" "region"="us-west"',
                '!H 1493773500 #20 30.0 #10 5.1 "request.latency" '
                'source="appServer1" "region"="us-west"',
                '!D 1493773500 #20 30.0 #10 5.1 "request.latency" '
                'source="appServer1" "region"="us-west"']),
            sorted(histogram_to_line_data(
                "request.latency", [(30.0, 20), (5.1, 10)],
                {histogram_granularity.MINUTE, histogram_granularity.HOUR,
                 histogram_granularity.DAY},
                1493773500, "appServer1", {"region": "us-west"},
                "defaultSource").splitlines()))

    def test_tracing_span_to_line_data(self):
        """
        Test wavefront_sdk.common.utils.tracing_span_to_line_data().
        """
        self.assertEqual(
            '"getAllUsers" source="localhost" '
            'traceId=7b3bf470-9456-11e8-9eb6-529269fb1459 '
            'spanId=0313bafe-9457-11e8-9eb6-529269fb1459 '
            'parent=2f64e538-9457-11e8-9eb6-529269fb1459 '
            'followsFrom=5f64e538-9457-11e8-9eb6-529269fb1459 '
            '"application"="Wavefront" '
            '"http.method"="GET" 1493773500 343500\n',
            tracing_span_to_line_data(
                "getAllUsers", 1493773500, 343500, "localhost",
                UUID("7b3bf470-9456-11e8-9eb6-529269fb1459"),
                UUID("0313bafe-9457-11e8-9eb6-529269fb1459"),
                [UUID("2f64e538-9457-11e8-9eb6-529269fb1459")],
                [UUID("5f64e538-9457-11e8-9eb6-529269fb1459")],
                [("application", "Wavefront"), ("http.method", "GET")],
                None, "defaultSource"))

        # null followsFrom
        self.assertEqual(
            '"getAllUsers" source="localhost" '
            'traceId=7b3bf470-9456-11e8-9eb6-529269fb1459 '
            'spanId=0313bafe-9457-11e8-9eb6-529269fb1459 '
            'parent=2f64e538-9457-11e8-9eb6-529269fb1459 '
            '"application"="Wavefront" '
            '"http.method"="GET" 1493773500 343500\n',
            tracing_span_to_line_data(
                "getAllUsers", 1493773500, 343500, "localhost",
                UUID("7b3bf470-9456-11e8-9eb6-529269fb1459"),
                UUID("0313bafe-9457-11e8-9eb6-529269fb1459"),
                [UUID("2f64e538-9457-11e8-9eb6-529269fb1459")],
                None, [("application", "Wavefront"), ("http.method", "GET")],
                None, "defaultSource"))

        # root span
        self.assertEqual(
            '"getAllUsers" source="localhost" '
            'traceId=7b3bf470-9456-11e8-9eb6-529269fb1459 '
            'spanId=0313bafe-9457-11e8-9eb6-529269fb1459 '
            '"application"="Wavefront" '
            '"http.method"="GET" 1493773500 343500\n',
            tracing_span_to_line_data(
                "getAllUsers", 1493773500, 343500, "localhost",
                UUID("7b3bf470-9456-11e8-9eb6-529269fb1459"),
                UUID("0313bafe-9457-11e8-9eb6-529269fb1459"), None, None,
                [("application", "Wavefront"), ("http.method", "GET")],
                None, "defaultSource"))

        # duplicate tags
        self.assertEqual(
            '"getAllUsers" source="localhost" '
            'traceId=7b3bf470-9456-11e8-9eb6-529269fb1459 '
            'spanId=0313bafe-9457-11e8-9eb6-529269fb1459 '
            '"application"="Wavefront" '
            '"http.method"="GET" 1493773500 343500\n',
            tracing_span_to_line_data(
                "getAllUsers", 1493773500, 343500, "localhost",
                UUID("7b3bf470-9456-11e8-9eb6-529269fb1459"),
                UUID("0313bafe-9457-11e8-9eb6-529269fb1459"), None, None,
                [("application", "Wavefront"), ("http.method", "GET"),
                 ("application", "Wavefront")],
                None, "defaultSource"))

        # null tags
        self.assertEqual(
            '"getAllUsers" source="localhost" '
            'traceId=7b3bf470-9456-11e8-9eb6-529269fb1459 '
            'spanId=0313bafe-9457-11e8-9eb6-529269fb1459 '
            '1493773500 343500\n',
            tracing_span_to_line_data(
                "getAllUsers", 1493773500, 343500, "localhost",
                UUID("7b3bf470-9456-11e8-9eb6-529269fb1459"),
                UUID("0313bafe-9457-11e8-9eb6-529269fb1459"),
                None, None, None, None, "defaultSource"))


if __name__ == '__main__':
    # run 'python -m unittest discover' from top-level to run tests
    unittest.main()
