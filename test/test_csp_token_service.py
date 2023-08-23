"""Unit Tests for CSP Token Service.

@author Jerry Belmonte (bjerry@vmware.com)
"""

import unittest
from base64 import b64decode
import uuid
import threading
import time
from unittest.mock import Mock
from unittest.mock import call

import requests

from wavefront_sdk.csp_token_service import CSPServerToServerTokenService


class TestCspTokenService(unittest.TestCase):
    """Test Functions of wavefront_sdk.csp_token_service."""

    def test_refresh_token_oauth(self):
        """Test refresh_token_oauth of CSPServerToServerTokenService."""
        token_service = CSPServerToServerTokenService(
            "https://console.cloud.vmware.com/", 
            csp_app_id="fake-csp-app-id", 
            csp_app_secret="fake-csp-app-secret",
        )
        self.assertIsNone(token_service.refresh_token_oauth())

    def test_refresh_token(self):
        """Test refresh_token of CSPServerToServerTokenService."""
        token_service = CSPServerToServerTokenService(
            "https://console.cloud.vmware.com/", 
            csp_api_token="fake-csp-api-token",
        )
        self.assertIsNone(token_service.refresh_token())

    def test_get_csp_token(self):
        """Test get_csp_token of CSPServerToServerTokenService."""
        # CSP OAuth App ID and App Secret
        token_service = CSPServerToServerTokenService(
            "https://console.cloud.vmware.com/", 
            csp_app_id="fake-csp-app-id", 
            csp_app_secret="fake-csp-app-secret",
        )
        self.assertIsNone(token_service.get_csp_token(auth_type="oauth"))
        # CSP Api Token
        token_service = CSPServerToServerTokenService(
            "https://console.cloud.vmware.com/", 
            csp_api_token="fake-csp-api-token",
        )
        self.assertIsNone(token_service.get_csp_token(auth_type="cspapitoken"))

    def test_encode_csp_credentials(self):
        """Test encode_csp_credentials of CSPServerToServerTokenService."""
        fake_oauth_app_id = "fake-csp-app-id"
        fake_oauth_app_secret = "fake-csp-app-secret"
        token_service = CSPServerToServerTokenService(
            "https://console.cloud.vmware.com/", 
            csp_app_id=fake_oauth_app_id, 
            csp_app_secret=fake_oauth_app_secret,
        )
        self.assertEqual(b64decode(token_service.encode_csp_credentials()).decode("utf-8"),
                         fake_oauth_app_id + ":" + fake_oauth_app_secret)

    def test_get_time_offset(self):
        """Test get_time_offset of CSPServerToServerTokenService."""
        expires_in_short = 30
        time_offset = CSPServerToServerTokenService.get_time_offset(expires_in_short)
        self.assertEqual(time_offset, 0)
        expires_in_long = 680
        time_offset = CSPServerToServerTokenService.get_time_offset(expires_in_long)
        self.assertEqual(time_offset, 500)


if __name__ == '__main__':
    # run 'python -m unittest discover' from top-level to run tests
    unittest.main()
