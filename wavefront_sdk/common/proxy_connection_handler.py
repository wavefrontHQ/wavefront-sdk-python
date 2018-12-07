# -*- coding: utf-8 -*-

"""
Connection Handler class for sending data to a Wavefront proxy.

@author: Hao Song (songhao@vmware.com)
"""

from __future__ import absolute_import

import socket
from wavefront_sdk.common.connection_handler import ConnectionHandler


class ProxyConnectionHandler(ConnectionHandler):
    """
    Connection Handler.

    For sending data to a Wavefront proxy listening on a given port.
    """

    def __init__(self, address, port):
        """
        Construct ProxyConnectionHandler.

        @param address: Proxy Address
        @param port: Proxy Port
        """
        ConnectionHandler.__init__(self)
        self._address = address
        self._port = int(port)
        self._reconnecting_socket = None

    def connect(self):
        """Initialize socket and connect to given address:port."""
        self._reconnecting_socket = socket.socket(socket.AF_INET,
                                                  socket.SOCK_STREAM)
        self._reconnecting_socket.connect((self._address, self._port))

    def close(self):
        """Close socket if it's open now."""
        if self._reconnecting_socket:
            self._reconnecting_socket.close()

    def send_data(self, line_data, reconnect=True):
        """
        Send data via proxy.

        @param line_data: Data to be sent
        @param reconnect: If it's the second time trying to send data
        """
        try:
            if not self._reconnecting_socket:
                self.connect()
            self._reconnecting_socket.sendall(line_data.encode('utf-8'))
        except socket.error as error:
            if reconnect:
                self._reconnecting_socket = None
                # Try to resend
                self.send_data(line_data, reconnect=False)
            else:
                # Second time trying failed
                raise error
