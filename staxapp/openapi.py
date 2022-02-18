import json
import os

import requests

from staxapp.api import Api
from staxapp.auth import ApiTokenAuth
from staxapp.config import Config
from staxapp.contract import StaxContract
from staxapp.exceptions import ApiException, ValidationException


class StaxClient:
    _operation_map = dict()
    _initialized = False
    _service_schemas = dict()

    def __init__(self, classname, force=False):
        # Stax feature, eg 'quotas', 'workloads'
        if force or not self._operation_map.get(classname):
            _operation_map = dict()
            self._map_paths_to_operations(classname)

        if not self._operation_map.get(classname):
            raise ValidationException(
                f"No such class: {classname}. Please use one of {list(self._operation_map)}"
            )
        self.classname = classname

        Config.auth_class = ApiTokenAuth
        self._initialized = True

    @classmethod
    def _load_schema(cls):
        services = Config.api_endpoints()
        for service in services:
            schema_url = service.get("schema_url")
            service_name = service.get("service_name")
            if schema_url:
                schema = requests.get(schema_url)
                schema.raise_for_status()
                schema_object = schema.json()
                StaxContract.set_schema_for_service(service_name, schema_object)
                cls._service_schemas[service_name] = schema_object

    @classmethod
    def _get_service_schema(cls, classname):
        schema = cls._service_schemas.get(classname)
        if not schema:
            return cls._service_schemas.get("coreapi")

        return schema

    @classmethod
    def _map_paths_to_operations(cls, classname):
        cls._load_schema()

        schema = cls._get_service_schema(classname)
        if not schema:
            raise Exception(f"api specification not loaded for service: {classname}")

        for path_name, path in schema["paths"].items():
            parameters = []

            for part in path_name.split("/"):
                if "{" in part:
                    parameters.append(part.replace("{", "").replace("}", ""))

            for method_type, method in path.items():
                method = path[method_type]
                operation = method.get("operationId", "").split(".")

                if len(operation) == 2:
                    api_class = operation[0]
                    method_name = operation[1]
                elif len(operation) == 1:
                    api_class = classname
                    method_name = operation[0]
                else:
                    continue

                parameter_path = {
                    "path": path_name,
                    "method": method_type,
                    "parameters": parameters,
                }

                if not cls._operation_map.get(api_class):
                    cls._operation_map[api_class] = dict()
                if not cls._operation_map.get(api_class, {}).get(method_name):
                    cls._operation_map[api_class][method_name] = []

                cls._operation_map[api_class][method_name].append(parameter_path)

    def __getattr__(self, name):
        self.name = name

        def stax_wrapper(*args, **kwargs):
            method_name = f"{self.classname}.{self.name}"
            method = self._operation_map[self.classname].get(self.name)
            if method is None:
                raise ValidationException(
                    f"No such operation: {self.name} for {self.classname}. Please use one of {list(self._operation_map[self.classname])}"
                )
            payload = {**kwargs}

            sorted_parameter_paths = sorted(
                self._operation_map[self.classname][self.name],
                key=lambda x: len(x["parameters"]),
            )
            # All parameters starting with the most dependant
            operation_parameters = [
                parameter_path["parameters"]
                for parameter_path in sorted_parameter_paths
            ]
            # Sort the operation map parameters
            parameter_index = -1
            # Check if the any of the parameter schemas match parameters provided
            for index in range(0, len(operation_parameters)):
                # Get any parameters from the keyword args and remove them from the payload
                if set(operation_parameters[index]).issubset(payload.keys()):
                    parameter_index = index
            if parameter_index == -1:
                raise ValidationException(
                    f"Missing one or more parameters: {operation_parameters[-1]}"
                )
            parameter_path = sorted_parameter_paths[parameter_index]
            split_path = parameter_path["path"].split("/")
            path = ""
            for part in split_path:
                if "{" in part:
                    parameter = part.replace("{", "").replace("}", "")
                    path = f"{path}/{payload.pop(parameter)}"
                else:
                    path = f"{path}/{part}"
            if parameter_path["method"].lower() in ["put", "post"]:
                # We only validate the payload for POST/PUT routes
                StaxContract.validate(self.classname, parameter_path["path"], parameter_path["method"].lower(), name, payload)
            ret = getattr(Api, parameter_path["method"])(self.classname, path, payload)
            return ret

        return stax_wrapper
