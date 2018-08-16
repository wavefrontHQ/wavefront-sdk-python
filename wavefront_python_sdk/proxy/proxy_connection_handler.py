from __future__ import absolute_import, division, print_function

from wavefront_python_sdk.common.connection_handler import IConnectionHandler
import socket


class ProxyConnectionHandler(IConnectionHandler):
    def __init__(self, address, port):
        IConnectionHandler.__init__(self)
        self._address = address
        self._port = int(port)
        self._reconnecting_socket = None

    def connect(self):
        self._reconnecting_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._reconnecting_socket.connect((self._address, self._port))

    def close(self):
        if self._reconnecting_socket:
            self._reconnecting_socket.close()

    def send_data(self, line_data, reconnect=True):
        try:
            if not self._reconnecting_socket:
                self.connect()
            self._reconnecting_socket.sendall(line_data.encode())
        except socket.error as e:
            if reconnect:
                self._reconnecting_socket = None
                self.send_data(line_data, reconnect=False)
            else:
                raise e
        except Exception as e:
            raise e
