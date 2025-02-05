# Copyright (c) Microsoft. All rights reserved.

from unittest.mock import Mock, patch

import boto3
import pytest
from botocore.exceptions import ClientError

from semantic_kernel.agents.bedrock.action_group_utils import kernel_function_to_bedrock_function_schema
from semantic_kernel.agents.bedrock.bedrock_agent_base import BedrockAgentBase
from semantic_kernel.agents.bedrock.models.bedrock_agent_status import BedrockAgentStatus


# Test case to verify the creation of an agent
@patch.object(boto3, "client", return_value=Mock())
async def test_create_agent(
    client,
    bedrock_agent_unit_test_env,
    bedrock_agent_model,
    bedrock_agent_model_with_id_not_prepared_dict,
):
    bedrock_agent_base = BedrockAgentBase(
        bedrock_agent_unit_test_env["BEDROCK_AGENT_AGENT_RESOURCE_ROLE_ARN"],
        bedrock_agent_model,
    )

    with (
        patch.object(bedrock_agent_base.bedrock_client, "create_agent") as mock_create_agent,
        patch.object(bedrock_agent_base.bedrock_client, "get_agent") as mock_get_agent,
    ):
        mock_create_agent.return_value = bedrock_agent_model_with_id_not_prepared_dict
        mock_get_agent.return_value = bedrock_agent_model_with_id_not_prepared_dict
        await bedrock_agent_base._create_agent("test_instruction")

        assert bedrock_agent_base.agent_model.agent_id == "test_agent_id"


# Test case to verify error handling when creating an agent that already exists
@patch.object(boto3, "client", return_value=Mock())
async def test_create_agent_already_exists(
    client,
    bedrock_agent_unit_test_env,
    bedrock_agent_model_with_id,
):
    bedrock_agent_base = BedrockAgentBase(
        bedrock_agent_unit_test_env["BEDROCK_AGENT_AGENT_RESOURCE_ROLE_ARN"],
        bedrock_agent_model_with_id,
    )

    with pytest.raises(ValueError, match="Agent already exists. Please delete the agent before creating a new one."):
        await bedrock_agent_base._create_agent("test_instruction")


# Test case to verify error handling when there is a client error during agent creation
@patch.object(boto3, "client", return_value=Mock())
async def test_create_agent_client_error(
    client,
    bedrock_agent_unit_test_env,
    bedrock_agent_model,
):
    bedrock_agent_base = BedrockAgentBase(
        bedrock_agent_unit_test_env["BEDROCK_AGENT_AGENT_RESOURCE_ROLE_ARN"],
        bedrock_agent_model,
    )

    with patch.object(bedrock_agent_base.bedrock_client, "create_agent") as mock_create_agent:
        mock_create_agent.side_effect = ClientError({"Error": {"Code": "500"}}, "create_agent")
        with pytest.raises(ClientError):
            await bedrock_agent_base._create_agent("test_instruction")


# Test case to verify the preparation of an agent
@patch.object(boto3, "client", return_value=Mock())
async def test_prepare_agent(
    client,
    bedrock_agent_unit_test_env,
    bedrock_agent_model_with_id,
    bedrock_agent_model_with_id_prepared_dict,
):
    bedrock_agent_base = BedrockAgentBase(
        bedrock_agent_unit_test_env["BEDROCK_AGENT_AGENT_RESOURCE_ROLE_ARN"],
        bedrock_agent_model_with_id,
    )

    with (
        patch.object(bedrock_agent_base.bedrock_client, "prepare_agent") as mock_prepare_agent,
        patch.object(bedrock_agent_base.bedrock_client, "get_agent") as mock_get_agent,
    ):
        mock_get_agent.return_value = bedrock_agent_model_with_id_prepared_dict
        await bedrock_agent_base.prepare_agent()

        mock_prepare_agent.assert_called_once_with(agentId=bedrock_agent_base.agent_model.agent_id)
        bedrock_agent_base.agent_model.agent_status = BedrockAgentStatus.PREPARED


# Test case to verify error handling when preparing an agent that does not exist
@patch.object(boto3, "client", return_value=Mock())
async def test_prepare_agent_no_id(client, bedrock_agent_unit_test_env, bedrock_agent_model):
    bedrock_agent_base = BedrockAgentBase(
        bedrock_agent_unit_test_env["BEDROCK_AGENT_AGENT_RESOURCE_ROLE_ARN"],
        bedrock_agent_model,
    )

    bedrock_agent_base.agent_model.agent_id = None
    with pytest.raises(ValueError, match="Agent does not exist. Please create the agent before preparing it."):
        await bedrock_agent_base.prepare_agent()


