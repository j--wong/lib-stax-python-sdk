import json
import logging
import os

import requests
from jsonschema import validate as json_validate
from prance import ResolvingParser

from staxapp.config import Config
from staxapp.exceptions import ValidationException

logging.getLogger("openapi_spec_validator.validators").setLevel(logging.WARNING)


class StaxContract:
    _service_schemas = dict()
    _resolved_service_schemas = dict()

    @staticmethod
    def resolve_schema_refs(schema) -> dict:
        """Replaces the $refs within an openapi3.0 schema with the referenced components"""
        parser = ResolvingParser(spec_string=schema, backend="openapi-spec-validator")
        return parser.specification

    @classmethod
    def set_schema_for_service(cls, service_name: str, schema):
        cls._service_schemas[service_name] = schema
        cls._resolved_service_schemas[service_name] = cls.resolve_schema_refs(json.dumps(schema))

    @classmethod
    def validate(cls, service: str, path, http_method, operation_name, data):
        """
        Validates a request body against an component in a openapi3.0 template
        """
        service_schema = cls._get_service_schema(service)
        resolved_schema = cls._get_resolved_service_schema(service)
        component = f"{service}.{operation_name}"

        if not service_schema:
            cls._service_schemas[service] = cls.default_swagger_template()

        components = resolved_schema.get("components")
        if components is not None:
            schemas = {**components.get("schemas", {})}
            payload_schema = dict()
            if component in schemas:
                payload_schema = schemas[components]
            elif component not in schemas:
                payload_schema = cls._get_payload_schema(resolved_schema, path.replace("//", "/"), http_method)

            if not payload_schema:
                raise ValidationException(f"SCHEMA: Does not contain {component}")

            try:
                json_validate(instance=data, schema=payload_schema)
            except Exception as err:
                raise ValidationException(str(err))

    @classmethod
    def _get_service_schema(cls, service):
        schema = cls._service_schemas.get(service)
        if not schema:
            return cls._service_schemas.get("coreapi")

        return schema

    @classmethod
    def _get_payload_schema(cls, resolved_schema, path: str, http_method: str) -> dict:
        return resolved_schema.get("paths", {}) \
            .get(path, {}).get(http_method, {}) \
            .get("requestBody", {}) \
            .get("content", {}) \
            .get("application/json", {}).get("schema", {})

    @classmethod
    def _get_resolved_service_schema(cls, service):
        resolved_schema = cls._resolved_service_schemas.get(service)
        if not resolved_schema:
            return cls._resolved_service_schemas.get("coreapi")

        return resolved_schema

    @staticmethod
    def default_swagger_template() -> dict:
        # Get the default swagger template from https://api.au1.staxapp.cloud/20190206/public/api-document
        schema_response = requests.get(Config.schema_url()).json()
        template = dict(
            openapi="3.0.0",
            info={
                "title": f"Stax Core API",
                "version": f"{os.getenv('GIT_VERSION')}",
                "description": f"The Stax API is organised around REST, uses resource-oriented URLs, return responses are JSON and uses standard HTTP response codes, authentication and verbs.",
                "termsOfService": "/there_is_no_tos",
                "contact": {"url": "https://stax.io"},
            },
            servers=[{"url": f"https://{Config.hostname}"}],
            paths=dict(),
            components={
                "securitySchemes": {
                    "sigv4": {
                        "type": "apiKey",
                        "name": "Authorization",
                        "in": "header",
                        "x-amazon-apigateway-authtype": "awsSigv4",
                    }
                },
                "schemas": schema_response.get("components").get("schemas"),
                "responses": dict(),
                "requestBodies": dict(),
            },
        )

        return template
