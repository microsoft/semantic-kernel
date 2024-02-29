from unittest.mock import patch

import pytest

from semantic_kernel.connectors.ai.open_ai.services.open_ai_chat_completion import OpenAIChatCompletion
from semantic_kernel.connectors.ai.open_ai.services.open_ai_text_completion import OpenAITextCompletion
from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.streaming_chat_message_content import StreamingChatMessageContent
from semantic_kernel.contents.text_content import TextContent
from semantic_kernel.exceptions import FunctionInitializationError
from semantic_kernel.functions.kernel_function_from_prompt import KernelFunctionFromPrompt
from semantic_kernel.kernel import Kernel
from semantic_kernel.prompt_template.input_variable import InputVariable
from semantic_kernel.prompt_template.kernel_prompt_template import KernelPromptTemplate
from semantic_kernel.prompt_template.prompt_template_config import PromptTemplateConfig


def test_init_minimal_prompt():
    function = KernelFunctionFromPrompt(
        function_name="test",
        plugin_name="test",
        prompt="test",
    )

    assert function.name == "test"
    assert function.plugin_name == "test"
    assert function.description is None
    assert function.prompt_template.prompt_template_config.template == "test"


def test_init_minimal_prompt_template():
    function = KernelFunctionFromPrompt(
        function_name="test",
        plugin_name="test",
        prompt_template=KernelPromptTemplate(prompt_template_config=PromptTemplateConfig(template="test")),
    )

    assert function.name == "test"
    assert function.plugin_name == "test"
    assert function.description is None
    assert function.prompt_template.prompt_template_config.template == "test"


def test_init_minimal_prompt_template_config():
    function = KernelFunctionFromPrompt(
        function_name="test", plugin_name="test", prompt_template_config=PromptTemplateConfig(template="test")
    )

    assert function.name == "test"
    assert function.plugin_name == "test"
    assert function.description is None
    assert function.prompt_template.prompt_template_config.template == "test"


def test_init_no_prompt():
    with pytest.raises(FunctionInitializationError):
        KernelFunctionFromPrompt(
            function_name="test",
            plugin_name="test",
        )


def test_init_invalid_name():
    with pytest.raises(FunctionInitializationError):
        KernelFunctionFromPrompt(function_name="test func", plugin_name="test", prompt="test")


def test_init_prompt_execution_settings_none():
    function = KernelFunctionFromPrompt(
        function_name="test",
        plugin_name="test",
        prompt="test",
        prompt_execution_settings=None,
    )

    assert function.name == "test"
    assert function.plugin_name == "test"
    assert function.description is None
    assert function.prompt_template.prompt_template_config.template == "test"


def test_init_prompt_execution_settings_none_with_prompt_template():
    function = KernelFunctionFromPrompt(
        function_name="test",
        plugin_name="test",
        prompt_template=KernelPromptTemplate(
            prompt_template_config=PromptTemplateConfig(template="test", execution_settings={})
        ),
        prompt_execution_settings=None,
    )

    assert function.name == "test"
    assert function.plugin_name == "test"
    assert function.description is None
    assert function.prompt_template.prompt_template_config.template == "test"


def test_init_prompt_execution_settings():
    function = KernelFunctionFromPrompt(
        function_name="test",
        plugin_name="test",
        prompt="test",
        prompt_execution_settings=PromptExecutionSettings(service_id="test"),
    )

    assert function.name == "test"
    assert function.plugin_name == "test"
    assert function.description is None
    assert function.prompt_template.prompt_template_config.template == "test"


def test_init_prompt_execution_settings_list():
    function = KernelFunctionFromPrompt(
        function_name="test",
        plugin_name="test",
        prompt="test",
        prompt_execution_settings=[PromptExecutionSettings(service_id="test")],
    )

    assert function.name == "test"
    assert function.plugin_name == "test"
    assert function.description is None
    assert function.prompt_template.prompt_template_config.template == "test"


def test_init_prompt_execution_settings_dict():
    function = KernelFunctionFromPrompt(
        function_name="test",
        plugin_name="test",
        prompt="test",
        prompt_execution_settings={"test": PromptExecutionSettings(service_id="test")},
    )

    assert function.name == "test"
    assert function.plugin_name == "test"
    assert function.description is None
    assert function.prompt_template.prompt_template_config.template == "test"


@pytest.mark.asyncio
async def test_invoke():
    kernel = Kernel()
    kernel.add_service(OpenAIChatCompletion(service_id="test", ai_model_id="test", api_key="test"))
    function = KernelFunctionFromPrompt(
        function_name="test",
        plugin_name="test",
        prompt="test",
        prompt_execution_settings=PromptExecutionSettings(service_id="test"),
    )
    with patch(
        "semantic_kernel.connectors.ai.open_ai.services.open_ai_chat_completion.OpenAIChatCompletion.complete_chat"
    ) as mock:
        mock.return_value = [ChatMessageContent(role="assistant", content="test", metadata={})]
        result = await function.invoke(kernel=kernel)
        assert str(result) == "test"

    with patch(
        "semantic_kernel.connectors.ai.open_ai.services.open_ai_chat_completion.OpenAIChatCompletion.complete_chat_stream"
    ) as mock:
        mock.__iter__.return_value = [
            StreamingChatMessageContent(choice_index=0, role="assistant", content="test", metadata={})
        ]
        async for result in function.invoke_stream(kernel=kernel):
            assert str(result) == "test"


