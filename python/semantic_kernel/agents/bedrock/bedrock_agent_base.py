# Copyright (c) Microsoft. All rights reserved.

import asyncio
import logging
from functools import partial
from typing import Any, ClassVar

import boto3
from botocore.exceptions import ClientError
from pydantic import Field, field_validator

from semantic_kernel.agents.agent import Agent
from semantic_kernel.agents.bedrock.action_group_utils import kernel_function_to_bedrock_function_schema
from semantic_kernel.agents.bedrock.models.bedrock_action_group_model import BedrockActionGroupModel
from semantic_kernel.agents.bedrock.models.bedrock_agent_model import BedrockAgentModel
from semantic_kernel.agents.bedrock.models.bedrock_agent_status import BedrockAgentStatus
from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceBehavior, FunctionChoiceType
from semantic_kernel.utils.async_utils import run_in_executor
from semantic_kernel.utils.feature_stage_decorator import experimental

logger = logging.getLogger(__name__)


@experimental
class BedrockAgentBase(Agent):
    """Bedrock Agent Base Class to provide common functionalities for Bedrock Agents."""

    # There is a default alias created by Bedrock for the working draft version of the agent.
    # https://docs.aws.amazon.com/bedrock/latest/userguide/agents-deploy.html
    WORKING_DRAFT_AGENT_ALIAS: ClassVar[str] = "TSTALIASID"

    # Amazon Bedrock Clients
    # Runtime Client: Use for inference
    bedrock_runtime_client: Any
    # Client: Use for model management
    bedrock_client: Any
    # Function Choice Behavior: this is primarily used to control the behavior of the kernel when
    # the agent requests functions, and to configure the kernel function action group (i.e. via filters).
    # When this is None, users won't be able to create a kernel function action groups.
    function_choice_behavior: FunctionChoiceBehavior = Field(default=FunctionChoiceBehavior.Auto())
    # Agent Model: stores the agent information
    agent_model: BedrockAgentModel

    def __init__(
        self,
        agent_model: BedrockAgentModel | dict[str, Any],
        *,
        function_choice_behavior: FunctionChoiceBehavior | None = None,
        bedrock_runtime_client: Any | None = None,
        bedrock_client: Any | None = None,
        **kwargs,
    ) -> None:
        """Initialize the Bedrock Agent Base.

        Args:
            agent_model: The Bedrock Agent Model.
            function_choice_behavior: The function choice behavior.
            bedrock_client: The Bedrock Client.
            bedrock_runtime_client: The Bedrock Runtime Client.
            kwargs: Additional keyword arguments.
        """
        agent_model = (
            agent_model if isinstance(agent_model, BedrockAgentModel) else BedrockAgentModel.model_validate(agent_model)
        )

        args = {
            "agent_model": agent_model,
            "id": agent_model.agent_id,
            "name": agent_model.agent_name,
            "bedrock_runtime_client": bedrock_runtime_client or boto3.client("bedrock-agent-runtime"),
            "bedrock_client": bedrock_client or boto3.client("bedrock-agent"),
            **kwargs,
        }
        if function_choice_behavior:
            args["function_choice_behavior"] = function_choice_behavior

        super().__init__(**args)

    @field_validator("function_choice_behavior", mode="after")
    @classmethod
    def validate_function_choice_behavior(
        cls, function_choice_behavior: FunctionChoiceBehavior | None
    ) -> FunctionChoiceBehavior | None:
        """Validate the function choice behavior."""
        if function_choice_behavior and function_choice_behavior.type_ != FunctionChoiceType.AUTO:
            # Users cannot specify REQUIRED or NONE for the Bedrock agents.
            # Please note that the function choice behavior only control if the kernel will automatically
            # execute the functions the agent requests. It does not control the behavior of the agent.
            raise ValueError("Only FunctionChoiceType.AUTO is supported.")
        return function_choice_behavior

    def __repr__(self):
        """Return the string representation of the Bedrock Agent."""
        return f"{self.agent_model}"

    # region Agent Management

    async def prepare_agent_and_wait_until_prepared(self) -> None:
        """Prepare the agent for use."""
        if not self.agent_model.agent_id:
            raise ValueError("Agent does not exist. Please create the agent before preparing it.")

        try:
            await run_in_executor(
                None,
                partial(
                    self.bedrock_client.prepare_agent,
                    agentId=self.agent_model.agent_id,
                ),
            )

            # The agent will take some time to enter the PREPARING status after the prepare operation is called.
            # We need to wait for the agent to reach the PREPARING status before we can proceed, otherwise we
            # will return immediately if the agent is already in PREPARED status.
            await self._wait_for_agent_status(BedrockAgentStatus.PREPARING)
            # The agent will enter the PREPARED status when the preparation is complete.
            await self._wait_for_agent_status(BedrockAgentStatus.PREPARED)
        except ClientError as e:
            logger.error(f"Failed to prepare agent {self.agent_model.agent_id}.")
            raise e

    async def delete_agent(self, **kwargs) -> None:
        """Delete an agent asynchronously."""
        if not self.agent_model.agent_id:
            raise ValueError("Agent does not exist. Please create the agent before deleting it.")

        try:
            await run_in_executor(
                None,
                partial(
                    self.bedrock_client.delete_agent,
                    agentId=self.agent_model.agent_id,
                    **kwargs,
                ),
            )

            self.agent_model.agent_id = None
        except ClientError as e:
            logger.error(f"Failed to delete agent {self.agent_model.agent_id}.")
            raise e

    async def _get_agent(self) -> None:
        """Get an agent."""
        if not self.agent_model.agent_id:
            raise ValueError("Agent does not exist. Please create the agent before getting it.")

        try:
            response = await run_in_executor(
                None,
                partial(
                    self.bedrock_client.get_agent,
                    agentId=self.agent_model.agent_id,
                ),
            )

            # Update the agent model
            self.agent_model = BedrockAgentModel(**response["agent"])
        except ClientError as e:
            logger.error(f"Failed to get agent {self.agent_model.agent_id}.")
            raise e

    async def _wait_for_agent_status(
        self,
        status: BedrockAgentStatus,
        interval: int = 2,
        max_attempts: int = 5,
    ) -> None:
        """Wait for the agent to reach a specific status."""
        for _ in range(max_attempts):
            await self._get_agent()
            if self.agent_model.agent_status == status:
                return

            await asyncio.sleep(interval)

        raise TimeoutError(
            f"Agent did not reach status {status} within the specified time."
            f" Current status: {self.agent_model.agent_status}"
        )

    # endregion Agent Management

    # region Action Group Management
    async def create_code_interpreter_action_group(self, **kwargs) -> BedrockActionGroupModel:
        """Create a code interpreter action group."""
        if not self.agent_model.agent_id:
            raise ValueError("Agent does not exist. Please create the agent before creating an action group for it.")

        try:
            response = await run_in_executor(
                None,
                partial(
                    self.bedrock_client.create_agent_action_group,
                    agentId=self.agent_model.agent_id,
                    agentVersion=self.agent_model.agent_version or "DRAFT",
                    actionGroupName=f"{self.agent_model.agent_name}_code_interpreter",
                    actionGroupState="ENABLED",
                    parentActionGroupSignature="AMAZON.CodeInterpreter",
                    **kwargs,
                ),
            )

            await self.prepare_agent_and_wait_until_prepared()

            return BedrockActionGroupModel(**response["agentActionGroup"])
        except ClientError as e:
            logger.error(f"Failed to create code interpreter action group for agent {self.agent_model.agent_id}.")
            raise e

    async def create_user_input_action_group(self, **kwargs) -> BedrockActionGroupModel:
        """Create a user input action group."""
        if not self.agent_model.agent_id:
            raise ValueError("Agent does not exist. Please create the agent before creating an action group for it.")

        try:
            response = await run_in_executor(
                None,
                partial(
                    self.bedrock_client.create_agent_action_group,
                    agentId=self.agent_model.agent_id,
                    agentVersion=self.agent_model.agent_version or "DRAFT",
                    actionGroupName=f"{self.agent_model.agent_name}_user_input",
                    actionGroupState="ENABLED",
                    parentActionGroupSignature="AMAZON.UserInput",
                    **kwargs,
                ),
            )

            await self.prepare_agent_and_wait_until_prepared()

            return BedrockActionGroupModel(**response["agentActionGroup"])
        except ClientError as e:
            logger.error(f"Failed to create user input action group for agent {self.agent_model.agent_id}.")
            raise e

    async def create_kernel_function_action_group(self, **kwargs) -> BedrockActionGroupModel | None:
        """Create a kernel function action group."""
        if not self.agent_model.agent_id:
            raise ValueError("Agent does not exist. Please create the agent before creating an action group for it.")

        function_call_choice_config = self.function_choice_behavior.get_config(self.kernel)
        if not function_call_choice_config.available_functions:
            logger.warning("No available functions. Skipping kernel function action group creation.")
            return None

        try:
            response = await run_in_executor(
                None,
                partial(
                    self.bedrock_client.create_agent_action_group,
                    agentId=self.agent_model.agent_id,
                    agentVersion=self.agent_model.agent_version or "DRAFT",
                    actionGroupName=f"{self.agent_model.agent_name}_kernel_function",
                    actionGroupState="ENABLED",
                    actionGroupExecutor={"customControl": "RETURN_CONTROL"},
                    functionSchema=kernel_function_to_bedrock_function_schema(function_call_choice_config),
                    **kwargs,
                ),
            )

            await self.prepare_agent_and_wait_until_prepared()

            return BedrockActionGroupModel(**response["agentActionGroup"])
        except ClientError as e:
            logger.error(f"Failed to create kernel function action group for agent {self.agent_model.agent_id}.")
            raise e

    # endregion Action Group Management

    # region Knowledge Base Management

    async def associate_agent_knowledge_base(self, knowledge_base_id: str, **kwargs) -> dict[str, Any]:
        """Associate an agent with a knowledge base."""
        if not self.agent_model.agent_id:
            raise ValueError(
                "Agent does not exist. Please create the agent before associating it with a knowledge base."
            )

        try:
            response = await run_in_executor(
                None,
                partial(
                    self.bedrock_client.associate_agent_knowledge_base,
                    agentId=self.agent_model.agent_id,
                    agentVersion=self.agent_model.agent_version,
                    knowledgeBaseId=knowledge_base_id,
                    **kwargs,
                ),
            )

            await self.prepare_agent_and_wait_until_prepared()

            return response
        except ClientError as e:
            logger.error(
                f"Failed to associate agent {self.agent_model.agent_id} with knowledge base {knowledge_base_id}."
            )
            raise e

    async def disassociate_agent_knowledge_base(self, knowledge_base_id: str, **kwargs) -> None:
        """Disassociate an agent with a knowledge base."""
        if not self.agent_model.agent_id:
            raise ValueError(
                "Agent does not exist. Please create the agent before disassociating it with a knowledge base."
            )

        try:
            response = await run_in_executor(
                None,
                partial(
                    self.bedrock_client.disassociate_agent_knowledge_base,
                    agentId=self.agent_model.agent_id,
                    agentVersion=self.agent_model.agent_version,
                    knowledgeBaseId=knowledge_base_id,
                    **kwargs,
                ),
            )

            await self.prepare_agent_and_wait_until_prepared()

            return response
        except ClientError as e:
            logger.error(
                f"Failed to disassociate agent {self.agent_model.agent_id} with knowledge base {knowledge_base_id}."
            )
            raise e

    async def list_associated_agent_knowledge_bases(self, **kwargs) -> dict[str, Any]:
        """List associated knowledge bases with an agent."""
        if not self.agent_model.agent_id:
            raise ValueError("Agent does not exist. Please create the agent before listing associated knowledge bases.")

        try:
            return await run_in_executor(
                None,
                partial(
                    self.bedrock_client.list_agent_knowledge_bases,
                    agentId=self.agent_model.agent_id,
                    agentVersion=self.agent_model.agent_version,
                    **kwargs,
                ),
            )
        except ClientError as e:
            logger.error(f"Failed to list associated knowledge bases for agent {self.agent_model.agent_id}.")
            raise e

    # endregion Knowledge Base Management

    async def _invoke_agent(
        self,
        session_id: str,
        input_text: str,
        agent_alias: str | None = None,
        **kwargs,
    ) -> dict[str, Any]:
        """Invoke an agent."""
        if not self.agent_model.agent_id:
            raise ValueError("Agent does not exist. Please create the agent before invoking it.")

        agent_alias = agent_alias or self.WORKING_DRAFT_AGENT_ALIAS

        try:
            return await run_in_executor(
                None,
                partial(
                    self.bedrock_runtime_client.invoke_agent,
                    agentAliasId=agent_alias,
                    agentId=self.agent_model.agent_id,
                    sessionId=session_id,
                    inputText=input_text,
                    **kwargs,
                ),
            )
        except ClientError as e:
            logger.error(f"Failed to invoke agent {self.agent_model.agent_id}.")
            raise e
