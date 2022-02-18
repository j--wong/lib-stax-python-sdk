import json
from urllib.parse import urlparse

import requests

from staxapp.config import Config
from staxapp.exceptions import ApiException


class Api:
    _service_requests_auth = dict()

    @classmethod
    def _headers(cls, custom_headers) -> dict:
        headers = {
            **custom_headers,
            "User-Agent": f"platform/{Config.platform} python/{Config.python_version} staxapp/{Config.sdk_version}",
        }
        return headers

    @classmethod
    def _auth(cls, **kwargs):
        hostname = kwargs.get("hostname")
        if not cls.get_service_requests_auth(hostname):
            cls._service_requests_auth[hostname] = Config.get_auth_class().requests_auth
        return cls._service_requests_auth[hostname](Config.access_key, Config.secret_key, **kwargs)

    @staticmethod
    def handle_api_response(response):
        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            raise ApiException(str(e), response)

    @classmethod
    def get_service_requests_auth(cls, hostname):
        cls._service_requests_auth.get(hostname)

    @classmethod
    def get(cls, service, url_frag, params={}, **kwargs):
        url_frag = url_frag.replace(f"/{Config.API_VERSION}", "")
        url = f"{Config.api_base_url(service)}/{url_frag.lstrip('/')}"
        hostname = urlparse(url).hostname

        response = requests.get(
            url,
            auth=cls._auth(hostname=hostname),
            params=params,
            headers=cls._headers(kwargs.get("headers", {})),
            **kwargs,
        )
        cls.handle_api_response(response)
        return response.json()

    @classmethod
    def post(cls, service, url_frag, payload={}, **kwargs):
        url_frag = url_frag.replace(f"/{Config.API_VERSION}", "")
        url = f"{Config.api_base_url(service)}/{url_frag.lstrip('/')}"
        hostname = urlparse(url).hostname

        response = requests.post(
            url,
            json=payload,
            auth=cls._auth(hostname=hostname),
            headers=cls._headers(kwargs.get("headers", {})),
            **kwargs,
        )
        cls.handle_api_response(response)
        return response.json()

    @classmethod
    def put(cls, service, url_frag, payload={}, **kwargs):
        url_frag = url_frag.replace(f"/{Config.API_VERSION}", "")
        url = f"{Config.api_base_url(service)}/{url_frag.lstrip('/')}"
        hostname = urlparse(url).hostname

        response = requests.put(
            url,
            json=payload,
            auth=cls._auth(hostname=hostname),
            headers=cls._headers(kwargs.get("headers", {})),
            **kwargs,
        )
        cls.handle_api_response(response)
        return response.json()

    @classmethod
    def delete(cls, service, url_frag, params={}, **kwargs):
        url_frag = url_frag.replace(f"/{Config.API_VERSION}", "")
        url = f"{Config.api_base_url(service)}/{url_frag.lstrip('/')}"
        hostname = urlparse(url).hostname

        response = requests.delete(
            url,
            auth=cls._auth(hostname=hostname),
            params=params,
            headers=cls._headers(kwargs.get("headers", {})),
            **kwargs,
        )
        cls.handle_api_response(response)
        return response.json()
