"""CSP Token Service Factory.

@author Jerry Belmonte (bjerry@vmware.com)
"""

from .token_service import CSPAPIToken, CSPClientCredentials, CSPTokenService, CSPServerToServerTokenService


class TokenServiceFactory:
    def __init__(self):
        self._builders = {}

    def add_builder(self, key, builder):
        self._builders[key] = builder

    def create(self, key, **kwargs):
        token_service_builder = self._builders.get(key)
        if not token_service_builder:
            raise ValueError(key)
        token_service_builder.create_builder()
        for name, value in kwargs.items():
            token_service_builder.add_property(name, value)
        return token_service_builder.build()


class CSPUserTokenServiceBuilder:
    def __init__(self):
        self._current_service = None

    def create_builder(self, base_url='https://console.cloud.vmware.com'):
        self._current_service = {'base_url': base_url,
                                 'auth_path': '/csp/gateway/am/api/auth/api-tokens/authorize'}

    def add_property(self, name, value):
        if value:
            self._current_service[name] = value

    def build(self):
        csp_api_token = CSPAPIToken(token=self._current_service['csp_api_token'],
                                    base_url=self._current_service['base_url'],
                                    auth_path=self._current_service['auth_path'])
        return CSPTokenService(csp_api_token)


class CSPServerToServerTokenServiceBuilder:
    def __init__(self):
        self._current_service = None

    def create_builder(self, base_url='https://console.cloud.vmware.com'):
        self._current_service = {'base_url': base_url,
                                 'auth_path': '/csp/gateway/am/api/auth',
                                 'csp_org_id': ''}

    def add_property(self, name, value):
        if value:
            self._current_service[name] = value

    def build(self):
        csp_client_credentials = CSPClientCredentials(client_id=self._current_service['csp_app_id'],
                                                      client_secret=self._current_service['csp_app_secret'],
                                                      org_id=self._current_service['csp_org_id'],
                                                      base_url=self._current_service['base_url'],
                                                      auth_path=self._current_service['auth_path'])
        return CSPServerToServerTokenService(csp_client_credentials)


class TokenServiceProvider(TokenServiceFactory):
    def __init__(self):
        super().__init__()
        self.add_builder('TOKEN', CSPUserTokenServiceBuilder())
        self.add_builder('OAUTH', CSPServerToServerTokenServiceBuilder())

    def get(self, service_id, **kwargs):
        return self.create(service_id, **kwargs)
