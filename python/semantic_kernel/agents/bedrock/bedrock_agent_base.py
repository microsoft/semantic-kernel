# Copyright (c) Microsoft. All rights reserved.

import asyncio
import logging
from functools import partial
from typing import Any

import boto3
from botocore.exceptions import ClientError

from semantic_kernel.agents.bedrock.action_group_utils import kernel_function_to_bedrock_function_schema
from semantic_kernel.agents.bedrock.models.bedrock_action_group_model import BedrockActionGroupModel
from semantic_kernel.agents.bedrock.models.bedrock_agent_model import BedrockAgentModel
from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceBehavior
from semantic_kernel.kernel import Kernel
from semantic_kernel.kernel_pydantic import KernelBaseModel
from semantic_kernel.utils.experimental_decorator import experimental_class

logger = logging.getLogger(__name__)


@experimental_class
class BedrockAgentBase(KernelBaseModel):
    """Bedrock Agent Base Class to provide common functionalities for Bedrock Agents."""

    # Amazon Bedrock Clients
    # Runtime Client: Use for inference
    bedrock_runtime_client: Any
    # Client: Use for model management
    bedrock_client: Any
    # Function Choice Behavior
    function_choice_behavior: FunctionChoiceBehavior | None = None
    # Agent Model
    agent_model: BedrockAgentModel | None = None

    def __init__(
        self,
        runtime_client: Any | None = None,
        client: Any | None = None,
        **kwargs,
    ) -> None:
        """Initialize the Bedrock Agent.

        Args:
            runtime_client: The Bedrock Runtime Client.
            client: The Bedrock Client.
            kwargs: Additional keyword arguments.
        """
        super().__init__(
            bedrock_runtime_client=runtime_client or boto3.client("bedrock-agent-runtime"),
            bedrock_client=client or boto3.client("bedrock-agent"),
            **kwargs,
        )

    async def _run_in_executor(executor, func, *args, **kwargs) -> Any:
        """Run a function in an executor."""
        return await asyncio.get_event_loop().run_in_executor(executor, partial(func, *args, **kwargs))

    # region Agent Management

    async def _create_agent(
        self,
        agent_name: str,
        foundational_model: str,
        role_arn: str,
        instruction: str,
        **kwargs,
    ) -> BedrockAgentModel:
        """Create an agent asynchronously."""
        if self.agent_model:
            raise ValueError("Agent already exists. Please delete the agent before creating a new one.")

        try:
            self.agent_model = await self._run_in_executor(
                None,
                partial(
                    self.bedrock_client.create_client,
                    agentName=agent_name,
                    foundationalModel=foundational_model,
                    agentResourceRoleArn=role_arn,
                    instruction=instruction,
                    **kwargs,
                ),
            )
            return self.agent_model
        except ClientError as e:
            logger.error(f"Failed to create agent {agent_name}.")
            raise e

    async def _update_agent(
        self,
        agent_id: str,
        agent_name: str,
        role_arn: str,
        foundational_model: str,
        **kwargs,
    ) -> BedrockAgentModel:
        """Update an agent asynchronously."""
        if not self.agent_model:
            raise ValueError("Agent does not exist. Please create the agent before updating it.")

        try:
            self.agent_model = await self._run_in_executor(
                None,
                partial(
                    self.bedrock_client.update_client,
                    agentId=agent_id,
                    agentName=agent_name,
                    agentResourceRoleArn=role_arn,
                    foundationalModel=foundational_model,
                    **kwargs,
                ),
            )

            return self.agent_model
        except ClientError as e:
            logger.error(f"Failed to update agent {agent_id}.")
            raise e

    async def _delete_agent(self, agent_id: str, **kwargs) -> None:
        """Delete an agent asynchronously."""
        try:
            await self._run_in_executor(
                None,
                partial(
                    self.bedrock_client.delete_client,
                    agentId=agent_id,
                    **kwargs,
                ),
            )

            self.agent_model = None
        except ClientError as e:
            logger.error(f"Failed to delete agent {agent_id}.")
            raise e

    # endregion Agent Management

    # region Action Group Management
    async def _create_code_interpreter_action_group(self, **kwargs) -> BedrockActionGroupModel:
        """Create a code interpreter action group."""
        try:
            return await self._run_in_executor(
                None,
                partial(
                    self.bedrock_client.create_agent_action_group,
                    agentId=self.agent_model.agent_id,
                    actionGroupName=f"{self.agent_model.agent_name}_code_interpreter",
                    actionGroupState="ENABLED",
                    parentActionGroupSignature="AMAZON.CodeInterpreter",
                    **kwargs,
                ),
            )
        except ClientError as e:
            logger.error(f"Failed to create code interpreter action group for agent {self.agent_model.agent_id}.")
            raise e

    async def _create_user_input_action_group(self, **kwargs) -> BedrockActionGroupModel:
        """Create a user input action group."""
        try:
            return await self._run_in_executor(
                None,
                partial(
                    self.bedrock_client.create_agent_action_group,
                    agentId=self.agent_model.agent_id,
                    actionGroupName=f"{self.agent_model.agent_name}_user_input",
                    actionGroupState="ENABLED",
                    parentActionGroupSignature="AMAZON.UserInput",
                    **kwargs,
                ),
            )
        except ClientError as e:
            logger.error(f"Failed to create user input action group for agent {self.agent_model.agent_id}.")
            raise e

    async def _create_kernel_function_action_group(self, kernel: Kernel, **kwargs) -> BedrockActionGroupModel | None:
        """Create a kernel function action group."""
        if not self.function_choice_behavior:
            logger.warning("Function Choice Behavior is not set. Skipping kernel function action group creation.")
            return None

        function_call_choice_config = self.function_choice_behavior.get_config(kernel)
        if not function_call_choice_config.available_functions:
            logger.warning("No available functions. Skipping kernel function action group creation.")
            return None

        try:
            return await self._run_in_executor(
                None,
                partial(
                    self.bedrock_client.create_agent_action_group,
                    agentId=self.agent_model.agent_id,
                    actionGroupName=f"{self.agent_model.agent_name}_kernel_function",
                    actionGroupState="ENABLED",
                    actionGroupExecutor={"customControl": "RETURN_CONTROL"},
                    functionSchema=kernel_function_to_bedrock_function_schema(function_call_choice_config),
                    **kwargs,
                ),
            )
        except ClientError as e:
            logger.error(f"Failed to create kernel function action group for agent {self.agent_model.agent_id}.")
            raise e

    # endregion Action Group Management

    # region Knowledge Base Management

    async def _associate_agent_knowledge_base(self, knowledge_base_id: str, **kwargs) -> dict[str, Any]:
        """Associate an agent with a knowledge base."""
        try:
            return await self._run_in_executor(
                None,
                partial(
                    self.bedrock_client.associate_client_knowledge_base,
                    agentId=self.agent_model.agent_id,
                    agentVersion=self.agent_model.agent_version,
                    knowledgeBaseId=knowledge_base_id,
                    **kwargs,
                ),
            )
        except ClientError as e:
            logger.error(
                f"Failed to associate agent {self.agent_model.agent_id} with knowledge base {knowledge_base_id}."
            )
            raise e

    async def _disassociate_agent_knowledge_base(self, knowledge_base_id: str, **kwargs) -> None:
        """Disassociate an agent with a knowledge base."""
        try:
            await self._run_in_executor(
                None,
                partial(
                    self.bedrock_client.disassociate_client_knowledge_base,
                    agentId=self.agent_model.agent_id,
                    agentVersion=self.agent_model.agent_version,
                    knowledgeBaseId=knowledge_base_id,
                    **kwargs,
                ),
            )
        except ClientError as e:
            logger.error(
                f"Failed to disassociate agent {self.agent_model.agent_id} with knowledge base {knowledge_base_id}."
            )
            raise e

    async def _list_associated_agent_knowledge_bases(self, **kwargs) -> dict[str, Any]:
        """List associated knowledge bases with an agent."""
        try:
            return await self._run_in_executor(
                None,
                partial(
                    self.bedrock_client.list_client_knowledge_bases,
                    agentId=self.agent_model.agent_id,
                    agentVersion=self.agent_model.agent_version,
                    **kwargs,
                ),
            )
        except ClientError:
            logger.error(f"Failed to list associated knowledge bases for agent {self.agent_model.agent_id}.")

    # endregion Knowledge Base Management
