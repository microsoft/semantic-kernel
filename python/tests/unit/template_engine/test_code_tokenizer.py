# Copyright (c) Microsoft. All rights reserved.

from pytest import mark, raises

from semantic_kernel.template_engine.blocks.block_errors import CodeBlockSyntaxError
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
        ("'foo'", "'foo'"),
        ("'foo' ", "'foo'"),
        (" 'foo'", "'foo'"),
        (' "bar" ', '"bar"'),
    ],
)
def test_it_parses_val_blocks(template, content):
    blocks = CodeTokenizer.tokenize(template)

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
    blocks = CodeTokenizer.tokenize(template)

    assert len(blocks) == 1
    assert blocks[0].content == content
    assert blocks[0].type == BlockTypes.FUNCTION_ID


def test_it_parses_function_calls():
    template1 = "x.y $foo"
    template2 = "xy $foo"
    template3 = "xy '$value'"

    blocks1 = CodeTokenizer.tokenize(template1)
    blocks2 = CodeTokenizer.tokenize(template2)
    blocks3 = CodeTokenizer.tokenize(template3)

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
    template = "func 'f\\'oo'"
    blocks = CodeTokenizer.tokenize(template)

    assert len(blocks) == 2
    assert blocks[0].content == "func"
    assert blocks[1].content == "'f'oo'"


def test_it_throws_when_separators_are_missing():
    template1 = "call 'f\\\\'xy'"
    template2 = "call 'f\\\\'x"

    with raises(CodeBlockSyntaxError):
        CodeTokenizer.tokenize(template1)

    with raises(CodeBlockSyntaxError):
        CodeTokenizer.tokenize(template2)


def test_named_args():
    template = 'plugin.function "direct" arg1=$arg1 arg2="arg2"'
    blocks = CodeTokenizer.tokenize(template)
    assert len(blocks) == 4
    assert blocks[0].content == "plugin.function"
    assert blocks[1].content == '"direct"'
    assert blocks[2].content == "arg1=$arg1"
    assert blocks[3].content == 'arg2="arg2"'
