"""Wavefront SDK Authentication.

@author Jerry Belmonte (bjerry@vmware.com)
"""

from .csp.authorize_response import AuthorizeResponse
from .csp.token_service_factory import TokenServiceProvider


__all__ = ['AuthorizeResponse',
           'TokenServiceProvider']
