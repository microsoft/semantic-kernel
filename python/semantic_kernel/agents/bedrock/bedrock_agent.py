# Copyright (c) Microsoft. All rights reserved.


from typing import Any

from semantic_kernel.agents.agent import Agent
from semantic_kernel.agents.bedrock.bedrock_agent_base import BedrockAgentBase
from semantic_kernel.agents.bedrock.models.bedrock_action_group_model import BedrockActionGroupModel
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
        foundation_model: str,
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
            foundation_model,
            role_arn,
            instruction,
            **kwargs,
        )
        await self._prepare_agent()

        if enable_code_interpreter:
            await self.create_code_interpreter_action_group()
        if enable_user_input:
            await self.create_user_input_action_group()
        if enable_kernel_function:
            await self.create_kernel_function_action_group()

        return self.agent_model

    @classmethod
    async def use_existing_agent(cls, agent_arn: str, agent_id: str, agent_name: str) -> "BedrockAgent":
        """Use an existing agent asynchronously."""
        bedrock_agent_model = BedrockAgentModel(
            agent_arn=agent_arn,
            agent_id=agent_id,
            agent_name=agent_name,
        )

        bedrock_agent = cls(agent_model=bedrock_agent_model)
        bedrock_agent_model = await bedrock_agent._get_agent()
        bedrock_agent.agent_model = bedrock_agent_model

        return bedrock_agent

    async def update_agent(
        self,
        agent_id,
        agent_name,
        role_arn,
        foundation_model,
        **kwargs,
    ) -> BedrockAgentModel:
        """Update an agent asynchronously."""
        return await self._update_agent(
            agent_id,
            agent_name,
            role_arn,
            foundation_model,
            **kwargs,
        )

    async def delete_agent(self, agent_id, **kwargs) -> None:
        """Delete an agent asynchronously."""
        await self._delete_agent(agent_id, **kwargs)

    async def create_code_interpreter_action_group(self, **kwargs) -> BedrockActionGroupModel:
        """Enable code interpretation."""
        return await self._create_code_interpreter_action_group(**kwargs)

    async def create_user_input_action_group(self, **kwargs) -> BedrockActionGroupModel:
        """Enable user input."""
        return await self._create_user_input_action_group(**kwargs)

    async def create_kernel_function_action_group(self, **kwargs) -> BedrockActionGroupModel:
        """Enable kernel function."""
        return await self._create_kernel_function_action_group(self.kernel, **kwargs)

    async def associate_agent_knowledge_base(self, knowledge_base_id, **kwargs) -> dict[str, Any]:
        """Associate an agent with a knowledge base."""
        return await self._associate_agent_knowledge_base(knowledge_base_id, **kwargs)

    async def disassociate_agent_knowledge_base(self, knowledge_base_id, **kwargs) -> None:
        """Disassociate an agent with a knowledge base."""
        return await self._disassociate_agent_knowledge_base(knowledge_base_id, **kwargs)

    async def list_associated_agent_knowledge_bases(self, **kwargs) -> dict[str, Any]:
        """List associated agent knowledge bases."""
        return await self._list_associated_agent_knowledge_bases(**kwargs)

    async def invoke(
        self,
        session_id: str,
        input_text: str,
        agent_alias: str | None = None,
        **kwargs,
    ) -> Any:
        """Invoke an agent."""
        response = await self._invoke_agent(session_id, input_text, agent_alias, **kwargs)

        completion = ""
        for event in response.get("completion", []):
            chunk = event["chunk"]
            completion += chunk["bytes"].decode()

        return completion

    async def invoke_stream(
        self,
        session_id: str,
        input_text: str,
        agent_alias: str | None = None,
        **kwargs,
    ) -> Any:
        """Invoke an agent."""
        return await self._invoke_agent(session_id, input_text, agent_alias, **kwargs)
