# Copyright (c) Microsoft. All rights reserved.


from semantic_kernel.contents import AuthorRole
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.functions import kernel_function
from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.kernel import Kernel
from semantic_kernel.prompt_template.jinja2_prompt_template import Jinja2PromptTemplate
from semantic_kernel.prompt_template.prompt_template_config import PromptTemplateConfig


def create_jinja2_prompt_template(template: str) -> Jinja2PromptTemplate:
    return Jinja2PromptTemplate(
        prompt_template_config=PromptTemplateConfig(
            name="test", description="test", template=template, template_format="jinja2"
        ),
        allow_dangerously_set_content=True,
    )


class MyPlugin:
    @kernel_function()
    def check123(self, input: str) -> str:
        print("check123 func called")
        return "123 ok" if input == "123" else f"{input} != 123"

    @kernel_function()
    def asis(self, input: str | None = None) -> str:
        return input or ""


async def test_it_supports_variables(kernel: Kernel):
    # Arrange
    input = "template tests"
    winner = "SK"
    template = "And the winner\n of {{input}} \nis: {{  winner }}!"

    arguments = KernelArguments(input=input, winner=winner)
    # Act
    result = await create_jinja2_prompt_template(template).render(kernel, arguments)
    # Assert
    expected = template.replace("{{input}}", input).replace("{{  winner }}", winner)
    assert expected == result


async def test_it_allows_to_pass_variables_to_functions(kernel: Kernel):
    # Arrange
    template = "== {{ my_check123() }} =="
    kernel.add_plugin(MyPlugin(), "my")

    arguments = KernelArguments(input="123")
    # Act
    result = await create_jinja2_prompt_template(template).render(kernel, arguments)

    # Assert
    assert result == "== 123 ok =="


async def test_it_allows_to_pass_values_to_functions(kernel: Kernel):
    # Arrange
    template = "== {{ my_check123(input=234) }} =="
    kernel.add_plugin(MyPlugin(), "my")

    # Act
    result = await create_jinja2_prompt_template(template).render(kernel, None)

    # Assert
    assert result == "== 234 != 123 =="


async def test_it_allows_to_pass_escaped_values1_to_functions(kernel: Kernel):
    # Arrange
    template = """== {{ my_check123(input="a'b") }} =="""
    kernel.add_plugin(MyPlugin(), "my")
    # Act
    result = await create_jinja2_prompt_template(template).render(kernel, None)

    # Assert
    assert result == "== a'b != 123 =="


async def test_it_allows_to_pass_escaped_values2_to_functions(kernel: Kernel):
    # Arrange
    template = '== {{my_check123(input="a\\"b")}} =='
    kernel.add_plugin(MyPlugin(), "my")

    # Act
    result = await create_jinja2_prompt_template(template).render(kernel, None)

    # Assert
    assert result == '== a"b != 123 =='


async def test_chat_history_round_trip(kernel: Kernel):
    template = """{% for item in chat_history %}{{ message(item) }}{% endfor %}"""
    target = create_jinja2_prompt_template(template)
    chat_history = ChatHistory()
    chat_history.add_user_message("User message")
    chat_history.add_assistant_message("Assistant message")
    rendered = await target.render(kernel, KernelArguments(chat_history=chat_history))
    expected = (
        '<message role="user"><text>User message</text></message>'
        '<message role="assistant"><text>Assistant message</text></message>'
    )
    assert rendered.strip() == expected
    chat_history2 = ChatHistory.from_rendered_prompt(rendered)
    assert chat_history2 == chat_history


async def test_from_rendered_prompt_backward_compat_old_format(kernel: Kernel):
    """from_rendered_prompt handles the old format without <text> wrapper for backward compatibility."""
    old_format = '<message role="user">User message</message><message role="assistant">Assistant message</message>'
    parsed = ChatHistory.from_rendered_prompt(old_format)
    assert len(parsed) == 2
    assert parsed[0].role == AuthorRole.USER
    assert parsed[0].content == "User message"
    assert parsed[1].role == AuthorRole.ASSISTANT
    assert parsed[1].content == "Assistant message"


async def test_chat_history_round_trip_with_xml_metacharacters(kernel: Kernel):
    template = """{% for item in chat_history %}{{ message(item) }}{% endfor %}"""
    target = create_jinja2_prompt_template(template)
    chat_history = ChatHistory()
    chat_history.add_user_message("What does a < b mean in Python?")
    chat_history.add_assistant_message('Use "&" carefully in XML and HTML.')

    rendered = await target.render(kernel, KernelArguments(chat_history=chat_history))

    assert "&lt;" in rendered
    assert "&amp;" in rendered
    assert '"&amp;"' in rendered
    assert ChatHistory.from_rendered_prompt(rendered) == chat_history


async def test_message_helper_preserves_system_role_with_xml_metacharacters(kernel: Kernel):
    template = """{{system_message}}{% for item in chat_history %}{{ message(item) }}{% endfor %}"""
    target = create_jinja2_prompt_template(template)
    system_message = "You are a helpful assistant."
    chat_history = ChatHistory()
    chat_history.add_user_message("What does a < b mean in Python?")

    rendered = await target.render(
        kernel,
        KernelArguments(system_message=system_message, chat_history=chat_history),
    )

    parsed = ChatHistory.from_rendered_prompt(rendered)
    assert parsed.messages[0].role == AuthorRole.SYSTEM
    assert parsed.messages[0].content == system_message
    assert parsed.messages[1].role == AuthorRole.USER

    assert parsed.messages[1].content == "What does a < b mean in Python?"


def test_from_rendered_prompt_backward_compat_old_format():
    """from_rendered_prompt must handle the old format without <text> wrapper."""
    old_format = '<message role="user">User message</message><message role="assistant">Assistant message</message>'
    parsed = ChatHistory.from_rendered_prompt(old_format)
    assert len(parsed.messages) == 2
    assert parsed.messages[0].role == AuthorRole.USER
    assert parsed.messages[0].content == "User message"
    assert parsed.messages[1].role == AuthorRole.ASSISTANT
    assert parsed.messages[1].content == "Assistant message"


def test_from_rendered_prompt_new_text_element_format():
    """from_rendered_prompt must handle the new format with <text> wrapper."""
    new_format = (
        '<message role="user"><text>User message</text></message>'
        '<message role="assistant"><text>Assistant message</text></message>'
    )
    parsed = ChatHistory.from_rendered_prompt(new_format)
    assert len(parsed.messages) == 2
    assert parsed.messages[0].role == AuthorRole.USER
    assert parsed.messages[0].content == "User message"
    assert parsed.messages[1].role == AuthorRole.ASSISTANT
    assert parsed.messages[1].content == "Assistant message"
