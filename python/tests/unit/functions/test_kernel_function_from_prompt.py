# Copyright (c) Microsoft. All rights reserved.

import os
from unittest.mock import patch

import pytest

from semantic_kernel.connectors.ai.open_ai.services.open_ai_chat_completion import OpenAIChatCompletion
from semantic_kernel.connectors.ai.open_ai.services.open_ai_text_completion import OpenAITextCompletion
from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
from semantic_kernel.const import METADATA_EXCEPTION_KEY
from semantic_kernel.contents import AuthorRole
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.streaming_chat_message_content import StreamingChatMessageContent
from semantic_kernel.contents.text_content import TextContent
from semantic_kernel.exceptions import FunctionInitializationError
from semantic_kernel.filters.functions.function_invocation_context import FunctionInvocationContext
from semantic_kernel.filters.kernel_filters_extension import _rebuild_function_invocation_context
from semantic_kernel.filters.prompts.prompt_render_context import PromptRenderContext
from semantic_kernel.functions.kernel_arguments import KernelArguments
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


async def test_invoke_chat_stream(openai_unit_test_env):
    kernel = Kernel()
    kernel.add_service(OpenAIChatCompletion(service_id="test", ai_model_id="test"))
    function = KernelFunctionFromPrompt(
        function_name="test",
        plugin_name="test",
        prompt="test",
        prompt_execution_settings=PromptExecutionSettings(service_id="test"),
    )

    # This part remains unchanged - for synchronous mocking example
    with patch(
        "semantic_kernel.connectors.ai.open_ai.services.open_ai_chat_completion.OpenAIChatCompletion.get_chat_message_contents"
    ) as mock:
        mock.return_value = [ChatMessageContent(role=AuthorRole.ASSISTANT, content="test", metadata={})]
        result = await function.invoke(kernel=kernel)
        assert str(result) == "test"

    with patch(
        "semantic_kernel.connectors.ai.open_ai.services.open_ai_chat_completion.OpenAIChatCompletion.get_streaming_chat_message_contents"
    ) as mock:
        mock.return_value = [
            StreamingChatMessageContent(choice_index=0, role=AuthorRole.ASSISTANT, content="test", metadata={})
        ]
        async for result in function.invoke_stream(kernel=kernel):
            assert str(result) == "test"


async def test_invoke_exception(openai_unit_test_env):
    kernel = Kernel()
    kernel.add_service(OpenAIChatCompletion(service_id="test", ai_model_id="test"))
    function = KernelFunctionFromPrompt(
        function_name="test",
        plugin_name="test",
        prompt="test",
        prompt_execution_settings=PromptExecutionSettings(service_id="test"),
    )
    with patch(
        "semantic_kernel.connectors.ai.open_ai.services.open_ai_chat_completion.OpenAIChatCompletion.get_chat_message_contents",
        side_effect=Exception,
    ) as mock:
        mock.return_value = [ChatMessageContent(role=AuthorRole.ASSISTANT, content="test", metadata={})]
        with pytest.raises(Exception, match="test"):
            await function.invoke(kernel=kernel)

    with patch(
        "semantic_kernel.connectors.ai.open_ai.services.open_ai_chat_completion.OpenAIChatCompletion.get_streaming_chat_message_contents",
        side_effect=Exception,
    ) as mock:
        mock.return_value = [
            StreamingChatMessageContent(choice_index=0, role=AuthorRole.ASSISTANT, content="test", metadata={})
        ]
        with pytest.raises(Exception):
            async for result in function.invoke_stream(kernel=kernel):
                assert isinstance(result.metadata[METADATA_EXCEPTION_KEY], Exception)


async def test_invoke_text(openai_unit_test_env):
    kernel = Kernel()
    kernel.add_service(OpenAITextCompletion(service_id="test", ai_model_id="test"))
    function = KernelFunctionFromPrompt(
        function_name="test",
        plugin_name="test",
        prompt="test",
        prompt_execution_settings=PromptExecutionSettings(service_id="test"),
    )
    with patch(
        "semantic_kernel.connectors.ai.open_ai.services.open_ai_text_completion.OpenAITextCompletion.get_text_contents",
    ) as mock:
        mock.return_value = [TextContent(text="test", metadata={})]
        result = await function.invoke(kernel=kernel)
        assert str(result) == "test"

    with patch(
        "semantic_kernel.connectors.ai.open_ai.services.open_ai_text_completion.OpenAITextCompletion.get_streaming_text_contents",
    ) as mock:
        mock.return_value = [TextContent(text="test", metadata={})]
        async for result in function.invoke_stream(kernel=kernel):
            assert str(result) == "test"


