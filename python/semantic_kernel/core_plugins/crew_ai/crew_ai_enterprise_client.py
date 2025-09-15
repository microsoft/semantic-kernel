# Copyright (c) Microsoft. All rights reserved.

from typing import Any

import aiohttp

from semantic_kernel.core_plugins.crew_ai.crew_ai_models import (
    CrewAIKickoffResponse,
    CrewAIRequiredInputs,
    CrewAIStatusResponse,
)
from semantic_kernel.utils.telemetry.user_agent import SEMANTIC_KERNEL_USER_AGENT


class CrewAIEnterpriseClient:
    """Client to interact with the Crew AI Enterprise API."""

    def __init__(
        self,
        endpoint: str,
        auth_token: str,
        session: aiohttp.ClientSession | None = None,
    ):
        """Initializes a new instance of the CrewAIEnterpriseClient class.

        Args:
            endpoint (str): The API endpoint.
            auth_token (str): The authentication token.
            session (aiohttp.ClientSession | None, optional): The HTTP client session. Defaults to None.
        """
        self.endpoint = endpoint
        self.auth_token = auth_token
        self.session = session if session is None else aiohttp.ClientSession()
        self.request_header = {
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json",
            "user_agent": SEMANTIC_KERNEL_USER_AGENT,
        }

    async def get_inputs(self) -> CrewAIRequiredInputs:
        """Get the required inputs for Crew AI.

        Returns:
            CrewAIRequiredInputs: The required inputs for Crew AI.
        """
        async with (
            self.session.get(f"{self.endpoint}/inputs", headers=self.request_header) as response,  # type: ignore
        ):
            response.raise_for_status()
            return CrewAIRequiredInputs.model_validate_json(await response.text())

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
            self.session.post(f"{self.endpoint}/kickoff", json=content, headers=self.request_header) as response,  # type: ignore
        ):
            response.raise_for_status()
            body = await response.text()
            return CrewAIKickoffResponse.model_validate_json(body)

    async def get_status(self, task_id: str) -> CrewAIStatusResponse:
        """Get the status of a Crew AI task.

        Args:
            task_id (str): The ID of the task.

        Returns:
            CrewAIStatusResponse: The status response of the task.
        """
        async with (
            self.session.get(f"{self.endpoint}/status/{task_id}", headers=self.request_header) as response,  # type: ignore
        ):
            response.raise_for_status()
            body = await response.text()
            return CrewAIStatusResponse.model_validate_json(body)

    async def __aenter__(self):
        """Enter the session."""
        await self.session.__aenter__()  # type: ignore
        return self

    async def __aexit__(self, *args, **kwargs):
        """Close the session."""
        await self.session.close()  # type: ignore
