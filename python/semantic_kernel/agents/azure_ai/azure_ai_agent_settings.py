# Copyright (c) Microsoft. All rights reserved.

from typing import ClassVar

from semantic_kernel.kernel_pydantic import KernelBaseSettings
from semantic_kernel.utils.feature_stage_decorator import experimental


@experimental
class AzureAIAgentSettings(KernelBaseSettings):
    """Azure AI Agent settings currently used by the AzureAIAgent.

    Args:
        model_deployment_name: Azure AI Agent (Env var AZURE_AI_AGENT_DEPLOYMENT_NAME)
        endpoint: Azure AI Agent Endpoint (Env var AZURE_AI_AGENT_ENDPOINT)
        api_version: Azure AI Agent API Version (Env var AZURE_AI_AGENT_API_VERSION)
    """

    env_prefix: ClassVar[str] = "AZURE_AI_AGENT_"

    deployment_name: str
    endpoint: str | None = None
    api_version: str | None = None
