"""Wavefront MultiClient to support Data Ingestion for Multiple Clients.

@author Yogesh Prasad Kurmi (ykurmi@vmware.com)
"""

import queue
from urllib.parse import urlparse

from wavefront_sdk.client import WavefrontClient
from wavefront_sdk.multi_clients import WavefrontMultiClient

from wavefront_sdk.csp_token_service import CSPServerToServerTokenService

class WavefrontClientFactory:
    """Wavefront client factory.

    Create wavefront direct/proxy data ingestion client.
    """

    PROXY_SCHEME = "proxy"
    HTTP_PROXY_SCHEME = "http"
    DIRECT_DATA_INGESTION_SCHEME = "https"
    DEFAULT_CSP_BASE_URL = "https://console.cloud.vmware.com/"

    def __init__(self):
        """Keep track of initialized clients on instance level."""
        self.clients = []

    # pylint: disable=too-many-arguments
    def add_client(self, url, max_queue_size=50000, batch_size=10000,
                   flush_interval_seconds=5, enable_internal_metrics=True,
                   queue_impl=queue.Queue,
                   csp_base_url=DEFAULT_CSP_BASE_URL,
                   csp_client_id=None,
                   csp_client_secret=None):
        """Create a unique client."""
        if csp_client_id is not None and csp_client_secret is not None:
            # In the CSP case, the user should only pass in the URL,
            # not token@url, but for consistency
            # I think we should preserve this function call.
            server, _ = self.get_server_info_from_endpoint(url)
            token_or_token_service = CSPServerToServerTokenService(
                csp_base_url,
                csp_client_id,
                csp_client_secret,
            )
        else:
            server, token_or_token_service = self.get_server_info_from_endpoint(url)

        if self.existing_client(server):
            raise RuntimeError("client with id " + url + " already exists.")

        client = WavefrontClient(
            server=server,
            token=token_or_token_service,
            max_queue_size=max_queue_size,
            batch_size=batch_size,
            flush_interval_seconds=flush_interval_seconds,
            enable_internal_metrics=enable_internal_metrics,
            queue_impl=queue_impl,
        )
        self.clients.append(client)

    def get_server_info_from_endpoint(self, url):
        """Get Server and API token from the end point.

        Return None for token if URL belongs to proxy.
        """
        base_url = urlparse(url)
        scheme = base_url.scheme
        if scheme == self.DIRECT_DATA_INGESTION_SCHEME:
            server = (f'{self.DIRECT_DATA_INGESTION_SCHEME}://'
                      f'{base_url.hostname}')
            token = base_url.username
        elif scheme in (self.PROXY_SCHEME, self.HTTP_PROXY_SCHEME):
            server = (f'{self.HTTP_PROXY_SCHEME}://'
                      f'{base_url.hostname}:{base_url.port}')
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
