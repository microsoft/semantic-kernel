# Copyright (c) Microsoft. All rights reserved.


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
    assert (
        rendered.strip()
        == """<message role="user">User message</message><message role="assistant">Assistant message</message>"""
    )
    chat_history2 = ChatHistory.from_rendered_prompt(rendered)
    assert chat_history2 == chat_history
