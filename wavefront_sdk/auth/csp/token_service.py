"""CSP Token Service.

@author Jerry Belmonte (bjerry@vmware.com)
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from base64 import b64encode
from time import time
from requests import post
from requests.exceptions import HTTPError, Timeout
from .authorize_response import AuthorizeResponse


LOGGER = logging.getLogger('wavefront_sdk.auth.csp.TokenService')
CSP_REQUEST_TIMEOUT_SEC = 30


class TokenService(ABC):
    """Service that gets access tokens."""
    @abstractmethod
    def get_token(self) -> str:
        pass

    @abstractmethod
    def get_type(self) -> str:
        pass


@dataclass(frozen=True)
class APIServerURL:
    base_url: str
    auth_path: str

    def get_server_url(self):
        if self.base_url.endswith('/'):
            return self.base_url.removesuffix('/') + self.auth_path
        return self.base_url + self.auth_path


@dataclass(frozen=True)
class CSPAPIToken(APIServerURL):
    token: str

    def get_data(self):
        return {'api_token': self.token}

    def get_headers(self):
        return {'Content-Type': 'application/x-www-form-urlencoded'}


@dataclass(frozen=True)
class CSPClientCredentials(APIServerURL):
    client_id: str
    client_secret: str
    org_id: str = ''

    def get_data(self):
        data = {'grant_type': 'client_credentials'}
        if self.org_id:
            data['orgId'] = self.org_id
        return data

    def encode_csp_credentials(self):
        csp_credentials = self.client_id + ":" + self.client_secret
        return b64encode(csp_credentials.encode("utf-8")).decode("utf-8")

    def get_headers(self):
        return {'Authorization': f'Basic {self.encode_csp_credentials()}',
                'Content-Type': 'application/x-www-form-urlencoded'}


class CSPTokenService(TokenService):
    """Service that gets access tokens via CSP API token."""
    def __init__(self, csp_api_token: CSPAPIToken):
        """Construct CSPTokenService.

        @param csp_api_token: CSP API Token.
        """
        self._csp_api_token = csp_api_token
        self._csp_type = 'TOKEN'
        self._csp_access_token = None
        self._token_expiration_time = 0
        self._csp_response = AuthorizeResponse()

    def get_type(self):
        return self._csp_type

    def get_token(self):
        """Gets the access token."""
        try:
            response = post(self._csp_api_token.get_server_url(),
                            data=self._csp_api_token.get_data(),
                            headers=self._csp_api_token.get_headers(),
                            timeout=CSP_REQUEST_TIMEOUT_SEC)
            data = response.json()
            if response.status_code == 200:
                self._csp_response.set_auth_response(data)
                if not self._csp_response.has_direct_inject_scope():
                    LOGGER.error("The CSP response did not find any scope matching "
                                 + "('aoa:directDataIngestion' or 'aoa:*' or 'aoa/*' or 'ALL_PERMISSIONS')"
                                 + ", which is required for Wavefront direct ingestion.")
                self._csp_access_token = self._csp_response.access_token
                self._token_expiration_time = time() + self._csp_response.get_time_offset()
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
            LOGGER.error("CSP authentication failed: request url %s timed out",
                         self._csp_api_token.get_server_url())
        return None

    def get_csp_access_token(self):
        if not self._csp_access_token or time() >= self._token_expiration_time:
            return self.get_token()
        return self._csp_access_token


class CSPServerToServerTokenService:
    """Server to server service that gets access tokens via CSP OAuth."""
    def __init__(self, csp_client_credentials: CSPClientCredentials):
        """Construct CSPServerToServerTokenService.

        @param csp_client_credentials: CSP Client Credentials.
        """
        self._csp_client_credentials = csp_client_credentials
        self._csp_type = 'OAUTH'
        self._csp_access_token = None
        self._token_expiration_time = 0
        self._csp_response = AuthorizeResponse()

    def get_type(self):
        return self._csp_type

    def get_token(self):
        """Gets the access token."""
        try:
            response = post(self._csp_client_credentials.get_server_url(),
                            data=self._csp_client_credentials.get_data(),
                            headers=self._csp_client_credentials.get_headers(),
                            timeout=CSP_REQUEST_TIMEOUT_SEC)
            data = response.json()
            if response.status_code == 200:
                self._csp_response.set_auth_response(data)
                if not self._csp_response.has_direct_inject_scope():
                    LOGGER.error("The CSP response did not find any scope matching "
                                 + "('aoa:directDataIngestion' or 'aoa:*' or 'aoa/*' or 'ALL_PERMISSIONS')"
                                 + ", which is required for Wavefront direct ingestion.")
                self._csp_access_token = self._csp_response.access_token
                self._token_expiration_time = time() + self._csp_response.get_time_offset()
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
            LOGGER.error("CSP authentication failed: request url %s timed out",
                         self._csp_client_credentials.get_server_url())
        return None

    def get_csp_access_token(self):
        if not self._csp_access_token or time() >= self._token_expiration_time:
            return self.get_token()
        return self._csp_access_token
