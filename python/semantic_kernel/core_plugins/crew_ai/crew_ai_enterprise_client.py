# Copyright (c) Microsoft. All rights reserved.

from typing import Any

import aiohttp

from semantic_kernel.connectors.memory.astradb.utils import AsyncSession
from semantic_kernel.core_plugins.crew_ai.crew_ai_models import (
    CrewAIKickoffResponse,
    CrewAIRequiredInputs,
    CrewAIStatusResponse,
)
from semantic_kernel.kernel_pydantic import KernelBaseModel
from semantic_kernel.utils.telemetry.user_agent import SEMANTIC_KERNEL_USER_AGENT


class CrewAIEnterpriseClient(KernelBaseModel):
    """Client to interact with the Crew AI Enterprise API."""

    endpoint: str
    auth_token: str
    request_header: dict[str, str]
    session: aiohttp.ClientSession | None

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
            session (Optional[aiohttp.ClientSession], optional): The HTTP client session. Defaults to None.
        """
        request_header = {
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json",
            "user_agent": SEMANTIC_KERNEL_USER_AGENT,
        }

        session = session
        super().__init__(endpoint=endpoint, auth_token=auth_token, request_header=request_header, session=session)

    async def get_inputs(self) -> CrewAIRequiredInputs:
        """Get the required inputs for Crew AI.

        Returns:
            CrewAIRequiredInputs: The required inputs for Crew AI.
        """
        async with (
            AsyncSession(self.session) as session,
            session.get(f"{self.endpoint}/inputs", headers=self.request_header) as response,
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
            AsyncSession(self.session) as session,
            session.post(f"{self.endpoint}/kickoff", json=content, headers=self.request_header) as response,
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
            AsyncSession(self.session) as session,
            session.get(f"{self.endpoint}/status/{task_id}", headers=self.request_header) as response,
        ):
            response.raise_for_status()
            body = await response.text()
            return CrewAIStatusResponse.model_validate_json(body)
