# Copyright (c) Microsoft. All rights reserved.

from typing import ClassVar

from pydantic import SecretStr

from semantic_kernel.kernel_pydantic import KernelBaseSettings
from semantic_kernel.utils.feature_stage_decorator import experimental


@experimental
class AzureAIAgentSettings(KernelBaseSettings):
    """Azure AI Agent settings currently used by the AzureAIAgent.

    Args:
        model_deployment_name: Azure AI Agent (Env var AZURE_AI_AGENT_MODEL_DEPLOYMENT_NAME)
        project_connection_string: Azure AI Agent Project Connection String
            (Env var AZURE_AI_AGENT_PROJECT_CONNECTION_STRING)
        endpoint: Azure AI Agent Endpoint (Env var AZURE_AI_AGENT_ENDPOINT)
        subscription_id: Azure AI Agent Subscription ID (Env var AZURE_AI_AGENT_SUBSCRIPTION_ID)
        resource_group_name: Azure AI Agent Resource Group Name (Env var AZURE_AI_AGENT_RESOURCE_GROUP_NAME)
        project_name: Azure AI Agent Project Name (Env var AZURE_AI_AGENT_PROJECT_NAME)
        bing_connection_id: Azure AI Agent Bing Connection ID (Env var AZURE_AI_AGENT_BING_CONNECTION_ID)
        azure_ai_search_connection_id: Azure AI Agent Azure AI Search Connection ID
            (Env var AZURE_AI_AGENT_AZURE_AI_SEARCH_CONNECTION_ID)
        azure_ai_search_index_name: Azure AI Agent Azure AI Search Index Name
    """

    env_prefix: ClassVar[str] = "AZURE_AI_AGENT_"

    model_deployment_name: str
    project_connection_string: SecretStr | None = None
    endpoint: str | None = None
    subscription_id: str | None = None
    resource_group_name: str | None = None
    project_name: str | None = None
    bing_connection_id: str | None = None
    azure_ai_search_connection_id: str | None = None
    azure_ai_search_index_name: str | None = None
