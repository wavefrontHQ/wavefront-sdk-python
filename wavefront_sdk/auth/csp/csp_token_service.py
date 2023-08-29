"""CSP Token Service implementation.

@author Jerry Belmonte (bjerry@vmware.com)
"""

import logging
from time import time
from requests import post, HTTPError, ConnectionError, Timeout
from .token_service import TokenService
from .authorize_response import AuthorizeResponse


LOGGER = logging.getLogger('wavefront_sdk.auth.csp.CSPTokenService')
CSP_API_TOKEN_SERVICE_TYPE = 'TOKEN'
CSP_OAUTH_TOKEN_SERVICE_TYPE = 'OAUTH'
CSP_REQUEST_TIMEOUT_SEC = 30


class CSPTokenService(TokenService):
    """CSP Token Service Implementation."""

    def __init__(self, csp_type: str, csp_service):
        """Construct CSP Token Service.

        @param csp_type: The csp token service type.
        @param csp_service: The csp service object.
        """
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
