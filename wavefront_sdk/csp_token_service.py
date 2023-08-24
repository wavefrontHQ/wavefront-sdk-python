"""Wavefront CSP Token Service to support CSP authentication.

@author Jerry Belmonte (bjerry@vmware.com)
"""

import logging
from base64 import b64encode
import time

from requests.exceptions import HTTPError
import requests

LOGGER = logging.getLogger('wavefront_sdk.CSPServerToServerTokenService')

class CSPAuthorizeResponse:
    """CSP Authorize Response."""
    access_token: str
    expires_in: int
    id_token: str
    refresh_token: str
    scope: str
    token_type: str

    def set_auth_response(self, response):
        """Sets the CSP auth response.

        @param response: The json-encoded response.
        """
        self.access_token = response.get("access_token")
        self.expires_in = response.get("expires_in")
        self.id_token = response.get("id_token")
        self.refresh_token = response.get("refresh_token")
        self.scope = response.get("scope")
        self.token_type = response.get("token_type")

class CSPTokenService:
    """Service that gets access tokens via CSP API token."""

    # The end-point for exchanging organization scoped API-tokens only
    oauth_path = "/csp/gateway/am/api/auth/api-tokens/authorize"

    def __init__(self, csp_base_url, csp_api_token):
        """Construct CSPTokenService.

        @param csp_base_url: CSP console URL.
        @param csp_api_token: CSP Api token.
        """
        self._csp_base_url = csp_base_url
        self._csp_api_token = csp_api_token
        self._csp_access_token = None
        self._token_expiration_time = 0
        self._csp_response = CSPAuthorizeResponse()

    def _get_request_url(self):
        if str(self._csp_base_url).endswith("/"):
            return str(self._csp_base_url).removesuffix("/") + CSPTokenService.oauth_path
        return self._csp_base_url + CSPTokenService.oauth_path

    def get_access_token(self):
        """Gets the access token."""
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        data = {"api_token": f"{self._csp_api_token}"}
        try:
            response = requests.post(self._get_request_url(), data, headers=headers, timeout=5)
            if response.status_code == 200:
                self._csp_response.set_auth_response(response.json())
                self._csp_access_token = self._csp_response.access_token
                self._token_expiration_time = time.time() + self._csp_response.expires_in
                LOGGER.info("CSP authentication succeeded, access token expires in %d seconds.",
                            self._csp_response.expires_in)
                return self._csp_access_token
            LOGGER.error("CSP authentication failed with status code: %d", response.status_code)
            response.raise_for_status()
        except HTTPError:
            LOGGER.error("CSP authentication failed: http error")
        except ConnectionError:
            LOGGER.error("CSP authentication failed: connection error")
        return None


class CSPServerToServerTokenService:
    """Server to server service that gets access tokens via CSP OAuth."""

    oauth_path = "/csp/gateway/am/api/auth/authorize"

    def __init__(self, csp_base_url, csp_app_id, csp_app_secret):
        """Construct CSPServerToServerTokenService.

        @param csp_base_url: CSP console URL.
        @param csp_app_id: CSP OAuth server to server app id.
        @param csp_app_secret: CSP OAuth server to server app secret.
        """
        self._csp_base_url = csp_base_url
        self._csp_app_id = csp_app_id
        self._csp_app_secret = csp_app_secret
        self._csp_access_token = None
        self._token_expiration_time = 0
        self._csp_response = CSPAuthorizeResponse()

    def _encode_csp_credentials(self):
        csp_credentials = self._csp_app_id + ":" + self._csp_app_secret
        return b64encode((csp_credentials).encode("utf-8")).decode("utf-8")

    def _get_auth_header_value(self):
        return "Basic " + self._encode_csp_credentials()

    def _get_request_url(self):
        if self._csp_base_url.endswith("/"):
            return self._csp_base_url.removesuffix("/") + CSPServerToServerTokenService.oauth_path
        return self._csp_base_url + CSPServerToServerTokenService.oauth_path

    def get_access_token(self):
        """Gets the access token."""
        headers = {"Authorization": self._get_auth_header_value(),
                   "Content-Type": "application/x-www-form-urlencoded"}
        data = {"grant_type": "client_credentials"}
        try:
            response = requests.post(self._get_request_url(), data, headers=headers, timeout=5)
            if response.status_code == 200:
                self._csp_response.set_auth_response(response.json())
                self._csp_access_token = self._csp_response.access_token
                self._token_expiration_time = time.time() + self._csp_response.expires_in
                LOGGER.info("CSP authentication succeeded, access token expires in %d seconds.",
                            self._csp_response.expires_in)
                return self._csp_access_token
            else:
                LOGGER.error("CSP authentication failed with status code: %d", response.status_code)
                response.raise_for_status()
        except HTTPError:
            LOGGER.error("CSP authentication failed: http error")
        except ConnectionError:
            LOGGER.error("CSP authentication failed: connection error")
        return None

    def get_time_offset(self, expires_in: int):
        """Returns the calculated time offset.

        Calculates the time offset for scheduling regular requests to a CSP
        based on the expiration time of a CSP access token.
        If the access token expiration time is less than 10 minutes,
        schedule requests 30 seconds before it expires.
        if the access token expiration time is 10 minutes or more,
        schedule requests 3 minutes before it expires.

        @param expires_in: The expiration time of the CSP access token in seconds.
        """
        if expires_in < 600:
            return expires_in - 30
        return expires_in - 180
