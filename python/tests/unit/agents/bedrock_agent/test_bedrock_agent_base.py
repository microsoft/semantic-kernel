# Copyright (c) Microsoft. All rights reserved.

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import boto3
import pytest
from botocore.exceptions import ClientError

from semantic_kernel.agents.bedrock.bedrock_agent_base import BedrockAgentBase
from semantic_kernel.agents.bedrock.models.bedrock_agent_model import BedrockAgentModel
from semantic_kernel.agents.bedrock.models.bedrock_agent_status import BedrockAgentStatus
from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceBehavior


@pytest.fixture
def bedrock_agent_model():
    return BedrockAgentModel(
        agent_id="test_agent_id",
        agent_name="test_agent_name",
        foundation_model="test_foundation_model",
        agent_status=BedrockAgentStatus.NOT_PREPARED,
    )


@pytest.fixture
def bedrock_agent(bedrock_agent_model):
    return BedrockAgentBase(
        agent_resource_role_arn="test_arn",
        agent_model=bedrock_agent_model,
        function_choice_behavior=FunctionChoiceBehavior.Auto(),
    )


# Test case to verify the creation of an agent
async def test_create_agent(bedrock_agent):
    with patch.object(bedrock_agent.bedrock_client, "create_agent", new_callable=AsyncMock) as mock_create_agent:
        mock_create_agent.return_value = {"agent": {"agentId": "new_agent_id"}}
        await bedrock_agent._create_agent("test_instruction")
        assert bedrock_agent.agent_model.agent_id == "new_agent_id"


# Test case to verify error handling when creating an agent that already exists
async def test_create_agent_already_exists(bedrock_agent):
    bedrock_agent.agent_model.agent_id = "existing_agent_id"
    with pytest.raises(ValueError, match="Agent already exists. Please delete the agent before creating a new one."):
        await bedrock_agent._create_agent("test_instruction")


# Test case to verify error handling when there is a client error during agent creation
async def test_create_agent_client_error(bedrock_agent):
    with patch.object(bedrock_agent.bedrock_client, "create_agent", new_callable=AsyncMock) as mock_create_agent:
        mock_create_agent.side_effect = ClientError({"Error": {"Code": "500"}}, "create_agent")
        with pytest.raises(ClientError):
            await bedrock_agent._create_agent("test_instruction")


# Test case to verify the preparation of an agent
async def test_prepare_agent(bedrock_agent):
    with patch.object(bedrock_agent.bedrock_client, "prepare_agent", new_callable=AsyncMock) as mock_prepare_agent:
        await bedrock_agent.prepare_agent()
        mock_prepare_agent.assert_called_once_with(agentId=bedrock_agent.agent_model.agent_id)


# Test case to verify error handling when preparing an agent that does not exist
async def test_prepare_agent_no_id(bedrock_agent):
    bedrock_agent.agent_model.agent_id = None
    with pytest.raises(ValueError, match="Agent does not exist. Please create the agent before preparing it."):
        await bedrock_agent.prepare_agent()


# Test case to verify error handling when there is a client error during agent preparation
async def test_prepare_agent_client_error(bedrock_agent):
    with patch.object(bedrock_agent.bedrock_client, "prepare_agent", new_callable=AsyncMock) as mock_prepare_agent:
        mock_prepare_agent.side_effect = ClientError({"Error": {"Code": "500"}}, "prepare_agent")
        with pytest.raises(ClientError):
            await bedrock_agent.prepare_agent()


# Test case to verify the creation of an agent alias
async def test_create_agent_alias(bedrock_agent):
    with patch.object(bedrock_agent.bedrock_client, "create_agent_alias", new_callable=AsyncMock) as mock_create_alias:
        await bedrock_agent._create_agent_alias("test_alias")
        mock_create_alias.assert_called_once_with(agentAliasName="test_alias", agentId=bedrock_agent.agent_model.agent_id)


# Test case to verify error handling when creating an alias for an agent that does not exist
async def test_create_agent_alias_no_id(bedrock_agent):
    bedrock_agent.agent_model.agent_id = None
    with pytest.raises(ValueError, match="Agent does not exist. Please create the agent before creating an alias."):
        await bedrock_agent._create_agent_alias("test_alias")


