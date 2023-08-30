"""Wavefront MultiClient to support Data Ingestion for Multiple Clients.

@author Yogesh Prasad Kurmi (ykurmi@vmware.com)
"""

import logging
import queue
from urllib.parse import urlparse

from wavefront_sdk.auth.csp.csp_token_service import \
    CSP_API_TOKEN_SERVICE_TYPE, CSP_OAUTH_TOKEN_SERVICE_TYPE
from wavefront_sdk.auth.csp.token_service_factory import TokenServiceProvider
from wavefront_sdk.client import WavefrontClient
from wavefront_sdk.multi_clients import WavefrontMultiClient


LOGGER = logging.getLogger('wavefront_sdk.WavefrontClientFactory')


class WavefrontClientFactory:
    """Wavefront client factory.

    Create wavefront direct/proxy data ingestion client.
    """

    PROXY_SCHEME = "proxy"
    HTTP_PROXY_SCHEME = "http"
    DIRECT_DATA_INGESTION_SCHEME = "https"

    def __init__(self):
        """Keep track of initialized clients on instance level."""
        self.clients = []

    # pylint: disable=too-many-arguments,too-many-locals
    def add_client(self, url, max_queue_size=50000, batch_size=10000,
                   flush_interval_seconds=5, enable_internal_metrics=True,
                   queue_impl=queue.Queue,
                   csp_base_url=None, csp_api_token=None,
                   csp_app_id=None, csp_app_secret=None, csp_org_id=None):
        """Create a unique client."""
        # In the CSP case, the user should only pass in the URL,
        # not token@url, but for consistency
        # I think we should preserve this function call.
        server, token_or_service = self.get_server_info_from_endpoint(url)
        if csp_app_id or csp_api_token:
            config = {
                'csp_app_id': csp_app_id,
                'csp_app_secret': csp_app_secret,
                'csp_org_id': csp_org_id,
                'csp_api_token': csp_api_token,
                'base_url': csp_base_url
            }
            services = TokenServiceProvider()
            if csp_app_id and csp_app_secret:
                token_type = CSP_OAUTH_TOKEN_SERVICE_TYPE
                token_or_service = services.get(token_type, **config)
                LOGGER.info("CSP OAuth server to server app credentials for "
                            + "further authentication. For the server %s",
                            csp_base_url)
            elif csp_app_id and not csp_app_secret:
                raise RuntimeError("Both 'csp_app_id' and 'csp_app_secret' "
                                   + "are required.")
            elif csp_api_token:
                token_type = CSP_API_TOKEN_SERVICE_TYPE
                token_or_service = services.get(token_type, **config)
                LOGGER.info("CSP api token for further authentication."
                            + " For the server %s", csp_base_url)

        if self.existing_client(server):
            raise RuntimeError("client with id " + url + " already exists.")

        client = WavefrontClient(
            server=server,
            token=token_or_service,
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
