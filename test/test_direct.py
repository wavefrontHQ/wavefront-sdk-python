"""Unit Tests for Wavefront Python SDK.

@author Travis Keep (travisk@vmware.com)
"""

import unittest
import uuid
from unittest.mock import ANY
from unittest.mock import Mock
from unittest.mock import patch

import requests

from wavefront_sdk.direct import WavefrontDirectClient
from wavefront_sdk.entities.tracing.span_log import SpanLog


class TestUtils(unittest.TestCase):
    """Test direct ingestion."""

    def setUp(self):
        self._sender = WavefrontDirectClient(
            'no_server',
            'no_token',
            flush_interval_seconds=86400,  # turn off auto flushing
            enable_internal_metrics=False)
        self._spans_log_buffer = self._sender._spans_log_buffer
        self._tracing_spans_buffer = self._sender._tracing_spans_buffer
        self._response = Mock()
        self._response.status_code = 200

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

        self.maxDiff = None

        # Verify span logs correctly emitted
        actual_line = self._spans_log_buffer.get()
        expected_line = (
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
        self.assertEqual(expected_line, actual_line)

        # Verify span correctly emitted
        actual_line = self._tracing_spans_buffer.get()
        expected_line = (
            '"spanName" source="localhost" '
            'traceId=11111111-2222-3333-4444-555555555555 '
            'spanId=11111111-0000-0001-0002-123456789012 '
            'parent=55555555-4444-3333-2222-111111111111 '
            '"application"="Wavefront" "service"="test-spans" '
            '"_spanLogs"="true" 1635123456789 12345\n')
        self.assertEqual(expected_line, actual_line)

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

        self.maxDiff = None

        # Assert no span logs emitted
        self.assertTrue(self._spans_log_buffer.empty())

        # Verify span correctly emitted
        actual_line = self._tracing_spans_buffer.get()
        expected_line = (
            '"spanName" source="localhost" '
            'traceId=11111111-2222-3333-4444-555555555555 '
            'spanId=11111111-0000-0001-0002-123456789012 '
            'parent=55555555-4444-3333-2222-111111111111 '
            '"application"="Wavefront" "service"="test-spans" '
            '1635123456789 12345\n')
        self.assertEqual(expected_line, actual_line)

    def test_report_event(self):

        with patch.object(
                requests, 'post', return_value=self._response) as mock_post:
            self._sender._report(
                '', self._sender.WAVEFRONT_EVENT_FORMAT, '', Mock())

        mock_post.assert_called_once_with(
            ANY,
            params=None,
            headers=ANY,
            data=ANY,
            timeout=self._sender.HTTP_TIMEOUT)

    def test_report_non_event(self):

        with patch.object(
                requests, 'post', return_value=self._response) as mock_post:
            self._sender._report('', 'metric', '', Mock())

        mock_post.assert_called_once_with(
            ANY,
            params=ANY,
            headers=ANY,
            data=ANY,
            timeout=self._sender.HTTP_TIMEOUT)


if __name__ == '__main__':
    # run 'python -m unittest discover' from top-level to run tests
    unittest.main()