# Test case to verify error handling when there is a client error during alias creation
async def test_create_agent_alias_client_error(bedrock_agent):
    with patch.object(bedrock_agent.bedrock_client, "create_agent_alias", new_callable=AsyncMock) as mock_create_alias:
        mock_create_alias.side_effect = ClientError({"Error": {"Code": "500"}}, "create_agent_alias")
        with pytest.raises(ClientError):
            await bedrock_agent._create_agent_alias("test_alias")


# Test case to verify the update of an agent
async def test_update_agent(bedrock_agent):
    with patch.object(bedrock_agent.bedrock_client, "update_agent", new_callable=AsyncMock) as mock_update_agent:
        mock_update_agent.return_value = {"agent": {"agentId": "updated_agent_id"}}
        await bedrock_agent.update_agent(agentName="updated_name")
        assert bedrock_agent.agent_model.agent_id == "updated_agent_id"


# Test case to verify error handling when updating an agent that does not exist
async def test_update_agent_no_id(bedrock_agent):
    bedrock_agent.agent_model.agent_id = None
    with pytest.raises(ValueError, match="Agent has not been created. Please create the agent before updating it."):
        await bedrock_agent.update_agent(agentName="updated_name")


# Test case to verify error handling when there is a client error during agent update
async def test_update_agent_client_error(bedrock_agent):
    with patch.object(bedrock_agent.bedrock_client, "update_agent", new_callable=AsyncMock) as mock_update_agent:
        mock_update_agent.side_effect = ClientError({"Error": {"Code": "500"}}, "update_agent")
        with pytest.raises(ClientError):
            await bedrock_agent.update_agent(agentName="updated_name")


# Test case to verify the deletion of an agent
async def test_delete_agent(bedrock_agent):
    with patch.object(bedrock_agent.bedrock_client, "delete_agent", new_callable=AsyncMock) as mock_delete_agent:
        await bedrock_agent.delete_agent()
        mock_delete_agent.assert_called_once_with(agentId=bedrock_agent.agent_model.agent_id)


# Test case to verify error handling when deleting an agent that does not exist
async def test_delete_agent_no_id(bedrock_agent):
    bedrock_agent.agent_model.agent_id = None
    with pytest.raises(ValueError, match="Agent does not exist. Please create the agent before deleting it."):
        await bedrock_agent.delete_agent()


# Test case to verify error handling when there is a client error during agent deletion
async def test_delete_agent_client_error(bedrock_agent):
    with patch.object(bedrock_agent.bedrock_client, "delete_agent", new_callable=AsyncMock) as mock_delete_agent:
        mock_delete_agent.side_effect = ClientError({"Error": {"Code": "500"}}, "delete_agent")
        with pytest.raises(ClientError):
            await bedrock_agent.delete_agent()


# Test case to verify the retrieval of an agent
async def test_get_agent(bedrock_agent):
    with patch.object(bedrock_agent.bedrock_client, "get_agent", new_callable=AsyncMock) as mock_get_agent:
        mock_get_agent.return_value = {"agent": {"agentId": "retrieved_agent_id"}}
        agent = await bedrock_agent._get_agent()
        assert agent.agent_id == "retrieved_agent_id"


# Test case to verify error handling when retrieving an agent that does not exist
async def test_get_agent_no_id(bedrock_agent):
    bedrock_agent.agent_model.agent_id = None
    with pytest.raises(ValueError, match="Agent does not exist. Please create the agent before getting it."):
        await bedrock_agent._get_agent()


# Test case to verify error handling when there is a client error during agent retrieval
async def test_get_agent_client_error(bedrock_agent):
    with patch.object(bedrock_agent.bedrock_client, "get_agent", new_callable=AsyncMock) as mock_get_agent:
        mock_get_agent.side_effect = ClientError({"Error": {"Code": "500"}}, "get_agent")
        with pytest.raises(ClientError):
            await bedrock_agent._get_agent()


