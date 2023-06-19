from logging import Logger
from typing import Optional

import guidance

from semantic_kernel.connectors.ai.complete_request_settings import (
    CompleteRequestSettings,
)
from semantic_kernel.connectors.ai.text_completion_client_base import (
    TextCompletionClientBase,
)
from semantic_kernel.orchestration.sk_context import SKContext
from semantic_kernel.utils.null_logger import NullLogger


class GuidanceOAITextCompletion(TextCompletionClientBase):
    def __init__(
        self,
        model_id: str,
        api_key: str,
        api_type: Optional[str] = None,
        api_version: Optional[str] = None,
        endpoint: Optional[str] = None,
        log: Optional[Logger] = None,
    ) -> None:
        self._model_id = model_id
        self._api_key = api_key
        self._api_type = api_type
        self._api_version = api_version
        self._endpoint = endpoint
        self._log = log if log is not None else NullLogger()

        guidance.llm = guidance.llms.OpenAI(model=self._model_id, api_key=self._api_key)

    async def complete_async(
        self, prompt: str, request_settings: CompleteRequestSettings, context: SKContext
    ) -> str:
        program = guidance.Program(prompt)

        if context is None:
            raise ValueError(
                "Context cannot be none for the GuidanceOAITextCompletion connector"
            )

        executed_program = program(**context.variables.dict)

        if not executed_program.text:
            raise ValueError("GuidanceOAITextCompletion returned an empty response")

        return executed_program.text

    async def complete_stream_async(
        self, prompt: str, request_settings: CompleteRequestSettings
    ):
        raise ValueError(
            "GuidanceOAITextCompletion complete_stream_async not implemented"
        )
