# Copyright (c) Microsoft. All rights reserved.

import logging

from mistralai.async_client import MistralAsyncClient
from pydantic import ConfigDict, Field, validate_call

from semantic_kernel.connectors.ai.mistral_ai.services.mistral_ai_handler import MistralAIHandler
from semantic_kernel.exceptions import ServiceInitializationError

logger: logging.Logger = logging.getLogger(__name__)


class MistralAIConfigBase(MistralAIHandler):
    @validate_call(config=ConfigDict(arbitrary_types_allowed=True))
    def __init__(
        self,
        ai_model_id: str = Field(min_length=1),
        api_key: str | None = Field(min_length=1),
        service_id: str | None = None,
        async_client: MistralAsyncClient | None = None,
    ) -> None:
        """Initialize a client for MistralAI services.

        This constructor sets up a client to interact with MistralAI's API, allowing for
        different types of AI model interactions, like chat or text completion.

        Args:
            ai_model_id (str): MistralAI model identifier. Must be non-empty.
                Default to a preset value.
            api_key (Optional[str]): MistralAI API key for authentication.
                Must be non-empty. (Optional)
            ai_model_type (Optional[MistralAIModelTypes]): The type of MistralAI
                model to interact with. Defaults to CHAT.
            service_id (Optional[str]): MistralAI service ID. This is optional.
            async_client (Optional[MistralAsyncClient]): An existing MistralAI client

        """
        if not async_client:
            if not api_key:
                raise ServiceInitializationError("Please provide an api_key")
            async_client = MistralAsyncClient(
                api_key=api_key,
            )
        args = {
            "ai_model_id": ai_model_id,
            "client": async_client,
        }
        if service_id:
            args["service_id"] = service_id
        super().__init__(**args)

    def to_dict(self) -> dict[str, str]:
        """Create a dict of the service settings."""
        client_settings = {
            "api_key": self.client.api_key,
        }

        base = self.model_dump(
            exclude={
                "prompt_tokens",
                "completion_tokens",
                "total_tokens",
                "api_type",
                "ai_model_type",
                "service_id",
                "client",
            },
            by_alias=True,
            exclude_none=True,
        )
        base.update(client_settings)
        return base
