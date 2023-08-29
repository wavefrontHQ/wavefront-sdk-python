"""CSP Token Service Factory.

@author Jerry Belmonte (bjerry@vmware.com)
"""

from .token_service import CSPAPIToken, CSPClientCredentials, CSPUserTokenService, \
                           CSPServerToServerTokenService


class TokenServiceFactory:
    """Token Service Factory."""
    def __init__(self):
        self._builders = {}

    def add_builder(self, service_id, builder):
        """Add a new builder type.

        @param service_id: Value used to identify the token service builder type.
        @param builder: The class name of the token service builder object.
        """
        self._builders[service_id] = builder

    def get_builder(self, service_id):
        """Get a new builder type.

        @param service_id: Value used to identify the token service builder type.
        @return: New instance of the builder.
        """
        token_service_builder = self._builders.get(service_id)
        if not token_service_builder:
            raise ValueError(service_id)
        return token_service_builder()

    def create(self, service_id, **kwargs):
        """Create a new token service.

        @param service_id: Value used to identify the token service type.
        @param **kwargs: Keyword arguments for the token service builder.
        @return: New instance of the token service.
        """
        token_service_builder = self.get_builder(service_id)
        token_service_builder.create_builder()
        for key, value in kwargs.items():
            token_service_builder.add_property(key, value)
        return token_service_builder.build()


class CSPUserTokenServiceBuilder:
    """CSP User Token Service Builder."""

    def __init__(self):
        self._current_service = None

    def create_builder(self, base_url='https://console.cloud.vmware.com'):
        """Create the token service builder.

        @param base_url: The CSP base URL. Defaults to 'https://console.cloud.vmware.com'.
        """
        self._current_service = {'base_url': base_url,
                                 'auth_path': '/csp/gateway/am/api/auth/api-tokens/authorize'}

    def add_property(self, name, value):
        """Add a property to the token service.

        @param name: The property name.
        @param value: The property value.
        """
        if value:
            self._current_service[name] = value

    def build(self):
        """Build the CSP Api token service.

        @return: New instance of the CSP Api token service.
        """
        csp_api_token = CSPAPIToken(token=self._current_service['csp_api_token'],
                                    base_url=self._current_service['base_url'],
                                    auth_path=self._current_service['auth_path'])
        return CSPUserTokenService(csp_api_token)


class CSPServerToServerTokenServiceBuilder:
    """CSP Server to Server Token Service Builder."""
    def __init__(self):
        self._current_service = None

    def create_builder(self, base_url='https://console.cloud.vmware.com'):
        """Create the token service builder.

        @param base_url: The CSP base URL. Defaults to 'https://console.cloud.vmware.com'.
        """
        self._current_service = {'base_url': base_url,
                                 'auth_path': '/csp/gateway/am/api/auth',
                                 'csp_org_id': ''}

    def add_property(self, name, value):
        """Add a property to the OAuth token service.

        @param name: The property name.
        @param value: The property value.
        """
        if value:
            self._current_service[name] = value

    def build(self):
        """Build the CSP OAuth token service.

        @return: New instance of the CSP OAuth token service.
        """
        csp_client_credentials = CSPClientCredentials(
            client_id=self._current_service['csp_app_id'],
            client_secret=self._current_service['csp_app_secret'],
            org_id=self._current_service['csp_org_id'],
            base_url=self._current_service['base_url'],
            auth_path=self._current_service['auth_path']
        )
        return CSPServerToServerTokenService(csp_client_credentials)


class TokenServiceProvider(TokenServiceFactory):
    """Token Service Provider."""
    def __init__(self):
        super().__init__()
        self.add_builder('TOKEN', CSPUserTokenServiceBuilder)
        self.add_builder('OAUTH', CSPServerToServerTokenServiceBuilder)

    def get(self, service, **kwargs):
        """Get the token service.

        @param service: The token service type (ex: 'TOKEN' or 'OAUTH').
        @param **kwargs: Keyword arguments for the token service builder.
        """
        return self.create(service, **kwargs)
