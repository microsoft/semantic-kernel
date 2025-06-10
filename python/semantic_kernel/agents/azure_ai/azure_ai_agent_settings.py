# Copyright (c) Microsoft. All rights reserved.

from typing import ClassVar

from semantic_kernel.kernel_pydantic import KernelBaseSettings
from semantic_kernel.utils.feature_stage_decorator import experimental


@experimental
class AzureAIAgentSettings(KernelBaseSettings):
    """Azure AI Agent settings currently used by the AzureAIAgent.

    Args:
        model_deployment_name: Azure AI Agent (Env var AZURE_AI_AGENT_MODEL_DEPLOYMENT_NAME)
        endpoint: Azure AI Agent Endpoint (Env var AZURE_AI_AGENT_ENDPOINT)
        api_version: Azure AI Agent API Version (Env var AZURE_AI_AGENT_API_VERSION)
    """

    env_prefix: ClassVar[str] = "AZURE_AI_AGENT_"

    model_deployment_name: str
    endpoint: str | None = None
    agent_id: str | None = None
    bing_connection_id: str | None = None
    azure_ai_search_connection_id: str | None = None
    azure_ai_search_index_name: str | None = None
    api_version: str | None = None
