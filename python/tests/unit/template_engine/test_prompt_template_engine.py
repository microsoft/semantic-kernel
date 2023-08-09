# Copyright (c) Microsoft. All rights reserved.

from unittest.mock import AsyncMock, Mock

from pytest import fixture, mark

from semantic_kernel.memory.null_memory import NullMemory
from semantic_kernel.orchestration.context_variables import ContextVariables
from semantic_kernel.orchestration.sk_context import SKContext
from semantic_kernel.orchestration.sk_function import SKFunction
from semantic_kernel.skill_definition import sk_function
from semantic_kernel.skill_definition.read_only_skill_collection import (
    ReadOnlySkillCollection,
)
from semantic_kernel.template_engine.blocks.block_types import BlockTypes
from semantic_kernel.template_engine.prompt_template_engine import PromptTemplateEngine
from semantic_kernel.utils.null_logger import NullLogger


@fixture
def target():
    return PromptTemplateEngine()


@fixture
def variables():
    return ContextVariables("X")


@fixture
def skills():
    return Mock(spec=ReadOnlySkillCollection)


@fixture
def context(variables, skills):
    return SKContext(variables, NullMemory(), skills, NullLogger())


def test_it_renders_variables(
    target: PromptTemplateEngine, variables: ContextVariables
):
    template = (
        "{$x11} This {$a} is {$_a} a {{$x11}} test {{$x11}} "
        "template {{foo}}{{bar $a}}{{baz $_a}}{{yay $x11}}"
    )

    blocks = target.extract_blocks(template)
    updated_blocks = target.render_variables(blocks, variables)

    assert len(blocks) == 9
    assert len(updated_blocks) == 9

    assert blocks[1].content == "$x11"
    assert updated_blocks[1].content == ""
    assert blocks[1].type == BlockTypes.VARIABLE
    assert updated_blocks[1].type == BlockTypes.TEXT

    assert blocks[3].content == "$x11"
    assert updated_blocks[3].content == ""
    assert blocks[3].type == BlockTypes.VARIABLE
    assert updated_blocks[3].type == BlockTypes.TEXT

    assert blocks[5].content == "foo"
    assert updated_blocks[5].content == "foo"
    assert blocks[5].type == BlockTypes.CODE
    assert updated_blocks[5].type == BlockTypes.CODE

    assert blocks[6].content == "bar $a"
    assert updated_blocks[6].content == "bar $a"
    assert blocks[6].type == BlockTypes.CODE
    assert updated_blocks[6].type == BlockTypes.CODE

    assert blocks[7].content == "baz $_a"
    assert updated_blocks[7].content == "baz $_a"
    assert blocks[7].type == BlockTypes.CODE
    assert updated_blocks[7].type == BlockTypes.CODE

    assert blocks[8].content == "yay $x11"
    assert updated_blocks[8].content == "yay $x11"
    assert blocks[8].type == BlockTypes.CODE
    assert updated_blocks[8].type == BlockTypes.CODE

    variables.set("x11", "x11 value")
    variables.set("a", "a value")
    variables.set("_a", "_a value")

    blocks = target.extract_blocks(template)
    updated_blocks = target.render_variables(blocks, variables)

    assert len(blocks) == 9
    assert len(updated_blocks) == 9

    assert blocks[1].content == "$x11"
    assert updated_blocks[1].content == "x11 value"
    assert blocks[1].type == BlockTypes.VARIABLE
    assert updated_blocks[1].type == BlockTypes.TEXT

    assert blocks[3].content == "$x11"
    assert updated_blocks[3].content == "x11 value"
    assert blocks[3].type == BlockTypes.VARIABLE
    assert updated_blocks[3].type == BlockTypes.TEXT

    assert blocks[5].content == "foo"
    assert updated_blocks[5].content == "foo"
    assert blocks[5].type == BlockTypes.CODE
    assert updated_blocks[5].type == BlockTypes.CODE

    assert blocks[6].content == "bar $a"
    assert updated_blocks[6].content == "bar $a"
    assert blocks[6].type == BlockTypes.CODE
    assert updated_blocks[6].type == BlockTypes.CODE

    assert blocks[7].content == "baz $_a"
    assert updated_blocks[7].content == "baz $_a"
    assert blocks[7].type == BlockTypes.CODE
    assert updated_blocks[7].type == BlockTypes.CODE

    assert blocks[8].content == "yay $x11"
    assert updated_blocks[8].content == "yay $x11"
    assert blocks[8].type == BlockTypes.CODE
    assert updated_blocks[8].type == BlockTypes.CODE


@mark.asyncio
async def test_it_renders_code_using_input_async(
    target: PromptTemplateEngine,
    variables: ContextVariables,
    context_factory,
):
    @sk_function(name="function")
    def my_function_async(cx: SKContext) -> str:
        return f"F({cx.variables.input})"

    func = SKFunction.from_native_method(my_function_async)
    assert func is not None

    variables.update("INPUT-BAR")
    template = "foo-{{function}}-baz"
    result = await target.render_async(template, context_factory(variables, func))

    assert result == "foo-F(INPUT-BAR)-baz"


@mark.asyncio
async def test_it_renders_code_using_variables_async(
    target: PromptTemplateEngine,
    variables: ContextVariables,
    context_factory,
):
    @sk_function(name="function")
    def my_function_async(cx: SKContext) -> str:
        return f"F({cx.variables.input})"

    func = SKFunction.from_native_method(my_function_async)
    assert func is not None

    variables.set("myVar", "BAR")
    template = "foo-{{function $myVar}}-baz"
    result = await target.render_async(template, context_factory(variables, func))

    assert result == "foo-F(BAR)-baz"


@mark.asyncio
async def test_it_renders_async_code_using_variables_async(
    target: PromptTemplateEngine,
    variables: ContextVariables,
    context_factory,
):
    @sk_function(name="function")
    async def my_function_async(cx: SKContext) -> str:
        return cx.variables.input

    func = SKFunction.from_native_method(my_function_async)
    assert func is not None

    variables.set("myVar", "BAR")

    template = "foo-{{function $myVar}}-baz"

    result = await target.render_async(template, context_factory(variables, func))

    assert result == "foo-BAR-baz"