# Test case to verify error handling when there is a client error during agent preparation
@patch.object(boto3, "client", return_value=Mock())
async def test_prepare_agent_client_error(client, bedrock_agent_unit_test_env, bedrock_agent_model_with_id):
    bedrock_agent_base = BedrockAgentBase(
        bedrock_agent_unit_test_env["BEDROCK_AGENT_AGENT_RESOURCE_ROLE_ARN"],
        bedrock_agent_model_with_id,
    )

    with patch.object(bedrock_agent_base.bedrock_client, "prepare_agent") as mock_prepare_agent:
        mock_prepare_agent.side_effect = ClientError({"Error": {"Code": "500"}}, "prepare_agent")
        with pytest.raises(ClientError):
            await bedrock_agent_base.prepare_agent()


# Test case to verify the update of an agent
@patch.object(boto3, "client", return_value=Mock())
async def test_update_agent(
    client,
    bedrock_agent_unit_test_env,
    bedrock_agent_model_with_id,
    bedrock_agent_model_with_id_prepared_dict,
):
    bedrock_agent_base = BedrockAgentBase(
        bedrock_agent_unit_test_env["BEDROCK_AGENT_AGENT_RESOURCE_ROLE_ARN"],
        bedrock_agent_model_with_id,
    )

    new_agent_name = "new_agent_name"
    bedrock_agent_model_with_id_prepared_dict["agent"]["agentName"] = new_agent_name

    with (
        patch.object(bedrock_agent_base.bedrock_client, "update_agent") as mock_update_agent,
        patch.object(bedrock_agent_base.bedrock_client, "get_agent") as mock_get_agent,
    ):
        mock_update_agent.return_value = bedrock_agent_model_with_id_prepared_dict
        mock_get_agent.return_value = bedrock_agent_model_with_id_prepared_dict
        await bedrock_agent_base.update_agent(agentName=new_agent_name)

        mock_update_agent.assert_called_once_with(
            agentId=bedrock_agent_base.agent_model.agent_id,
            agentResourceRoleArn=bedrock_agent_base.agent_resource_role_arn,
            agentName=new_agent_name,
            foundationModel=bedrock_agent_base.agent_model.foundation_model,
        )
        assert bedrock_agent_base.agent_model.agent_status == BedrockAgentStatus.PREPARED


# Test case to verify error handling when updating an agent that does not exist
@patch.object(boto3, "client", return_value=Mock())
async def test_update_agent_no_id(
    client,
    bedrock_agent_unit_test_env,
    bedrock_agent_model,
):
    bedrock_agent_base = BedrockAgentBase(
        bedrock_agent_unit_test_env["BEDROCK_AGENT_AGENT_RESOURCE_ROLE_ARN"],
        bedrock_agent_model,
    )

    with pytest.raises(ValueError, match="Agent has not been created. Please create the agent before updating it."):
        await bedrock_agent_base.update_agent()


# Test case to verify error handling when there is a client error during agent update
@patch.object(boto3, "client", return_value=Mock())
async def test_update_agent_client_error(
    client,
    bedrock_agent_unit_test_env,
    bedrock_agent_model_with_id,
):
    bedrock_agent_base = BedrockAgentBase(
        bedrock_agent_unit_test_env["BEDROCK_AGENT_AGENT_RESOURCE_ROLE_ARN"],
        bedrock_agent_model_with_id,
    )

    with patch.object(bedrock_agent_base.bedrock_client, "update_agent") as mock_update_agent:
        mock_update_agent.side_effect = ClientError({"Error": {"Code": "500"}}, "update_agent")
        with pytest.raises(ClientError):
            await bedrock_agent_base.update_agent()


