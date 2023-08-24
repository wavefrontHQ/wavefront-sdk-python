"""Wavefront CSP Token Service to support CSP authentication.

@author Jerry Belmonte (bjerry@vmware.com)
"""

import logging
import re
from base64 import b64encode
import time

from requests.exceptions import HTTPError, Timeout
import requests

LOGGER = logging.getLogger('wavefront_sdk.CSPServerToServerTokenService')

class CSPAuthorizeResponse:
    """CSP Authorize Response."""
    access_token: str
    expires_in: int
    scope: str

    def set_auth_response(self, response):
        """Sets the CSP auth response.

        @param response: The json-encoded response.
        """
        self.access_token = response.get("access_token")
        self.expires_in = response.get("expires_in")
        self.scope = response.get("scope")

    def get_time_offset(self):
        """Returns the calculated time offset.

        Calculates the time offset for scheduling regular requests to a CSP
        based on the expiration time of a CSP access token.
        If the access token expiration time is less than 10 minutes,
        schedule requests 30 seconds before it expires.
        if the access token expiration time is 10 minutes or more,
        schedule requests 3 minutes before it expires.

        @param expires_in: The expiration time of the CSP access token in seconds.
        """
        if self.expires_in < 600:
            return self.expires_in - 30
        return self.expires_in - 180

    def has_direct_inject_scope(self):
        allowed_scopes = ["ALL_PERMISSIONS", "aoa:directDataIngestion", "aoa:*", "aoa/*"]
        r = re.compile('ALL_PERMISSIONS|aoa:directDataIngestion|aoa:*|aoa/*')
        return any(r.match(scope) for scope in allowed_scopes)


class CSPTokenService:
    """Service that gets access tokens via CSP API token."""

    # The end-point for exchanging organization scoped API-tokens only
    oauth_path = "/csp/gateway/am/api/auth/api-tokens/authorize"
    timeout_seconds = 30

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
            response = requests.post(self._get_request_url(), data, headers=headers,
                                     timeout=CSPTokenService.timeout_seconds)
            if response.status_code == 200:
                self._csp_response.set_auth_response(response.json())
                self._csp_access_token = self._csp_response.access_token
                self._token_expiration_time = time.time() + self._csp_response.get_time_offset()
                LOGGER.info("CSP authentication succeeded, access token expires in %d seconds.",
                            self._csp_response.expires_in)
                return self._csp_access_token
            LOGGER.error("CSP authentication failed with status code: %d", response.status_code)
            response.raise_for_status()
        except HTTPError:
            LOGGER.error("CSP authentication failed: http error")
        except ConnectionError:
            LOGGER.error("CSP authentication failed: connection error")
        except Timeout:
            LOGGER.error("CSP authentication failed: request url %s timed out", self._get_request_url())
        return None

    def get_csp_access_token(self):
        if not self._csp_access_token or time.time() >= self._token_expiration_time:
            return self.get_access_token()
        return self._csp_access_token

class CSPServerToServerTokenService:
    """Server to server service that gets access tokens via CSP OAuth."""

    oauth_path = "/csp/gateway/am/api/auth/authorize"
    timeout_seconds = 30

    def __init__(self, csp_base_url, csp_app_id, csp_app_secret, csp_org_id=None):
        """Construct CSPServerToServerTokenService.

        @param csp_base_url: CSP console URL.
        @param csp_app_id: CSP OAuth server to server app id.
        @param csp_app_secret: CSP OAuth server to server app secret.
        """
        self._csp_base_url = csp_base_url
        self._csp_app_id = csp_app_id
        self._csp_app_secret = csp_app_secret
        self._csp_org_id = csp_org_id
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
        data = {"grant_type": "client_credentials",
                "orgId": self._csp_org_id}
        try:
            response = requests.post(self._get_request_url(), data, headers=headers,
                                     timeout=CSPServerToServerTokenService.timeout_seconds)
            if response.status_code == 200:
                self._csp_response.set_auth_response(response.json())
                if not self._csp_response.has_direct_inject_scope():
                    LOGGER.error("The CSP response did not find any scope matching 'ALL_PERMISSIONS' or 'aoa/*' or 'aoa:*' 'aoa:directDataIngestion' which is required for Wavefront direct ingestion.")
                self._csp_access_token = self._csp_response.access_token
                self._token_expiration_time = time.time() + self._csp_response.get_time_offset()
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
        except Timeout:
            LOGGER.error("CSP authentication failed: request url: %s timed out", self._get_request_url())
        return None

    def get_csp_access_token(self):
        if not self._csp_access_token or time.time() >= self._token_expiration_time:
            return self.get_access_token()
        return self._csp_access_token
