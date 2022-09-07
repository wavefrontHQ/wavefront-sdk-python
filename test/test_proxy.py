"""Unit Tests for Wavefront Python SDK.

@author Travis Keep (travisk@vmware.com)
"""

import unittest
import uuid
from unittest.mock import Mock
from unittest.mock import call

from wavefront_sdk.common.proxy_connection_handler import (
    ProxyConnectionHandler)
from wavefront_sdk.entities.tracing.span_log import SpanLog
from wavefront_sdk.proxy import WavefrontProxyClient


class TestUtils(unittest.TestCase):
    """Test proxy ingestion."""

    def setUp(self):
        self._sender = WavefrontProxyClient(
            'no_host',
            None,
            None,
            None,
            enable_internal_metrics=False)
        self._sender._tracing_proxy_connection_handler = (
            Mock(spec=ProxyConnectionHandler))
        self._tracing = self._sender._tracing_proxy_connection_handler

    def test_send_span_with_span_logs(self):

        self._sender.send_span(
            'spanName',
            1635123456789,
            12345,
            'localhost',
            uuid.UUID('11111111-2222-3333-4444-555555555555'),
            uuid.UUID('11111111-0000-0001-0002-123456789012'),
            [uuid.UUID('55555555-4444-3333-2222-111111111111')],
            None,
            [('application', 'Wavefront'), ('service', 'test-spans')],
            [SpanLog(
                 1635123789456000,
                 {"FooLogKey": "FooLogValue"})])

        expected_span_line = (
            '"spanName" source="localhost" '
            'traceId=11111111-2222-3333-4444-555555555555 '
            'spanId=11111111-0000-0001-0002-123456789012 '
            'parent=55555555-4444-3333-2222-111111111111 '
            '"application"="Wavefront" "service"="test-spans" '
            '"_spanLogs"="true" 1635123456789 12345\n')
        expected_span_log_line = (
            '{"traceId": "11111111-2222-3333-4444-555555555555", '
            '"spanId": "11111111-0000-0001-0002-123456789012", '
            '"logs": [{"timestamp": 1635123789456000, '
            '"fields": {"FooLogKey": "FooLogValue"}}], '
            '"span": "\\"spanName\\" source=\\"localhost\\" '
            'traceId=11111111-2222-3333-4444-555555555555 '
            'spanId=11111111-0000-0001-0002-123456789012 '
            'parent=55555555-4444-3333-2222-111111111111 '
            '\\"application\\"=\\"Wavefront\\" \\"service\\"=\\"test-spans\\" '
            '\\"_spanLogs\\"=\\"true\\" 1635123456789 12345\\n"}\n')
        self._tracing.send_data.assert_has_calls(
            [call(expected_span_line), call(expected_span_log_line)])
        self.assertEqual(2, self._tracing.send_data.call_count)

    def test_send_span_without_span_logs(self):

        self._sender.send_span(
            'spanName',
            1635123456789,
            12345,
            'localhost',
            uuid.UUID('11111111-2222-3333-4444-555555555555'),
            uuid.UUID('11111111-0000-0001-0002-123456789012'),
            [uuid.UUID('55555555-4444-3333-2222-111111111111')],
            None,
            [('application', 'Wavefront'), ('service', 'test-spans')],
            [])

        expected_span_line = (
            '"spanName" source="localhost" '
            'traceId=11111111-2222-3333-4444-555555555555 '
            'spanId=11111111-0000-0001-0002-123456789012 '
            'parent=55555555-4444-3333-2222-111111111111 '
            '"application"="Wavefront" "service"="test-spans" '
            '1635123456789 12345\n')
        self._tracing.send_data.assert_called_once_with(expected_span_line)


if __name__ == '__main__':
    # run 'python -m unittest discover' from top-level to run tests
    unittest.main()
