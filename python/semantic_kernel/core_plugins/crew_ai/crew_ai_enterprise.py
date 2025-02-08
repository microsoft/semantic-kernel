# Copyright (c) Microsoft. All rights reserved.

import asyncio
import json
import logging
from collections.abc import Awaitable, Callable
from typing import Any

from pydantic import Field

from semantic_kernel.core_plugins.crew_ai.crew_ai_client import CrewAIEnterpriseClient
from semantic_kernel.core_plugins.crew_ai.crew_ai_models import (
    CrewAIEnterpriseKickoffState,
    CrewAIStatusResponse,
    InputMetadata,
)
from semantic_kernel.core_plugins.crew_ai.crew_ai_settings import CrewAISettings
from semantic_kernel.exceptions.function_exceptions import (
    FunctionExecutionException,
    FunctionResultError,
    PluginInitializationError,
)
from semantic_kernel.functions import kernel_function
from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.functions.kernel_function_from_method import KernelFunctionFromMethod
from semantic_kernel.functions.kernel_parameter_metadata import KernelParameterMetadata
from semantic_kernel.functions.kernel_plugin import KernelPlugin
from semantic_kernel.kernel_pydantic import KernelBaseModel

logger: logging.Logger = logging.getLogger(__name__)


class CrewAIEnterprise(KernelBaseModel):
    """Class to interface with Crew.AI Crews from Semantic Kernel."""

    client: CrewAIEnterpriseClient
    polling_interval: float = Field(default=1.0)

    def __init__(self, settings: CrewAISettings, auth_token_provider: Callable[..., Awaitable[str]] | None = None):
        """Initialize a new instance of the class.

        Args:
            settings (CrewAISettings): The API endpoint.
            auth_token_provider (Optional[callable], optional): A callable to provide the authentication token.
        """
        if not auth_token_provider:
            if not settings.auth_token:
                raise PluginInitializationError("An auth token provider or auth token must be provided.")

            async def auth_token_provider() -> Awaitable[str]:
                await asyncio.sleep(0)  # Yield control to the event loop
                return settings.auth_token.get_secret_value()

        client = CrewAIEnterpriseClient(endpoint=settings.endpoint, auth_token_provider=auth_token_provider)

        super().__init__(
            client=client,
            polling_interval=settings.polling_interval,
        )

    async def kickoff(
        self,
        inputs: dict[str, Any] | None = None,
        task_webhook_url: str | None = None,
        step_webhook_url: str | None = None,
        crew_webhook_url: str | None = None,
    ) -> str:
        """Kickoff a new Crew AI task.

        Args:
            inputs (dict[str, Any], optional): The inputs for the task. Defaults to None.
            task_webhook_url (str | None, optional): The webhook URL for task updates. Defaults to None.
            step_webhook_url (str | None, optional): The webhook URL for step updates. Defaults to None.
            crew_webhook_url (str | None, optional): The webhook URL for crew updates. Defaults to None.

        Returns:
            str: The ID of the kickoff response.
        """
        try:
            kickoff_response = await self.client.kickoff(inputs, task_webhook_url, step_webhook_url, crew_webhook_url)
            logger.info(f"CrewAI Crew kicked off with Id: {kickoff_response.kickoff_id}")
            return kickoff_response.kickoff_id
        except Exception as ex:
            raise FunctionExecutionException("Failed to kickoff CrewAI Crew.") from ex

    @kernel_function(description="Get the status of a Crew AI kickoff.")
    async def get_crew_kickoff_status(self, kickoff_id: str) -> CrewAIStatusResponse:
        """Get the status of a Crew AI task.

        Args:
            kickoff_id (str): The ID of the kickoff response.

        Returns:
            CrewAIStatusResponse: The status response of the task.
        """
        try:
            status_response = await self.client.get_status(kickoff_id)
            logger.info(f"CrewAI Crew status for kickoff Id: {kickoff_id} is {status_response.state}")
            return status_response
        except Exception as ex:
            raise FunctionExecutionException(
                f"Failed to get status of CrewAI Crew with kickoff Id: {kickoff_id}."
            ) from ex

    @kernel_function(description="Wait for the completion of a Crew AI kickoff.")
    async def wait_for_crew_completion(self, kickoff_id: str) -> str:
        """Wait for the completion of a Crew AI task.

        Args:
            kickoff_id (str): The ID of the kickoff response.

        Returns:
            str: The result of the task.

        Raises:
            FunctionExecutionException: If the task fails or an error occurs while waiting for completion.
        """
        try:
            status_response = None
            status = CrewAIEnterpriseKickoffState.Pending
            while status not in [
                CrewAIEnterpriseKickoffState.Failed,
                CrewAIEnterpriseKickoffState.Failure,
                CrewAIEnterpriseKickoffState.Success,
                CrewAIEnterpriseKickoffState.Not_Found,
            ]:
                logger.info(
                    f"Waiting for CrewAI Crew with kickoff Id: {kickoff_id} to complete. Current state: {status}"
                )

                await asyncio.sleep(self.polling_interval)
                status_response = await self.client.get_status(kickoff_id)
                status = status_response.state

            logger.info(f"CrewAI Crew with kickoff Id: {kickoff_id} completed with status: {status_response.state}")
            if status in ["Failed", "Failure"]:
                raise FunctionResultError(f"CrewAI Crew failed with error: {status_response.result}")
            return status_response.result or ""
        except Exception as ex:
            raise FunctionExecutionException(
                f"Failed to wait for completion of CrewAI Crew with kickoff Id: {kickoff_id}."
            ) from ex

    def create_kernel_plugin(
        self,
        name: str,
        description: str,
        input_metadata: list[InputMetadata] | None = None,
        task_webhook_url: str | None = None,
        step_webhook_url: str | None = None,
        crew_webhook_url: str | None = None,
    ) -> dict[str, Any]:
        """Creates a kernel plugin that can be used to invoke the CrewAI Crew.

        Args:
            name (str): The name of the kernel plugin.
            description (str): The description of the kernel plugin.
            input_metadata (Optional[List[InputMetadata]], optional): The definitions of the Crew's
            required inputs. Defaults to None.
            task_webhook_url (Optional[str], optional): The task level webhook URL. Defaults to None.
            step_webhook_url (Optional[str], optional): The step level webhook URL. Defaults to None.
            crew_webhook_url (Optional[str], optional): The crew level webhook URL. Defaults to None.

        Returns:
            dict[str, Any]: A dictionary representing the kernel plugin.
        """

        def build_metadata(input_metadata: InputMetadata) -> KernelParameterMetadata:
            return KernelParameterMetadata(
                name=input_metadata.name,
                description=input_metadata.description,
                default_value=None,
                type=input_metadata.type,
                is_required=True,
            )

        parameters = [
            KernelParameterMetadata(name="arguments", description=None, type="KernelArguments", is_required=True)
        ]
        parameters.extend([build_metadata(input) for input in input_metadata or []])

        @kernel_function(description="Kickoff the CrewAI task.")
        async def kickoff(arguments: KernelArguments, **kwargs: Any) -> str:
            args = self._build_arguments(input_metadata, arguments)
            return await self.kickoff(
                inputs=args,
                task_webhook_url=task_webhook_url,
                step_webhook_url=step_webhook_url,
                crew_webhook_url=crew_webhook_url,
            )

        @kernel_function(description="Kickoff the CrewAI task and wait for completion.")
        async def kickoff_and_wait(arguments: KernelArguments, **kwargs: Any) -> str:
            args = self._build_arguments(input_metadata, arguments)
            kickoff_id = await self.kickoff(
                inputs=args,
                task_webhook_url=task_webhook_url,
                step_webhook_url=step_webhook_url,
                crew_webhook_url=crew_webhook_url,
            )
            return await self.wait_for_crew_completion(kickoff_id)

        return KernelPlugin(
            name,
            description,
            {
                "kickoff": KernelFunctionFromMethod(kickoff, stream_method=None, parameters=parameters),
                "kickoff_and_wait": KernelFunctionFromMethod(
                    kickoff_and_wait, stream_method=None, parameters=parameters
                ),
                "get_status": self.get_crew_kickoff_status,
                "wait_for_completion": self.wait_for_crew_completion,
            },
        )

    def _build_arguments(
        self, input_metadata: list[InputMetadata] | None, arguments: KernelArguments
    ) -> dict[str, Any]:
        """Builds the arguments for the CrewAI task from the provided metadata and arguments.

        Args:
            input_metadata (Optional[List[InputMetadata]]): The metadata for the inputs.
            arguments (dict[str, Any]): The provided arguments.

        Returns:
            dict[str, Any]: The built arguments.
        """
        args = {}
        if input_metadata:
            for input in input_metadata:
                name = input.name
                if name not in arguments:
                    raise PluginInitializationError(f"Missing required input '{name}' for CrewAI.")
                value = arguments[name]
                if input.type == "string":
                    args[name] = value
                else:
                    args[name] = json.loads(value)
        return args
