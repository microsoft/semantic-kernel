# Copyright (c) Microsoft. All rights reserved.


from semantic_kernel.agents.agent import Agent
from semantic_kernel.agents.bedrock.bedrock_agent_base import BedrockAgentBase
from semantic_kernel.agents.bedrock.models.bedrock_agent_model import BedrockAgentModel
from semantic_kernel.utils.experimental_decorator import experimental_class


@experimental_class
class BedrockAgent(BedrockAgentBase, Agent):
    """Bedrock Agent.

    Manages the interaction with Amazon Bedrock Agent Service.
    """

    async def create_agent(
        self,
        agent_name: str,
        foundational_model: str,
        role_arn: str,
        instruction: str,
        enable_code_interpreter: bool | None = None,
        enable_user_input: bool | None = None,
        enable_kernel_function: bool | None = None,
        **kwargs,
    ) -> BedrockAgentModel:
        """Create an agent asynchronously."""
        await self._create_agent(
            agent_name,
            foundational_model,
            role_arn,
            instruction,
            **kwargs,
        )

        if enable_code_interpreter:
            await self.create_code_interpreter_action_group()
        if enable_user_input:
            await self.create_user_input_action_group()
        if enable_kernel_function:
            await self.create_kernel_function_action_group()

        return self.agent_model

    async def update_agent(
        self,
        agent_id,
        agent_name,
        role_arn,
        foundational_model,
        **kwargs,
    ) -> BedrockAgentModel:
        """Update an agent asynchronously."""
        return await self._update_agent(
            agent_id,
            agent_name,
            role_arn,
            foundational_model,
            **kwargs,
        )

    async def delete_agent(self, agent_id, **kwargs) -> None:
        """Delete an agent asynchronously."""
        await self._delete_agent(agent_id, **kwargs)

    async def create_code_interpreter_action_group(self, **kwargs):
        """Enable code interpretation."""
        return await self._create_code_interpreter_action_group(**kwargs)

    async def create_user_input_action_group(self, **kwargs):
        """Enable user input."""
        return await self._create_user_input_action_group(**kwargs)

    async def create_kernel_function_action_group(self, **kwargs):
        """Enable kernel function."""
        return await self._create_kernel_function_action_group(self.kernel, **kwargs)
