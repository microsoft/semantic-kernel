# Copyright (c) Microsoft. All rights reserved.


from logging import Logger
from typing import TYPE_CHECKING, Any, Dict, Optional

from pydantic import Field, constr

from semantic_kernel.connectors.ai.open_ai.services.open_ai_handler import (
    OpenAIHandler,
    OpenAIModelTypes,
)
from semantic_kernel.sk_pydantic import HttpsUrl

if TYPE_CHECKING:
    pass


class AzureOpenAIConfigBase(OpenAIHandler):
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