# Test case to verify the deletion of an agent
@patch.object(boto3, "client", return_value=Mock())
async def test_delete_agent(
    client,
    bedrock_agent_unit_test_env,
    bedrock_agent_model_with_id,
):
    bedrock_agent_base = BedrockAgentBase(
        bedrock_agent_unit_test_env["BEDROCK_AGENT_AGENT_RESOURCE_ROLE_ARN"],
        bedrock_agent_model_with_id,
    )

    agent_id = bedrock_agent_base.agent_model.agent_id
    with patch.object(bedrock_agent_base.bedrock_client, "delete_agent") as mock_delete_agent:
        await bedrock_agent_base.delete_agent()

        mock_delete_agent.assert_called_once_with(agentId=agent_id)
        assert bedrock_agent_base.agent_model.agent_id is None


# Test case to verify error handling when deleting an agent that does not exist
@patch.object(boto3, "client", return_value=Mock())
async def test_delete_agent_no_id(
    client,
    bedrock_agent_unit_test_env,
    bedrock_agent_model,
):
    bedrock_agent_base = BedrockAgentBase(
        bedrock_agent_unit_test_env["BEDROCK_AGENT_AGENT_RESOURCE_ROLE_ARN"],
        bedrock_agent_model,
    )

    bedrock_agent_base.agent_model.agent_id = None
    with pytest.raises(ValueError, match="Agent does not exist. Please create the agent before deleting it."):
        await bedrock_agent_base.delete_agent()


# Test case to verify error handling when there is a client error during agent deletion
@patch.object(boto3, "client", return_value=Mock())
async def test_delete_agent_client_error(
    client,
    bedrock_agent_unit_test_env,
    bedrock_agent_model_with_id,
):
    bedrock_agent_base = BedrockAgentBase(
        bedrock_agent_unit_test_env["BEDROCK_AGENT_AGENT_RESOURCE_ROLE_ARN"],
        bedrock_agent_model_with_id,
    )

    with patch.object(bedrock_agent_base.bedrock_client, "delete_agent") as mock_delete_agent:
        mock_delete_agent.side_effect = ClientError({"Error": {"Code": "500"}}, "delete_agent")
        with pytest.raises(ClientError):
            await bedrock_agent_base.delete_agent()


# Test case to verify the retrieval of an agent
@patch.object(boto3, "client", return_value=Mock())
async def test_get_agent(
    client,
    bedrock_agent_unit_test_env,
    bedrock_agent_model_with_id,
    bedrock_agent_model_with_id_prepared_dict,
):
    bedrock_agent_base = BedrockAgentBase(
        bedrock_agent_unit_test_env["BEDROCK_AGENT_AGENT_RESOURCE_ROLE_ARN"],
        bedrock_agent_model_with_id,
    )

    with patch.object(bedrock_agent_base.bedrock_client, "get_agent") as mock_get_agent:
        mock_get_agent.return_value = bedrock_agent_model_with_id_prepared_dict
        await bedrock_agent_base._get_agent()

        mock_get_agent.assert_called_once_with(agentId=bedrock_agent_base.agent_model.agent_id)


# Test case to verify error handling when retrieving an agent that does not exist
@patch.object(boto3, "client", return_value=Mock())
async def test_get_agent_no_id(
    client,
    bedrock_agent_unit_test_env,
    bedrock_agent_model,
):
    bedrock_agent_base = BedrockAgentBase(
        bedrock_agent_unit_test_env["BEDROCK_AGENT_AGENT_RESOURCE_ROLE_ARN"],
        bedrock_agent_model,
    )

    with pytest.raises(ValueError, match="Agent does not exist. Please create the agent before getting it."):
        await bedrock_agent_base._get_agent()


# Test case to verify error handling when there is a client error during agent retrieval
@patch.object(boto3, "client", return_value=Mock())
async def test_get_agent_client_error(
    client,
    bedrock_agent_unit_test_env,
    bedrock_agent_model_with_id,
):
    bedrock_agent_base = BedrockAgentBase(
        bedrock_agent_unit_test_env["BEDROCK_AGENT_AGENT_RESOURCE_ROLE_ARN"],
        bedrock_agent_model_with_id,
    )

    with patch.object(bedrock_agent_base.bedrock_client, "get_agent") as mock_get_agent:
        mock_get_agent.side_effect = ClientError({"Error": {"Code": "500"}}, "get_agent")
        with pytest.raises(ClientError):
            await bedrock_agent_base._get_agent()


