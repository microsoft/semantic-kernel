# Copyright (c) Microsoft. All rights reserved.

from unittest.mock import AsyncMock, Mock, PropertyMock, patch

import boto3
import pytest

from semantic_kernel.agents.bedrock.action_group_utils import (
    kernel_function_to_bedrock_function_schema,
    parse_function_result_contents,
)
from semantic_kernel.agents.bedrock.bedrock_agent import BedrockAgent, BedrockAgentThread
from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceBehavior
from semantic_kernel.contents.function_result_content import FunctionResultContent
from semantic_kernel.exceptions.agent_exceptions import AgentInitializationException, AgentInvokeException
from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.kernel import Kernel

# region Agent Initialization Tests


# Test case to verify BedrockAgent initialization
@patch.object(boto3, "client", return_value=Mock())
async def test_bedrock_agent_initialization(client, bedrock_agent_model_with_id):
    agent = BedrockAgent(bedrock_agent_model_with_id)

    assert agent.name == bedrock_agent_model_with_id.agent_name
    assert agent.agent_model.agent_name == bedrock_agent_model_with_id.agent_name
    assert agent.agent_model.agent_id == bedrock_agent_model_with_id.agent_id
    assert agent.agent_model.foundation_model == bedrock_agent_model_with_id.foundation_model


# Test case to verify error handling during BedrockAgent initialization with non-auto function choice
@patch.object(boto3, "client", return_value=Mock())
async def test_bedrock_agent_initialization_error_with_non_auto_function_choice(client, bedrock_agent_model_with_id):
    with pytest.raises(ValueError, match="Only FunctionChoiceType.AUTO is supported."):
        BedrockAgent(
            bedrock_agent_model_with_id,
            function_choice_behavior=FunctionChoiceBehavior.NoneInvoke(),
        )


# Test case to verify the creation of BedrockAgent
@patch.object(boto3, "client", return_value=Mock())
@pytest.mark.parametrize(
    "kernel, function_choice_behavior, arguments",
    [
        (None, None, None),
        (Kernel(), None, None),
        (Kernel(), FunctionChoiceBehavior.Auto(), None),
        (Kernel(), FunctionChoiceBehavior.Auto(), KernelArguments()),
    ],
)
async def test_bedrock_agent_create_and_prepare_agent(
    client,
    bedrock_agent_model_with_id_not_prepared_dict,
    bedrock_agent_unit_test_env,
    kernel,
    function_choice_behavior,
    arguments,
):
    with (
        patch.object(client, "create_agent") as mock_create_agent,
        patch.object(BedrockAgent, "_wait_for_agent_status", new_callable=AsyncMock),
        patch.object(BedrockAgent, "prepare_agent_and_wait_until_prepared", new_callable=AsyncMock),
    ):
        mock_create_agent.return_value = bedrock_agent_model_with_id_not_prepared_dict

        agent = await BedrockAgent.create_and_prepare_agent(
            name=bedrock_agent_model_with_id_not_prepared_dict["agent"]["agentName"],
            instructions="test_instructions",
            bedrock_client=client,
            env_file_path="fake_path",
            kernel=kernel,
            function_choice_behavior=function_choice_behavior,
            arguments=arguments,
        )

        mock_create_agent.assert_called_once_with(
            agentName=bedrock_agent_model_with_id_not_prepared_dict["agent"]["agentName"],
            foundationModel=bedrock_agent_unit_test_env["BEDROCK_AGENT_FOUNDATION_MODEL"],
            agentResourceRoleArn=bedrock_agent_unit_test_env["BEDROCK_AGENT_AGENT_RESOURCE_ROLE_ARN"],
            instruction="test_instructions",
        )
        assert agent.agent_model.agent_id == bedrock_agent_model_with_id_not_prepared_dict["agent"]["agentId"]
        assert agent.id == bedrock_agent_model_with_id_not_prepared_dict["agent"]["agentId"]
        assert agent.agent_model.agent_name == bedrock_agent_model_with_id_not_prepared_dict["agent"]["agentName"]
        assert agent.name == bedrock_agent_model_with_id_not_prepared_dict["agent"]["agentName"]
        assert (
            agent.agent_model.foundation_model
            == bedrock_agent_model_with_id_not_prepared_dict["agent"]["foundationModel"]
        )
        assert agent.kernel is not None
        assert agent.function_choice_behavior is not None
        if arguments:
            assert agent.arguments is not None


