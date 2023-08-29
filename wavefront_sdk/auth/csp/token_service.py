"""CSP Token Service.

@author Jerry Belmonte (bjerry@vmware.com)
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from base64 import b64encode
from time import time
from requests import post, HTTPError, ConnectionError, Timeout
from .authorize_response import AuthorizeResponse


LOGGER = logging.getLogger('wavefront_sdk.auth.csp.TokenService')
CSP_API_TOKEN_SERVICE_TYPE = 'TOKEN'
CSP_OAUTH_TOKEN_SERVICE_TYPE = 'OAUTH'
CSP_REQUEST_TIMEOUT_SEC = 30
CSP_SCOPE_ERROR_MESSAGE = ("The CSP response did not find any scope matching: 'aoa:*' or 'aoa/*'"
                           + " or 'aoa:directDataIngestion' or 'ALL_PERMISSIONS', which is "
                           + "required for Wavefront direct ingestion.")


class TokenService(ABC):
    """Service that gets access tokens."""

    @abstractmethod
    def get_token(self) -> str:
        """Get the token service access token.

        @return: The access token.
        """

    @abstractmethod
    def get_type(self) -> str:
        """Get the token service type.

        @return: The service type.
        """


@dataclass(frozen=True)
class APIServerURL:
    """API Server URL.

    @param base_url: The base URL for the server.
    @param auth_path: The authentication end-point.
    """
    base_url: str
    auth_path: str

    def get_server_url(self):
        """Gets the full authentication server URL.

        @return: The authentication server URL.
        """
        if self.base_url.endswith('/'):
            return self.base_url.removesuffix('/') + self.auth_path
        return self.base_url + self.auth_path


@dataclass(frozen=True)
class CSPAPIToken(APIServerURL):
    """CSP Api Token.

    @param token: The value of the API token.
    """
    token: str

    def get_data(self):
        """Get the HTTP request body.

        @return: The data for the request body.
        """
        return {'api_token': self.token}

    def get_headers(self):
        """Get the HTTP request headers.

        @return: The parameters for request headers.
        """
        return {'Content-Type': 'application/x-www-form-urlencoded'}


@dataclass(frozen=True)
class CSPClientCredentials(APIServerURL):
    """CSP Client Credentials.

    @param client_id: The CSP OAuth app id.
    @param client_secret: The CSP OAuth app secret.
    @param org_id: Unique identifier (GUID) of the organization.
    """
    client_id: str
    client_secret: str
    org_id: str = ''

    def get_data(self):
        """Get the HTTP request body.

        @return: The data for the request body.
        """
        data = {'grant_type': 'client_credentials'}
        if self.org_id:
            data['orgId'] = self.org_id
        return data

    def encode_csp_credentials(self):
        """Encodes the CSP client credentials.

        @return: Base64 encoded client credentials.
        """
        csp_credentials = self.client_id + ":" + self.client_secret
        return b64encode(csp_credentials.encode("utf-8")).decode("utf-8")

    def get_headers(self):
        """Get the HTTP request headers.

        @return: The parameters for request headers.
        """
        return {'Authorization': f'Basic {self.encode_csp_credentials()}',
                'Content-Type': 'application/x-www-form-urlencoded'}


class CSPTokenService(TokenService):
    """CSP Token Service Implementation."""

    def __init__(self, csp_type: str, csp_service):
        self._csp_type = csp_type
        self._csp_service = csp_service
        self._csp_access_token = None
        self._token_expiration_time = 0
        self._csp_response = None

    def get_type(self):
        return self._csp_type

    def get_token(self):
        try:
            response = post(self._csp_service.get_server_url(),
                            data=self._csp_service.get_data(),
                            headers=self._csp_service.get_headers(),
                            timeout=CSP_REQUEST_TIMEOUT_SEC)
            code = response.status_code
            if code == 200:
                self._csp_response = AuthorizeResponse()
                self._csp_response.set_auth_response(response.json())
                if not self._csp_response.has_direct_inject_scope():
                    LOGGER.error(CSP_SCOPE_ERROR_MESSAGE)
                self._csp_access_token = self._csp_response.access_token
                self._token_expiration_time = time() + self._csp_response.get_time_offset()
                LOGGER.info("CSP authentication succeeded, access token expires in %d seconds.",
                            self._csp_response.expires_in)
                return self._csp_access_token
            elif not response.ok:
                data = response.json()
                LOGGER.error("CSP authentication failed with status code: %d %s", code, data.get("message"))
                response.raise_for_status()

        except HTTPError as error:
            LOGGER.error("CSP HTTP Error: %s", error)
        except ConnectionError as error:
            LOGGER.error("CSP Connection Error: %s", error)
        except Timeout as error:
            LOGGER.error("CSP Timeout Error: %s", error)
        except Exception as error:
            LOGGER.error("CSP authentication failed: %s", error)
        return None

    def get_csp_access_token(self):
        """Get the CSP access token.

        @return: The access token.
        """
        if not self._csp_access_token or time() >= self._token_expiration_time:
            return self.get_token()
        return self._csp_access_token
