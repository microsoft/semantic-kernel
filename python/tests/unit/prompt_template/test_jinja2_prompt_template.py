# Copyright (c) Microsoft. All rights reserved.

import pytest
from pytest import mark

from semantic_kernel.connectors.ai.open_ai.contents.function_call import FunctionCall
from semantic_kernel.connectors.ai.open_ai.contents.open_ai_chat_message_content import OpenAIChatMessageContent
from semantic_kernel.connectors.ai.open_ai.contents.tool_calls import ToolCall
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.exceptions.template_engine_exceptions import Jinja2TemplateRenderException
from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.kernel import Kernel
from semantic_kernel.prompt_template.jinja2_prompt_template import Jinja2PromptTemplate
from semantic_kernel.prompt_template.prompt_template_config import PromptTemplateConfig


def create_jinja2_prompt_template(template: str) -> Jinja2PromptTemplate:
    return Jinja2PromptTemplate(
        prompt_template_config=PromptTemplateConfig(
            name="test", description="test", template=template, template_format="jinja2"
        )
    )


def test_init():
    template = Jinja2PromptTemplate(
        prompt_template_config=PromptTemplateConfig(
            name="test", description="test", template="{{ input }}", template_format="jinja2"
        )
    )
    assert template.prompt_template_config.template == "{{ input }}"


def test_init_template_validation_fail():
    with pytest.raises(ValueError):
        Jinja2PromptTemplate(
            prompt_template_config=PromptTemplateConfig(
                name="test", description="test", template="{{ input }}", template_format="semantic-kernel"
            )
        )


def test_config_without_prompt():
    config = PromptTemplateConfig(name="test", description="test", template_format="jinja2")
    template = Jinja2PromptTemplate(prompt_template_config=config)
    assert template._env is None


@pytest.mark.asyncio
async def test_render_without_prompt(kernel: Kernel):
    config = PromptTemplateConfig(name="test", description="test", template_format="jinja2")
    template = Jinja2PromptTemplate(prompt_template_config=config)
    rendered = await template.render(kernel, None)
    assert rendered == ""


@pytest.mark.asyncio
async def test_it_renders_variables(kernel: Kernel):
    template = "Foo {% if bar %}{{ bar }}{% else %}No Bar{% endif %}"
    target = create_jinja2_prompt_template(template)

    rendered = await target.render(kernel, KernelArguments(bar="Bar"))
    assert rendered == "Foo Bar"

    rendered = await target.render(kernel, KernelArguments())
    assert rendered == "Foo No Bar"


@pytest.mark.asyncio
async def test_it_renders_nested_variables(kernel: Kernel):
    template = "{{ foo.bar }}"
    target = create_jinja2_prompt_template(template)

    rendered = await target.render(kernel, KernelArguments(foo={"bar": "Foo Bar"}))
    assert rendered == "Foo Bar"


@pytest.mark.asyncio
async def test_it_renders_with_comments(kernel: Kernel):
    template = "{# This comment will not show up in the output #}{{ bar }}"
    target = create_jinja2_prompt_template(template)

    rendered = await target.render(kernel, KernelArguments(bar="Bar"))
    assert rendered == "Bar"


@pytest.mark.asyncio
async def test_it_renders_fail(kernel: Kernel):
    template = "{{ plug-func 'test1'}}"
    target = create_jinja2_prompt_template(template)
    with pytest.raises(Jinja2TemplateRenderException):
        await target.render(kernel, KernelArguments())


@pytest.mark.asyncio
async def test_it_renders_list(kernel: Kernel):
    template = "List: {% for item in items %}{{ item }}{% endfor %}"
    target = create_jinja2_prompt_template(template)

    rendered = await target.render(kernel, KernelArguments(items=["item1", "item2", "item3"]))
    assert rendered == "List: item1item2item3"


@pytest.mark.asyncio
async def test_it_renders_kernel_functions_arg_from_template(kernel: Kernel, decorated_native_function):
    kernel.register_function_from_method(plugin_name="plug", method=decorated_native_function)
    template = "Function: {{ plug_getLightStatus(arg1='test') }}"
    target = create_jinja2_prompt_template(template)

    rendered = await target.render(kernel, KernelArguments())
    assert rendered == "Function: test"


