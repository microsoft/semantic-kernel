<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
# Copyright (c) Microsoft. All rights reserved.

import pytest

from semantic_kernel.exceptions.template_engine_exceptions import (
    TemplateRenderException,
)
from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.functions.kernel_function import KernelFunction
from semantic_kernel.functions.kernel_function_decorator import kernel_function
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
=======
from unittest.mock import Mock

from pytest import fixture, mark

from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.functions.kernel_function import KernelFunction
from semantic_kernel.functions.kernel_function_decorator import kernel_function
from semantic_kernel.functions.kernel_plugin_collection import (
    KernelPluginCollection,
)
>>>>>>> f40c1f2075e2443c31c57c34f5f66c2711a8db75
>>>>>>> main
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
from semantic_kernel.kernel import Kernel
from semantic_kernel.prompt_template.input_variable import InputVariable
from semantic_kernel.prompt_template.kernel_prompt_template import KernelPromptTemplate
from semantic_kernel.prompt_template.prompt_template_config import PromptTemplateConfig
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
from semantic_kernel.template_engine.blocks.var_block import VarBlock


def create_kernel_prompt_template(
    template: str, allow_dangerously_set_content: bool = False
) -> KernelPromptTemplate:
    return KernelPromptTemplate(
        prompt_template_config=PromptTemplateConfig(
            name="test",
            description="test",
            template=template,
            allow_dangerously_set_content=allow_dangerously_set_content,
        )
    )


