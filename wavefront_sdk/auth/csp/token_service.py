"""CSP Token Service.

@author Jerry Belmonte (bjerry@vmware.com)
"""

from abc import ABC, abstractmethod


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
