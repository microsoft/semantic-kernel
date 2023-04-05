# Copyright (c) Microsoft. All rights reserved.


from logging import Logger
from typing import Any, Literal, Optional, Union

from semantic_kernel.ai.open_ai.services.open_ai_text_embedding import (
    OpenAITextEmbedding,
)
from semantic_kernel.utils.notebooks import try_get_api_info_from_synapse_mlflow


class AzureTextEmbedding(OpenAITextEmbedding):
    _endpoint: str
    _api_version: str
    _api_type: str

    def __init__(
        self,
        deployment_name: str,
        endpoint: Optional[str] = None,
        api_key: Optional[str] = None,
        api_version: str = "2022-12-01",
        logger: Optional[Logger] = None,
        api_type: Union[Literal["azure"], Literal["azure_ad"]] = "azure",
    ) -> None:
        if endpoint is None or api_key is None:
            # Try to get endpoint/api_key via alternative methods
            results = try_get_api_info_from_synapse_mlflow()
            if results is not None:
                endpoint, api_key = results

        if not deployment_name:
            raise ValueError("The deployment name cannot be `None` or empty")
        if not api_key:
            raise ValueError("The Azure API key cannot be `None` or empty`")
        if not endpoint:
            raise ValueError("The Azure endpoint cannot be `None` or empty")
        if not endpoint.startswith("https://") and api_type == "azure":
            raise ValueError("The Azure endpoint must start with https://")
        if api_type not in ["azure", "azure_ad"]:
            raise ValueError("api_type must be either 'azure' or 'azure_ad'")

        self._endpoint = endpoint
        self._api_version = api_version
        self._api_type = api_type

        super().__init__(deployment_name, api_key, org_id=None, log=logger)

    def _setup_open_ai(self) -> Any:
        import openai

        openai.api_type = self._api_type
        openai.api_key = self._api_key
        openai.api_base = self._endpoint
        openai.api_version = self._api_version

        return openai