# Test case to verify waiting for an agent to reach a specific status
@patch.object(boto3, "client", return_value=Mock())
async def test_wait_for_agent_status(
    client,
    bedrock_agent_unit_test_env,
    bedrock_agent_model_with_id,
    bedrock_agent_model_with_id_prepared_dict,
):
    bedrock_agent_base = BedrockAgentBase(
        bedrock_agent_unit_test_env["BEDROCK_AGENT_AGENT_RESOURCE_ROLE_ARN"],
        bedrock_agent_model_with_id,
    )

    with patch.object(bedrock_agent_base.bedrock_client, "get_agent") as mock_get_agent:
        mock_get_agent.return_value = bedrock_agent_model_with_id_prepared_dict

        await bedrock_agent_base._wait_for_agent_status(BedrockAgentStatus.PREPARED)

        mock_get_agent.assert_called_once()


# Test case to verify error handling when waiting for an agent to reach a specific status times out
@patch.object(boto3, "client", return_value=Mock())
async def test_wait_for_agent_status_timeout(
    client,
    bedrock_agent_unit_test_env,
    bedrock_agent_model_with_id,
    bedrock_agent_model_with_id_not_prepared_dict,
):
    bedrock_agent_base = BedrockAgentBase(
        bedrock_agent_unit_test_env["BEDROCK_AGENT_AGENT_RESOURCE_ROLE_ARN"],
        bedrock_agent_model_with_id,
    )

    with patch.object(bedrock_agent_base.bedrock_client, "get_agent") as mock_get_agent:
        mock_get_agent.return_value = bedrock_agent_model_with_id_not_prepared_dict

        with pytest.raises(
            TimeoutError,
            match=f"Agent did not reach status {BedrockAgentStatus.PREPARED} within the specified time.",
        ):
            await bedrock_agent_base._wait_for_agent_status(BedrockAgentStatus.PREPARED, max_attempts=3)

            assert mock_get_agent.call_count == 3


# Test case to verify the creation of a code interpreter action group
@patch.object(boto3, "client", return_value=Mock())
async def test_create_code_interpreter_action_group(
    client,
    bedrock_agent_unit_test_env,
    bedrock_agent_model_with_id,
    bedrock_action_group_mode_dict,
):
    bedrock_agent_base = BedrockAgentBase(
        bedrock_agent_unit_test_env["BEDROCK_AGENT_AGENT_RESOURCE_ROLE_ARN"],
        bedrock_agent_model_with_id,
    )

    with patch.object(bedrock_agent_base.bedrock_client, "create_agent_action_group") as mock_create_action_group:
        mock_create_action_group.return_value = bedrock_action_group_mode_dict
        action_group_model = await bedrock_agent_base.create_code_interpreter_action_group()

        mock_create_action_group.assert_called_once_with(
            agentId=bedrock_agent_base.agent_model.agent_id,
            agentVersion=bedrock_agent_base.agent_model.agent_version or "DRAFT",
            actionGroupName=f"{bedrock_agent_base.agent_model.agent_name}_code_interpreter",
            actionGroupState="ENABLED",
            parentActionGroupSignature="AMAZON.CodeInterpreter",
        )
        assert action_group_model.action_group_id == bedrock_action_group_mode_dict["agentActionGroup"]["actionGroupId"]


# Test case to verify error handling when creating a code interpreter action group for an agent that does not exist
@patch.object(boto3, "client", return_value=Mock())
async def test_create_code_interpreter_action_group_no_id(
    client,
    bedrock_agent_unit_test_env,
    bedrock_agent_model,
):
    bedrock_agent_base = BedrockAgentBase(
        bedrock_agent_unit_test_env["BEDROCK_AGENT_AGENT_RESOURCE_ROLE_ARN"],
        bedrock_agent_model,
    )

    with pytest.raises(
        ValueError, match="Agent does not exist. Please create the agent before creating an action group for it."
    ):
        await bedrock_agent_base.create_code_interpreter_action_group()


# Test case to verify error handling when there is a client error during code interpreter action group creation
@patch.object(boto3, "client", return_value=Mock())
async def test_create_code_interpreter_action_group_client_error(
    client,
    bedrock_agent_unit_test_env,
    bedrock_agent_model_with_id,
):
    bedrock_agent_base = BedrockAgentBase(
        bedrock_agent_unit_test_env["BEDROCK_AGENT_AGENT_RESOURCE_ROLE_ARN"],
        bedrock_agent_model_with_id,
    )

    with patch.object(bedrock_agent_base.bedrock_client, "create_agent_action_group") as mock_create_action_group:
        mock_create_action_group.side_effect = ClientError({"Error": {"Code": "500"}}, "create_agent_action_group")
        with pytest.raises(ClientError):
            await bedrock_agent_base.create_code_interpreter_action_group()