# Test case to verify waiting for an agent to reach a specific status
async def test_wait_for_agent_status(bedrock_agent):
    with patch.object(bedrock_agent, "_get_agent", new_callable=AsyncMock) as mock_get_agent:
        mock_get_agent.return_value = MagicMock(agent_status=BedrockAgentStatus.NOT_PREPARED)
        await bedrock_agent._wait_for_agent_status(BedrockAgentStatus.NOT_PREPARED)


# Test case to verify error handling when waiting for an agent to reach a specific status times out
async def test_wait_for_agent_status_timeout(bedrock_agent):
    with patch.object(bedrock_agent, "_get_agent", new_callable=AsyncMock) as mock_get_agent:
        mock_get_agent.return_value = MagicMock(agent_status=BedrockAgentStatus.CREATING)
        with pytest.raises(TimeoutError, match="Agent did not reach status NOT_PREPARED within the specified time."):
            await bedrock_agent._wait_for_agent_status(BedrockAgentStatus.NOT_PREPARED)


# Test case to verify the creation of a code interpreter action group
async def test_create_code_interpreter_action_group(bedrock_agent):
    with patch.object(bedrock_agent.bedrock_client, "create_agent_action_group", new_callable=AsyncMock) as mock_create_action_group:
        await bedrock_agent.create_code_interpreter_action_group()
        mock_create_action_group.assert_called_once_with(
            agentId=bedrock_agent.agent_model.agent_id,
            agentVersion=bedrock_agent.agent_model.agent_version or "DRAFT",
            actionGroupName=f"{bedrock_agent.agent_model.agent_name}_code_interpreter",
            actionGroupState="ENABLED",
            parentActionGroupSignature="AMAZON.CodeInterpreter",
        )


# Test case to verify error handling when creating a code interpreter action group for an agent that does not exist
async def test_create_code_interpreter_action_group_no_id(bedrock_agent):
    bedrock_agent.agent_model.agent_id = None
    with pytest.raises(ValueError, match="Agent does not exist. Please create the agent before creating an action group for it."):
        await bedrock_agent.create_code_interpreter_action_group()


# Test case to verify error handling when there is a client error during code interpreter action group creation
async def test_create_code_interpreter_action_group_client_error(bedrock_agent):
    with patch.object(bedrock_agent.bedrock_client, "create_agent_action_group", new_callable=AsyncMock) as mock_create_action_group:
        mock_create_action_group.side_effect = ClientError({"Error": {"Code": "500"}}, "create_agent_action_group")
        with pytest.raises(ClientError):
            await bedrock_agent.create_code_interpreter_action_group()


# Test case to verify the creation of a user input action group
async def test_create_user_input_action_group(bedrock_agent):
    with patch.object(bedrock_agent.bedrock_client, "create_agent_action_group", new_callable=AsyncMock) as mock_create_action_group:
        await bedrock_agent.create_user_input_action_group()
        mock_create_action_group.assert_called_once_with(
            agentId=bedrock_agent.agent_model.agent_id,
            agentVersion=bedrock_agent.agent_model.agent_version or "DRAFT",
            actionGroupName=f"{bedrock_agent.agent_model.agent_name}_user_input",
            actionGroupState="ENABLED",
            parentActionGroupSignature="AMAZON.UserInput",
        )


# Test case to verify error handling when creating a user input action group for an agent that does not exist
async def test_create_user_input_action_group_no_id(bedrock_agent):
    bedrock_agent.agent_model.agent_id = None
    with pytest.raises(ValueError, match="Agent does not exist. Please create the agent before creating an action group for it."):
        await bedrock_agent.create_user_input_action_group()


# Test case to verify error handling when there is a client error during user input action group creation
async def test_create_user_input_action_group_client_error(bedrock_agent):
    with patch.object(bedrock_agent.bedrock_client, "create_agent_action_group", new_callable=AsyncMock) as mock_create_action_group:
        mock_create_action_group.side_effect = ClientError({"Error": {"Code": "500"}}, "create_agent_action_group")
        with pytest.raises(ClientError):
            await bedrock_agent.create_user_input_action_group()


