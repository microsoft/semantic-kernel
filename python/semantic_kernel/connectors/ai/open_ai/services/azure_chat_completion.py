# Copyright (c) Microsoft. All rights reserved.


from logging import Logger
from typing import Optional

from pydantic import HttpUrl

from semantic_kernel.connectors.ai.open_ai.services.open_ai_chat_completion import (
    OpenAIChatCompletionBase,
)


class AzureChatCompletion(OpenAIChatCompletionBase):
    def __init__(
        self,
        deployment_name: str,
        endpoint: HttpUrl,
        api_key: str,
        api_version: Optional[str] = "2023-03-15-preview",
        ad_auth: bool = False,
        log: Optional[Logger] = None,
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
        """
        kwargs = {
            "model_id": deployment_name,
            "endpoint": endpoint,
            "api_key": api_key,
            "api_version": api_version,
            "api_type": "azure_ad" if ad_auth else "azure",
        }
        if log:
            kwargs["log"] = log
        super().__init__(**kwargs)
