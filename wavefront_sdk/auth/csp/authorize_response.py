"""CSP Authorize Response.

@author Jerry Belmonte (bjerry@vmware.com)
"""

from dataclasses import dataclass, field


@dataclass
class AuthorizeResponse:
    """Authorize Response."""

    access_token: str = field(default='', repr=False)
    expires_in: int = 0

    def set_auth_response(self, response):
        """Set the CSP auth response.

        @param response: The json-encoded response.
        """
        self.access_token = response.get("access_token")
        self.expires_in = response.get("expires_in")

    def get_time_offset(self):
        """Calculate the time offset.

        Calculates the time offset for scheduling regular requests to CSP based
        on the expiration time of the token. If the access token expiration
        time is less than 10 minutes, schedule requests 30 seconds before it
        expires. If the access token expiration time is 10 minutes or more,
        schedule requests 3 minutes before it expires.

        @return: The expiration time offset of the CSP access token in seconds.
        """
        if self.expires_in < 600:
            return self.expires_in - 30
        return self.expires_in - 180
