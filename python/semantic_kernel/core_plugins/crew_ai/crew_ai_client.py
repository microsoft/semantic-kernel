# Copyright (c) Microsoft. All rights reserved.

import json
from collections.abc import Awaitable, Callable
from typing import Any

import aiohttp

from semantic_kernel.core_plugins.crew_ai.crew_ai_models import (
    CrewAIKickoffResponse,
    CrewAIRequiredInputs,
    CrewAIStatusResponse,
)
from semantic_kernel.kernel_pydantic import KernelBaseModel


class CrewAIEnterpriseClient(KernelBaseModel):
    """Client to interact with the Crew AI Enterprise API."""

    endpoint: str
    auth_token_provider: Callable[..., Awaitable[str]]

    async def get_inputs(self) -> CrewAIRequiredInputs:
        """Get the required inputs for Crew AI.

        Returns:
            CrewAIRequiredInputs: The required inputs for Crew AI.
        """
        async with await self._create_http_client() as client, client.get(f"{self.endpoint}/inputs") as response:
            response.raise_for_status()
            body = await response.text()
            return CrewAIRequiredInputs(**json.loads(body))

    async def kickoff(
        self,
        inputs: dict[str, Any] | None = None,
        task_webhook_url: str | None = None,
        step_webhook_url: str | None = None,
        crew_webhook_url: str | None = None,
    ) -> CrewAIKickoffResponse:
        """Kickoff a new Crew AI task.

        Args:
            inputs (Optional[dict[str, Any]], optional): The inputs for the task. Defaults to None.
            task_webhook_url (Optional[str], optional): The webhook URL for task updates. Defaults to None.
            step_webhook_url (Optional[str], optional): The webhook URL for step updates. Defaults to None.
            crew_webhook_url (Optional[str], optional): The webhook URL for crew updates. Defaults to None.

        Returns:
            CrewAIKickoffResponse: The response from the kickoff request.
        """
        content = {
            "inputs": inputs,
            "taskWebhookUrl": task_webhook_url,
            "stepWebhookUrl": step_webhook_url,
            "crewWebhookUrl": crew_webhook_url,
        }
        async with (
            await self._create_http_client() as client,
            client.post(f"{self.endpoint}/kickoff", json=content) as response,
        ):
            response.raise_for_status()
            body = await response.text()
            return CrewAIKickoffResponse(**json.loads(body))

    async def get_status(self, task_id: str) -> CrewAIStatusResponse:
        """Get the status of a Crew AI task.

        Args:
            task_id (str): The ID of the task.

        Returns:
            CrewAIStatusResponse: The status response of the task.
        """
        async with (
            await self._create_http_client() as client,
            client.get(f"{self.endpoint}/status/{task_id}") as response,
        ):
            response.raise_for_status()
            body = await response.text()
            return CrewAIStatusResponse(**json.loads(body))

    async def _create_http_client(self) -> aiohttp.ClientSession:
        """Create an HTTP client session with the necessary headers.

        Returns:
            aiohttp.ClientSession: The HTTP client session.
        """
        auth_token = await self.auth_token_provider()
        headers = {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}
        return aiohttp.ClientSession(headers=headers)
