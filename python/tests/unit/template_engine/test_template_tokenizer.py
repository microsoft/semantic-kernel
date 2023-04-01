# Copyright (c) Microsoft. All rights reserved.

from pytest import mark

from semantic_kernel.template_engine.blocks.block_types import BlockTypes
from semantic_kernel.template_engine.template_tokenizer import TemplateTokenizer


@mark.parametrize(
    "text, block_type",
    [
        (None, BlockTypes.TEXT),
        ("", BlockTypes.TEXT),
        (" ", BlockTypes.TEXT),
        ("   ", BlockTypes.TEXT),
        (" {}  ", BlockTypes.TEXT),
        (" {{}  ", BlockTypes.TEXT),
        (" {{ } } }  ", BlockTypes.TEXT),
        (" { { }} }", BlockTypes.TEXT),
        ("{{}}", BlockTypes.TEXT),
        ("{{ }}", BlockTypes.TEXT),
        ("{{  }}", BlockTypes.TEXT),
        ("{{  '}}x", BlockTypes.TEXT),
        ('{{  "}}x', BlockTypes.TEXT),
    ],
)
def test_it_parses_text_without_code(text, block_type):
    target = TemplateTokenizer()
    blocks = target.tokenize(text)

    assert len(blocks) == 1
    assert blocks[0].type == block_type


@mark.parametrize(
    "text, block_type",
    [
        ("", BlockTypes.TEXT),
        (" ", BlockTypes.TEXT),
        ("   ", BlockTypes.TEXT),
        (" aaa  ", BlockTypes.TEXT),
        ("{{$}}", BlockTypes.VARIABLE),
        ("{{$a}}", BlockTypes.VARIABLE),
        ("{{ $a}}", BlockTypes.VARIABLE),
        ("{{ $a }}", BlockTypes.VARIABLE),
        ("{{  $a  }}", BlockTypes.VARIABLE),
        ("{{code}}", BlockTypes.CODE),
        ("{{code }}", BlockTypes.CODE),
        ("{{ code }}", BlockTypes.CODE),
        ("{{  code }}", BlockTypes.CODE),
        ("{{  code  }}", BlockTypes.CODE),
        ("{{''}}", BlockTypes.VALUE),
        ("{{' '}}", BlockTypes.VALUE),
        ("{{ ' '}}", BlockTypes.VALUE),
        ("{{ ' ' }}", BlockTypes.VALUE),
        ("{{  ' ' }}", BlockTypes.VALUE),
        ("{{  ' '  }}", BlockTypes.VALUE),
    ],
)
def test_it_parses_basic_blocks(text, block_type):
    target = TemplateTokenizer()
    blocks = target.tokenize(text)

    assert len(blocks) == 1
    assert blocks[0].type == block_type


@mark.parametrize(
    "template, block_count",
    [
        (None, 1),
        ("", 1),
        ("}}{{a}} {{b}}x", 5),
        ("}}{{ -a}} {{b}}x", 5),
        ("}}{{ -a\n}} {{b}}x", 5),
        ("}}{{ -a\n} } {{b}}x", 3),
    ],
)
def test_it_tokenizes_the_right_token_count(template, block_count):
    target = TemplateTokenizer()
    blocks = target.tokenize(template)

    assert len(blocks) == block_count


def test_it_tokenizes_edge_cases_correctly_1():
    target = TemplateTokenizer()

    blocks1 = target.tokenize("{{{{a}}")
    blocks2 = target.tokenize("{{'{{a}}")
    blocks3 = target.tokenize("{{'a}}")
    blocks4 = target.tokenize("{{a'}}")

    assert len(blocks1) == 2
    assert len(blocks2) == 1
    assert len(blocks3) == 1
    assert len(blocks4) == 1

    assert blocks1[0].type == BlockTypes.TEXT
    assert blocks1[1].type == BlockTypes.CODE

    assert blocks1[0].content == "{{"
    assert blocks1[1].content == "a"


def test_it_tokenizes_edge_cases_correctly_2():
    target = TemplateTokenizer()

    template = "}}{{{ {$a}}}} {{b}}x}}"

    blocks = target.tokenize(template)

    assert len(blocks) == 5

    assert blocks[0].content == "}}{"
    assert blocks[0].type == BlockTypes.TEXT

    assert blocks[1].content == "{$a"
    assert blocks[1].type == BlockTypes.CODE

    assert blocks[2].content == "}} "
    assert blocks[2].type == BlockTypes.TEXT

    assert blocks[3].content == "b"
    assert blocks[3].type == BlockTypes.CODE

    assert blocks[4].content == "x}}"
    assert blocks[4].type == BlockTypes.TEXT


def test_it_tokenizes_edge_cases_correctly_3():
    target = TemplateTokenizer()

    template = "}}{{{{$a}}}} {{b}}$x}}"

    blocks = target.tokenize(template)

    assert len(blocks) == 5

    assert blocks[0].content == "}}{{"
    assert blocks[0].type == BlockTypes.TEXT

    assert blocks[1].content == "$a"
    assert blocks[1].type == BlockTypes.VARIABLE

    assert blocks[2].content == "}} "
    assert blocks[2].type == BlockTypes.TEXT

    assert blocks[3].content == "b"
    assert blocks[3].type == BlockTypes.CODE

    assert blocks[4].content == "$x}}"
    assert blocks[4].type == BlockTypes.TEXT


@mark.parametrize(
    "template",
    [
        ("{{a$}}"),
        ("{{a$a}}"),
        ("{{a''}}"),
        ('{{a""}}'),
        ("{{a'b'}}"),
        ('{{a"b"}}'),
        ("{{a'b'   }}"),
        ('{{a"b"    }}'),
        ("{{ asis 'f\\'oo' }}"),
    ],
)
def test_it_tokenizes_edge_cases_correctly_4(template):
    target = TemplateTokenizer()

    blocks = target.tokenize(template)

    assert len(blocks) == 1
    assert blocks[0].type == BlockTypes.CODE
    assert blocks[0].content == template[2:-2].strip()


def test_it_tokenizes_a_typical_prompt():
    target = TemplateTokenizer()

    template = (
        "this is a {{ $prompt }} with {{$some}} variables "
        "and {{function $calls}} {{ and 'values' }}"
    )

    blocks = target.tokenize(template)

    assert len(blocks) == 8

    assert blocks[0].content == "this is a "
    assert blocks[0].type == BlockTypes.TEXT

    assert blocks[1].content == "$prompt"
    assert blocks[1].type == BlockTypes.VARIABLE

    assert blocks[2].content == " with "
    assert blocks[2].type == BlockTypes.TEXT

    assert blocks[3].content == "$some"
    assert blocks[3].type == BlockTypes.VARIABLE

    assert blocks[4].content == " variables and "
    assert blocks[4].type == BlockTypes.TEXT

    assert blocks[5].content == "function $calls"
    assert blocks[5].type == BlockTypes.CODE

    assert blocks[6].content == " "
    assert blocks[6].type == BlockTypes.TEXT

    assert blocks[7].content == "and 'values'"
    assert blocks[7].type == BlockTypes.CODE
