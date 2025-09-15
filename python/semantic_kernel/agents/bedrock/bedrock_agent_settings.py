# Copyright (c) Microsoft. All rights reserved.

from typing import ClassVar

from semantic_kernel.kernel_pydantic import KernelBaseSettings
from semantic_kernel.utils.feature_stage_decorator import experimental


@experimental
class BedrockAgentSettings(KernelBaseSettings):
    """Amazon Bedrock Agent service settings.

    The settings are first loaded from environment variables with
    the prefix 'BEDROCK_AGENT_'.
    If the environment variables are not found, the settings can
    be loaded from a .env file with the encoding 'utf-8'.
    If the settings are not found in the .env file, the settings
    are ignored; however, validation will fail alerting that the
    settings are missing.

    Optional settings for prefix 'BEDROCK_' are:
        - agent_resource_role_arn: str - The Amazon Bedrock agent resource role ARN.
            https://docs.aws.amazon.com/bedrock/latest/userguide/getting-started.html
            (Env var BEDROCK_AGENT_AGENT_RESOURCE_ROLE_ARN)
        - foundation_model: str - The Amazon Bedrock foundation model ID to use.
            (Env var BEDROCK_AGENT_FOUNDATION_MODEL)
    """

    env_prefix: ClassVar[str] = "BEDROCK_AGENT_"

    agent_resource_role_arn: str
    foundation_model: str
