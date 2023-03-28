# Copyright (c) Microsoft. All rights reserved.

from logging import Logger

from pytest import mark, raises

from semantic_kernel.orchestration.context_variables import ContextVariables
from semantic_kernel.template_engine.blocks.block_types import BlockTypes
from semantic_kernel.template_engine.blocks.symbols import Symbols
from semantic_kernel.template_engine.blocks.var_block import VarBlock


def test_init():
    var_block = VarBlock(content="$test_var", log=Logger("test_logger"))
    assert var_block.content == "$test_var"
    assert isinstance(var_block.log, Logger)


def test_type_property():
    var_block = VarBlock(content="$test_var")
    assert var_block.type == BlockTypes.VARIABLE


def test_is_valid():
    var_block = VarBlock(content="$test_var")
    is_valid, error_msg = var_block.is_valid()
    assert is_valid
    assert error_msg == ""


def test_is_valid_no_prefix():
    var_block = VarBlock(content="test_var")
    is_valid, error_msg = var_block.is_valid()
    assert not is_valid
    assert error_msg == f"A variable must start with the symbol {Symbols.VAR_PREFIX}"


def test_is_valid_invalid_characters():
    var_block = VarBlock(content="$test-var")
    is_valid, error_msg = var_block.is_valid()
    assert not is_valid
    assert (
        error_msg == "The variable name 'test-var' contains invalid characters. "
        "Only alphanumeric chars and underscore are allowed."
    )


def test_render():
    var_block = VarBlock(content="$test_var")
    context_variables = ContextVariables()
    context_variables.set("test_var", "test_value")
    rendered_value = var_block.render(context_variables)
    assert rendered_value == "test_value"


def test_render_variable_not_found():
    var_block = VarBlock(content="$test_var")
    context_variables = ContextVariables()
    rendered_value = var_block.render(context_variables)
    assert rendered_value == ""


def test_init_empty():
    block = VarBlock(content="$")

    assert block.name == ""


def test_it_trims_spaces():
    assert VarBlock(content="  $x  ").content == "$x"


def test_it_ignores_spaces_around():
    target = VarBlock(content="  $var \n ")
    assert target.content == "$var"


def test_it_renders_to_empty_string_without_variables():
    target = VarBlock(content="  $var \n ")
    result = target.render(None)
    assert result == ""


def test_it_renders_to_empty_string_if_variable_is_missing():
    target = VarBlock(content="  $var \n ")
    variables = ContextVariables(variables={"foo": "bar"})
    result = target.render(variables)
    assert result == ""


def test_it_renders_to_variable_value_when_available():
    target = VarBlock(content="  $var \n ")
    variables = ContextVariables(variables={"foo": "bar", "var": "able"})
    result = target.render(variables)
    assert result == "able"


def test_it_throws_if_the_var_name_is_empty():
    variables = ContextVariables(variables={"foo": "bar", "var": "able"})

    with raises(ValueError):
        target = VarBlock(content=" $ ")
        target.render(variables)


@mark.parametrize(
    "name, is_valid",
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
def test_it_allows_underscore_letters_and_digits(name, is_valid):
    target = VarBlock(content=f" ${name} ")
    variables = ContextVariables(variables={name: "value"})
    result = target.render(variables)

    assert target.is_valid()[0] == is_valid
    if is_valid:
        assert target.name == name
        assert result == "value"