# Test case to verify the creation of a user input action group
@patch.object(boto3, "client", return_value=Mock())
async def test_create_user_input_action_group(
    client,
    bedrock_agent_unit_test_env,
    bedrock_agent_model_with_id,
    bedrock_action_group_mode_dict,
):
    bedrock_agent_base = BedrockAgentBase(
        bedrock_agent_unit_test_env["BEDROCK_AGENT_AGENT_RESOURCE_ROLE_ARN"],
        bedrock_agent_model_with_id,
    )

    with patch.object(bedrock_agent_base.bedrock_client, "create_agent_action_group") as mock_create_action_group:
        mock_create_action_group.return_value = bedrock_action_group_mode_dict
        action_group_model = await bedrock_agent_base.create_user_input_action_group()

        mock_create_action_group.assert_called_once_with(
            agentId=bedrock_agent_base.agent_model.agent_id,
            agentVersion=bedrock_agent_base.agent_model.agent_version or "DRAFT",
            actionGroupName=f"{bedrock_agent_base.agent_model.agent_name}_user_input",
            actionGroupState="ENABLED",
            parentActionGroupSignature="AMAZON.UserInput",
        )
        assert action_group_model.action_group_id == bedrock_action_group_mode_dict["agentActionGroup"]["actionGroupId"]


# Test case to verify error handling when creating a user input action group for an agent that does not exist
@patch.object(boto3, "client", return_value=Mock())
async def test_create_user_input_action_group_no_id(
    client,
    bedrock_agent_unit_test_env,
    bedrock_agent_model,
):
    bedrock_agent_base = BedrockAgentBase(
        bedrock_agent_unit_test_env["BEDROCK_AGENT_AGENT_RESOURCE_ROLE_ARN"],
        bedrock_agent_model,
    )

    with pytest.raises(
        ValueError, match="Agent does not exist. Please create the agent before creating an action group for it."
    ):
        await bedrock_agent_base.create_user_input_action_group()


# Test case to verify error handling when there is a client error during user input action group creation
@patch.object(boto3, "client", return_value=Mock())
async def test_create_user_input_action_group_client_error(
    client,
    bedrock_agent_unit_test_env,
    bedrock_agent_model_with_id,
):
    bedrock_agent_base = BedrockAgentBase(
        bedrock_agent_unit_test_env["BEDROCK_AGENT_AGENT_RESOURCE_ROLE_ARN"],
        bedrock_agent_model_with_id,
    )

    with patch.object(bedrock_agent_base.bedrock_client, "create_agent_action_group") as mock_create_action_group:
        mock_create_action_group.side_effect = ClientError({"Error": {"Code": "500"}}, "create_agent_action_group")
        with pytest.raises(ClientError):
            await bedrock_agent_base.create_user_input_action_group()


# Test case to verify the creation of a kernel function action group
@patch.object(boto3, "client", return_value=Mock())
async def test_create_kernel_function_action_group(
    client,
    kernel_with_function,
    bedrock_agent_unit_test_env,
    bedrock_agent_model_with_id,
    bedrock_action_group_mode_dict,
):
    bedrock_agent_base = BedrockAgentBase(
        bedrock_agent_unit_test_env["BEDROCK_AGENT_AGENT_RESOURCE_ROLE_ARN"],
        bedrock_agent_model_with_id,
    )

    with patch.object(bedrock_agent_base.bedrock_client, "create_agent_action_group") as mock_create_action_group:
        mock_create_action_group.return_value = bedrock_action_group_mode_dict

        action_group_model = await bedrock_agent_base._create_kernel_function_action_group(kernel_with_function)

        mock_create_action_group.assert_called_once_with(
            agentId=bedrock_agent_base.agent_model.agent_id,
            agentVersion=bedrock_agent_base.agent_model.agent_version or "DRAFT",
            actionGroupName=f"{bedrock_agent_base.agent_model.agent_name}_kernel_function",
            actionGroupState="ENABLED",
            actionGroupExecutor={"customControl": "RETURN_CONTROL"},
            functionSchema=kernel_function_to_bedrock_function_schema(
                bedrock_agent_base.function_choice_behavior.get_config(kernel_with_function)
            ),
        )
        assert action_group_model.action_group_id == bedrock_action_group_mode_dict["agentActionGroup"]["actionGroupId"]