# Test case to verify the creation of BedrockAgent
@pytest.mark.parametrize(
    "exclude_list",
    [
        ["BEDROCK_AGENT_AGENT_RESOURCE_ROLE_ARN"],
        ["BEDROCK_AGENT_FOUNDATION_MODEL"],
    ],
    indirect=True,
)
@patch.object(boto3, "client", return_value=Mock())
async def test_bedrock_agent_create_and_prepare_agent_settings_validation_error(
    client,
    bedrock_agent_model_with_id_not_prepared_dict,
    bedrock_agent_unit_test_env,
):
    with pytest.raises(AgentInitializationException):
        await BedrockAgent.create_and_prepare_agent(
            name=bedrock_agent_model_with_id_not_prepared_dict["agent"]["agentName"],
            instructions="test_instructions",
            env_file_path="fake_path",
        )


# Test case to verify the creation of BedrockAgent
@patch.object(boto3, "client", return_value=Mock())
async def test_bedrock_agent_create_and_prepare_agent_service_exception(
    client,
    bedrock_agent_model_with_id_not_prepared_dict,
    bedrock_agent_unit_test_env,
):
    with (
        patch.object(client, "create_agent") as mock_create_agent,
        patch.object(BedrockAgent, "prepare_agent_and_wait_until_prepared", new_callable=AsyncMock),
    ):
        from botocore.exceptions import ClientError

        mock_create_agent.side_effect = ClientError({}, "create_agent")

        with pytest.raises(AgentInitializationException):
            await BedrockAgent.create_and_prepare_agent(
                name=bedrock_agent_model_with_id_not_prepared_dict["agent"]["agentName"],
                instructions="test_instructions",
                bedrock_client=client,
                env_file_path="fake_path",
            )


@patch.object(boto3, "client", return_value=Mock())
async def test_bedrock_agent_prepare_agent_and_wait_until_prepared(
    client,
    bedrock_agent_unit_test_env,
    bedrock_agent_model_with_id,
    bedrock_agent_model_with_id_preparing_dict,
    bedrock_agent_model_with_id_prepared_dict,
):
    agent = BedrockAgent(bedrock_agent_model_with_id, bedrock_client=client)

    with (
        patch.object(client, "get_agent") as mock_get_agent,
        patch.object(client, "prepare_agent") as mock_prepare_agent,
    ):
        mock_get_agent.side_effect = [
            bedrock_agent_model_with_id_preparing_dict,
            bedrock_agent_model_with_id_prepared_dict,
        ]

        await agent.prepare_agent_and_wait_until_prepared()

        mock_prepare_agent.assert_called_once_with(agentId=bedrock_agent_model_with_id.agent_id)
        assert mock_get_agent.call_count == 2
        assert agent.agent_model.agent_status == "PREPARED"


@patch.object(boto3, "client", return_value=Mock())
async def test_bedrock_agent_prepare_agent_and_wait_until_prepared_fail(
    client,
    bedrock_agent_unit_test_env,
    bedrock_agent_model_with_id,
    bedrock_agent_model_with_id_preparing_dict,
):
    agent = BedrockAgent(bedrock_agent_model_with_id, bedrock_client=client)

    with (
        patch.object(client, "get_agent") as mock_get_agent,
        patch.object(client, "prepare_agent"),
    ):
        mock_get_agent.side_effect = [
            bedrock_agent_model_with_id_preparing_dict,
            bedrock_agent_model_with_id_preparing_dict,
            bedrock_agent_model_with_id_preparing_dict,
            bedrock_agent_model_with_id_preparing_dict,
            bedrock_agent_model_with_id_preparing_dict,
            bedrock_agent_model_with_id_preparing_dict,
        ]

        with pytest.raises(TimeoutError):
            await agent.prepare_agent_and_wait_until_prepared()


