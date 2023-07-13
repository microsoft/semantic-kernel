# Copyright (c) Microsoft. All rights reserved.

import os
from typing import List, Tuple

from pytest import mark, raises

from semantic_kernel import Kernel
from semantic_kernel.skill_definition import sk_function
from semantic_kernel.template_engine.prompt_template_engine import PromptTemplateEngine


def _get_template_language_tests() -> List[Tuple[str, str]]:
    path = __file__
    path = os.path.dirname(path)

    with open(os.path.join(path, "tests.txt"), "r") as file:
        content = file.readlines()

    key = ""
    test_data = []
    for raw_line in content:
        value = raw_line.strip()
        if not value or value.startswith("#"):
            continue

        if not key:
            key = raw_line
        else:
            test_data.append((key, raw_line))
            key = ""

    return test_data


class MySkill:
    @sk_function()
    def check123(self, input: str) -> str:
        return "123 ok" if input == "123" else f"{input} != 123"

    @sk_function()
    def asis(self, input: str) -> str:
        return input


class TestPromptTemplateEngine:
    def setup_method(self):
        self.target = PromptTemplateEngine()

    @mark.asyncio
    async def test_it_supports_variables_async(self):
        # Arrange
        input = "template tests"
        winner = "SK"
        template = "And the winner\n of {{$input}} \nis: {{  $winner }}!"

        kernel = Kernel()
        context = kernel.create_new_context()
        context["input"] = input
        context["winner"] = winner

        # Act
        result = await self.target.render_async(template, context)

        # Assert
        expected = template.replace("{{$input}}", input).replace(
            "{{  $winner }}", winner
        )
        assert expected == result

    @mark.asyncio
    async def test_it_supports_values_async(self):
        # Arrange
        template = "And the winner\n of {{'template\ntests'}} \nis: {{  \"SK\" }}!"
        expected = "And the winner\n of template\ntests \nis: SK!"

        kernel = Kernel()
        context = kernel.create_new_context()

        # Act
        result = await self.target.render_async(template, context)

        # Assert
        assert expected == result

    @mark.asyncio
    async def test_it_allows_to_pass_variables_to_functions_async(self):
        # Arrange
        template = "== {{my.check123 $call}} =="
        kernel = Kernel()
        kernel.import_skill(MySkill(), "my")
        context = kernel.create_new_context()
        context["call"] = "123"

        # Act
        result = await self.target.render_async(template, context)

        # Assert
        assert "== 123 ok ==" == result

    @mark.asyncio
    async def test_it_allows_to_pass_values_to_functions_async(self):
        # Arrange
        template = "== {{my.check123 '234'}} =="
        kernel = Kernel()
        kernel.import_skill(MySkill(), "my")
        context = kernel.create_new_context()

        # Act
        result = await self.target.render_async(template, context)

        # Assert
        assert "== 234 != 123 ==" == result

    @mark.asyncio
    async def test_it_allows_to_pass_escaped_values1_to_functions_async(self):
        # Arrange
        template = "== {{my.check123 'a\\'b'}} =="
        kernel = Kernel()
        kernel.import_skill(MySkill(), "my")
        context = kernel.create_new_context()

        # Act
        result = await self.target.render_async(template, context)

        # Assert
        assert "== a'b != 123 ==" == result

    @mark.asyncio
    async def test_it_allows_to_pass_escaped_values2_to_functions_async(self):
        # Arrange
        template = '== {{my.check123 "a\\"b"}} =='
        kernel = Kernel()
        kernel.import_skill(MySkill(), "my")
        context = kernel.create_new_context()

        # Act
        result = await self.target.render_async(template, context)

        # Assert
        assert '== a"b != 123 ==' == result

    @mark.asyncio
    @mark.parametrize(
        "template,expected_result", [(t, r) for t, r in _get_template_language_tests()]
    )
    async def test_it_handle_edge_cases_async(
        self, template: str, expected_result: str
    ):
        # Arrange
        kernel = Kernel()
        kernel.import_skill(MySkill())
        context = kernel.create_new_context()

        # Act
        if expected_result.startswith("ERROR"):
            with raises(ValueError):
                await self.target.render_async(template, context)
        else:
            result = await self.target.render_async(template, context)

            # Assert
            assert expected_result == result
