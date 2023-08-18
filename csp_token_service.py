import base64
import sys
import time

import requests

from example import main as runExample

class CSPServerToServerTokenService:
    def __init__(self, csp_base_url, csp_client_id, csp_client_secret):
        self.csp_base_url = csp_base_url
        self.csp_client_id = csp_client_id
        self.csp_client_secret = csp_client_secret
        self.csp_access_token = None
        self.token_expiration_time = 0

    def refresh_token(self):
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
            self.csp_access_token = data.get("access_token")
            expires_in = data.get("expires_in")
            self.token_expiration_time = time.time() + expires_in
            print("Token refreshed:", self.csp_access_token)
        else:
            print("Token refresh failed with status code:", response.status_code)

    def get_csp_token(self):
        current_time = time.time()
        if not self.csp_access_token or current_time >= self.token_expiration_time:
            self.refresh_token()
        return self.csp_access_token

    def encode_csp_credentials(self):
        return base64.b64encode((self.csp_client_id+":"+self.csp_client_secret).encode("utf-8")).decode("utf-8")

def main():
    # Example usage
    csp_base_url = "https://console-stg.cloud.vmware.com/"
    csp_client_id = sys.argv[1]
    csp_client_secret = sys.argv[2]
    token_service = CSPServerToServerTokenService(csp_base_url, csp_client_id, csp_client_secret)
    csp_token = token_service.get_csp_token()
    # print("CSPToken:", csp_token)
    wavefront_url = f"https://{csp_token}@nimba.wavefront.com"

    runExample(wavefront_url)


if __name__ == '__main__':
    main()
