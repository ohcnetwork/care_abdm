import json
import logging

import requests
from django.core.cache import cache

from abdm.settings import plugin_settings as settings

ABDM_GATEWAY_URL = settings.ABDM_URL + "/gateway"
ABDM_TOKEN_URL = ABDM_GATEWAY_URL + "/v0.5/sessions"
ABDM_TOKEN_CACHE_KEY = "abdm_token"

logger = logging.getLogger(__name__)


class Request:
    def __init__(self, base_url):
        self.url = base_url

    def user_header(self, user_token):
        if not user_token:
            return {}
        return {"X-Token": "Bearer " + user_token}

    def auth_header(self):
        token = cache.get(ABDM_TOKEN_CACHE_KEY)
        if not token:
            data = json.dumps(
                {
                    "clientId": settings.ABDM_CLIENT_ID,
                    "clientSecret": settings.ABDM_CLIENT_SECRET,
                }
            )
            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json",
            }

            response = requests.post(
                ABDM_TOKEN_URL, data=data, headers=headers, timeout=10
            )

            if response.status_code < 300:
                if response.headers["Content-Type"] != "application/json":
                    logger.error(
                        f"Invalid content type: {response.headers['Content-Type']}"
                    )
                    return None
                else:
                    data = response.json()
                    token = data["accessToken"]
                    expires_in = data["expiresIn"]

                    cache.set(ABDM_TOKEN_CACHE_KEY, token, expires_in)
            else:
                logger.error(f"Error while fetching token: {response.text}")
                return None

        return {"Authorization": f"Bearer {token}"}

    def headers(self, additional_headers=None, auth=None):
        return {
            "Content-Type": "application/json",
            "Accept": "*/*",
            **(additional_headers or {}),
            **(self.user_header(auth) or {}),
            **(self.auth_header() or {}),
        }

    # TODO: retry on token expiry
    def get(self, path, params=None, headers=None, auth=None):
        url = self.url + path
        headers = self.headers(headers, auth)

        response = requests.get(url, headers=headers, params=params, timeout=10)

        if response.status_code == 400:
            result = response.json()
            if "code" in result and result["code"] == "900901":
                cache.delete(ABDM_TOKEN_CACHE_KEY)
                return self.post(path, params, headers, auth)

        return self._handle_response(response)

    def post(self, path, data=None, headers=None, auth=None):
        url = self.url + path
        payload = json.dumps(data)
        headers = self.headers(headers, auth)

        response = requests.post(url, data=payload, headers=headers, timeout=10)

        if response.status_code == 400:
            result = response.json()
            if "code" in result and result["code"] == "900901":
                cache.delete(ABDM_TOKEN_CACHE_KEY)
                return self.post(path, data, headers, auth)

        return self._handle_response(response)

    def _handle_response(self, response: requests.Response):
        def custom_json():
            try:
                return json.loads(response.text)
            except json.JSONDecodeError as json_err:
                logger.error(f"JSON Decode error: {json_err}")
                return {"error": response.text}
            except Exception as err:
                logger.error(f"Unknown error while decoding json: {err}")
                return {}

        response.json = custom_json
        return response