@pytest.mark.asyncio
async def test_it_renders_kernel_functions_arg_from_arguments(kernel: Kernel, decorated_native_function):
    kernel.register_function_from_method(plugin_name="plug", method=decorated_native_function)
    template = "Function: {{ plug_getLightStatus() }}"
    target = create_jinja2_prompt_template(template)

    rendered = await target.render(kernel, KernelArguments(arg1="test"))
    assert rendered == "Function: test"


@mark.parametrize(
    "function, input, expected",
    [
        ("array", "'test1', 'test2', 'test3'", "['test1', 'test2', 'test3']"),
        ("camel_case", "'test_string'", "TestString"),
        ("camelCase", "'test_string'", "TestString"),
        ("snake_case", "'TestString'", "test_string"),
        ("snakeCase", "'TestString'", "test_string"),
    ],
)
@mark.asyncio
async def test_helpers(function, input, expected, kernel: Kernel):
    template = f"{{{{ {function}({input}) }}}}"
    target = create_jinja2_prompt_template(template)

    rendered = await target.render(kernel, None)
    assert rendered == expected


@pytest.mark.parametrize(
    "function, input, expected",
    [
        ("==", "1, 1", "True"),
        ("==", "1, 2", "False"),
        (">", "2, 1", "True"),
        ("<", "1, 2", "True"),
        ("<=", "1, 2", "True"),
        (">=", "2, 1", "True"),
        ("!=", "1, 1", "False"),
        ("!=", "1, 2", "True"),
        ("in", "'test', 'test'", "True"),
        ("not in", "'test', 'test'", "False"),
    ],
)
@pytest.mark.asyncio
async def test_builtin_test_filters(function, input, expected, kernel: Kernel):
    input_values = input.split(", ")
    template = f"""
        {{%- if {input_values[0]} {function} {input_values[1]} -%}}
        True
        {{%- else -%}}
        False
        {{%- endif -%}}
    """
    target = create_jinja2_prompt_template(template)

    rendered = await target.render(kernel, None)
    assert rendered == expected


@pytest.mark.parametrize(
    "input, expected",
    [
        ("5", "[0, 1, 2, 3, 4]"),
        ("0, 5", "[0, 1, 2, 3, 4]"),
        ("0, 5, 1", "[0, 1, 2, 3, 4]"),
        ("0, 5, 2", "[0, 2, 4]"),
    ],
)
@mark.asyncio
async def test_range_function(input, expected, kernel: Kernel):
    template = f"{{{{ range({input}) | list }}}}"
    target = create_jinja2_prompt_template(template)

    rendered = await target.render(kernel, None)
    assert rendered == expected


@mark.asyncio
async def test_helpers_set_get(kernel: Kernel):
    template = """{% set arg = 'test' %}{{ arg }} {{ arg }}"""
    target = create_jinja2_prompt_template(template)

    rendered = await target.render(kernel, None)
    assert rendered == "test test"


@mark.asyncio
async def test_helpers_empty_get(kernel: Kernel):
    template = """{{get()}}"""
    target = create_jinja2_prompt_template(template)

    rendered = await target.render(kernel, None)
    assert rendered == ""


@mark.asyncio
async def test_helpers_set_get_from_kernel_arguments(kernel: Kernel):
    template = """{% set arg = arg1 %}{{ arg }} {{ arg }} {{ arg1 }}"""
    target = create_jinja2_prompt_template(template)

    rendered = await target.render(kernel, KernelArguments(arg1="test"))
    assert rendered == "test test test"


@mark.asyncio
async def test_helpers_array_from_args(kernel: Kernel):
    template = """{{array(arg1, arg2, arg3)}}"""
    target = create_jinja2_prompt_template(template)

    rendered = await target.render(kernel, KernelArguments(arg1="test1", arg2="test2", arg3="test3"))
    assert rendered == "['test1', 'test2', 'test3']"


@mark.asyncio
async def test_helpers_double_open_close_style_one(kernel: Kernel):
    template = "{{ '{{' }}{{ '}}' }}"
    target = create_jinja2_prompt_template(template)

    rendered = await target.render(kernel, None)
    assert rendered == "{{}}"


@mark.asyncio
async def test_helpers_double_open_close_style_two(kernel: Kernel):
    template = """{{double_open()}}{{double_close()}}"""
    target = create_jinja2_prompt_template(template)

    rendered = await target.render(kernel, None)
    assert rendered == "{{}}"


