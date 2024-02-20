# Copyright (c) Microsoft. All rights reserved.

from unittest.mock import Mock

from pytest import fixture, mark

from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.functions.kernel_function import KernelFunction
from semantic_kernel.functions.kernel_function_decorator import kernel_function
from semantic_kernel.functions.kernel_plugin_collection import (
    KernelPluginCollection,
)
from semantic_kernel.kernel import Kernel
from semantic_kernel.template_engine.blocks.block_types import BlockTypes
from semantic_kernel.template_engine.prompt_template_engine import PromptTemplateEngine


@fixture
def target():
    return PromptTemplateEngine()


@fixture
def plugins():
    return Mock(spec=KernelPluginCollection)


def test_extract_from_empty(target: PromptTemplateEngine):
    blocks = target.extract_blocks(None)
    assert len(blocks) == 0

    blocks = target.extract_blocks("")
    assert len(blocks) == 0


def test_it_renders_variables(target: PromptTemplateEngine, plugins):
    kernel = Kernel(plugins=plugins)
    arguments = KernelArguments()

    template = (
        "{$x11} This {$a} is {$_a} a {{$x11}} test {{$x11}} "
        "template {{foo}}{{bar $a}}{{baz $_a arg1=$arg}}{{yay $x11}}"
    )

    blocks = target.extract_blocks(template)
    updated_blocks = target.render_variables(blocks, kernel, arguments)

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

    assert blocks[7].content == "baz $_a arg1=$arg"
    assert updated_blocks[7].content == "baz $_a arg1=$arg"
    assert blocks[7].type == BlockTypes.CODE
    assert updated_blocks[7].type == BlockTypes.CODE

    assert blocks[8].content == "yay $x11"
    assert updated_blocks[8].content == "yay $x11"
    assert blocks[8].type == BlockTypes.CODE
    assert updated_blocks[8].type == BlockTypes.CODE

    arguments = KernelArguments(x11="x11 value", a="a value", _a="_a value")

    blocks = target.extract_blocks(template)
    updated_blocks = target.render_variables(blocks, kernel, arguments)

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

    assert blocks[7].content == "baz $_a arg1=$arg"
    assert updated_blocks[7].content == "baz $_a arg1=$arg"
    assert blocks[7].type == BlockTypes.CODE
    assert updated_blocks[7].type == BlockTypes.CODE

    assert blocks[8].content == "yay $x11"
    assert updated_blocks[8].content == "yay $x11"
    assert blocks[8].type == BlockTypes.CODE
    assert updated_blocks[8].type == BlockTypes.CODE


@mark.asyncio
async def test_it_renders_code(target: PromptTemplateEngine):
    kernel = Kernel()
    arguments = KernelArguments()

    @kernel_function(name="function")
    def my_function(arguments: KernelArguments) -> str:
        return f"F({arguments.get('_a')}-{arguments.get('arg1')})"

    func = KernelFunction.from_native_method(my_function, "test")
    assert func is not None
    kernel.plugins.add_plugin_from_functions("test", [func])

    arguments["_a"] = "foo"
    arguments["arg"] = "bar"
    template = "template {{'val'}}{{test.function $_a arg1=$arg}}"

    blocks = target.extract_blocks(template)
    result = await target.render_code(blocks, kernel, arguments)
    assert result[0] == blocks[0]
    assert result[1] == blocks[1]
    assert result[2].type == BlockTypes.TEXT
    assert result[2].content == "F(foo-bar)"


@mark.asyncio
async def test_it_renders_code_using_input(target: PromptTemplateEngine):
    kernel = Kernel()
    arguments = KernelArguments()

    @kernel_function(name="function")
    def my_function(arguments: KernelArguments) -> str:
        return f"F({arguments.get('input')})"

    func = KernelFunction.from_native_method(my_function, "test")
    assert func is not None
    kernel.plugins.add_plugin_from_functions("test", [func])

    arguments["input"] = "INPUT-BAR"
    template = "foo-{{test.function}}-baz"
    result = await target.render(template, kernel, arguments)

    assert result == "foo-F(INPUT-BAR)-baz"


@mark.asyncio
async def test_it_renders_code_using_variables(
    target: PromptTemplateEngine,
):
    kernel = Kernel()
    arguments = KernelArguments()

    @kernel_function(name="function")
    def my_function(myVar: str) -> str:
        return f"F({myVar})"

    func = KernelFunction.from_native_method(my_function, "test")
    assert func is not None
    kernel.plugins.add_plugin_from_functions("test", [func])

    arguments["myVar"] = "BAR"
    template = "foo-{{test.function $myVar}}-baz"
    result = await target.render(template, kernel, arguments)

    assert result == "foo-F(BAR)-baz"


@mark.asyncio
async def test_it_renders_code_using_variables_async(
    target: PromptTemplateEngine,
):
    kernel = Kernel()
    arguments = KernelArguments()

    @kernel_function(name="function")
    async def my_function(myVar: str) -> str:
        return myVar

    func = KernelFunction.from_native_method(my_function, "test")
    assert func is not None
    kernel.plugins.add_plugin_from_functions("test", [func])

    arguments["myVar"] = "BAR"

    template = "foo-{{test.function $myVar}}-baz"

    result = await target.render(template, kernel, arguments)

    assert result == "foo-BAR-baz"