# Test case to verify error handling when creating a kernel function action group for an agent that does not exist
@patch.object(boto3, "client", return_value=Mock())
async def test_create_kernel_function_action_group_no_id(
    client,
    kernel_with_function,
    bedrock_agent_unit_test_env,
    bedrock_agent_model,
):
    bedrock_agent_base = BedrockAgentBase(
        bedrock_agent_unit_test_env["BEDROCK_AGENT_AGENT_RESOURCE_ROLE_ARN"],
        bedrock_agent_model,
    )

    with pytest.raises(
        ValueError, match="Agent does not exist. Please create the agent before creating an action group for it."
    ):
        await bedrock_agent_base._create_kernel_function_action_group(kernel_with_function)


# Test case to verify error handling when there are no available functions for the kernel function action group
@patch.object(boto3, "client", return_value=Mock())
async def test_create_kernel_function_action_group_no_functions(
    client,
    kernel,
    bedrock_agent_unit_test_env,
    bedrock_agent_model_with_id,
):
    bedrock_agent_base = BedrockAgentBase(
        bedrock_agent_unit_test_env["BEDROCK_AGENT_AGENT_RESOURCE_ROLE_ARN"],
        bedrock_agent_model_with_id,
    )

    with patch.object(bedrock_agent_base.bedrock_client, "create_agent_action_group") as mock_create_action_group:
        action_group_model = await bedrock_agent_base._create_kernel_function_action_group(kernel)

        assert action_group_model is None
        mock_create_action_group.assert_not_called()


# Test case to verify error handling when there is a client error during kernel function action group creation
@patch.object(boto3, "client", return_value=Mock())
async def test_create_kernel_function_action_group_client_error(
    client,
    kernel_with_function,
    bedrock_agent_unit_test_env,
    bedrock_agent_model_with_id,
):
    bedrock_agent_base = BedrockAgentBase(
        bedrock_agent_unit_test_env["BEDROCK_AGENT_AGENT_RESOURCE_ROLE_ARN"],
        bedrock_agent_model_with_id,
    )

    with patch.object(bedrock_agent_base.bedrock_client, "create_agent_action_group") as mock_create_action_group:
        mock_create_action_group.side_effect = ClientError({"Error": {"Code": "500"}}, "create_agent_action_group")
        with pytest.raises(ClientError):
            await bedrock_agent_base._create_kernel_function_action_group(kernel_with_function)


# Test case to verify the association of an agent with a knowledge base
@patch.object(boto3, "client", return_value=Mock())
async def test_associate_agent_knowledge_base(
    client,
    bedrock_agent_unit_test_env,
    bedrock_agent_model_with_id,
):
    bedrock_agent_base = BedrockAgentBase(
        bedrock_agent_unit_test_env["BEDROCK_AGENT_AGENT_RESOURCE_ROLE_ARN"],
        bedrock_agent_model_with_id,
    )

    with patch.object(
        bedrock_agent_base.bedrock_client, "associate_agent_knowledge_base"
    ) as mock_associate_knowledge_base:
        await bedrock_agent_base.associate_agent_knowledge_base("test_knowledge_base_id")

        mock_associate_knowledge_base.assert_called_once_with(
            agentId=bedrock_agent_base.agent_model.agent_id,
            agentVersion=bedrock_agent_base.agent_model.agent_version,
            knowledgeBaseId="test_knowledge_base_id",
        )


# Test case to verify error handling when associating an agent with a knowledge base that does not exist
@patch.object(boto3, "client", return_value=Mock())
async def test_associate_agent_knowledge_base_no_id(
    client,
    bedrock_agent_unit_test_env,
    bedrock_agent_model,
):
    bedrock_agent_base = BedrockAgentBase(
        bedrock_agent_unit_test_env["BEDROCK_AGENT_AGENT_RESOURCE_ROLE_ARN"],
        bedrock_agent_model,
    )

    with pytest.raises(
        ValueError, match="Agent does not exist. Please create the agent before associating it with a knowledge base."
    ):
        await bedrock_agent_base.associate_agent_knowledge_base("test_knowledge_base_id")


