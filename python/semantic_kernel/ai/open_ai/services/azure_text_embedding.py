# Copyright (c) Microsoft. All rights reserved.


from logging import Logger
from typing import Any, Optional

from semantic_kernel.ai.open_ai.services.open_ai_text_embedding import (
    OpenAITextEmbedding,
)


class AzureTextEmbedding(OpenAITextEmbedding):
    _endpoint: str
    _api_version: str

    def __init__(
        self,
        deployment_name: str,
        endpoint: str,
        api_key: str,
        api_version: str = "2022-12-01",
        logger: Optional[Logger] = None,
    ) -> None:
        if not deployment_name:
            raise ValueError("The deployment name cannot be `None` or empty")
        if not api_key:
            raise ValueError("The Azure API key cannot be `None` or empty`")
        if not endpoint:
            raise ValueError("The Azure endpoint cannot be `None` or empty")
        if not endpoint.startswith("https://"):
            raise ValueError("The Azure endpoint must start with https://")

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
