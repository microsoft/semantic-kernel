# Copyright (c) Microsoft. All rights reserved.

from __future__ import annotations

import json
import logging

import httpx

from semantic_kernel.connectors.openai_plugin.openai_function_execution_parameters import (
    OpenAIAuthenticationConfig,
    OpenAIFunctionExecutionParameters,
)
from semantic_kernel.connectors.openapi import import_plugin_from_openapi
from semantic_kernel.connectors.utils.document_loader import DocumentLoader
from semantic_kernel.exceptions import KernelException, ServiceInvalidExecutionSettingsError
from semantic_kernel.functions.kernel_plugin import KernelPlugin
from semantic_kernel.kernel import Kernel
from semantic_kernel.utils.validation import validate_plugin_name

logger: logging.Logger = logging.getLogger(__name__)


async def import_plugin_from_openai(
    kernel: Kernel,
    plugin_name: str,
    plugin_url: str,
    execution_parameters: OpenAIFunctionExecutionParameters | None = None,
) -> KernelPlugin:
    """Create a plugin from the Open AI manifest."""
    if kernel is None:
        raise ServiceInvalidExecutionSettingsError("Kernel cannot be `None`")

    if execution_parameters is None:
        execution_parameters = OpenAIFunctionExecutionParameters()

    validate_plugin_name(plugin_name)

    http_client = execution_parameters.http_client if execution_parameters.http_client else httpx.AsyncClient()

    openai_manifest = await DocumentLoader.load_document_from_uri(
        url=plugin_url, http_client=http_client, auth_callback=None, user_agent=execution_parameters.user_agent
    )

    return await _create_plugin(
        kernel=kernel,
        plugin_name=plugin_name,
        openai_manifest=openai_manifest,
        execution_parameters=execution_parameters,
    )


async def _create_plugin(
    kernel: Kernel,
    plugin_name: str,
    openai_manifest: str,
    execution_parameters: OpenAIFunctionExecutionParameters,
) -> KernelPlugin:
    """Create a plugin from the Open AI manifest."""
    try:
        plugin_json = json.loads(openai_manifest)
        openai_auth_config = OpenAIAuthenticationConfig(**plugin_json["auth"])
    except json.JSONDecodeError as ex:
        raise KernelException("Parsing of Open AI manifest failed.") from ex

    # Modify the auth callback in execution parameters if it's provided
    if execution_parameters and execution_parameters.auth_callback:
        original_callback = execution_parameters.auth_callback

        async def modified_auth_callback(client, url):
            await original_callback(client, url, plugin_name, openai_auth_config)

        execution_parameters.auth_callback = modified_auth_callback

    openapi_spec_url = parse_openai_manifest_for_openapi_spec_url(plugin_json)

    return import_plugin_from_openapi(
        kernel=kernel,
        plugin_name=plugin_name,
        openapi_document=openapi_spec_url,
    )


def parse_openai_manifest_for_openapi_spec_url(plugin_json):
    """Extract the OpenAPI Spec URL from the plugin JSON."""
    try:
        return plugin_json["api"]["url"]
    except KeyError as ex:
        raise KernelException("OpenAI manifest is missing the OpenAPI Spec URL.") from ex
