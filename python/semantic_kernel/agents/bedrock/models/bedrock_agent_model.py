# Copyright (c) Microsoft. All rights reserved.

from pydantic import ConfigDict, Field

from semantic_kernel.kernel_pydantic import KernelBaseModel
from semantic_kernel.utils.experimental_decorator import experimental_class


@experimental_class
class BedrockAgentModel(KernelBaseModel):
    """Bedrock Agent Model.

    Model field definitions for the Amazon Bedrock Agent Service:
    https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/bedrock-agent/client/create_agent.html
    """

    # This model_config will merge with the KernelBaseModel.model_config
    model_config = ConfigDict(extra="allow")

    agent_arn: str = Field(..., alias="agentArn", description="The Amazon Resource Name (ARN) of the agent.")
    agent_id: str = Field(..., alias="agentId", description="The unique identifier of the agent.")
    agent_name: str = Field(..., alias="agentName", description="The name of the agent.")
    agent_version: str = Field(..., alias="agentVersion", description="The version of the agent.")