# Test case to verify the creation of a code interpreter action group
@patch.object(boto3, "client", return_value=Mock())
async def test_create_code_interpreter_action_group(
    client,
    bedrock_agent_unit_test_env,
    bedrock_agent_model_with_id,
    bedrock_action_group_mode_dict,
):
    agent = BedrockAgent(bedrock_agent_model_with_id, bedrock_client=client)

    with (
        patch.object(client, "create_agent_action_group") as mock_create_action_group,
        patch.object(
            BedrockAgent, "prepare_agent_and_wait_until_prepared"
        ) as mock_prepare_agent_and_wait_until_prepared,
    ):
        mock_create_action_group.return_value = bedrock_action_group_mode_dict
        action_group_model = await agent.create_code_interpreter_action_group()

        mock_create_action_group.assert_called_once_with(
            agentId=agent.agent_model.agent_id,
            agentVersion=agent.agent_model.agent_version or "DRAFT",
            actionGroupName=f"{agent.agent_model.agent_name}_code_interpreter",
            actionGroupState="ENABLED",
            parentActionGroupSignature="AMAZON.CodeInterpreter",
        )
        assert action_group_model.action_group_id == bedrock_action_group_mode_dict["agentActionGroup"]["actionGroupId"]
        mock_prepare_agent_and_wait_until_prepared.assert_called_once()


# Test case to verify the creation of BedrockAgent with plugins
@patch.object(boto3, "client", return_value=Mock())
async def test_bedrock_agent_create_with_plugin_via_constructor(
    client,
    bedrock_agent_unit_test_env,
    bedrock_agent_model_with_id,
    custom_plugin_class,
):
    agent = BedrockAgent(
        bedrock_agent_model_with_id,
        plugins=[custom_plugin_class()],
        bedrock_client=client,
    )

    assert agent.kernel.plugins is not None
    assert len(agent.kernel.plugins) == 1


# Test case to verify the creation of a user input action group
@patch.object(boto3, "client", return_value=Mock())
async def test_create_user_input_action_group(
    client,
    bedrock_agent_unit_test_env,
    bedrock_agent_model_with_id,
    bedrock_action_group_mode_dict,
):
    agent = BedrockAgent(bedrock_agent_model_with_id, bedrock_client=client)

    with (
        patch.object(agent.bedrock_client, "create_agent_action_group") as mock_create_action_group,
        patch.object(
            BedrockAgent, "prepare_agent_and_wait_until_prepared"
        ) as mock_prepare_agent_and_wait_until_prepared,
    ):
        mock_create_action_group.return_value = bedrock_action_group_mode_dict
        action_group_model = await agent.create_user_input_action_group()

        mock_create_action_group.assert_called_once_with(
            agentId=agent.agent_model.agent_id,
            agentVersion=agent.agent_model.agent_version or "DRAFT",
            actionGroupName=f"{agent.agent_model.agent_name}_user_input",
            actionGroupState="ENABLED",
            parentActionGroupSignature="AMAZON.UserInput",
        )
        assert action_group_model.action_group_id == bedrock_action_group_mode_dict["agentActionGroup"]["actionGroupId"]
        mock_prepare_agent_and_wait_until_prepared.assert_called_once()


# Test case to verify the creation of a kernel function action group
@patch.object(boto3, "client", return_value=Mock())
async def test_create_kernel_function_action_group(
    client,
    kernel_with_function,
    bedrock_agent_unit_test_env,
    bedrock_agent_model_with_id,
    bedrock_action_group_mode_dict,
):
    agent = BedrockAgent(bedrock_agent_model_with_id, kernel=kernel_with_function, bedrock_client=client)

    with (
        patch.object(agent.bedrock_client, "create_agent_action_group") as mock_create_action_group,
        patch.object(
            BedrockAgent, "prepare_agent_and_wait_until_prepared"
        ) as mock_prepare_agent_and_wait_until_prepared,
    ):
        mock_create_action_group.return_value = bedrock_action_group_mode_dict

        action_group_model = await agent.create_kernel_function_action_group()

        mock_create_action_group.assert_called_once_with(
            agentId=agent.agent_model.agent_id,
            agentVersion=agent.agent_model.agent_version or "DRAFT",
            actionGroupName=f"{agent.agent_model.agent_name}_kernel_function",
            actionGroupState="ENABLED",
            actionGroupExecutor={"customControl": "RETURN_CONTROL"},
            functionSchema=kernel_function_to_bedrock_function_schema(
                agent.function_choice_behavior.get_config(kernel_with_function)
            ),
        )
        assert action_group_model.action_group_id == bedrock_action_group_mode_dict["agentActionGroup"]["actionGroupId"]
        mock_prepare_agent_and_wait_until_prepared.assert_called_once()


