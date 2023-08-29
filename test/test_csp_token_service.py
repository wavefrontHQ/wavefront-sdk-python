"""Unit Tests for CSP Token Service.

@author Jerry Belmonte (bjerry@vmware.com)
"""

import unittest
from unittest.mock import Mock, patch, ANY

from requests.exceptions import HTTPError
import requests

from wavefront_sdk.auth.csp.token_service_factory import TokenServiceProvider
from wavefront_sdk.auth.csp.token_service import CSPTokenService, CSPAPIToken, CSPClientCredentials


class TestCspTokenService(unittest.TestCase):
    """Tests for wavefront_sdk.csp_token_service."""

    def setUp(self):
        self._services = TokenServiceProvider()
        self._response = Mock()
        self._response.status_code = 200

    # CSPUserTokenService tests
    def test_csp_user_token_service_builder(self):
        """Test CSP User Token Service Builder."""
        config = {
            'csp_app_id': None,
            'csp_app_secret': None,
            'csp_org_id': None,
            'csp_api_token': 'fake-token',
            'base_url': 'https://cspbaseurl.vmware.com/'
        }
        token_service = self._services.get('TOKEN', **config)
        self.assertTrue(isinstance(token_service, CSPTokenService))
        self.assertEqual('TOKEN', token_service.get_type())

    def test_csp_api_successful_response(self):
        """Test successful CSP api token response"""
        self._response.json.return_value = {
            "access_token": "abc123",
            "expires_in": 600,
            "id_token": "abc",
            "refresh_token": "def",
            "scope": "aoa:directDataIngestion",
            "token_type": "bearer"
        }
        config = {
                'base_url': 'https://cspbaseurl.vmware.com/',
                'csp_api_token': 'fake-token'
        }

        with patch.object(requests, 'post', return_value=self._response) as mock_post:
            token_service = self._services.get('TOKEN', **config)
            actual_access_token = token_service.get_csp_access_token()
            mock_post.assert_called_once_with(ANY, {"api_token": "fake-token"}, headers=ANY, timeout=ANY)

        self.assertIsNotNone(actual_access_token)
        self.assertEqual(actual_access_token, "abc123")

    def test_csp_api_unsuccessful_response(self):
        """Test unsuccessful CSP api token response"""
        response = {
            "requestId": "abc123",
            "message": "invalid_grant: Invalid refresh token: xxxx...token",
            "metadata": None,
            "statusCode": 400
        }
        config = {
            'base_url': 'https://cspbaseurl.vmware.com/',
            'csp_api_token': 'fake-token'
        }

        token_service = self._services.get('TOKEN', **config)

        with patch.object(requests, 'post', return_value=response) as mock:
            actual_access_token = token_service.get_csp_access_token()

        mock.assert_called_once_with(ANY, {"api_token": "fake-token"}, headers=ANY, timeout=ANY)
        self.assertIsNone(actual_access_token)
        self.assertRaises(HTTPError)

    # CSPServerToServerTokenService tests
    def test_csp_server_to_server_token_service_builder(self):
        """Test CSP Server to Server Token Service Builder."""
        config = {
            'csp_app_id': 'fake-id',
            'csp_app_secret': 'fake-secret',
            'csp_org_id': None,
            'csp_api_token': None,
            'base_url': 'https://cspbaseurl.vmware.com'
        }
        token_service = self._services.get('OAUTH', **config)
        self.assertTrue(isinstance(token_service, CSPTokenService))
        self.assertEqual('OAUTH', token_service.get_type())

    def test_oauth_app_successful_response(self):
        """Test successful CSP OAuth app response"""
        response = {
            "access_token": "abc123",
            "expires_in": 60,
            "id_token": None,
            "refresh_token": None,
            "scope": "csp:org_member aoa/* aoa:*",
            "token_type": "bearer"
        }
        config = {
            'base_url': 'https://cspbaseurl.vmware.com',
            'csp_app_id': 'fake-id',
            'csp_app_secret': 'fake-secret'
        }

        token_service = self._services.get('OAUTH', **config)

        with patch.object(requests, 'post', return_value=response) as mock:
            actual_access_token = token_service.get_csp_access_token()

        mock.assert_called_once_with(ANY, {"grant_type": "client_credentials"}, headers=ANY, timeout=ANY)
        self.assertIsNotNone(actual_access_token)
        self.assertEqual(actual_access_token, "abc123")

    def test_oauth_app_unsuccessful_response(self):
        """Test unsuccessful CSP OAuth app response"""
        response = {
            "requestId": "abc123",
            "message": "Unauthorized: Bad credentials",
            "metadata": None,
            "statusCode": 401
        }
        config = {
            'base_url': 'https://cspbaseurl.vmware.com',
            'csp_app_id': 'fake-id',
            'csp_app_secret': 'fake-secret'
        }

        token_service = self._services.get('OAUTH', **config)

        with patch.object(requests, 'post', return_value=response) as mock:
            actual_access_token = token_service.get_csp_access_token()

        mock.assert_called_once_with(ANY, {"grant_type": "client_credentials"}, headers=ANY, timeout=ANY)
        self.assertIsNone(actual_access_token)
        self.assertRaises(HTTPError)


if __name__ == '__main__':
    # run 'python -m unittest discover' from top-level to run tests
    unittest.main()