# Test case to verify the creation of a kernel function action group
async def test_create_kernel_function_action_group(bedrock_agent):
    mock_kernel = MagicMock(spec=Kernel)
    with patch.object(bedrock_agent.bedrock_client, "create_agent_action_group", new_callable=AsyncMock) as mock_create_action_group:
        await bedrock_agent._create_kernel_function_action_group(mock_kernel)
        mock_create_action_group.assert_called_once()


# Test case to verify error handling when creating a kernel function action group for an agent that does not exist
async def test_create_kernel_function_action_group_no_id(bedrock_agent):
    bedrock_agent.agent_model.agent_id = None
    mock_kernel = MagicMock(spec=Kernel)
    with pytest.raises(ValueError, match="Agent does not exist. Please create the agent before creating an action group for it."):
        await bedrock_agent._create_kernel_function_action_group(mock_kernel)


# Test case to verify error handling when there are no available functions for the kernel function action group
async def test_create_kernel_function_action_group_no_functions(bedrock_agent):
    mock_kernel = MagicMock(spec=Kernel)
    bedrock_agent.function_choice_behavior.get_config.return_value.available_functions = []
    with patch.object(bedrock_agent.bedrock_client, "create_agent_action_group", new_callable=AsyncMock) as mock_create_action_group:
        await bedrock_agent._create_kernel_function_action_group(mock_kernel)
        mock_create_action_group.assert_not_called()


# Test case to verify error handling when there is a client error during kernel function action group creation
async def test_create_kernel_function_action_group_client_error(bedrock_agent):
    mock_kernel = MagicMock(spec=Kernel)
    with patch.object(bedrock_agent.bedrock_client, "create_agent_action_group", new_callable=AsyncMock) as mock_create_action_group:
        mock_create_action_group.side_effect = ClientError({"Error": {"Code": "500"}}, "create_agent_action_group")
        with pytest.raises(ClientError):
            await bedrock_agent._create_kernel_function_action_group(mock_kernel)


# Test case to verify the association of an agent with a knowledge base
async def test_associate_agent_knowledge_base(bedrock_agent):
    with patch.object(bedrock_agent.bedrock_client, "associate_agent_knowledge_base", new_callable=AsyncMock) as mock_associate_knowledge_base:
        await bedrock_agent.associate_agent_knowledge_base("test_knowledge_base_id")
        mock_associate_knowledge_base.assert_called_once_with(
            agentId=bedrock_agent.agent_model.agent_id,
            agentVersion=bedrock_agent.agent_model.agent_version,
            knowledgeBaseId="test_knowledge_base_id",
        )


# Test case to verify error handling when associating an agent with a knowledge base that does not exist
async def test_associate_agent_knowledge_base_no_id(bedrock_agent):
    bedrock_agent.agent_model.agent_id = None
    with pytest.raises(ValueError, match="Agent does not exist. Please create the agent before associating it with a knowledge base."):
        await bedrock_agent.associate_agent_knowledge_base("test_knowledge_base_id")


# Test case to verify error handling when there is a client error during knowledge base association
async def test_associate_agent_knowledge_base_client_error(bedrock_agent):
    with patch.object(bedrock_agent.bedrock_client, "associate_agent_knowledge_base", new_callable=AsyncMock) as mock_associate_knowledge_base:
        mock_associate_knowledge_base.side_effect = ClientError({"Error": {"Code": "500"}}, "associate_agent_knowledge_base")
        with pytest.raises(ClientError):
            await bedrock_agent.associate_agent_knowledge_base("test_knowledge_base_id")


# Test case to verify the disassociation of an agent with a knowledge base
async def test_disassociate_agent_knowledge_base(bedrock_agent):
    with patch.object(bedrock_agent.bedrock_client, "disassociate_agent_knowledge_base", new_callable=AsyncMock) as mock_disassociate_knowledge_base:
        await bedrock_agent.disassociate_agent_knowledge_base("test_knowledge_base_id")
        mock_disassociate_knowledge_base.assert_called_once_with(
            agentId=bedrock_agent.agent_model.agent_id,
            agentVersion=bedrock_agent.agent_model.agent_version,
            knowledgeBaseId="test_knowledge_base_id",
        )


