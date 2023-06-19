from logging import Logger
from typing import Optional

import guidance

from semantic_kernel.connectors.ai.guidance.services.guidance_oai_text_completion import (
    GuidanceOAITextCompletion,
)
from semantic_kernel.utils.null_logger import NullLogger


class GuidanceAOAITextCompletion(GuidanceOAITextCompletion):
    def __init__(
        self,
        model_id: str,
        deployment_name: str,
        api_key: str,
        api_type: Optional[str] = None,
        api_version: Optional[str] = "2022-12-01",
        endpoint: Optional[str] = None,
        logger: Optional[Logger] = None,
    ) -> None:
        self._log = logger if logger is not None else NullLogger()

        if api_type == "azure_ad":
            raise ValueError("Azure AD is not supported for this connector")

        if not deployment_name:
            raise ValueError("The deployment name cannot be `None` or empty")
        if not api_key:
            raise ValueError("The Azure API key cannot be `None` or empty`")
        if not endpoint:
            raise ValueError("The Azure endpoint cannot be `None` or empty")
        if not endpoint.startswith("https://"):
            raise ValueError("The Azure endpoint must start with https://")

        guidance.llm = guidance.llms.OpenAI(
            model=model_id,
            api_base=endpoint,
            api_type="azure",
            deployment_id=deployment_name,
            api_key=api_key,
            api_version=api_version,
            endpoint=endpoint,
        )