# Test case to verify the association of an agent with a knowledge base
@patch.object(boto3, "client", return_value=Mock())
async def test_associate_agent_knowledge_base(
    client,
    bedrock_agent_unit_test_env,
    bedrock_agent_model_with_id,
):
    agent = BedrockAgent(bedrock_agent_model_with_id, bedrock_client=client)

    with (
        patch.object(agent.bedrock_client, "associate_agent_knowledge_base") as mock_associate_knowledge_base,
        patch.object(
            BedrockAgent, "prepare_agent_and_wait_until_prepared"
        ) as mock_prepare_agent_and_wait_until_prepared,
    ):
        await agent.associate_agent_knowledge_base("test_knowledge_base_id")

        mock_associate_knowledge_base.assert_called_once_with(
            agentId=agent.agent_model.agent_id,
            agentVersion=agent.agent_model.agent_version,
            knowledgeBaseId="test_knowledge_base_id",
        )
        mock_prepare_agent_and_wait_until_prepared.assert_called_once()


# Test case to verify the disassociation of an agent with a knowledge base
@patch.object(boto3, "client", return_value=Mock())
async def test_disassociate_agent_knowledge_base(
    client,
    bedrock_agent_unit_test_env,
    bedrock_agent_model_with_id,
):
    agent = BedrockAgent(bedrock_agent_model_with_id, bedrock_client=client)

    with (
        patch.object(agent.bedrock_client, "disassociate_agent_knowledge_base") as mock_disassociate_knowledge_base,
        patch.object(
            BedrockAgent, "prepare_agent_and_wait_until_prepared"
        ) as mock_prepare_agent_and_wait_until_prepared,
    ):
        await agent.disassociate_agent_knowledge_base("test_knowledge_base_id")
        mock_disassociate_knowledge_base.assert_called_once_with(
            agentId=agent.agent_model.agent_id,
            agentVersion=agent.agent_model.agent_version,
            knowledgeBaseId="test_knowledge_base_id",
        )
        mock_prepare_agent_and_wait_until_prepared.assert_called_once()


# Test case to verify listing associated knowledge bases with an agent
@patch.object(boto3, "client", return_value=Mock())
async def test_list_associated_agent_knowledge_bases(
    client,
    bedrock_agent_unit_test_env,
    bedrock_agent_model_with_id,
):
    agent = BedrockAgent(bedrock_agent_model_with_id, bedrock_client=client)

    with patch.object(agent.bedrock_client, "list_agent_knowledge_bases") as mock_list_knowledge_bases:
        await agent.list_associated_agent_knowledge_bases()

        mock_list_knowledge_bases.assert_called_once_with(
            agentId=agent.agent_model.agent_id,
            agentVersion=agent.agent_model.agent_version,
        )


# endregion

# region Agent Deletion Tests


@patch.object(boto3, "client", return_value=Mock())
async def test_delete_agent(
    client,
    bedrock_agent_unit_test_env,
    bedrock_agent_model_with_id,
):
    agent = BedrockAgent(bedrock_agent_model_with_id, bedrock_client=client)

    agent_id = bedrock_agent_model_with_id.agent_id
    with patch.object(agent.bedrock_client, "delete_agent") as mock_delete_agent:
        await agent.delete_agent()

        mock_delete_agent.assert_called_once_with(agentId=agent_id)
        assert agent.agent_model.agent_id is None


# Test case to verify error handling when deleting an agent that does not exist
@patch.object(boto3, "client", return_value=Mock())
async def test_delete_agent_twice_error(
    client,
    bedrock_agent_unit_test_env,
    bedrock_agent_model_with_id,
):
    agent = BedrockAgent(bedrock_agent_model_with_id, bedrock_client=client)

    with patch.object(agent.bedrock_client, "delete_agent"):
        await agent.delete_agent()

        with pytest.raises(ValueError):
            await agent.delete_agent()


# Test case to verify error handling when there is a client error during agent deletion
@patch.object(boto3, "client", return_value=Mock())
async def test_delete_agent_client_error(
    client,
    bedrock_agent_unit_test_env,
    bedrock_agent_model_with_id,
):
    agent = BedrockAgent(bedrock_agent_model_with_id, bedrock_client=client)

    with patch.object(agent.bedrock_client, "delete_agent") as mock_delete_agent:
        from botocore.exceptions import ClientError

        mock_delete_agent.side_effect = ClientError({"Error": {"Code": "500"}}, "delete_agent")

        with pytest.raises(ClientError):
            await agent.delete_agent()


