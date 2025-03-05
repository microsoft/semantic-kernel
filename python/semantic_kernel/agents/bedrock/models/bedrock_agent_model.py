# Copyright (c) Microsoft. All rights reserved.

from pydantic import ConfigDict, Field

from semantic_kernel.kernel_pydantic import KernelBaseModel
from semantic_kernel.utils.feature_stage_decorator import experimental


@experimental
class BedrockAgentModel(KernelBaseModel):
    """Bedrock Agent Model.

    Model field definitions for the Amazon Bedrock Agent Service:
    https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/bedrock-agent/client/create_agent.html
    """

    # This model_config will merge with the KernelBaseModel.model_config
    model_config = ConfigDict(extra="allow")

    agent_id: str | None = Field(default=None, alias="agentId", description="The unique identifier of the agent.")
    agent_name: str | None = Field(default=None, alias="agentName", description="The name of the agent.")
    agent_version: str | None = Field(default=None, alias="agentVersion", description="The version of the agent.")
    foundation_model: str | None = Field(default=None, alias="foundationModel", description="The foundation model.")
    agent_status: str | None = Field(default=None, alias="agentStatus", description="The status of the agent.")
