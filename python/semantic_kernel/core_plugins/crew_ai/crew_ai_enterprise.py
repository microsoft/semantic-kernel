# Copyright (c) Microsoft. All rights reserved.

import asyncio
import logging
from typing import Any

import aiohttp
from pydantic import Field, ValidationError

from semantic_kernel.core_plugins.crew_ai.crew_ai_enterprise_client import CrewAIEnterpriseClient
from semantic_kernel.core_plugins.crew_ai.crew_ai_models import CrewAIEnterpriseKickoffState, CrewAIStatusResponse
from semantic_kernel.core_plugins.crew_ai.crew_ai_settings import CrewAISettings
from semantic_kernel.exceptions.function_exceptions import (
    FunctionExecutionException,
    FunctionResultError,
    PluginInitializationError,
)
from semantic_kernel.functions import kernel_function
from semantic_kernel.functions.kernel_function_from_method import KernelFunctionFromMethod
from semantic_kernel.functions.kernel_parameter_metadata import KernelParameterMetadata
from semantic_kernel.functions.kernel_plugin import KernelPlugin
from semantic_kernel.kernel_pydantic import KernelBaseModel
from semantic_kernel.utils.feature_stage_decorator import experimental

logger: logging.Logger = logging.getLogger(__name__)


@experimental
class CrewAIEnterprise(KernelBaseModel):
    """Class to interface with Crew.AI Crews from Semantic Kernel.

    This object can be used directly or as a plugin in the Kernel.
    """

    client: CrewAIEnterpriseClient
    polling_interval: float = Field(default=1.0)
    polling_timeout: float = Field(default=30.0)

    def __init__(
        self,
        endpoint: str | None = None,
        auth_token: str | None = None,
        polling_interval: float | None = 1.0,
        polling_timeout: float | None = 30.0,
        session: aiohttp.ClientSession | None = None,
        env_file_path: str | None = None,
        env_file_encoding: str | None = None,
    ):
        """Initialize a new instance of the class.  This object can be used directly or as a plugin in the Kernel.

        Args:
            endpoint (str | None, optional): The API endpoint.
            auth_token (str | None, optional): The authentication token.
            polling_interval (float, optional): The polling interval in seconds. Defaults to 1.0.
            polling_timeout (float, optional): The polling timeout in seconds. Defaults to 30.0.
            session (aiohttp.ClientSession | None, optional): The HTTP client session. Defaults to None.
            env_file_path (str | None): Use the environment settings file as a
                fallback to environment variables. (Optional)
            env_file_encoding (str | None): The encoding of the environment settings file. (Optional)
        """
        try:
            settings = CrewAISettings(
                endpoint=endpoint,
                auth_token=auth_token,
                polling_interval=polling_interval,
                polling_timeout=polling_timeout,
                env_file_path=env_file_path,
                env_file_encoding=env_file_encoding,
            )
        except ValidationError as ex:
            raise PluginInitializationError("Failed to initialize CrewAI settings.") from ex

        client = CrewAIEnterpriseClient(
            endpoint=settings.endpoint, auth_token=settings.auth_token.get_secret_value(), session=session
        )

        super().__init__(
            client=client,
            polling_interval=settings.polling_interval,
            polling_timeout=settings.polling_timeout,
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
        status_response: CrewAIStatusResponse | None = None
        state: str = CrewAIEnterpriseKickoffState.Pending

        async def poll_status():
            nonlocal state, status_response
            while state not in [
                CrewAIEnterpriseKickoffState.Failed,
                CrewAIEnterpriseKickoffState.Failure,
                CrewAIEnterpriseKickoffState.Success,
                CrewAIEnterpriseKickoffState.Not_Found,
            ]:
                logger.debug(
                    f"Waiting for CrewAI Crew with kickoff Id: {kickoff_id} to complete. Current state: {state}"
                )

                await asyncio.sleep(self.polling_interval)

                try:
                    status_response = await self.client.get_status(kickoff_id)
                    state = status_response.state
                except Exception as ex:
                    raise FunctionExecutionException(
                        f"Failed to wait for completion of CrewAI Crew with kickoff Id: {kickoff_id}."
                    ) from ex

        await asyncio.wait_for(poll_status(), timeout=self.polling_timeout)

        logger.info(f"CrewAI Crew with kickoff Id: {kickoff_id} completed with status: {state}")
        result = status_response.result if status_response is not None and status_response.result is not None else ""

        if state in ["Failed", "Failure"]:
            raise FunctionResultError(f"CrewAI Crew failed with error: {result}")

        return result

    def create_kernel_plugin(
        self,
        name: str,
        description: str,
        parameters: list[KernelParameterMetadata] | None = None,
        task_webhook_url: str | None = None,
        step_webhook_url: str | None = None,
        crew_webhook_url: str | None = None,
    ) -> KernelPlugin:
        """Creates a kernel plugin that can be used to invoke the CrewAI Crew.

        Args:
            name (str): The name of the kernel plugin.
            description (str): The description of the kernel plugin.
            parameters (List[KernelParameterMetadata] | None, optional): The definitions of the Crew's
            required inputs. Defaults to None.
            task_webhook_url (Optional[str], optional): The task level webhook URL. Defaults to None.
            step_webhook_url (Optional[str], optional): The step level webhook URL. Defaults to None.
            crew_webhook_url (Optional[str], optional): The crew level webhook URL. Defaults to None.

        Returns:
            dict[str, Any]: A dictionary representing the kernel plugin.
        """

        @kernel_function(description="Kickoff the CrewAI task.")
        async def kickoff(**kwargs: Any) -> str:
            args = self._build_arguments(parameters, kwargs)
            return await self.kickoff(
                inputs=args,
                task_webhook_url=task_webhook_url,
                step_webhook_url=step_webhook_url,
                crew_webhook_url=crew_webhook_url,
            )

        @kernel_function(description="Kickoff the CrewAI task and wait for completion.")
        async def kickoff_and_wait(**kwargs: Any) -> str:
            args = self._build_arguments(parameters, kwargs)
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
        self, parameters: list[KernelParameterMetadata] | None, arguments: dict[str, Any]
    ) -> dict[str, Any]:
        """Builds the arguments for the CrewAI task from the provided parameters and arguments.

        Args:
            parameters (List[KernelParameterMetadata] | None): The metadata for the inputs.
            arguments (dict[str, Any]): The provided arguments.

        Returns:
            dict[str, Any]: The built arguments.
        """
        args = {}
        if parameters:
            for input in parameters:
                name = input.name
                if name not in arguments:
                    raise PluginInitializationError(f"Missing required input '{name}' for CrewAI.")
                args[name] = arguments[name]
        return args

    async def __aenter__(self):
        """Enter the session."""
        await self.client.__aenter__()
        return self

    async def __aexit__(self, *args, **kwargs):
        """Close the session."""
        await self.client.__aexit__()
