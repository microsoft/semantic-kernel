# Copyright (c) Microsoft. All rights reserved.

import asyncio
import contextlib
from abc import ABC
from enum import Enum
from typing import Any

from azure.ai.inference.aio import ChatCompletionsClient, EmbeddingsClient
from azure.core.credentials import AzureKeyCredential
from pydantic import ValidationError

from semantic_kernel.connectors.ai.azure_ai_inference.azure_ai_inference_settings import AzureAIInferenceSettings
from semantic_kernel.exceptions.service_exceptions import ServiceInitializationError
from semantic_kernel.kernel_pydantic import KernelBaseModel
from semantic_kernel.utils.authentication.async_default_azure_credential_wrapper import (
    AsyncDefaultAzureCredentialWrapper,
)
from semantic_kernel.utils.feature_stage_decorator import experimental
from semantic_kernel.utils.telemetry.user_agent import SEMANTIC_KERNEL_USER_AGENT


class AzureAIInferenceClientType(Enum):
    """Client type for Azure AI Inference."""

    ChatCompletions = "ChatCompletions"
    Embeddings = "Embeddings"

    @classmethod
    def get_client_class(cls, client_type: "AzureAIInferenceClientType") -> Any:
        """Get the client class based on the client type."""
        class_mapping = {
            cls.ChatCompletions: ChatCompletionsClient,
            cls.Embeddings: EmbeddingsClient,
        }

        return class_mapping[client_type]


@experimental
class AzureAIInferenceBase(KernelBaseModel, ABC):
    """Azure AI Inference Chat Completion Service."""

    client: ChatCompletionsClient | EmbeddingsClient
    managed_client: bool = False

    def __init__(
        self,
        client_type: AzureAIInferenceClientType,
        api_key: str | None = None,
        endpoint: str | None = None,
        env_file_path: str | None = None,
        env_file_encoding: str | None = None,
        client: ChatCompletionsClient | EmbeddingsClient | None = None,
        instruction_role: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize the Azure AI Inference Chat Completion service.

        If no arguments are provided, the service will attempt to load the settings from the environment.
        The following environment variables are used:
        - AZURE_AI_INFERENCE_API_KEY
        - AZURE_AI_INFERENCE_ENDPOINT

        Args:
            client_type (AzureAIInferenceClientType): The client type to use.
            api_key (str | None): The API key for the Azure AI Inference service deployment. (Optional)
            endpoint (str | None): The endpoint of the Azure AI Inference service deployment. (Optional)
            env_file_path (str | None): The path to the environment file. (Optional)
            env_file_encoding (str | None): The encoding of the environment file. (Optional)
            client (ChatCompletionsClient | None): The Azure AI Inference client to use. (Optional)
            instruction_role (str | None): The role to use for 'instruction' messages. (Optional)
            **kwargs: Additional keyword arguments.

        Raises:
            ServiceInitializationError: If an error occurs during initialization.
        """
        managed_client = client is None
        if not client:
            try:
                azure_ai_inference_settings = AzureAIInferenceSettings(
                    api_key=api_key,
                    endpoint=endpoint,
                    env_file_path=env_file_path,
                    env_file_encoding=env_file_encoding,
                )
            except ValidationError as e:
                raise ServiceInitializationError(f"Failed to validate Azure AI Inference settings: {e}") from e

            endpoint = str(azure_ai_inference_settings.endpoint)
            if azure_ai_inference_settings.api_key is not None:
                client = AzureAIInferenceClientType.get_client_class(client_type)(
                    endpoint=endpoint,
                    credential=AzureKeyCredential(azure_ai_inference_settings.api_key.get_secret_value()),
                    user_agent=SEMANTIC_KERNEL_USER_AGENT,
                )
            else:
                # Try to create the client with a DefaultAzureCredential
                client = AzureAIInferenceClientType.get_client_class(client_type)(
                    endpoint=endpoint,
                    credential=AsyncDefaultAzureCredentialWrapper(),
                    user_agent=SEMANTIC_KERNEL_USER_AGENT,
                )

        args: dict[str, Any] = {
            "client": client,
            "managed_client": managed_client,
            **kwargs,
        }

        if instruction_role:
            args["instruction_role"] = instruction_role

        super().__init__(**args)

    def __del__(self) -> None:
        """Close the client when the object is deleted."""
        if self.managed_client:
            with contextlib.suppress(Exception):
                asyncio.get_running_loop().create_task(self.client.close())
