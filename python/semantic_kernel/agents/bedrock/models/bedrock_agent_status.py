# Copyright (c) Microsoft. All rights reserved.


from enum import Enum

from semantic_kernel.utils.feature_stage_decorator import experimental


@experimental
class BedrockAgentStatus(str, Enum):
    """Bedrock Agent Status.

    https://docs.aws.amazon.com/bedrock/latest/APIReference/API_agent_PrepareAgent.html#API_agent_PrepareAgent_ResponseElements
    """

    CREATING = "CREATING"
    PREPARING = "PREPARING"
    PREPARED = "PREPARED"
    NOT_PREPARED = "NOT_PREPARED"
    DELETING = "DELETING"
    FAILED = "FAILED"
    VERSIONING = "VERSIONING"
    UPDATING = "UPDATING"