@pytest.mark.asyncio
async def test_invoke_exception():
    kernel = Kernel()
    kernel.add_service(OpenAIChatCompletion(service_id="test", ai_model_id="test", api_key="test"))
    function = KernelFunctionFromPrompt(
        function_name="test",
        plugin_name="test",
        prompt="test",
        prompt_execution_settings=PromptExecutionSettings(service_id="test"),
    )
    with patch(
        "semantic_kernel.connectors.ai.open_ai.services.open_ai_chat_completion.OpenAIChatCompletion.complete_chat",
        side_effect=Exception,
    ) as mock:
        mock.return_value = [ChatMessageContent(role="assistant", content="test", metadata={})]
        result = await function.invoke(kernel=kernel)
        assert isinstance(result.metadata["error"], Exception)

    with patch(
        "semantic_kernel.connectors.ai.open_ai.services.open_ai_chat_completion.OpenAIChatCompletion.complete_chat_stream",
        side_effect=Exception,
    ) as mock:
        mock.__iter__.return_value = [
            StreamingChatMessageContent(choice_index=0, role="assistant", content="test", metadata={})
        ]
        async for result in function.invoke_stream(kernel=kernel):
            assert isinstance(result.metadata["error"], Exception)


@pytest.mark.asyncio
async def test_invoke_text():
    kernel = Kernel()
    kernel.add_service(OpenAITextCompletion(service_id="test", ai_model_id="test", api_key="test"))
    function = KernelFunctionFromPrompt(
        function_name="test",
        plugin_name="test",
        prompt="test",
        prompt_execution_settings=PromptExecutionSettings(service_id="test"),
    )
    with patch(
        "semantic_kernel.connectors.ai.open_ai.services.open_ai_text_completion.OpenAITextCompletion.complete",
    ) as mock:
        mock.return_value = [TextContent(text="test", metadata={})]
        result = await function.invoke(kernel=kernel)
        assert str(result) == "test"

    with patch(
        "semantic_kernel.connectors.ai.open_ai.services.open_ai_text_completion.OpenAITextCompletion.complete_stream",
    ) as mock:
        mock.__iter__.return_value = [TextContent(text="test", metadata={})]
        async for result in function.invoke_stream(kernel=kernel):
            assert str(result) == "test"


@pytest.mark.asyncio
async def test_invoke_exception_text():
    kernel = Kernel()
    kernel.add_service(OpenAITextCompletion(service_id="test", ai_model_id="test", api_key="test"))
    function = KernelFunctionFromPrompt(
        function_name="test",
        plugin_name="test",
        prompt="test",
        prompt_execution_settings=PromptExecutionSettings(service_id="test"),
    )
    with patch(
        "semantic_kernel.connectors.ai.open_ai.services.open_ai_text_completion.OpenAITextCompletion.complete",
        side_effect=Exception,
    ) as mock:
        mock.return_value = [TextContent(text="test", metadata={})]
        result = await function.invoke(kernel=kernel)
        assert isinstance(result.metadata["error"], Exception)

    with patch(
        "semantic_kernel.connectors.ai.open_ai.services.open_ai_text_completion.OpenAITextCompletion.complete_stream",
        side_effect=Exception,
    ) as mock:
        mock.__iter__.return_value = []
        async for result in function.invoke_stream(kernel=kernel):
            assert isinstance(result.metadata["error"], Exception)


@pytest.mark.asyncio
async def test_invoke_defaults():
    kernel = Kernel()
    kernel.add_service(OpenAIChatCompletion(service_id="test", ai_model_id="test", api_key="test"))
    function = KernelFunctionFromPrompt(
        function_name="test",
        plugin_name="test",
        prompt_template_config=PromptTemplateConfig(
            template="{{$input}}",
            input_variables=[InputVariable(name="input", type="str", default="test", is_required=False)],
        ),
        prompt_execution_settings=PromptExecutionSettings(service_id="test"),
    )
    with patch(
        "semantic_kernel.connectors.ai.open_ai.services.open_ai_chat_completion.OpenAIChatCompletion.complete_chat"
    ) as mock:
        mock.return_value = [ChatMessageContent(role="assistant", content="test", metadata={})]
        result = await function.invoke(kernel=kernel)
        assert str(result) == "test"


def test_create_with_multiple_settings():
    function = KernelFunctionFromPrompt(
        function_name="test",
        plugin_name="test",
        prompt_template_config=PromptTemplateConfig(
            template="test",
            execution_settings=[
                PromptExecutionSettings(service_id="test", temperature=0.0),
                PromptExecutionSettings(service_id="test2", temperature=1.0),
            ],
        ),
    )
    assert (
        function.prompt_template.prompt_template_config.execution_settings["test"].extension_data["temperature"] == 0.0
    )
    assert (
        function.prompt_template.prompt_template_config.execution_settings["test2"].extension_data["temperature"] == 1.0
    )
