# Copyright (c) Microsoft. All rights reserved.


from logging import Logger
from typing import Any, Dict, List, Optional, Union

from pydantic import Field, constr

from semantic_kernel.connectors.ai import TextCompletionClientBase
from semantic_kernel.connectors.ai.complete_request_settings import (
    CompleteRequestSettings,
)
from semantic_kernel.connectors.ai.open_ai.services.base_open_ai_service_calls import (
    OpenAIModelTypes,
    OpenAIServiceCalls,
)
from semantic_kernel.sk_pydantic import HttpsUrl


class AzureTextCompletion(OpenAIServiceCalls, TextCompletionClientBase):
    model_id: constr(strip_whitespace=True, min_length=1) = Field(
        ..., alias="deployment_name"
    )
    api_version: Optional[str] = None
    endpoint: Optional[HttpsUrl] = None
    api_type: str = "azure"

    def __init__(
        self,
        deployment_name: str,
        endpoint: str,
        api_key: str,
        api_version: str = "2022-12-01",
        ad_auth=False,
        log: Optional[Logger] = None,
        logger: Optional[Logger] = None,
    ) -> None:
        """
        Initialize an AzureTextCompletion service.

        Arguments:
            deployment_name: The name of the Azure deployment. This value
                will correspond to the custom name you chose for your deployment
                when you deployed a model. This value can be found under
                Resource Management > Deployments in the Azure portal or, alternatively,
                under Management > Deployments in Azure OpenAI Studio.
            endpoint: The endpoint of the Azure deployment. This value
                can be found in the Keys & Endpoint section when examining
                your resource from the Azure portal.
            api_key: The API key for the Azure deployment. This value can be
                found in the Keys & Endpoint section when examining your resource in
                the Azure portal. You can use either KEY1 or KEY2.
            api_version: The API version to use. (Optional)
                The default value is "2023-03-15-preview".
            ad_auth: Whether to use Azure Active Directory authentication. (Optional)
                The default value is False.
            log: The logger instance to use. (Optional)
            logger: deprecated, use 'log' instead.
        """
        if logger:
            logger.warning("The 'logger' argument is deprecated, use 'log' instead.")
        super().__init__(
            model_id=deployment_name,
            endpoint=endpoint,
            api_key=api_key,
            api_version=api_version,
            log=log or logger,
            model_type=OpenAIModelTypes.TEXT,
            api_type="azure_ad" if ad_auth else "azure",
        )

    @classmethod
    def from_dict(cls, settings: Dict[str, str]) -> "AzureTextCompletion":
        """
        Initialize an AzureChatCompletion service from a dictionary of settings.

        Arguments:
            settings: A dictionary of settings for the service.
                should contains keys: deployment_name, endpoint, api_key
                and optionally: api_version, ad_auth, log
        """
        if "api_type" in settings:
            settings["ad_auth"] = settings["api_type"] == "azure_ad"
            del settings["api_type"]

        return AzureTextCompletion(
            deployment_name=settings["deployment_name"],
            endpoint=settings["endpoint"],
            api_key=settings["api_key"],
            api_version=settings.get("api_version"),
            ad_auth=settings.get("ad_auth", False),
            log=settings.get("log"),
        )

    def to_dict(self) -> Dict[str, str]:
        return self.dict(
            exclude={
                "prompt_tokens",
                "completion_tokens",
                "total_tokens",
                "api_type",
                "org_id",
                "model_type",
            },
            by_alias=True,
            exclude_none=True,
        )

    def get_model_args(self) -> Dict[str, Any]:
        return {
            "deployment_id": self.model_id,
            "api_type": self.api_type,
            "api_base": self.endpoint,
            "api_version": self.api_version,
        }

    async def complete_stream_async(
        self,
        prompt: str,
        settings: CompleteRequestSettings,
        logger: Optional[Logger] = None,
    ):
        response = await self._send_request(
            prompt=prompt, request_settings=settings, stream=True
        )

        async for chunk in response:
            if settings.number_of_responses > 1:
                for choice in chunk.choices:
                    completions = [""] * settings.number_of_responses
                    completions[choice.index] = choice.text
                    yield completions
            else:
                yield chunk.choices[0].text

    async def complete_async(
        self,
        prompt: str,
        settings: CompleteRequestSettings,
        logger: Optional[Logger] = None,
    ) -> Union[str, List[str]]:
        response = await self._send_request(
            prompt=prompt, request_settings=settings, stream=False
        )

        if len(response.choices) == 1:
            return response.choices[0].text
        else:
            return [choice.text for choice in response.choices]