# Test case to verify error handling when there is a client error during knowledge base association
@patch.object(boto3, "client", return_value=Mock())
async def test_associate_agent_knowledge_base_client_error(
    client,
    bedrock_agent_unit_test_env,
    bedrock_agent_model_with_id,
):
    bedrock_agent_base = BedrockAgentBase(
        bedrock_agent_unit_test_env["BEDROCK_AGENT_AGENT_RESOURCE_ROLE_ARN"],
        bedrock_agent_model_with_id,
    )

    with patch.object(
        bedrock_agent_base.bedrock_client, "associate_agent_knowledge_base"
    ) as mock_associate_knowledge_base:
        mock_associate_knowledge_base.side_effect = ClientError(
            {"Error": {"Code": "500"}}, "associate_agent_knowledge_base"
        )
        with pytest.raises(ClientError):
            await bedrock_agent_base.associate_agent_knowledge_base("test_knowledge_base_id")


# Test case to verify the disassociation of an agent with a knowledge base
@patch.object(boto3, "client", return_value=Mock())
async def test_disassociate_agent_knowledge_base(
    client,
    bedrock_agent_unit_test_env,
    bedrock_agent_model_with_id,
):
    bedrock_agent_base = BedrockAgentBase(
        bedrock_agent_unit_test_env["BEDROCK_AGENT_AGENT_RESOURCE_ROLE_ARN"],
        bedrock_agent_model_with_id,
    )

    with patch.object(
        bedrock_agent_base.bedrock_client, "disassociate_agent_knowledge_base"
    ) as mock_disassociate_knowledge_base:
        await bedrock_agent_base.disassociate_agent_knowledge_base("test_knowledge_base_id")
        mock_disassociate_knowledge_base.assert_called_once_with(
            agentId=bedrock_agent_base.agent_model.agent_id,
            agentVersion=bedrock_agent_base.agent_model.agent_version,
            knowledgeBaseId="test_knowledge_base_id",
        )


# Test case to verify error handling when disassociating an agent with a knowledge base that does not exist
@patch.object(boto3, "client", return_value=Mock())
async def test_disassociate_agent_knowledge_base_no_id(
    client,
    bedrock_agent_unit_test_env,
    bedrock_agent_model,
):
    bedrock_agent_base = BedrockAgentBase(
        bedrock_agent_unit_test_env["BEDROCK_AGENT_AGENT_RESOURCE_ROLE_ARN"],
        bedrock_agent_model,
    )

    with pytest.raises(
        ValueError,
        match="Agent does not exist. Please create the agent before disassociating it with a knowledge base.",
    ):
        await bedrock_agent_base.disassociate_agent_knowledge_base("test_knowledge_base_id")


# Test case to verify error handling when there is a client error during knowledge base disassociation
@patch.object(boto3, "client", return_value=Mock())
async def test_disassociate_agent_knowledge_base_client_error(
    client,
    bedrock_agent_unit_test_env,
    bedrock_agent_model_with_id,
):
    bedrock_agent_base = BedrockAgentBase(
        bedrock_agent_unit_test_env["BEDROCK_AGENT_AGENT_RESOURCE_ROLE_ARN"],
        bedrock_agent_model_with_id,
    )

    with patch.object(
        bedrock_agent_base.bedrock_client, "disassociate_agent_knowledge_base"
    ) as mock_disassociate_knowledge_base:
        mock_disassociate_knowledge_base.side_effect = ClientError(
            {"Error": {"Code": "500"}}, "disassociate_agent_knowledge_base"
        )
        with pytest.raises(ClientError):
            await bedrock_agent_base.disassociate_agent_knowledge_base("test_knowledge_base_id")


# Test case to verify listing associated knowledge bases with an agent
@patch.object(boto3, "client", return_value=Mock())
async def test_list_associated_agent_knowledge_bases(
    client,
    bedrock_agent_unit_test_env,
    bedrock_agent_model_with_id,
):
    bedrock_agent_base = BedrockAgentBase(
        bedrock_agent_unit_test_env["BEDROCK_AGENT_AGENT_RESOURCE_ROLE_ARN"],
        bedrock_agent_model_with_id,
    )

    with patch.object(bedrock_agent_base.bedrock_client, "list_agent_knowledge_bases") as mock_list_knowledge_bases:
        await bedrock_agent_base.list_associated_agent_knowledge_bases()

        mock_list_knowledge_bases.assert_called_once_with(
            agentId=bedrock_agent_base.agent_model.agent_id,
            agentVersion=bedrock_agent_base.agent_model.agent_version,
        )


