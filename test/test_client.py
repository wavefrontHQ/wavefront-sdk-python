"""Unit Tests for Wavefront Python SDK.

@author Hao Song (songhao@vmware.com)
"""

import unittest
import uuid

from wavefront_sdk.client import WavefrontClient
from wavefront_sdk.entities.tracing.span_log import SpanLog


class TestUtils(unittest.TestCase):
    """Test direct ingestion."""

    def setUp(self):
        self._sender = WavefrontClient(
            'no_server',
            'no_token',
            flush_interval_seconds=86400,  # turn off auto flushing
            enable_internal_metrics=False)
        self._spans_log_buffer = self._sender._spans_log_buffer
        self._tracing_spans_buffer = self._sender._tracing_spans_buffer

    def test_send_span_with_span_logs(self):

        # Call code under test
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

        # show long diffs
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

        # Call code under test
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

        # Show long diffs
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


if __name__ == '__main__':
    # run 'python -m unittest discover' from top-level to run tests
    unittest.main()
