# Copyright (c) Microsoft. All rights reserved.

from logging import Logger
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union

from semantic_kernel.connectors.ai import TextCompletionClientBase
from semantic_kernel.connectors.ai.complete_request_settings import (
    CompleteRequestSettings,
)
from semantic_kernel.connectors.ai.open_ai.services.base_open_ai_service_calls import (
    OpenAIModelTypes,
    OpenAIServiceCalls,
)

if TYPE_CHECKING:
    from semantic_kernel.connectors.ai.open_ai.services.open_ai_chat_completion import (
        OpenAIChatCompletion,
    )


class OpenAITextCompletion(OpenAIServiceCalls, TextCompletionClientBase):
    api_type: str
    org_id: Optional[str] = None

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
            api_type="open_ai",
            log=log,
            model_type=OpenAIModelTypes.TEXT,
        )

    @classmethod
    def from_dict(
        cls, settings: Dict[str, str]
    ) -> Union["OpenAITextCompletion", "OpenAIChatCompletion"]:
        """
        Initialize an OpenAIChatCompletion service from a dictionary of settings.

        Arguments:
            settings: A dictionary of settings for the service.
        """
        return cls(
            model_id=settings["model_id"],
            api_key=settings["api_key"],
            org_id=settings.get("org_id"),
            log=settings.get("log"),
        )

    def to_dict(self) -> Dict[str, str]:
        """
        Create a dict of the service settings.
        """
        return self.dict(
            exclude={
                "prompt_tokens",
                "completion_tokens",
                "total_tokens",
                "api_type",
                "model_type",
            },
            by_alias=True,
            exclude_none=True,
        )

    def get_model_args(self) -> Dict[str, Any]:
        model_args = {
            "model": self.model_id,
            "api_type": "open_ai",
        }
        if self.org_id:
            model_args["organization"] = self.org_id
        return model_args

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
            prompt=prompt, request_settings=settings, stream=True
        )

        if len(response.choices) == 1:
            return response.choices[0].text
        else:
            return [choice.text for choice in response.choices]
