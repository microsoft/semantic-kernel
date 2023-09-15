# Copyright (c) Microsoft. All rights reserved.


from logging import Logger
from typing import Dict, Optional

from pydantic import Field, HttpUrl, constr

from semantic_kernel.connectors.ai.open_ai.services.open_ai_chat_completion_base import (
    OpenAIChatCompletionBase,
)


class AzureChatCompletion(OpenAIChatCompletionBase):
    model_id: constr(strip_whitespace=True, min_length=1) = Field(
        ..., alias="deployment_name"
    )

    def __init__(
        self,
        deployment_name: str,
        endpoint: HttpUrl,
        api_key: str,
        api_version: Optional[str] = "2023-03-15-preview",
        ad_auth: bool = False,
        log: Optional[Logger] = None,
        logger: Optional[Logger] = None,
    ) -> None:
        """
        Initialize an AzureChatCompletion service.

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
        kwargs = {
            "model_id": deployment_name,
            "endpoint": endpoint,
            "api_key": api_key,
            "api_version": api_version,
            "api_type": "azure_ad" if ad_auth else "azure",
        }
        if logger:
            logger.warning("The 'logger' argument is deprecated, use 'log' instead.")
            kwargs["log"] = logger
        if log:
            kwargs["log"] = log
        super().__init__(**kwargs)

    @classmethod
    def from_dict(cls, settings: Dict[str, str]) -> "AzureChatCompletion":
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

        return AzureChatCompletion(
            deployment_name=settings["deployment_name"],
            endpoint=settings["endpoint"],
            api_key=settings["api_key"],
            api_version=settings.get("api_version"),
            ad_auth=settings.get("ad_auth", False),
            log=settings.get("log"),
            # TODO: figure out if we need to be able to reinitialize the token counters.
        )

    def to_dict(self) -> Dict[str, str]:
        """
        Create a dict of the service settings.
        """
        # TODO: figure out if we need to be able to reinitialize the token counters.
        return self.dict(
            exclude={
                "prompt_tokens",
                "completion_tokens",
                "total_tokens",
                "api_type",
                "org_id",
            },
            by_alias=True,
        )
