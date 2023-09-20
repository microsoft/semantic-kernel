# Copyright (c) Microsoft. All rights reserved.


from logging import Logger
from typing import TYPE_CHECKING, Any, Dict, Optional

from pydantic import Field, constr

from semantic_kernel.connectors.ai.open_ai.services.base_open_ai_functions import (
    OpenAIModelTypes,
    OpenAIServiceCalls,
)
from semantic_kernel.sk_pydantic import HttpsUrl

if TYPE_CHECKING:
    pass


class BaseAzureConfig(OpenAIServiceCalls):
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
        model_type: Optional[OpenAIModelTypes],
        api_version: str = "2022-12-01",
        ad_auth: bool = False,
        log: Optional[Logger] = None,
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
        super().__init__(
            model_id=deployment_name,
            endpoint=endpoint,
            api_key=api_key,
            api_version=api_version,
            log=log,
            model_type=model_type,
            api_type="azure_ad" if ad_auth else "azure",
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
