# Copyright (c) Microsoft. All rights reserved.


from logging import Logger
from typing import Any, Optional

from semantic_kernel.ai.open_ai.services.open_ai_text_completion import (
    OpenAITextCompletion,
)
from semantic_kernel.utils.notebooks import try_get_api_info_from_synapse_mlflow


class AzureTextCompletion(OpenAITextCompletion):
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
        use_ad_auth=False,
    ) -> None:
        if use_ad_auth and (endpoint is None or api_key is None):
            # Try to get endpoint/api_key via alternative methods
            results = try_get_api_info_from_synapse_mlflow()
            if results is not None:
                endpoint, api_key = results
            else:
                raise ValueError(
                    "Azure AD authentication failed. Alternatively "
                    "provide an endpoint and API key."
                )

        if not deployment_name:
            raise ValueError("The deployment name cannot be `None` or empty")
        if not api_key:
            raise ValueError("The Azure API key cannot be `None` or empty`")
        if not endpoint:
            raise ValueError("The Azure endpoint cannot be `None` or empty")
        if not endpoint.startswith("https://") and not use_ad_auth:
            raise ValueError("The Azure endpoint must start with https://")

        self._endpoint = endpoint
        self._api_version = api_version
        self._api_type = "azure_ad" if use_ad_auth else "azure"

        super().__init__(deployment_name, api_key, org_id=None, log=logger)

    def _setup_open_ai(self) -> Any:
        import openai

        openai.api_type = self._api_type
        openai.api_key = self._api_key
        openai.api_base = self._endpoint
        openai.api_version = self._api_version

        return openai
