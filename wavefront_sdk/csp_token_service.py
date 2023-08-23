import logging
import base64
import threading
import time

import requests

LOGGER = logging.getLogger('wavefront_sdk.CSPServerToServerTokenService')
token_ready = False

class TokenExchangeResponse:
    id_token: str
    token_type: str
    expires_in: int
    scope: str
    access_token: str
    refresh_token: str


class CSPServerToServerTokenService:
    """CSP Server to Server Token Service."""

    def __init__(self, csp_base_url, csp_app_id=None, csp_app_secret=None, csp_api_token=None):
        """Construct CSPServerToServerTokenService.

        @param csp_base_url: CSP console URL.
        @param csp_app_id: CSP OAuth server to server app id.
        @param csp_app_secret: CSP OAuth server to server app secret.
        @param csp_api_token: CSP Api token.
        """
        self.csp_base_url = csp_base_url
        self.csp_app_id = csp_app_id
        self.csp_app_secret = csp_app_secret
        self.csp_api_token = csp_api_token
        self.csp_access_token = None
        self.token_expiration_time = 0
        self.lock = threading.Lock()
        self._auth_type = ""
        self._set_auth_type()
        self._response = TokenExchangeResponse()
        self._closed = False
        self._schedule_lock = threading.RLock()
        self._timer = None

    def _set_auth_type(self):
        if self.csp_app_id and self.csp_app_secret:
            self._auth_type = "csp_oauth_app"
        elif self.csp_api_token:
            self._auth_type = "csp_api_token"

    def _schedule_timer(self):
        if not self._closed:
            self._timer = threading.Timer(self.reporting_interval_secs,
                                          self._run)
            self._timer.daemon = True
            self._timer.start()

    def refresh_token_oauth(self):
        oauthPath = "/csp/gateway/am/api/auth/authorize"
        headers = {
            "Authorization": f"Basic {self.encode_csp_credentials()}",
            "Content-Type": "application/x-www-form-urlencoded"
        }

        data = {
            "grant_type": "client_credentials"
        }

        response = requests.post(self.csp_base_url + oauthPath, data, headers=headers)
        LOGGER.debug("response: %s", response.json())

        if response.status_code == 200:
            data = response.json()
            self._response.id_token = data.get("id_token")
            self._response.token_type = data.get("token_type")
            self._response.expires_in = data.get("expires_in")
            self._response.scope = data.get("scope")
            self._response.access_token = data.get("access_token")
            self._response.refresh_token = data.get("refresh_token")
            self.token_expiration_time = time.time() + self._response.expires_in
            LOGGER.info("Token refreshed, which expires in %d seconds.", self._response.expires_in)
            return self._response.access_token
        else:
            LOGGER.error("Token refresh failed with status code: %d", response.status_code)
            return None

    def refresh_token(self):
        def refresh_thread(expires_in):
            time.sleep(self.get_time_offset(expires_in))  # Wait for expires_in - 3 minutes
            oauthPath = "/am/api/auth/api-tokens/authorize"
            headers = {
                "Content-Type": "application/x-www-form-urlencoded"
            }

            data = {
                "api_token": f"{self.csp_api_token}"
            }

            response = requests.post(self.csp_base_url + oauthPath, data, headers=headers)

            if response.status_code == 200:
                data = response.json()

                if not self.has_direct_ingest_scope(data.get("scope")):
                    print("The CSP response did not find any scope matching 'aoa:directDataIngestion' which is required for Wavefront direct ingestion.");

                # Schedule token refresh in future before it expires.
                thread_delay = data.get("expires_in")
                print(f"A CSP token has been received. Will schedule the CSP token to be refreshed in: " + {thread_delay} + " seconds");

                self.token_expiration_time = time.time() + thread_delay
                thread = threading.Thread(target=refresh_thread, args=thread_delay)
                thread.start()
                print(f"Token refreshed, which expires in {thread_delay} seconds:", self.csp_access_token)
                return data.get("access_token")

            else:
                print("Token refresh failed with status code:", response.status_code)
                if response.status_code >= 500 and response.status_code < 600:
                    print("The Wavefront SDK will try to reauthenticate with CSP on the next request.")
                    global token_ready
                    token_ready = False
        thread = threading.Thread(target=refresh_thread, args=0)
        thread.start()

    def get_csp_token(self, auth_type="cspapitoken"):
        with self.lock:
            current_time = time.time()
            # TODO: Replace global variable with synchronized lock?
            global token_ready
            if not token_ready:
            # if not self.csp_access_token or current_time >= self.token_expiration_time:
                if auth_type == "oauth":
                    self.csp_access_token = self.refresh_token_oauth()
                else:
                    #TODO: Get this working
                    self.csp_access_token = self.refresh_token()
                token_ready = True
            return self.csp_access_token

    def encode_csp_credentials(self):
        return base64.b64encode((self.csp_app_id + ":" + self.csp_app_secret).encode("utf-8")).decode("utf-8")

    def get_time_offset(expires_in: int):
        """Returns the calculated time offset.

        Calculates the time offset for scheduling regular requests to a CSP
        based on the expiration time of a CSP access token.
        If the access token expiration time is less than 10 minutes,
        schedule requests 30 seconds before it expires.
        if the access token expiration time is 10 minutes or more,
        schedule requests 3 minutes before it expires.

        @param expires_in: The expiration time of the CSP access token in seconds.
        """
        if expires_in < 600:
            return expires_in - 30
        return expires_in - 180

    def has_direct_ingest_scope(scope_list):
        if scope_list:
            parsed_scopes = scope_list.split()
            return any("aoa:directDataIngestion" in s or "aoa/*" in s or "aoa:*" in s for s in parsed_scopes)
        return False

# TODO: Remove below
# csp api token auth type                                            expired scenario
# - inputcreds(api_token) -> server                 | function call to refresh token to be made just before ttl expires, this would refresh ttl also -> cspapi(api_token) -> server
#   accesstoken(ttl of api_token) <- server
#   client(accesstoken) -> wavefrontserver
#
# oauth auth type                                             expired scenario
# - inputcreds(appid+secret) -> server              | before expiry call -> inputcreds(appid+secret) -> server
#   accesstoken(ttl) <- server                      |
#   client(accesstoken) -> wavefrontserver          |