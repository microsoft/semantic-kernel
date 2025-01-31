# Copyright (c) Microsoft. All rights reserved.

from typing import ClassVar

from pydantic import SecretStr

from semantic_kernel.kernel_pydantic import KernelBaseSettings
from semantic_kernel.utils.experimental_decorator import experimental_class


@experimental_class
class AzureAIAgentSettings(KernelBaseSettings):
    """AzureAI Agent settings currently used by the AzureAIAgent.

    Args:
    - model_deployment_name: AzureAI Agent (Env var AZURE_AI_AGENT_MODEL_DEPLOYMENT_NAME)
    - project_connection_string: AzureAI Agent Project Connection String
        (Env var AZURE_AI_AGENT_PROJECT_CONNECTION_STRING)
    """

    env_prefix: ClassVar[str] = "AZURE_AI_AGENT_"

    model_deployment_name: str
    project_connection_string: SecretStr
