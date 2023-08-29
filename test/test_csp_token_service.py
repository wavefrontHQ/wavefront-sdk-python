"""Unit Tests for CSP Token Service.

@author Jerry Belmonte (bjerry@vmware.com)
"""

import unittest
from uuid import uuid4
from unittest.mock import Mock, patch, ANY

from requests.exceptions import HTTPError
import requests

from wavefront_sdk.auth.csp.token_service_factory import TokenServiceProvider


class TestCspTokenService(unittest.TestCase):
    """Tests for wavefront_sdk.csp_token_service."""

    def setUp(self):
        self._services = TokenServiceProvider()

    # CSPTokenService tests
    def test_csp_api_successful_response(self):
        """Test successful CSP api token response"""
        expected_access_token = uuid4()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "access_token": expected_access_token,
            "expires_in": 600,
            "id_token": "abc",
            "refresh_token": "def",
            "scope": "aoa:directDataIngestion",
            "token_type": "bearer"
        }

        token_service = self._services.get('TOKEN', **{
            'base_url': 'https://cspbaseurl.vmware.com/',
            'csp_api_token': 'fake-token'
        })
        with patch.object(requests, 'post', return_value=mock_response) as mock:
            actual_access_token = token_service.get_csp_access_token()

        mock.assert_called_once_with(ANY, {"api_token": "fake-token"}, headers=ANY, timeout=ANY)
        self.assertIsNotNone(actual_access_token)
        self.assertEqual(actual_access_token, expected_access_token)

    def test_csp_api_unsuccessful_response(self):
        """Test unsuccessful CSP api token response"""
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.json.return_value = {
            "uri": "string",
            "requestId": "string",
            "message": "string",
            "cspError": {
                "moduleCode": "CSP_ONBOARD_TOOL_TEST",
                "metadata": {
                    "additionalProp1": {},
                    "additionalProp2": {},
                    "additionalProp3": {}
                },
                "errorMessageCode": "string",
                "numericModuleCode": 0,
                "errorCode": 0
            },
            "causes": [
                "string"
            ],
            "statusCode": 0
        }

        token_service = self._services.get('TOKEN', **{
            'base_url': 'https://cspbaseurl.vmware.com/',
            'csp_api_token': 'fake-token'
        })

        with patch.object(requests, 'post', return_value=mock_response) as mock:
            actual_access_token = token_service.get_access_token()

        mock.assert_called_once_with(ANY, {"api_token": "fake-token"}, headers=ANY, timeout=ANY)
        self.assertIsNone(actual_access_token)
        self.assertRaises(HTTPError)

    # CSPServerToServerTokenService tests
    def test_oauth_app_successful_response(self):
        """Test successful CSP OAuth app response"""
        expected_access_token = uuid4()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "access_token": expected_access_token,
            "expires_in": 600,
            "id_token": "abc",
            "refresh_token": "def",
            "scope": "aoa:directDataIngestion",
            "token_type": "bearer"
        }

        token_service = self._services.get('OAUTH', **{
            'base_url': 'https://cspbaseurl.vmware.com',
            'csp_app_id': 'fake-id',
            'csp_app_secret': 'fake-secret'
        })

        with patch.object(requests, 'post', return_value=mock_response) as mock:
            actual_access_token = token_service.get_csp_access_token()

        mock.assert_called_once_with(ANY, {"grant_type": "client_credentials"}, headers=ANY, timeout=ANY)
        self.assertIsNotNone(actual_access_token)
        self.assertEqual(actual_access_token, expected_access_token)

    def test_oauth_app_unsuccessful_response(self):
        """Test unsuccessful CSP OAuth app response"""
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.json.return_value = {
            "uri": "string",
            "requestId": "string",
            "message": "string",
            "cspError": {
                "moduleCode": "CSP_ONBOARD_TOOL_TEST",
                "metadata": {
                    "additionalProp1": {},
                    "additionalProp2": {},
                    "additionalProp3": {}
                },
                "errorMessageCode": "string",
                "numericModuleCode": 0,
                "errorCode": 0
            },
            "causes": [
                "string"
            ],
            "statusCode": 0
        }

        token_service = self._services.get('OAUTH', **{
            'base_url': 'https://cspbaseurl.vmware.com',
            'csp_app_id': 'fake-id',
            'csp_app_secret': 'fake-secret'
        })

        with patch.object(requests, 'post', return_value=mock_response) as mock:
            actual_access_token = token_service.get_csp_access_token()

        mock.assert_called_once_with(ANY, {"grant_type": "client_credentials"}, headers=ANY, timeout=ANY)
        self.assertIsNone(actual_access_token)
        self.assertRaises(HTTPError)


if __name__ == '__main__':
    # run 'python -m unittest discover' from top-level to run tests
    unittest.main()
