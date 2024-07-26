# Copyright (c) Microsoft. All rights reserved.


import logging
from typing import Any

from semantic_kernel.exceptions.function_exceptions import PluginInitializationError

logger: logging.Logger = logging.getLogger(__name__)


class OpenAIUtils:
    """Utility functions for OpenAI plugins."""

    @staticmethod
    def parse_openai_manifest_for_openapi_spec_url(plugin_json: dict[str, Any]) -> str:
        """Extract the OpenAPI Spec URL from the plugin JSON."""
        try:
            api_type = plugin_json["api"]["type"]
        except KeyError as ex:
            raise PluginInitializationError("OpenAI manifest is missing the API type.") from ex

        if api_type != "openapi":
            raise PluginInitializationError("OpenAI manifest is not of type OpenAPI.")

        try:
            return plugin_json["api"]["url"]
        except KeyError as ex:
            raise PluginInitializationError("OpenAI manifest is missing the OpenAPI Spec URL.") from ex