async def test_invoke_exception_text(openai_unit_test_env):
    kernel = Kernel()
    kernel.add_service(OpenAITextCompletion(service_id="test", ai_model_id="test"))
    function = KernelFunctionFromPrompt(
        function_name="test",
        plugin_name="test",
        prompt="test",
        prompt_execution_settings=PromptExecutionSettings(service_id="test"),
    )
    with patch(
        "semantic_kernel.connectors.ai.open_ai.services.open_ai_text_completion.OpenAITextCompletion.get_text_contents",
        side_effect=Exception,
    ) as mock:
        mock.return_value = [TextContent(text="test", metadata={})]
        with pytest.raises(Exception, match="test"):
            await function.invoke(kernel=kernel)

    with patch(
        "semantic_kernel.connectors.ai.open_ai.services.open_ai_text_completion.OpenAITextCompletion.get_streaming_text_contents",
        side_effect=Exception,
    ) as mock:
        mock.return_value = []
        with pytest.raises(Exception):
            async for result in function.invoke_stream(kernel=kernel):
                assert isinstance(result.metadata[METADATA_EXCEPTION_KEY], Exception)


async def test_invoke_defaults(openai_unit_test_env):
    kernel = Kernel()
    kernel.add_service(OpenAIChatCompletion(service_id="test", ai_model_id="test"))
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
        "semantic_kernel.connectors.ai.open_ai.services.open_ai_chat_completion.OpenAIChatCompletion.get_chat_message_contents"
    ) as mock:
        mock.return_value = [ChatMessageContent(role=AuthorRole.ASSISTANT, content="test", metadata={})]
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


async def test_create_with_multiple_settings_one_service_registered(openai_unit_test_env):
    kernel = Kernel()
    kernel.add_service(OpenAIChatCompletion(service_id="test2", ai_model_id="test"))
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
    with patch(
        "semantic_kernel.connectors.ai.open_ai.services.open_ai_chat_completion.OpenAIChatCompletion.get_chat_message_contents"
    ) as mock:
        mock.return_value = [ChatMessageContent(role=AuthorRole.ASSISTANT, content="test", metadata={})]
        result = await function.invoke(kernel=kernel)
        assert str(result) == "test"


def test_from_yaml_fail():
    with pytest.raises(FunctionInitializationError):
        KernelFunctionFromPrompt.from_yaml("template_format: something_else")


def test_from_directory_prompt_only():
    with pytest.raises(FunctionInitializationError):
        KernelFunctionFromPrompt.from_directory(
            path=os.path.join(
                os.path.dirname(__file__),
                "../../assets",
                "test_plugins",
                "TestPlugin",
                "TestFunctionPromptOnly",
            ),
            plugin_name="test",
        )


def test_from_directory_config_only():
    with pytest.raises(FunctionInitializationError):
        KernelFunctionFromPrompt.from_directory(
            path=os.path.join(
                os.path.dirname(__file__),
                "../../assets",
                "test_plugins",
                "TestPlugin",
                "TestFunctionConfigOnly",
            ),
            plugin_name="test",
        )


async def test_prompt_render(kernel: Kernel, openai_unit_test_env):
    kernel.add_service(OpenAIChatCompletion(service_id="default", ai_model_id="test"))
    function = KernelFunctionFromPrompt(
        function_name="test",
        plugin_name="test",
        prompt="test",
        template_format="semantic-kernel",
    )
    _rebuild_function_invocation_context()
    context = FunctionInvocationContext(function=function, kernel=kernel, arguments=KernelArguments())
    prompt_render_result = await function._render_prompt(context)
    assert prompt_render_result.rendered_prompt == "test"


async def test_prompt_render_with_filter(kernel: Kernel, openai_unit_test_env):
    kernel.add_service(OpenAIChatCompletion(service_id="default", ai_model_id="test"))

    @kernel.filter("prompt_rendering")
    async def prompt_rendering_filter(context: PromptRenderContext, next):
        await next(context)
        context.rendered_prompt = f"preface {context.rendered_prompt or ''}"

    function = KernelFunctionFromPrompt(
        function_name="test",
        plugin_name="test",
        prompt="test",
        template_format="semantic-kernel",
    )
    _rebuild_function_invocation_context()
    context = FunctionInvocationContext(function=function, kernel=kernel, arguments=KernelArguments())
    prompt_render_result = await function._render_prompt(context)
    assert prompt_render_result.rendered_prompt == "preface test"


@pytest.mark.parametrize(
    ("mode"),
    [
        ("python"),
        ("json"),
    ],
)
def test_function_model_dump(mode: str):
    function = KernelFunctionFromPrompt(
        function_name="test",
        plugin_name="test",
        prompt="test",
        template_format="semantic-kernel",
        prompt_template_config=PromptTemplateConfig(
            template="test",
            input_variables=[InputVariable(name="input", type="str", default="test", is_required=False)],
        ),
    )
    model_dump = function.model_dump(mode=mode)
    assert isinstance(model_dump, dict)
    assert "metadata" in model_dump
    assert len(model_dump["metadata"]["parameters"]) == 1


def test_function_model_dump_json():
    function = KernelFunctionFromPrompt(
        function_name="test",
        plugin_name="test",
        prompt="test",
        template_format="semantic-kernel",
    )
    model_dump_json = function.model_dump_json()
    assert isinstance(model_dump_json, str)
    assert "test" in model_dump_json
