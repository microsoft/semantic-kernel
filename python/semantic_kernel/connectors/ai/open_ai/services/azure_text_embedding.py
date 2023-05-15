# Copyright (c) Microsoft. All rights reserved.


from logging import Logger
from typing import Optional

from semantic_kernel.connectors.ai.open_ai.services.open_ai_text_embedding import (
    OpenAITextEmbedding,
)


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
        ad_auth=False,
    ) -> None:
        """
        Initialize an AzureTextEmbedding service.

        You must provide:
        - A deployment_name, endpoint, and api_key (plus, optionally: ad_auth)

        :param deployment_name: The name of the Azure deployment. This value
            will correspond to the custom name you chose for your deployment
            when you deployed a model. This value can be found under
            Resource Management > Deployments in the Azure portal or, alternatively,
            under Management > Deployments in Azure OpenAI Studio.
        :param endpoint: The endpoint of the Azure deployment. This value
            can be found in the Keys & Endpoint section when examining
            your resource from the Azure portal.
        :param api_key: The API key for the Azure deployment. This value can be
            found in the Keys & Endpoint section when examining your resource in
            the Azure portal. You can use either KEY1 or KEY2.
        :param api_version: The API version to use. (Optional)
            The default value is "2022-12-01".
        :param logger: The logger instance to use. (Optional)
        :param ad_auth: Whether to use Azure Active Directory authentication.
            (Optional) The default value is False.
        """
        if not deployment_name:
            raise ValueError("The deployment name cannot be `None` or empty")
        if not api_key:
            raise ValueError("The Azure API key cannot be `None` or empty`")
        if not endpoint:
            raise ValueError("The Azure endpoint cannot be `None` or empty")
        if not endpoint.startswith("https://"):
            raise ValueError("The Azure endpoint must start with https://")

        self._api_type = "azure_ad" if ad_auth else "azure"

        super().__init__(
            deployment_name,
            api_key,
            api_type=self._api_type,
            api_version=api_version,
            endpoint=endpoint,
            org_id=None,
            log=logger,
        )