# Test case to verify error handling when disassociating an agent with a knowledge base that does not exist
async def test_disassociate_agent_knowledge_base_no_id(bedrock_agent):
    bedrock_agent.agent_model.agent_id = None
    with pytest.raises(ValueError, match="Agent does not exist. Please create the agent before disassociating it with a knowledge base."):
        await bedrock_agent.disassociate_agent_knowledge_base("test_knowledge_base_id")


# Test case to verify error handling when there is a client error during knowledge base disassociation
async def test_disassociate_agent_knowledge_base_client_error(bedrock_agent):
    with patch.object(bedrock_agent.bedrock_client, "disassociate_agent_knowledge_base", new_callable=AsyncMock) as mock_disassociate_knowledge_base:
        mock_disassociate_knowledge_base.side_effect = ClientError({"Error": {"Code": "500"}}, "disassociate_agent_knowledge_base")
        with pytest.raises(ClientError):
            await bedrock_agent.disassociate_agent_knowledge_base("test_knowledge_base_id")


# Test case to verify listing associated knowledge bases with an agent
async def test_list_associated_agent_knowledge_bases(bedrock_agent):
    with patch.object(bedrock_agent.bedrock_client, "list_agent_knowledge_bases", new_callable=AsyncMock) as mock_list_knowledge_bases:
        await bedrock_agent.list_associated_agent_knowledge_bases()
        mock_list_knowledge_bases.assert_called_once_with(
            agentId=bedrock_agent.agent_model.agent_id,
            agentVersion=bedrock_agent.agent_model.agent_version,
        )


# Test case to verify error handling when listing associated knowledge bases for an agent that does not exist
async def test_list_associated_agent_knowledge_bases_no_id(bedrock_agent):
    bedrock_agent.agent_model.agent_id = None
    with pytest.raises(ValueError, match="Agent does not exist. Please create the agent before listing associated knowledge bases."):
        await bedrock_agent.list_associated_agent_knowledge_bases()


# Test case to verify error handling when there is a client error during listing associated knowledge bases
async def test_list_associated_agent_knowledge_bases_client_error(bedrock_agent):
    with patch.object(bedrock_agent.bedrock_client, "list_agent_knowledge_bases", new_callable=AsyncMock) as mock_list_knowledge_bases:
        mock_list_knowledge_bases.side_effect = ClientError({"Error": {"Code": "500"}}, "list_agent_knowledge_bases")
        with pytest.raises(ClientError):
            await bedrock_agent.list_associated_agent_knowledge_bases()


# Test case to verify invoking an agent
async def test_invoke_agent(bedrock_agent):
    with patch.object(bedrock_agent.bedrock_runtime_client, "invoke_agent", new_callable=AsyncMock) as mock_invoke_agent:
        await bedrock_agent._invoke_agent("test_session_id", "test_input_text")
        mock_invoke_agent.assert_called_once_with(
            agentAliasId=bedrock_agent.WORKING_DRAFT_AGENT_ALIAS,
            agentId=bedrock_agent.agent_model.agent_id,
            sessionId="test_session_id",
            inputText="test_input_text",
        )


# Test case to verify error handling when invoking an agent that does not exist
async def test_invoke_agent_no_id(bedrock_agent):
    bedrock_agent.agent_model.agent_id = None
    with pytest.raises(ValueError, match="Agent does not exist. Please create the agent before invoking it."):
        await bedrock_agent._invoke_agent("test_session_id", "test_input_text")


# Test case to verify error handling when there is a client error during agent invocation
async def test_invoke_agent_client_error(bedrock_agent):
    with patch.object(bedrock_agent.bedrock_runtime_client, "invoke_agent", new_callable=AsyncMock) as mock_invoke_agent:
        mock_invoke_agent.side_effect = ClientError({"Error": {"Code": "500"}}, "invoke_agent")
        with pytest.raises(ClientError):
            await bedrock_agent._invoke_agent("test_session_id", "test_input_text")
