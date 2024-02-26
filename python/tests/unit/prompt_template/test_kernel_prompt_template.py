from unittest.mock import Mock

from pytest import fixture, mark

from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.functions.kernel_function import KernelFunction
from semantic_kernel.functions.kernel_function_decorator import kernel_function
from semantic_kernel.functions.kernel_plugin_collection import (
    KernelPluginCollection,
)
from semantic_kernel.kernel import Kernel
from semantic_kernel.prompt_template.input_variable import InputVariable
from semantic_kernel.prompt_template.kernel_prompt_template import KernelPromptTemplate
from semantic_kernel.prompt_template.prompt_template_config import PromptTemplateConfig
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
    )
    assert template._blocks == [VarBlock(content="$input", name="input")]
    assert len(template._blocks) == 1


def test_input_variables():
    config = PromptTemplateConfig(name="test", description="test", template="{{plug.func input=$input}}")
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
    arguments = KernelArguments()

    @kernel_function(name="function")
    def my_function(arguments: KernelArguments) -> str:
        return f"F({arguments.get('input')})"

    func = KernelFunction.from_native_method(my_function, "test")
    assert func is not None
    kernel.plugins.add_plugin_from_functions("test", [func])

    arguments["input"] = "INPUT-BAR"
    template = "foo-{{test.function}}-baz"
    target = create_kernel_prompt_template(template)
    result = await target.render(kernel, arguments)

    assert result == "foo-F(INPUT-BAR)-baz"


@mark.asyncio
async def test_it_renders_code_using_variables():
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
    target = create_kernel_prompt_template(template)
    result = await target.render(kernel, arguments)

    assert result == "foo-F(BAR)-baz"


@mark.asyncio
async def test_it_renders_code_using_variables_async():
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

    target = create_kernel_prompt_template(template)
    result = await target.render(kernel, arguments)

    assert result == "foo-BAR-baz"
