# Copyright (c) Microsoft. All rights reserved.


from logging import Logger
from typing import Any, Optional

from semantic_kernel.ai.open_ai.services.open_ai_chat_completion import (
    OpenAIChatCompletion,
)
from semantic_kernel.diagnostics.verify import Verify


class AzureChatCompletion(OpenAIChatCompletion):
    _endpoint: str
    _api_version: str

    def __init__(
        self,
        deployment_name: str,
        endpoint: str,
        api_key: str,
        api_version: str,
        logger: Optional[Logger] = None,
    ) -> None:
        Verify.not_empty(deployment_name, "You must provide a deployment name")
        Verify.not_empty(api_key, "The Azure API key cannot be empty")
        Verify.not_empty(endpoint, "The Azure endpoint cannot be empty")
        Verify.starts_with(
            endpoint, "https://", "The Azure endpoint must start with https://"
        )

        self._endpoint = endpoint
        self._api_version = api_version

        super().__init__(deployment_name, api_key, org_id=None, log=logger)

    def _setup_open_ai(self) -> Any:
        import openai

        openai.api_type = "azure"
        openai.api_key = self._api_key
        openai.api_base = self._endpoint
        openai.api_version = self._api_version

        return openai
