# Copyright (c) Microsoft. All rights reserved.


from pytest import mark, raises

from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.kernel import Kernel
from semantic_kernel.template_engine.blocks.block_types import BlockTypes
from semantic_kernel.template_engine.blocks.function_id_block import FunctionIdBlock


def test_init():
    function_id_block = FunctionIdBlock(content="plugin.function")
    assert function_id_block.content == "plugin.function"
    assert function_id_block.type == BlockTypes.FUNCTION_ID


def test_init_without_content():
    function_id_block = FunctionIdBlock(content="", plugin_name="plugin", function_name="function")
    assert function_id_block.content == ""
    assert function_id_block.plugin_name == "plugin"
    assert function_id_block.function_name == "function"


def test_render():
    kernel = Kernel()
    function_id_block = FunctionIdBlock(content="plugin.function")
    rendered_value = function_id_block.render(kernel, KernelArguments())
    assert rendered_value == "plugin.function"


def test_empty_identifier_value_error():
    with raises(ValueError):
        FunctionIdBlock(content="")


def test_init_value_error():
    with raises(ValueError):
        FunctionIdBlock(content="plugin.nope.function")


def test_it_trims_spaces():
    assert FunctionIdBlock(content="  aa  ").content == "aa"


@mark.parametrize(
    "name, parses",
    [
        ("0", True),
        ("1", True),
        ("a", True),
        ("_", True),
        ("01", True),
        ("01a", True),
        ("a01", True),
        ("_0", True),
        ("a01_", True),
        ("_a01", True),
        (".", False),
        (".a", False),
        ("a.", False),
        ("a.b", True),
        ("-", False),
        ("a b", False),
        ("a\nb", False),
        ("a\tb", False),
        ("a\rb", False),
        ("a,b", False),
        ("a-b", False),
        ("a+b", False),
        ("a~b", False),
        ("a`b", False),
        ("a!b", False),
        ("a@b", False),
        ("a#b", False),
        ("a$b", False),
        ("a%b", False),
        ("a^b", False),
        ("a*b", False),
        ("a(b", False),
        ("a)b", False),
        ("a|b", False),
        ("a{b", False),
        ("a}b", False),
        ("a[b", False),
        ("a]b", False),
        ("a:b", False),
        ("a;b", False),
        ("a'b", False),
        ('a"b', False),
        ("a<b", False),
        ("a>b", False),
        ("a/b", False),
        ("a\\b", False),
        ("a.b.c", False),
    ],
)
def test_it_allows_underscore_dots_letters_and_digits(name, parses):
    if parses:
        FunctionIdBlock(content=f" {name} ")
    else:
        with raises(ValueError):
            FunctionIdBlock(content=f" {name} ")
