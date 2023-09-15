# Copyright (c) Microsoft. All rights reserved.

from logging import Logger
from typing import Dict, Optional

from semantic_kernel.connectors.ai.open_ai.services.open_ai_chat_completion_base import (
    OpenAIChatCompletionBase,
)


class OpenAIChatCompletion(OpenAIChatCompletionBase):
    def __init__(
        self,
        model_id: str,
        api_key: str,
        org_id: Optional[str] = None,
        log: Optional[Logger] = None,
    ) -> None:
        """
        Initialize an OpenAIChatCompletion service.

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
        kwargs = {
            "model_id": model_id,
            "api_key": api_key,
            "org_id": org_id,
            "api_type": "open_ai",
        }
        if log:
            kwargs["log"] = log
        super().__init__(**kwargs)

    @classmethod
    def from_dict(cls, settings: Dict[str, str]) -> "OpenAIChatCompletion":
        """
        Initialize an OpenAIChatCompletion service from a dictionary of settings.

        Arguments:
            settings: A dictionary of settings for the service.
                should contain keys: model_id, api_key
                and optionally: org_id, log
        """
        if "api_type" in settings:
            settings["ad_auth"] = settings["api_type"] == "azure_ad"
            del settings["api_type"]

        return OpenAIChatCompletion(
            model_id=settings["model_id"],
            api_key=settings["api_key"],
            org_id=settings.get("org_id"),
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
                "api_version",
                "endpoint",
                "api_type",
            },
            by_alias=True,
            exclude_none=True,
        )
