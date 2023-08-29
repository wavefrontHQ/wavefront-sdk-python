"""CSP Authorize Response.

@author Jerry Belmonte (bjerry@vmware.com)
"""

from dataclasses import dataclass, field


@dataclass
class AuthorizeResponse:
    """Authorize Response.

    @param access_token: The access token.
    @param scope: The scope of access needed for the token.
    @param expires_in: Access token expiration in seconds.
    @param id_token: The ID Token is a signed JWT token returned from the authorization server.
    @param token_type: The type of the token.
    """
    access_token: str = field(default='', repr=False)
    scope: str = ''
    expires_in: int = 0
    id_token: str = field(default='', repr=False)
    refresh_token: str = field(default='', repr=False)
    token_type: str = ''

    def set_auth_response(self, response):
        """Sets the CSP auth response.

        @param response: The json-encoded response.
        """
        self.access_token = response.get("access_token")
        self.expires_in = response.get("expires_in")
        self.scope = response.get("scope")

    def get_time_offset(self):
        """Calculates the time offset.

        Calculates the time offset for scheduling regular requests to CSP based on the expiration
        time of the token. If the access token expiration time is less than 10 minutes, schedule
        requests 30 seconds before it expires. If the access token expiration time is 10 minutes
        or more, schedule requests 3 minutes before it expires.

        @return: The expiration time offset of the CSP access token in seconds.
        """
        if self.expires_in < 600:
            return self.expires_in - 30
        return self.expires_in - 180

    def get_scopes(self):
        """Get the scopes for the token.

        @return: List of scopes.
        """
        return self.scope.split()

    def has_direct_inject_scope(self):
        """Check if the scope is valid.

        @return: True if scope is valid for direct injestion.
        """
        valid_scopes = ['aoa:directDataIngestion', 'aoa:*', 'aoa/*', 'ALL_PERMISSIONS']
        for scope in self.get_scopes():
            if any(scope.endswith(valid) for valid in valid_scopes):
                return True
        return False
