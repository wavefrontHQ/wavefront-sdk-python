"""Connection Handler class for sending data to a Wavefront proxy.

@author: Hao Song (songhao@vmware.com)
"""

from __future__ import absolute_import

import socket

from . import connection_handler


# pylint: disable=too-many-instance-attributes
class ProxyConnectionHandler(connection_handler.ConnectionHandler):
    """Connection Handler.

    For sending data to a Wavefront proxy listening on a given port.
    """

    # pylint: disable=too-many-arguments
    def __init__(self, address, port, wavefront_sdk_metrics_registry,
                 entity_prefix=None, timeout=None):
        """Construct ProxyConnectionHandler.

        @param address: Proxy Address
        @param port: Proxy Port
        """
        super().__init__()
        self._address = address
        self._port = int(port)
        self.entity_prefix = '' if not entity_prefix else entity_prefix + ''
        self.timeout = timeout
        self.wf_metrics_registry = wavefront_sdk_metrics_registry
        self._write_successes = self.wf_metrics_registry.new_delta_counter(
            self.entity_prefix + 'write.success')
        self._write_errors = self.wf_metrics_registry.new_delta_counter(
            self.entity_prefix + 'write.errors')
        self._reconnecting_socket = None

    def connect(self):
        """Initialize socket and connect to given address:port."""
        self._reconnecting_socket = socket.socket(socket.AF_INET,
                                                  socket.SOCK_STREAM)
        self._reconnecting_socket.settimeout(self.timeout)
        self._reconnecting_socket.connect((self._address, self._port))

    def close(self):
        """Close socket if it's open now."""
        if self._reconnecting_socket:
            self._reconnecting_socket.close()

    def send_data(self, line_data, reconnect=True):
        """Send data via proxy.

        @param line_data: Data to be sent
        @param reconnect: If it's the second time trying to send data
        """
        try:
            if not self._reconnecting_socket:
                self.connect()
            self._reconnecting_socket.sendall(line_data.encode('utf-8'))
            self._write_successes.inc()
        except socket.error as error:
            if reconnect:
                self._reconnecting_socket = None
                # Try to resend
                self.send_data(line_data, reconnect=False)
            else:
                # Second time trying failed
                self._write_errors.inc()
                raise error
