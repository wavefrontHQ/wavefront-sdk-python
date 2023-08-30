"""CSP Request types.

@author Jerry Belmonte (bjerry@vmware.com)
"""

from base64 import b64encode
from dataclasses import dataclass


@dataclass(frozen=True)
class AuthServerURL:
    """Auth Server URL."""

    base_url: str
    auth_path: str

    def get_server_url(self):
        """Get the full authentication server URL.

        @return: The authentication server URL.
        """
        if self.base_url.endswith('/'):
            return self.base_url[:-1] + self.auth_path
        return self.base_url + self.auth_path


@dataclass(frozen=True)
class CSPAPIToken(AuthServerURL):
    """CSP Api Token."""

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
class CSPClientCredentials(AuthServerURL):
    """CSP Client Credentials."""

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
        """Encode the CSP client credentials.

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
