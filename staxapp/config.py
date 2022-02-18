import logging
import os
import platform as sysinfo

import requests

import staxapp
from staxapp.exceptions import ApiException

logging.getLogger().setLevel(logging.DEBUG)
logging.getLogger("boto3").setLevel(logging.WARNING)
logging.getLogger("botocore").setLevel(logging.WARNING)
logging.getLogger("nose").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)


class Config:
    """
    Insert doco here
    """

    STAX_REGION = os.getenv("STAX_REGION", "au1.staxapp.cloud")
    API_VERSION = "20190206"

    api_config = dict()
    access_key = None
    secret_key = None
    auth_class = None
    _initialized = False
    base_url = None
    hostname = f"api.{STAX_REGION}"
    org_id = None
    service_auths = dict()
    expiration = None
    load_live_schema = True

    platform = sysinfo.platform()
    python_version = sysinfo.python_version()
    sdk_version = staxapp.__version__

    service_api_endpoints = dict()

    @classmethod
    def set_config(cls):
        cls.base_url = f"https://{cls.hostname}/{cls.API_VERSION}"
        config_url = f"{cls.base_url}/public/config"
        config_response = requests.get(config_url)
        try:
            config_response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            logging.error(f"{config_response.status_code}: {config_response.json()}")
            raise ApiException(
                str(e), config_response, detail=" Could not load API config."
            )

        cls.api_config = config_response.json()

    @classmethod
    def init(cls, config=None):
        if cls._initialized:
            return

        if not config:
            cls.set_config()

        cls._initialized = True

    @classmethod
    def api_base_url(cls, service_name=None):
        service = cls.service_api_endpoints.get(service_name)
        if service:
            return service.get("base_url")

        # if no direct match, fallback to coreapi
        core_api = cls.service_api_endpoints.get("coreapi")
        if core_api:
            return core_api.get("base_url")

        raise Exception(f"unable to get base url for service: {service_name}")

    @classmethod
    def branch(cls):
        return os.getenv("STAX_BRANCH", "master")

    @classmethod
    def schema_url(cls):
        return f"{cls.base_url}/public/api-document"

    @classmethod
    def api_endpoints(cls) -> list:
        if len(cls.service_api_endpoints) > 0:
            return list(cls.service_api_endpoints.values())

        api_endpoints = dict()
        api: dict = cls.api_config.get("API")
        endpoints: list = api.get("endpoints")

        for endpoint in endpoints:
            api_base_url = endpoint.get("endpoint")
            schema_url = f"{api_base_url}/public/api-document"
            service_name = endpoint.get("name")
            api_endpoints[service_name] = {
                "service_name": service_name,
                "region": endpoint.get("region"),
                "base_url": api_base_url,
                "schema_url": schema_url,
            }

        cls.service_api_endpoints = api_endpoints

        return list(cls.service_api_endpoints.values())

    @classmethod
    def get_auth_class(cls):
        if cls.auth_class is None:
            from staxapp.auth import ApiTokenAuth

            cls.auth_class = ApiTokenAuth
        return cls.auth_class


Config.init()
