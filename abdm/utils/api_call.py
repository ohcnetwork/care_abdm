import json
import logging
from base64 import b64encode

import requests
from Crypto.Cipher import PKCS1_v1_5
from Crypto.PublicKey import RSA
from django.core.cache import cache

from abdm.settings import plugin_settings as settings

GATEWAY_API_URL = settings.ABDM_URL
HEALTH_SERVICE_API_URL = settings.HEALTH_SERVICE_API_URL
ABDM_DEVSERVICE_URL = GATEWAY_API_URL + "/devservice"
ABDM_GATEWAY_URL = GATEWAY_API_URL + "/gateway"
ABDM_TOKEN_URL = ABDM_GATEWAY_URL + "/v0.5/sessions"
ABDM_TOKEN_CACHE_KEY = "abdm_token"
ABDM_FACILITY_URL = settings.ABDM_FACILITY_URL

# TODO: Exception handling for all api calls, need to gracefully handle known exceptions

logger = logging.getLogger(__name__)


def encrypt_with_public_key(a_message):
    rsa_public_key = RSA.importKey(
        requests.get(HEALTH_SERVICE_API_URL + "/v2/auth/cert").text.strip()
    )
    rsa_public_key = PKCS1_v1_5.new(rsa_public_key)
    encrypted_text = rsa_public_key.encrypt(a_message.encode())
    return b64encode(encrypted_text).decode()


class APIGateway:
    def __init__(self, gateway, token):
        if gateway == "health":
            self.url = HEALTH_SERVICE_API_URL
        elif gateway == "abdm":
            self.url = GATEWAY_API_URL
        elif gateway == "abdm_gateway":
            self.url = ABDM_GATEWAY_URL
        elif gateway == "abdm_devservice":
            self.url = ABDM_DEVSERVICE_URL
        elif gateway == "facility":
            self.url = ABDM_FACILITY_URL
        else:
            self.url = GATEWAY_API_URL
        self.token = token

    # def encrypt(self, data):
    #     cert = cache.get("abdm_cert")
    #     if not cert:
    #         cert = requests.get(settings.ABDM_CERT_URL).text
    #         cache.set("abdm_cert", cert, 3600)

    def add_user_header(self, headers, user_token):
        headers.update(
            {
                "X-Token": "Bearer " + user_token,
            }
        )
        return headers

    def add_auth_header(self, headers):
        token = cache.get(ABDM_TOKEN_CACHE_KEY)
        if not token:
            logger.info("No Token in Cache")
            data = {
                "clientId": settings.ABDM_CLIENT_ID,
                "clientSecret": settings.ABDM_CLIENT_SECRET,
            }
            auth_headers = {
                "Content-Type": "application/json",
                "Accept": "application/json",
            }
            resp = requests.post(
                ABDM_TOKEN_URL, data=json.dumps(data), headers=auth_headers
            )
            logger.info("Token Response Status: {}".format(resp.status_code))
            if resp.status_code < 300:
                # Checking if Content-Type is application/json
                if resp.headers["Content-Type"] != "application/json":
                    logger.info(
                        "Unsupported Content-Type: {}".format(
                            resp.headers["Content-Type"]
                        )
                    )
                    logger.info("Response: {}".format(resp.text))
                    return None
                else:
                    data = resp.json()
                    token = data["accessToken"]
                    expires_in = data["expiresIn"]
                    logger.info("New Token: {}".format(token))
                    logger.info("Expires in: {}".format(expires_in))
                    cache.set(ABDM_TOKEN_CACHE_KEY, token, expires_in)
            else:
                logger.info("Bad Response: {}".format(resp.text))
                return None
        # logger.info("Returning Authorization Header: Bearer {}".format(token))
        logger.info("Adding Authorization Header")
        auth_header = {"Authorization": "Bearer {}".format(token)}
        return {**headers, **auth_header}

    def add_additional_headers(self, headers, additional_headers):
        return {**headers, **additional_headers}

    def get(self, path, params=None, auth=None):
        url = self.url + path
        headers = {}
        headers = self.add_auth_header(headers)
        if auth:
            headers = self.add_user_header(headers, auth)
        logger.info("Making GET Request to: {}".format(url))
        response = requests.get(url, headers=headers, params=params)
        logger.info("{} Response: {}".format(response.status_code, response.text))
        return response

    def post(self, path, data=None, auth=None, additional_headers=None, method="POST"):
        url = self.url + path
        headers = {
            "Content-Type": "application/json",
            "accept": "*/*",
            "Accept-Language": "en-US",
        }
        headers = self.add_auth_header(headers)
        if auth:
            headers = self.add_user_header(headers, auth)
        if additional_headers:
            headers = self.add_additional_headers(headers, additional_headers)
        # headers_string = " ".join(
        #     ['-H "{}: {}"'.format(k, v) for k, v in headers.items()]
        # )
        data_json = json.dumps(data)
        # logger.info("curl -X POST {} {} -d {}".format(url, headers_string, data_json))
        logger.info("Posting Request to: {}".format(url))
        response = requests.request(method, url, headers=headers, data=data_json)
        logger.info("{} Response: {}".format(response.status_code, response.text))
        return response

class Bridge:
    def __init__(self):
        self.api = APIGateway("abdm_devservice", None)

    def add_update_service(self, data):
        path = "/v1/bridges/addUpdateServices"
        response = self.api.post(path, data, method="PUT")
        return response


class Facility:
    def __init__(self) -> None:
        self.api = APIGateway("facility", None)

    def add_update_service(self, data):
        path = "/v1/bridges/MutipleHRPAddUpdateServices"
        response = self.api.post(path, data, method="POST")
        return response
