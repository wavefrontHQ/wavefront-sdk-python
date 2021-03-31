"""Wavefront MultiClient to support Data Ingestion for Multiple Clients.

@author Yogesh Prasad Kurmi (ykurmi@vmware.com)
"""

from urllib.parse import urlparse

from wavefront_sdk.client import WavefrontClient
from wavefront_sdk.multi_clients import WavefrontMultiClient


# pylint: disable=W0232  # Class has no __init__ method
class WavefrontClientFactory:
    """Wavefront client factory.

    Create wavefront direct/proxy data ingestion client.
    """

    PROXY_SCHEME = "proxy"
    HTTP_PROXY_SCHEME = "http"
    DIRECT_DATA_INGESTION_SCHEME = "https"
    clients = []

    # pylint: disable=too-many-arguments
    def add_client(self, url, max_queue_size=50000,
                   batch_size=10000,
                   flush_interval_seconds=5,
                   enable_internal_metrics=True):
        """Create a unique client."""
        server, token = self.get_server_info_from_endpoint(url)

        if self.existing_client(server):
            raise RuntimeError("client with id " + url + " already exists.")
        self.clients.append(WavefrontClient(server, token, max_queue_size,
                                            batch_size, flush_interval_seconds,
                                            enable_internal_metrics))

    def get_server_info_from_endpoint(self, url):
        """Get Server and API token from the end point.

        Return None for token if URL belongs to proxy.
        """
        base_url = urlparse(url)
        scheme = base_url.scheme
        if scheme == self.DIRECT_DATA_INGESTION_SCHEME:
            server = '{}://{}'.format(self.DIRECT_DATA_INGESTION_SCHEME,
                                      base_url.hostname)
            token = base_url.username
        elif scheme in (self.PROXY_SCHEME, self.HTTP_PROXY_SCHEME):
            server = '{}://{}:{}'.format(self.HTTP_PROXY_SCHEME,
                                         base_url.hostname, base_url.port)
            token = None
        else:
            raise RuntimeError("Unknown scheme specified while attempting to"
                               " create a client " + str(scheme))
        return server, token

    def existing_client(self, server):
        """Check if client exists."""
        for client in self.clients:
            if client.server == server:
                return True
        return False

    def get_client(self):
        """Get client.

        Return
          None, if there is no client
          Client, if there is only one client
          Multi-Client, if there are multiple clients

        """
        data = None
        if len(self.clients) == 1:
            data = self.clients[0]
        elif len(self.clients) > 1:
            wf_multi_clients = WavefrontMultiClient()
            for client in self.clients:
                wf_multi_clients.with_wavefront_sender(client)
            data = wf_multi_clients
        return data
