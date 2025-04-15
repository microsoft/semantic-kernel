# Copyright (c) Microsoft. All rights reserved.

from unittest.mock import AsyncMock

import pytest
from azure.ai.projects.aio import AIProjectClient
from azure.ai.projects.models import Agent as AzureAIAgentModel


@pytest.fixture
def ai_project_client() -> AsyncMock:
    return AsyncMock(spec=AIProjectClient)


@pytest.fixture
def ai_agent_definition() -> AsyncMock:
    definition = AsyncMock(spec=AzureAIAgentModel)
    definition.id = "agent123"
    definition.name = "agentName"
    definition.description = "desc"
    definition.instructions = "test agent"

    return definition