@mark.asyncio
async def test_helpers_json_style_two(kernel: Kernel):
    template = "{{input_json | tojson}}"
    target = create_jinja2_prompt_template(template)

    rendered = await target.render(kernel, KernelArguments(input_json={"key": "value"}))
    assert rendered == '{"key": "value"}'


@mark.asyncio
async def test_helpers_message(kernel: Kernel):
    template = """{% for item in chat_history %}{{ message(item) }}{% endfor %}"""
    target = create_jinja2_prompt_template(template)
    chat_history = ChatHistory()
    chat_history.add_user_message("User message")
    chat_history.add_assistant_message("Assistant message")
    rendered = await target.render(kernel, KernelArguments(chat_history=chat_history))

    assert "User message" in rendered
    assert "Assistant message" in rendered


@mark.asyncio
async def test_helpers_openai_message_tool_call(kernel: Kernel):
    template = """
    {% for chat in chat_history %}
    <message role="{{ chat.role }}" tool_calls="{{ chat.tool_calls }}" tool_call_id="{{ chat.tool_call_id }}">
        {{ chat.content }}
    </message>
    {% endfor %}
    """
    target = create_jinja2_prompt_template(template)
    chat_history = ChatHistory()
    chat_history.add_message(ChatMessageContent(role="user", content="User message"))
    chat_history.add_message(
        OpenAIChatMessageContent(
            role="assistant", tool_calls=[ToolCall(id="test", function=FunctionCall(name="plug-test"))]
        )
    )
    chat_history.add_message(OpenAIChatMessageContent(role="tool", content="Tool message", tool_call_id="test"))
    rendered = await target.render(kernel, KernelArguments(chat_history=chat_history))

    assert "User message" in rendered
    assert "ToolCall" in rendered
    assert "plug-test" in rendered
    assert "Tool message" in rendered


@mark.asyncio
async def test_helpers_message_to_prompt(kernel: Kernel):
    template = """
    {% for chat in chat_history %}
    {{ message_to_prompt(chat) }}
    {% endfor %}"""
    target = create_jinja2_prompt_template(template)
    chat_history = ChatHistory()
    chat_history.add_message(OpenAIChatMessageContent(role="user", content="User message"))
    chat_history.add_message(
        OpenAIChatMessageContent(
            role="assistant", tool_calls=[ToolCall(id="test", function=FunctionCall(name="plug-test"))]
        )
    )
    rendered = await target.render(kernel, KernelArguments(chat_history=chat_history))

    assert "User message" in rendered
    assert "tool_calls=" in rendered
    assert "plug-test" in rendered


@mark.asyncio
async def test_helpers_message_to_prompt_other(kernel: Kernel):
    # NOTE: The template contains an example of how to strip new lines and whitespaces, if needed
    template = """
    {% for item in other_list -%}
    {{- message_to_prompt(item) }}{% if not loop.last %} {% endif -%}
    {%- endfor %}
    """
    target = create_jinja2_prompt_template(template)
    other_list = ["test1", "test2"]
    rendered = await target.render(kernel, KernelArguments(other_list=other_list))
    assert rendered.strip() == """test1 test2"""


@mark.asyncio
async def test_helpers_messageToPrompt_other(kernel: Kernel):
    template = """
    {% for item in other_list -%}
    {{- messageToPrompt(item) }}{% if not loop.last %} {% endif -%}
    {%- endfor %}
    """
    target = create_jinja2_prompt_template(template)
    other_list = ["test1", "test2"]
    rendered = await target.render(kernel, KernelArguments(other_list=other_list))
    assert rendered.strip() == """test1 test2"""


@mark.asyncio
async def test_helpers_chat_history_messages(kernel: Kernel):
    template = """{{ messages(chat_history) }}"""
    target = create_jinja2_prompt_template(template)
    chat_history = ChatHistory()
    chat_history.add_user_message("User message")
    chat_history.add_assistant_message("Assistant message")
    rendered = await target.render(kernel, KernelArguments(chat_history=chat_history))
    assert (
        rendered.strip()
        == """<chat_history><message role="user">User message</message><message role="assistant">Assistant message</message></chat_history>"""  # noqa E501
    )
