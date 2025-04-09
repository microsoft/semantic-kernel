# Copyright (c) Microsoft. All rights reserved.


from semantic_kernel import Kernel
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.functions import kernel_function
from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.prompt_template.handlebars_prompt_template import HandlebarsPromptTemplate
from semantic_kernel.prompt_template.prompt_template_config import PromptTemplateConfig


def create_handlebars_prompt_template(template: str) -> HandlebarsPromptTemplate:
    return HandlebarsPromptTemplate(
        prompt_template_config=PromptTemplateConfig(
            name="test", description="test", template=template, template_format="handlebars"
        ),
        allow_dangerously_set_content=True,
    )


class MyPlugin:
    @kernel_function()
    def check123(self, input: str) -> str:
        return "123 ok" if input == "123" else f"{input} != 123"

    @kernel_function()
    def asis(self, input: str | None = None) -> str:
        return input or ""


class TestHandlebarsPromptTemplateEngine:
    async def test_it_supports_variables(self, kernel: Kernel):
        # Arrange
        input = "template tests"
        winner = "SK"
        template = "And the winner\n of {{input}} \nis: {{  winner }}!"

        arguments = KernelArguments(input=input, winner=winner)
        # Act
        result = await create_handlebars_prompt_template(template).render(kernel, arguments)
        # Assert
        expected = template.replace("{{input}}", input).replace("{{  winner }}", winner)
        assert expected == result

    async def test_it_allows_to_pass_variables_to_functions(self, kernel: Kernel):
        # Arrange
        template = "== {{my-check123 input=call}} =="
        kernel.add_plugin(MyPlugin(), "my")

        arguments = KernelArguments(call="123")
        # Act
        result = await create_handlebars_prompt_template(template).render(kernel, arguments)

        # Assert
        assert result == "== 123 ok =="

    async def test_it_allows_to_pass_values_to_functions(self, kernel: Kernel):
        # Arrange
        template = "== {{my-check123 input=234}} =="
        kernel.add_plugin(MyPlugin(), "my")

        # Act
        result = await create_handlebars_prompt_template(template).render(kernel, None)

        # Assert
        assert result == "== 234 != 123 =="

    async def test_it_allows_to_pass_escaped_values1_to_functions(self, kernel: Kernel):
        # Arrange
        template = "== {{my-check123 input='a\\'b'}} =="
        kernel.add_plugin(MyPlugin(), "my")
        # Act
        result = await create_handlebars_prompt_template(template).render(kernel, None)

        # Assert
        assert result == "== a'b != 123 =="

    async def test_it_allows_to_pass_escaped_values2_to_functions(self, kernel: Kernel):
        # Arrange
        template = '== {{my-check123 input="a\\"b"}} =='
        kernel.add_plugin(MyPlugin(), "my")

        # Act
        result = await create_handlebars_prompt_template(template).render(kernel, None)

        # Assert
        assert result == '== a"b != 123 =='

    async def test_chat_history_round_trip(self, kernel: Kernel):
        # Arrange
        template = """{{#each chat_history}}{{#message role=role}}{{~content~}}{{/message}} {{/each}}"""
        target = create_handlebars_prompt_template(template)
        chat_history = ChatHistory()
        chat_history.add_user_message("User message")
        chat_history.add_assistant_message("Assistant message")
        rendered = await target.render(kernel, KernelArguments(chat_history=chat_history))
        assert (
            rendered.strip()
            == """<message role="user">User message</message> <message role="assistant">Assistant message</message>"""
        )
        chat_history2 = ChatHistory.from_rendered_prompt(rendered)
        assert chat_history2 == chat_history
