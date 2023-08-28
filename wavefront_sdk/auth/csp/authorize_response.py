"""CSP Authorize Response.

@author Jerry Belmonte (bjerry@vmware.com)
"""

from dataclasses import dataclass, field


@dataclass
class AuthorizeResponse:
    access_token: str = field(repr=False)
    scope: str
    expires_in: int = 0
    id_token: str = field(default='', repr=False)
    refresh_token: str = field(default='', repr=False)
    token_type: str = ''

    def get_scopes(self):
        return self.scope.split()

    def has_direct_inject_scope(self):
        valid_scopes = ['aoa:directDataIngestion', 'aoa:*', 'aoa/*', 'ALL_PERMISSIONS']
        for scope in self.get_scopes():
            if any(scope.endswith(valid) for valid in valid_scopes):
                return True
        return False
