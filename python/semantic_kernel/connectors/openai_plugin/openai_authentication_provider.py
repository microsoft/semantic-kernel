# Copyright (c) Microsoft. All rights reserved.

from typing import Dict, Optional

from aiohttp import ClientRequest, ClientSession

from semantic_kernel.connectors.openai_plugin.openai_function_execution_parameters import OpenAIAuthenticationType


class OpenAIAuthenticationProvider:
    def __init__(
        self, oauth_values: Optional[Dict[str, Dict[str, str]]] = None, credentials: Optional[Dict[str, str]] = None
    ):
        self.oauth_values = oauth_values or {}
        self.credentials = credentials or {}

    async def authenticate_request_async(
        self, request: ClientRequest, plugin_name: str, openai_auth_config: OpenAIAuthenticationType
    ) -> None:
        if openai_auth_config.type == OpenAIAuthenticationType.NoneType:
            return

        scheme = ""
        credential = ""

        if openai_auth_config.type == OpenAIAuthenticationType.OAuth:
            if not openai_auth_config.authorization_url:
                raise ValueError("Authorization URL is required for OAuth.")

            domain = openai_auth_config.authorization_url.host
            domain_oauth_values = self.oauth_values.get(domain)

            if not domain_oauth_values:
                raise ValueError("No OAuth values found for the provided authorization URL.")

            values = domain_oauth_values | {"scope": openai_auth_config.scope or ""}

            content_type = openai_auth_config.authorization_content_type or "application/x-www-form-urlencoded"
            async with ClientSession() as session:
                if content_type == "application/x-www-form-urlencoded":
                    response = await session.post(openai_auth_config.authorization_url, data=values)
                elif content_type == "application/json":
                    response = await session.post(openai_auth_config.authorization_url, json=values)
                else:
                    raise ValueError(f"Unsupported authorization content type: {content_type}")

                response.raise_for_status()

                token_response = await response.json()
                scheme = token_response.get("token_type", "")
                credential = token_response.get("access_token", "")

        else:
            token = openai_auth_config.verification_tokens.get(plugin_name, "")
            scheme = openai_auth_config.authorization_type.value
            credential = token

        request.headers["Authorization"] = f"{scheme} {credential}"
