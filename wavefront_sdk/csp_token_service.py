import base64
import threading
import time

import requests

token_ready = False

class CSPServerToServerTokenService:
    def __init__(self, csp_base_url, csp_app_id=None, csp_app_secret=None, csp_api_token=None):
        self.csp_base_url = csp_base_url
        self.csp_app_id = csp_app_id
        self.csp_app_secret = csp_app_secret
        self.csp_api_token = csp_api_token
        self.csp_access_token = None
        self.token_expiration_time = 0
        self.lock = threading.Lock()

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

        if response.status_code == 200:
            data = response.json()
            expires_in = data.get("expires_in")
            self.token_expiration_time = time.time() + expires_in
            print(f"Token refreshed, which expires in {expires_in} seconds:", self.csp_access_token)
            return data.get("access_token")
        else:
            print("Token refresh failed with status code:", response.status_code)

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

    def get_time_offset(expires_in):
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