# endregion

# region Agent Invoke Tests


# Test case to verify the `get_response` method of BedrockAgent
@pytest.mark.parametrize(
    "thread",
    [
        None,
        BedrockAgentThread(None, session_id="test_session_id"),
    ],
)
@patch.object(boto3, "client", return_value=Mock())
async def test_bedrock_agent_get_response(
    client,
    thread,
    bedrock_agent_unit_test_env,
    bedrock_agent_model_with_id,
    bedrock_agent_non_streaming_simple_response,
    simple_response,
):
    with (
        patch.object(BedrockAgent, "_invoke_agent", new_callable=AsyncMock) as mock_invoke_agent,
        patch.object(BedrockAgentThread, "create", new_callable=AsyncMock) as mock_start,
        patch(
            "semantic_kernel.agents.bedrock.bedrock_agent.BedrockAgentThread.id",
            new_callable=PropertyMock,
        ) as mock_id,
    ):
        agent = BedrockAgent(bedrock_agent_model_with_id)
        mock_id.return_value = "mock-thread-id"

        mock_invoke_agent.return_value = bedrock_agent_non_streaming_simple_response
        mock_start.return_value = "test_session_id"

        response = await agent.get_response(messages="test_input_text", thread=thread)
        assert response.message.content == simple_response

        mock_invoke_agent.assert_called_once()


# Test case to verify the `get_response` method of BedrockAgent
@patch.object(boto3, "client", return_value=Mock())
async def test_bedrock_agent_get_response_exception(
    client,
    bedrock_agent_unit_test_env,
    bedrock_agent_model_with_id,
    bedrock_agent_non_streaming_empty_response,
):
    with (
        patch.object(BedrockAgent, "_invoke_agent", new_callable=AsyncMock) as mock_invoke_agent,
        patch.object(BedrockAgentThread, "create", new_callable=AsyncMock) as mock_start,
        patch(
            "semantic_kernel.agents.bedrock.bedrock_agent.BedrockAgentThread.id",
            new_callable=PropertyMock,
        ) as mock_id,
    ):
        agent = BedrockAgent(bedrock_agent_model_with_id)
        mock_id.return_value = "mock-thread-id"

        mock_invoke_agent.return_value = bedrock_agent_non_streaming_empty_response
        mock_start.return_value = "test_session_id"

        with pytest.raises(AgentInvokeException):
            await agent.get_response(messages="test_input_text")


# Test case to verify the invocation of BedrockAgent
@pytest.mark.parametrize(
    "thread",
    [
        None,
        BedrockAgentThread(None, session_id="test_session_id"),
    ],
)
@patch.object(boto3, "client", return_value=Mock())
async def test_bedrock_agent_invoke(
    client,
    thread,
    bedrock_agent_unit_test_env,
    bedrock_agent_model_with_id,
    bedrock_agent_non_streaming_simple_response,
    simple_response,
):
    with (
        patch.object(BedrockAgent, "_invoke_agent", new_callable=AsyncMock) as mock_invoke_agent,
        patch.object(BedrockAgentThread, "create", new_callable=AsyncMock) as mock_start,
        patch.object(BedrockAgentThread, "id", "test_session_id"),
    ):
        agent = BedrockAgent(bedrock_agent_model_with_id)

        mock_invoke_agent.return_value = bedrock_agent_non_streaming_simple_response
        mock_start.return_value = "test_session_id"

        async for response in agent.invoke(messages="test_input_text", thread=thread):
            assert response.message.content == simple_response

        mock_invoke_agent.assert_called_once_with(
            "test_session_id",
            "test_input_text",
            None,
            streamingConfigurations={"streamFinalResponse": False},
            sessionState={},
        )


