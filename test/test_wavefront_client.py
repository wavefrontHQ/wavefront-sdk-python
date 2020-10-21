"""Unit Tests for Wavefront Client.

@Yogesh Prasad Kurmi (ykurmi@vmware.com)
"""

import unittest

import wavefront_sdk
from wavefront_sdk.client_factory import WavefrontClientFactory


class WavefrontClient(unittest.TestCase):
    """Test Functions of wavefront_sdk.client_factory."""

    def test_get_server_info_from_endpoint(self):
        """Test get_server_info_from_endpoint of WavefrontClientFactory"""
        direct_base_url = ("https://a87826d5-889d-4b23-98f0-2f3558zd007a"
                           "@wfcluster.wavefront.com")
        server, token = WavefrontClientFactory(
            ).get_server_info_from_endpoint(direct_base_url)
        self.assertEqual(server, "https://wfcluster.wavefront.com")
        self.assertEqual(token, "a87826d5-889d-4b23-98f0-2f3558zd007a")

        proxy_base_url = "proxy://10.112.71.230:2878"
        server, token = WavefrontClientFactory(
            ).get_server_info_from_endpoint(proxy_base_url)
        self.assertEqual(server, "http://10.112.71.230:2878")
        self.assertEqual(token, None)

        http_proxy_base_url = "http://192.114.71.230:2878"
        server, token = WavefrontClientFactory(
            ).get_server_info_from_endpoint(http_proxy_base_url)
        self.assertEqual(server, "http://192.114.71.230:2878")
        self.assertEqual(token, None)

    def test_get_client(self):
        """Test get_client of WavefrontClientFactory"""

        # get_client should return None if there is no client
        client = WavefrontClientFactory().get_client()
        self.assertEqual(client, None)

        # get_client should return instance of WavefrontClient
        # if there is only one client
        direct_base_url = ("https://a87826d5-889d-4b23-98f0-2f3558zd007a"
                           "@wfcluster.wavefront.com")
        multi_client_factory = WavefrontClientFactory()
        multi_client_factory.add_client(direct_base_url)
        self.assertTrue(isinstance(multi_client_factory.get_client(),
                                   wavefront_sdk.client.WavefrontClient))

        # get_client should return instance of WavefrontMultiClient
        # if there is more than one client
        proxy_base_url = "proxy://192.114.71.230:2878"
        multi_client_factory.add_client(proxy_base_url)
        self.assertTrue(isinstance(multi_client_factory.get_client(),
                                   wavefront_sdk.multi_clients
                                   .WavefrontMultiClient))

    def test_existing_client(self):
        """Test existing_client of WavefrontClientFactory"""
        server = "http://192.114.71.230:2878"

        # existing_client should return False if client does not exists
        self.assertFalse(WavefrontClientFactory().existing_client(server))


if __name__ == '__main__':
    # run 'python -m unittest discover' from top-level to run tests
    unittest.main()