# Test case to verify error handling when listing associated knowledge bases for an agent that does not exist
@patch.object(boto3, "client", return_value=Mock())
async def test_list_associated_agent_knowledge_bases_no_id(
    client,
    bedrock_agent_unit_test_env,
    bedrock_agent_model,
):
    bedrock_agent_base = BedrockAgentBase(
        bedrock_agent_unit_test_env["BEDROCK_AGENT_AGENT_RESOURCE_ROLE_ARN"],
        bedrock_agent_model,
    )

    with pytest.raises(
        ValueError, match="Agent does not exist. Please create the agent before listing associated knowledge bases."
    ):
        await bedrock_agent_base.list_associated_agent_knowledge_bases()


# Test case to verify error handling when there is a client error during listing associated knowledge bases
@patch.object(boto3, "client", return_value=Mock())
async def test_list_associated_agent_knowledge_bases_client_error(
    client,
    bedrock_agent_unit_test_env,
    bedrock_agent_model_with_id,
):
    bedrock_agent_base = BedrockAgentBase(
        bedrock_agent_unit_test_env["BEDROCK_AGENT_AGENT_RESOURCE_ROLE_ARN"],
        bedrock_agent_model_with_id,
    )

    with patch.object(bedrock_agent_base.bedrock_client, "list_agent_knowledge_bases") as mock_list_knowledge_bases:
        mock_list_knowledge_bases.side_effect = ClientError({"Error": {"Code": "500"}}, "list_agent_knowledge_bases")
        with pytest.raises(ClientError):
            await bedrock_agent_base.list_associated_agent_knowledge_bases()


# Test case to verify invoking an agent
@patch.object(boto3, "client", return_value=Mock())
async def test_invoke_agent(
    client,
    bedrock_agent_unit_test_env,
    bedrock_agent_model_with_id,
):
    bedrock_agent_base = BedrockAgentBase(
        bedrock_agent_unit_test_env["BEDROCK_AGENT_AGENT_RESOURCE_ROLE_ARN"],
        bedrock_agent_model_with_id,
    )

    with patch.object(bedrock_agent_base.bedrock_runtime_client, "invoke_agent") as mock_invoke_agent:
        await bedrock_agent_base._invoke_agent("test_session_id", "test_input_text")

        mock_invoke_agent.assert_called_once_with(
            agentAliasId=bedrock_agent_base.WORKING_DRAFT_AGENT_ALIAS,
            agentId=bedrock_agent_base.agent_model.agent_id,
            sessionId="test_session_id",
            inputText="test_input_text",
        )


# Test case to verify error handling when invoking an agent that does not exist
@patch.object(boto3, "client", return_value=Mock())
async def test_invoke_agent_no_id(
    client,
    bedrock_agent_unit_test_env,
    bedrock_agent_model,
):
    bedrock_agent_base = BedrockAgentBase(
        bedrock_agent_unit_test_env["BEDROCK_AGENT_AGENT_RESOURCE_ROLE_ARN"],
        bedrock_agent_model,
    )

    with pytest.raises(ValueError, match="Agent does not exist. Please create the agent before invoking it."):
        await bedrock_agent_base._invoke_agent("test_session_id", "test_input_text")


# Test case to verify error handling when there is a client error during agent invocation
@patch.object(boto3, "client", return_value=Mock())
async def test_invoke_agent_client_error(
    client,
    bedrock_agent_unit_test_env,
    bedrock_agent_model_with_id,
):
    bedrock_agent_base = BedrockAgentBase(
        bedrock_agent_unit_test_env["BEDROCK_AGENT_AGENT_RESOURCE_ROLE_ARN"],
        bedrock_agent_model_with_id,
    )

    with patch.object(bedrock_agent_base.bedrock_runtime_client, "invoke_agent") as mock_invoke_agent:
        mock_invoke_agent.side_effect = ClientError({"Error": {"Code": "500"}}, "invoke_agent")
        with pytest.raises(ClientError):
            await bedrock_agent_base._invoke_agent("test_session_id", "test_input_text")
