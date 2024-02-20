# Copyright (c) Microsoft. All rights reserved.

import logging

from pytest import mark, raises

from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.kernel import Kernel
from semantic_kernel.template_engine.blocks.block_types import BlockTypes
from semantic_kernel.template_engine.blocks.var_block import VarBlock

logger = logging.getLogger(__name__)


def test_init():
    var_block = VarBlock(content="$test_var")
    assert var_block.content == "$test_var"
    assert var_block.name == "test_var"
    assert var_block.type == BlockTypes.VARIABLE


def test_no_prefix():
    with raises(ValueError):
        VarBlock(content="test_var")


def test_is_valid_invalid_characters():
    with raises(ValueError):
        VarBlock(content="$test-var")


def test_render():
    var_block = VarBlock(content="$test_var")
    rendered_value = var_block.render(Kernel(), KernelArguments(test_var="test_value"))
    assert rendered_value == "test_value"


def test_render_variable_not_found():
    var_block = VarBlock(content="$test_var")
    rendered_value = var_block.render(Kernel(), KernelArguments())
    assert rendered_value == ""


def test_init_only_prefix():
    with raises(ValueError):
        VarBlock(content="$")


def test_it_trims_spaces():
    assert VarBlock(content="  $x  ").content == "$x"


def test_it_ignores_spaces_around():
    target = VarBlock(content="  $var \n ")
    assert target.content == "$var"
    assert target.name == "var"


def test_render_no_args():
    target = VarBlock(content="$var")
    result = target.render(Kernel())
    assert result == ""


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
        ("-", False),
        ("a b", False),
        ("a\nb", False),
        ("a\tb", False),
        ("a\rb", False),
        ("a.b", False),
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
    ],
)
def test_it_allows_underscore_letters_and_digits(name, parses):
    if not parses:
        with raises(ValueError):
            VarBlock(content=f"${name}")
        return
    target = VarBlock(content=f" ${name} ")
    result = target.render(Kernel(), KernelArguments(**{name: "value"}))
    assert target.name == name
    assert result == "value"
