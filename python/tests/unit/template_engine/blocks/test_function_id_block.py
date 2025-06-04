# Copyright (c) Microsoft. All rights reserved.


from pytest import mark, raises

from semantic_kernel.exceptions import FunctionIdBlockSyntaxError
from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.kernel import Kernel
from semantic_kernel.template_engine.blocks.block_types import BlockTypes
from semantic_kernel.template_engine.blocks.function_id_block import FunctionIdBlock


def test_init():
    function_id_block = FunctionIdBlock(content="plugin.function")
    assert function_id_block.content == "plugin.function"
    assert function_id_block.plugin_name == "plugin"
    assert function_id_block.function_name == "function"
    assert function_id_block.type == BlockTypes.FUNCTION_ID


def test_init_function_only():
    function_id_block = FunctionIdBlock(content="function")
    assert function_id_block.content == "function"
    assert not function_id_block.plugin_name
    assert function_id_block.function_name == "function"
    assert function_id_block.type == BlockTypes.FUNCTION_ID


def test_it_trims_spaces():
    assert FunctionIdBlock(content="  aa  ").content == "aa"


@mark.parametrize(
    "name",
    [
        "0",
        "1",
        "a",
        "_",
        "01",
        "01a",
        "a01",
        "_0",
        "a01_",
        "_a01",
    ],
)
def test_valid_syntax(name):
    target = FunctionIdBlock(content=name)
    assert target.content == name


@mark.parametrize(
    "content",
    ["", "plugin.nope.function", "func-tion", "plu-in.function", ".function"],
    ids=["empty", "three_parts", "invalid_function", "invalid_plugin", "no_plugin"],
)
def test_syntax_error(content):
    with raises(FunctionIdBlockSyntaxError, match=rf".*{content}.*"):
        FunctionIdBlock(content=content)


def test_render():
    kernel = Kernel()
    function_id_block = FunctionIdBlock(content="plugin.function")
    rendered_value = function_id_block.render(kernel, KernelArguments())
    assert rendered_value == "plugin.function"


def test_render_function_only():
    kernel = Kernel()
    function_id_block = FunctionIdBlock(content="function")
    rendered_value = function_id_block.render(kernel, KernelArguments())
    assert rendered_value == "function"
