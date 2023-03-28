# Copyright (c) Microsoft. All rights reserved.

from pytest import mark, raises

from semantic_kernel.template_engine.blocks.block_types import BlockTypes
from semantic_kernel.template_engine.code_tokenizer import CodeTokenizer


def test_it_parses_empty_text():
    target = CodeTokenizer()

    assert not target.tokenize(None)
    assert not target.tokenize("")
    assert not target.tokenize(" ")
    assert not target.tokenize(" \n ")


@mark.parametrize(
    "template, content",
    [
        ("$", "$"),
        (" $ ", "$"),
        ("$foo", "$foo"),
        ("$foo ", "$foo"),
        (" $foo", "$foo"),
        (" $bar ", "$bar"),
    ],
)
def test_it_parses_var_blocks(template, content):
    target = CodeTokenizer()
    blocks = target.tokenize(template)

    assert len(blocks) == 1
    assert blocks[0].content == content
    assert blocks[0].type == BlockTypes.VARIABLE


@mark.parametrize(
    "template, content",
    [
        ("'", "'"),
        (' " ', '"'),
        ("'foo'", "'foo'"),
        ("'foo' ", "'foo'"),
        (" 'foo'", "'foo'"),
        (' "bar" ', '"bar"'),
    ],
)
def test_it_parses_val_blocks(template, content):
    target = CodeTokenizer()
    blocks = target.tokenize(template)

    assert len(blocks) == 1
    assert blocks[0].content == content
    assert blocks[0].type == BlockTypes.VALUE


@mark.parametrize(
    "template, content",
    [
        ("f", "f"),
        (" x ", "x"),
        ("foo", "foo"),
        ("fo.o ", "fo.o"),
        (" f.oo", "f.oo"),
        (" bar ", "bar"),
    ],
)
def test_it_parses_function_id_blocks(template, content):
    target = CodeTokenizer()
    blocks = target.tokenize(template)

    assert len(blocks) == 1
    assert blocks[0].content == content
    assert blocks[0].type == BlockTypes.FUNCTION_ID


def test_it_parses_function_calls():
    target = CodeTokenizer()

    template1 = "x.y $foo"
    template2 = "xy $foo"
    template3 = "xy '$value'"

    blocks1 = target.tokenize(template1)
    blocks2 = target.tokenize(template2)
    blocks3 = target.tokenize(template3)

    assert len(blocks1) == 2
    assert len(blocks2) == 2
    assert len(blocks3) == 2

    assert blocks1[0].content == "x.y"
    assert blocks2[0].content == "xy"
    assert blocks3[0].content == "xy"

    assert blocks1[0].type == BlockTypes.FUNCTION_ID
    assert blocks2[0].type == BlockTypes.FUNCTION_ID
    assert blocks3[0].type == BlockTypes.FUNCTION_ID

    assert blocks1[1].content == "$foo"
    assert blocks2[1].content == "$foo"
    assert blocks3[1].content == "'$value'"

    assert blocks1[1].type == BlockTypes.VARIABLE
    assert blocks2[1].type == BlockTypes.VARIABLE
    assert blocks3[1].type == BlockTypes.VALUE


def test_it_supports_escaping():
    target = CodeTokenizer()

    template = "func 'f\\'oo'"
    blocks = target.tokenize(template)

    assert len(blocks) == 2
    assert blocks[0].content == "func"
    assert blocks[1].content == "'f'oo'"


def test_it_throws_when_separators_are_missing():
    target = CodeTokenizer()

    template1 = "call 'f\\\\'xy'"
    template2 = "call 'f\\\\'x"

    with raises(ValueError):
        target.tokenize(template1)

    with raises(ValueError):
        target.tokenize(template2)