# Test case to verify the streaming invocation of BedrockAgent
@pytest.mark.parametrize(
    "thread",
    [
        None,
        BedrockAgentThread(None, session_id="test_session_id"),
    ],
)
@patch.object(boto3, "client", return_value=Mock())
async def test_bedrock_agent_invoke_stream(
    client,
    thread,
    bedrock_agent_unit_test_env,
    bedrock_agent_model_with_id,
    bedrock_agent_streaming_simple_response,
    simple_response,
):
    with (
        patch.object(BedrockAgent, "_invoke_agent", new_callable=AsyncMock) as mock_invoke_agent,
        patch.object(BedrockAgentThread, "create", new_callable=AsyncMock) as mock_start,
        patch.object(BedrockAgentThread, "id", "test_session_id"),
    ):
        agent = BedrockAgent(bedrock_agent_model_with_id)

        mock_invoke_agent.return_value = bedrock_agent_streaming_simple_response
        mock_start.return_value = "test_session_id"

        full_message = ""
        async for response in agent.invoke_stream(messages="test_input_text", thread=thread):
            full_message += response.message.content

        assert full_message == simple_response
        mock_invoke_agent.assert_called_once_with(
            "test_session_id",
            "test_input_text",
            None,
            streamingConfigurations={"streamFinalResponse": True},
            sessionState={},
        )


# Test case to verify the invocation of BedrockAgent with function call
@patch.object(boto3, "client", return_value=Mock())
async def test_bedrock_agent_invoke_with_function_call(
    client,
    bedrock_agent_unit_test_env,
    bedrock_agent_model_with_id,
    bedrock_agent_function_call_response,
    bedrock_agent_non_streaming_simple_response,
):
    with (
        patch.object(BedrockAgent, "_invoke_agent", new_callable=AsyncMock) as mock_invoke_agent,
        patch.object(BedrockAgent, "_handle_function_call_contents") as mock_handle_function_call_contents,
        patch.object(BedrockAgentThread, "create", new_callable=AsyncMock) as mock_start,
        patch.object(BedrockAgentThread, "id", "test_session_id"),
    ):
        agent = BedrockAgent(bedrock_agent_model_with_id)

        function_result_contents = [
            FunctionResultContent(
                id="test_id",
                name="test_function",
                result="test_result",
                metadata={"functionInvocationInput": {"actionGroup": "test_action_group"}},
            )
        ]
        mock_handle_function_call_contents.return_value = function_result_contents
        agent.function_choice_behavior.maximum_auto_invoke_attempts = 2

        mock_invoke_agent.side_effect = [
            bedrock_agent_function_call_response,
            bedrock_agent_non_streaming_simple_response,
        ]
        mock_start.return_value = "test_session_id"
        async for _ in agent.invoke(messages="test_input_text"):
            mock_invoke_agent.assert_called_with(
                "test_session_id",
                "test_input_text",
                None,
                streamingConfigurations={"streamFinalResponse": False},
                sessionState={
                    "invocationId": "test_invocation_id",
                    "returnControlInvocationResults": parse_function_result_contents(function_result_contents),
                },
            )


# Test case to verify the streaming invocation of BedrockAgent with function call
@patch.object(boto3, "client", return_value=Mock())
async def test_bedrock_agent_invoke_stream_with_function_call(
    client,
    bedrock_agent_unit_test_env,
    bedrock_agent_model_with_id,
    bedrock_agent_function_call_response,
    bedrock_agent_streaming_simple_response,
):
    with (
        patch.object(BedrockAgent, "_invoke_agent", new_callable=AsyncMock) as mock_invoke_agent,
        patch.object(BedrockAgent, "_handle_function_call_contents") as mock_handle_function_call_contents,
        patch.object(BedrockAgentThread, "create", new_callable=AsyncMock) as mock_start,
        patch.object(BedrockAgentThread, "id", "test_session_id"),
    ):
        agent = BedrockAgent(bedrock_agent_model_with_id)

        function_result_contents = [
            FunctionResultContent(
                id="test_id",
                name="test_function",
                result="test_result",
                metadata={"functionInvocationInput": {"actionGroup": "test_action_group"}},
            )
        ]
        mock_handle_function_call_contents.return_value = function_result_contents
        agent.function_choice_behavior.maximum_auto_invoke_attempts = 2

        mock_invoke_agent.side_effect = [
            bedrock_agent_function_call_response,
            bedrock_agent_streaming_simple_response,
        ]
        mock_start.return_value = "test_session_id"
        async for _ in agent.invoke_stream(messages="test_input_text"):
            mock_invoke_agent.assert_called_with(
                "test_session_id",
                "test_input_text",
                None,
                streamingConfigurations={"streamFinalResponse": True},
                sessionState={
                    "invocationId": "test_invocation_id",
                    "returnControlInvocationResults": parse_function_result_contents(function_result_contents),
                },
            )


# endregion