def test_init():
    template = KernelPromptTemplate(
        prompt_template_config=PromptTemplateConfig(
            name="test", description="test", template="{{$input}}"
        )
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
=======
from semantic_kernel.template_engine.blocks.block_types import BlockTypes
from semantic_kernel.template_engine.blocks.var_block import VarBlock


def create_kernel_prompt_template(template: str) -> KernelPromptTemplate:
    return KernelPromptTemplate(
        prompt_template_config=PromptTemplateConfig(name="test", description="test", template=template)
    )


@fixture
def plugins():
    return Mock(spec=KernelPluginCollection)


def test_init():
    template = KernelPromptTemplate(
        prompt_template_config=PromptTemplateConfig(name="test", description="test", template="{{$input}}")
>>>>>>> f40c1f2075e2443c31c57c34f5f66c2711a8db75
>>>>>>> main
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
    )
    assert template._blocks == [VarBlock(content="$input", name="input")]
    assert len(template._blocks) == 1


<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
def test_init_validate_template_format_fail():
    with pytest.raises(ValueError):
        KernelPromptTemplate(
            prompt_template_config=PromptTemplateConfig(
                name="test",
                description="test",
                template="{{$input}}",
                template_format="handlebars",
            )
        )


def test_input_variables():
    config = PromptTemplateConfig(
        name="test", description="test", template="{{plug.func input=$input}}"
    )
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
=======
def test_input_variables():
    config = PromptTemplateConfig(name="test", description="test", template="{{plug.func input=$input}}")
>>>>>>> f40c1f2075e2443c31c57c34f5f66c2711a8db75
>>>>>>> main
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
    assert config.input_variables == []
    KernelPromptTemplate(prompt_template_config=config)
    assert config.input_variables[0] == InputVariable(name="input")


def test_config_without_prompt():
    config = PromptTemplateConfig(name="test", description="test")
    template = KernelPromptTemplate(prompt_template_config=config)
    assert template._blocks == []


def test_extract_from_empty():
    blocks = create_kernel_prompt_template(None)._blocks
    assert len(blocks) == 0

    blocks = create_kernel_prompt_template("")._blocks
    assert len(blocks) == 0


<<<<<<< Updated upstream
<<<<<<< Updated upstream
@pytest.mark.asyncio
async def test_it_renders_code_using_input(kernel: Kernel):
=======
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
@pytest.mark.asyncio
async def test_it_renders_code_using_input(kernel: Kernel):
=======
<<<<<<< HEAD
@pytest.mark.asyncio
async def test_it_renders_code_using_input(kernel: Kernel):
=======
def test_it_renders_variables(plugins):
    kernel = Kernel(plugins=plugins)
    arguments = KernelArguments()

    template = (
        "{$x11} This {$a} is {$_a} a {{$x11}} test {{$x11}} "
        "template {{foo}}{{bar $a}}{{baz $_a arg1=$arg}}{{yay $x11}}"
    )

    target = create_kernel_prompt_template(template)
    blocks = target._blocks
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

    target = create_kernel_prompt_template(template)
    blocks = target._blocks
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
async def test_it_renders_code():
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

    target = create_kernel_prompt_template(template)
    blocks = target._blocks
    result = await target.render_code(blocks, kernel, arguments)
    assert result[0] == blocks[0]
    assert result[1] == blocks[1]
    assert result[2].type == BlockTypes.TEXT
    assert result[2].content == "F(foo-bar)"


@mark.asyncio
async def test_it_renders_code_using_input():
    kernel = Kernel()
>>>>>>> f40c1f2075e2443c31c57c34f5f66c2711a8db75
>>>>>>> main
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
    arguments = KernelArguments()

    @kernel_function(name="function")
    def my_function(arguments: KernelArguments) -> str:
        return f"F({arguments.get('input')})"

<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
    func = KernelFunction.from_method(my_function, "test")
    assert func is not None
    kernel.add_function("test", func)

    arguments["input"] = "INPUT-BAR"
    template = "foo-{{test.function}}-baz"
    target = create_kernel_prompt_template(template, allow_dangerously_set_content=True)
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
=======
    func = KernelFunction.from_native_method(my_function, "test")
    assert func is not None
    kernel.plugins.add_plugin_from_functions("test", [func])

    arguments["input"] = "INPUT-BAR"
    template = "foo-{{test.function}}-baz"
    target = create_kernel_prompt_template(template)
>>>>>>> f40c1f2075e2443c31c57c34f5f66c2711a8db75
>>>>>>> main
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
    result = await target.render(kernel, arguments)

    assert result == "foo-F(INPUT-BAR)-baz"


<<<<<<< Updated upstream
<<<<<<< Updated upstream
@pytest.mark.asyncio
async def test_it_renders_code_using_variables(kernel: Kernel):
=======
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
@pytest.mark.asyncio
async def test_it_renders_code_using_variables(kernel: Kernel):
=======
<<<<<<< HEAD
@pytest.mark.asyncio
async def test_it_renders_code_using_variables(kernel: Kernel):
=======
@mark.asyncio
async def test_it_renders_code_using_variables():
    kernel = Kernel()
>>>>>>> f40c1f2075e2443c31c57c34f5f66c2711a8db75
>>>>>>> main
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
    arguments = KernelArguments()

    @kernel_function(name="function")
    def my_function(myVar: str) -> str:
        return f"F({myVar})"

<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
    func = KernelFunction.from_method(my_function, "test")
    assert func is not None
    kernel.add_function("test", func)

    arguments["myVar"] = "BAR"
    template = "foo-{{test.function $myVar}}-baz"
    target = create_kernel_prompt_template(template, allow_dangerously_set_content=True)
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
=======
    func = KernelFunction.from_native_method(my_function, "test")
    assert func is not None
    kernel.plugins.add_plugin_from_functions("test", [func])

    arguments["myVar"] = "BAR"
    template = "foo-{{test.function $myVar}}-baz"
    target = create_kernel_prompt_template(template)
>>>>>>> f40c1f2075e2443c31c57c34f5f66c2711a8db75
>>>>>>> main
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
    result = await target.render(kernel, arguments)

    assert result == "foo-F(BAR)-baz"


<<<<<<< Updated upstream
<<<<<<< Updated upstream
@pytest.mark.asyncio
async def test_it_renders_code_using_variables_async(kernel: Kernel):
=======
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
@pytest.mark.asyncio
async def test_it_renders_code_using_variables_async(kernel: Kernel):
=======
<<<<<<< HEAD
@pytest.mark.asyncio
async def test_it_renders_code_using_variables_async(kernel: Kernel):
=======
@mark.asyncio
async def test_it_renders_code_using_variables_async():
    kernel = Kernel()
>>>>>>> f40c1f2075e2443c31c57c34f5f66c2711a8db75
>>>>>>> main
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
    arguments = KernelArguments()

    @kernel_function(name="function")
    async def my_function(myVar: str) -> str:
        return myVar

<<<<<<< Updated upstream
<<<<<<< Updated upstream
    func = KernelFunction.from_method(my_function, "test")
    assert func is not None
    kernel.add_function("test", func)
=======
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
    func = KernelFunction.from_method(my_function, "test")
    assert func is not None
    kernel.add_function("test", func)
=======
<<<<<<< HEAD
    func = KernelFunction.from_method(my_function, "test")
    assert func is not None
    kernel.add_function("test", func)
=======
    func = KernelFunction.from_native_method(my_function, "test")
    assert func is not None
    kernel.plugins.add_plugin_from_functions("test", [func])
>>>>>>> f40c1f2075e2443c31c57c34f5f66c2711a8db75
>>>>>>> main
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes

    arguments["myVar"] = "BAR"

    template = "foo-{{test.function $myVar}}-baz"

<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
    target = create_kernel_prompt_template(template, allow_dangerously_set_content=True)
    result = await target.render(kernel, arguments)

    assert result == "foo-BAR-baz"


@pytest.mark.asyncio
async def test_it_renders_code_error(kernel: Kernel):
    arguments = KernelArguments()

    @kernel_function(name="function")
    def my_function(arguments: KernelArguments) -> str:
        raise ValueError("Error")

    func = KernelFunction.from_method(my_function, "test")
    assert func is not None
    kernel.add_function("test", func)

    arguments["input"] = "INPUT-BAR"
    template = "foo-{{test.function}}-baz"
    target = create_kernel_prompt_template(template, allow_dangerously_set_content=True)
    with pytest.raises(TemplateRenderException):
        await target.render(kernel, arguments)
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
=======
    target = create_kernel_prompt_template(template)
    result = await target.render(kernel, arguments)

    assert result == "foo-BAR-baz"
>>>>>>> f40c1f2075e2443c31c57c34f5f66c2711a8db75
>>>>>>> main
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
