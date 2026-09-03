# Copyright (c) Microsoft. All rights reserved.

import ipaddress
import json
import logging
from collections import OrderedDict
from collections.abc import Awaitable, Callable, Mapping
from inspect import isawaitable
from typing import Any
from urllib.parse import urlparse, urlunparse
from urllib.request import getproxies

import httpx
from openapi_core import Spec

from semantic_kernel.connectors.openapi_plugin.models.rest_api_expected_response import (
    RestApiExpectedResponse,
)
from semantic_kernel.connectors.openapi_plugin.models.rest_api_operation import RestApiOperation
from semantic_kernel.connectors.openapi_plugin.models.rest_api_payload import RestApiPayload
from semantic_kernel.connectors.openapi_plugin.models.rest_api_run_options import RestApiRunOptions
from semantic_kernel.connectors.openapi_plugin.server_url_validator import (
    ServerUrlValidationOptions,
    validate_server_url,
)
from semantic_kernel.exceptions.function_exceptions import FunctionExecutionException
from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.utils.feature_stage_decorator import experimental
from semantic_kernel.utils.telemetry.user_agent import APP_INFO, prepend_semantic_kernel_to_user_agent

logger: logging.Logger = logging.getLogger(__name__)


def _pin_url_to_address(url: str, address: ipaddress.IPv4Address | ipaddress.IPv6Address) -> tuple[str, str, str]:
    """Rewrite a URL so the connection targets `address` while keeping the original host identity.

    Returns the address-form URL, the `Host` header value and the TLS SNI hostname, all
    derived from the original URL so that the request on the wire is unchanged apart from
    the address it is delivered to. IPv6 bracketing, the port and any userinfo are
    preserved by `httpx.URL.copy_with`.
    """
    original = httpx.URL(url)
    return (
        str(original.copy_with(host=str(address))),
        original.netloc.decode("ascii"),
        original.raw_host.decode("ascii"),
    )


def _has_environment_proxy() -> bool:
    """Return whether a proxy is configured in the environment for outbound HTTP requests.

    Deliberately conservative: any configured proxy disables address pinning, because a
    proxy resolves the target name itself, so an address resolved locally is neither the
    one used for the connection nor necessarily reachable or correct from the proxy.
    """
    proxies = getproxies()
    return any(proxies.get(scheme) for scheme in ("http", "https", "all"))


