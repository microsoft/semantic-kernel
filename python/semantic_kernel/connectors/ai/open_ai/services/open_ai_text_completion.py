# Copyright (c) Microsoft. All rights reserved.

from logging import Logger
from typing import Dict, Optional

from semantic_kernel.connectors.ai.open_ai.services.base_config_open_ai import (
    BaseOpenAIConfig,
)
from semantic_kernel.connectors.ai.open_ai.services.base_open_ai_functions import (
    OpenAIModelTypes,
)
from semantic_kernel.connectors.ai.open_ai.services.base_text_completion import (
    BaseTextCompletion,
)


class OpenAITextCompletion(BaseTextCompletion, BaseOpenAIConfig):
    def __init__(
        self,
        model_id: str,
        api_key: str,
        org_id: Optional[str] = None,
        log: Optional[Logger] = None,
    ) -> None:
        """
        Initialize an OpenAITextCompletion service.

        Arguments:
            model_id {str} -- OpenAI model name, see
                https://platform.openai.com/docs/models
            api_key {str} -- OpenAI API key, see
                https://platform.openai.com/account/api-keys
            org_id {Optional[str]} -- OpenAI organization ID.
                This is usually optional unless your
                account belongs to multiple organizations.
            log {Optional[Logger]} -- The logger instance to use. (Optional)
        """
        super().__init__(
            model_id=model_id,
            api_key=api_key,
            org_id=org_id,
            log=log,
            model_type=OpenAIModelTypes.TEXT,
        )

    @classmethod
    def from_dict(cls, settings: Dict[str, str]) -> "OpenAITextCompletion":
        """
        Initialize an Open AI service from a dictionary of settings.

        Arguments:
            settings: A dictionary of settings for the service.
        """

        return OpenAITextCompletion(
            model_id=settings["model_id"],
            api_key=settings["api_key"],
            org_id=settings.get("org_id"),
            log=settings.get("log"),
        )