@experimental
class OpenApiRunner:
    """The OpenApiRunner that runs the operations defined in the OpenAPI manifest."""

    payload_argument_name = "payload"
    media_type_application_json = "application/json"

    def __init__(
        self,
        parsed_openapi_document: Mapping[str, str],
        auth_callback: Callable[..., dict[str, str] | Awaitable[dict[str, str]]] | None = None,
        http_client: httpx.AsyncClient | None = None,
        enable_dynamic_payload: bool = True,
        enable_payload_namespacing: bool = False,
        server_url_validation_options: ServerUrlValidationOptions | None = None,
    ):
        """Initialize the OpenApiRunner."""
        self.spec = Spec.from_dict(parsed_openapi_document)  # type: ignore
        self.auth_callback = auth_callback
        self.http_client = http_client
        self.enable_dynamic_payload = enable_dynamic_payload
        self.enable_payload_namespacing = enable_payload_namespacing
        self.server_url_validation_options = server_url_validation_options or ServerUrlValidationOptions()

    def build_full_url(self, base_url, query_string):
        """Build the full URL."""
        url_parts = list(urlparse(base_url))
        url_parts[4] = query_string
        return urlunparse(url_parts)

    def build_operation_url(
        self, operation: RestApiOperation, arguments: KernelArguments, server_url_override=None, api_host_url=None
    ):
        """Build the operation URL."""
        url = operation.build_operation_url(arguments, server_url_override, api_host_url)
        return self.build_full_url(url, operation.build_query_string(arguments))

    def build_json_payload(self, payload_metadata: RestApiPayload, arguments: dict[str, Any]) -> tuple[str, str]:
        """Build the JSON payload."""
        if self.enable_dynamic_payload:
            if payload_metadata is None:
                raise FunctionExecutionException(
                    "Payload can't be built dynamically due to the missing payload metadata."
                )

            payload = self.build_json_object(payload_metadata.properties, arguments)
            content = json.dumps(payload)
            return content, payload_metadata.media_type

        argument = arguments.get(self.payload_argument_name)
        if not isinstance(argument, str):
            raise FunctionExecutionException(f"No payload is provided by the argument '{self.payload_argument_name}'.")

        return argument, argument

    def build_json_object(self, properties, arguments, property_namespace=None):
        """Build the JSON payload object."""
        result = {}

        for property_metadata in properties:
            argument_name = self.get_argument_name_for_payload(property_metadata.name, property_namespace)
            if property_metadata.type == "object":
                node = self.build_json_object(property_metadata.properties, arguments, argument_name)
                result[property_metadata.name] = node
                continue
            property_value = arguments.get(argument_name)
            if property_value is not None:
                result[property_metadata.name] = property_value
                continue
            if property_metadata.is_required:
                raise FunctionExecutionException(
                    f"No argument is found for the '{property_metadata.name}' payload property."
                )
        return result

    def build_operation_payload(
        self, operation: RestApiOperation, arguments: KernelArguments
    ) -> tuple[str, str] | tuple[None, None]:
        """Build the operation payload."""
        if operation.request_body is None and self.payload_argument_name not in arguments:
            return None, None

        if operation.request_body is not None:
            return self.build_json_payload(operation.request_body, arguments)

        return None, None

    def get_argument_name_for_payload(self, property_name, property_namespace=None):
        """Get argument name for the payload."""
        if not self.enable_payload_namespacing:
            return property_name
        return f"{property_namespace}.{property_name}" if property_namespace else property_name

    def _get_first_response_media_type(self, responses: OrderedDict[str, RestApiExpectedResponse] | None) -> str:
        if responses:
            first_response = next(iter(responses.values()))
            return first_response.media_type if first_response.media_type else self.media_type_application_json
        return self.media_type_application_json

    async def run_operation(
        self,
        operation: RestApiOperation,
        arguments: KernelArguments | None = None,
        options: RestApiRunOptions | None = None,
    ) -> str:
        """Runs the operation defined in the OpenAPI manifest.

        When the URL is validated by DNS resolution, the request issued by the built-in
        client is pinned to one of the validated addresses. Requests made through a
        caller-supplied `http_client`, or while an environment proxy is configured, use
        that transport's own name resolution and are not pinned.
        """
        if not arguments:
            arguments = KernelArguments()
        url = self.build_operation_url(
            operation=operation,
            arguments=arguments,
            server_url_override=options.server_url_override if options else None,
            api_host_url=options.api_host_url if options else None,
        )
        validated_addresses = await validate_server_url(url, self.server_url_validation_options)
        headers = operation.build_headers(arguments=arguments)
        payload, _ = self.build_operation_payload(operation=operation, arguments=arguments)

        if self.auth_callback:
            headers_update = self.auth_callback(**headers)
            if isawaitable(headers_update):
                headers_update = await headers_update
            # at this point, headers_update is a valid dictionary
            headers.update(headers_update)  # type: ignore

        if APP_INFO:
            headers.update(APP_INFO)
            headers = prepend_semantic_kernel_to_user_agent(headers)

        if "Content-Type" not in headers:
            responses = (
                operation.responses
                if isinstance(operation.responses, OrderedDict)
                else OrderedDict(operation.responses or {})
            )
            headers["Content-Type"] = self._get_first_response_media_type(responses)

        timeout = options.timeout if options and hasattr(options, "timeout") and options.timeout is not None else None

        # Pin the connection to an address the validator actually vetted so that a name which
        # resolves to a public address during validation cannot resolve to a private one at
        # connect time (DNS rebinding). The list is empty when there is nothing to pin.
        pinned_addresses = validated_addresses
        if pinned_addresses and _has_environment_proxy():
            logger.debug("An environment proxy is configured; the OpenAPI request address is not pinned.")
            pinned_addresses = []

        async def fetch():
            async def make_request(
                client: httpx.AsyncClient,
                pin_to: ipaddress.IPv4Address | ipaddress.IPv6Address | None = None,
            ):
                merged_headers = client.headers.copy()
                merged_headers.update(headers)
                request_url = url
                extensions: dict[str, Any] = {}
                if pin_to is not None:
                    request_url, merged_headers["Host"], extensions["sni_hostname"] = _pin_url_to_address(url, pin_to)
                response = await client.request(
                    method=operation.method,
                    url=request_url,
                    headers=merged_headers,
                    json=json.loads(payload) if payload else None,
                    extensions=extensions,
                )
                response.raise_for_status()
                return response.text

            if hasattr(self, "http_client") and self.http_client is not None:
                # A caller-supplied client owns its transport configuration (proxies, mounts,
                # custom resolvers), so its connections are left untouched.
                return await make_request(self.http_client)
            async with httpx.AsyncClient(timeout=timeout) as client:
                if not pinned_addresses:
                    return await make_request(client)
                # Every vetted address is an acceptable target, so keep the resolver's
                # fallback behaviour by trying the next one when a connection cannot be
                # established. Only connection failures are retried, so no request is
                # ever delivered more than once.
                *fallback_addresses, final_address = pinned_addresses
                for address in fallback_addresses:
                    try:
                        return await make_request(client, pin_to=address)
                    except (httpx.ConnectError, httpx.ConnectTimeout):
                        logger.debug("Could not connect to validated address %s, trying the next one.", address)
                return await make_request(client, pin_to=final_address)

        return await fetch()
