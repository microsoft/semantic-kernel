# Copyright (c) Microsoft. All rights reserved.

from pytest import mark, raises

from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.kernel import Kernel
from semantic_kernel.template_engine.blocks.block_errors import ValBlockSyntaxError
from semantic_kernel.template_engine.blocks.block_types import BlockTypes
from semantic_kernel.template_engine.blocks.val_block import ValBlock


def test_init_single_quote():
    val_block = ValBlock(content="'test value'")
    assert val_block.content == "'test value'"
    assert val_block.value == "test value"
    assert val_block.quote == "'"
    assert val_block.type == BlockTypes.VALUE


def test_init_double_quote():
    val_block = ValBlock(content='"test value"')
    assert val_block.content == '"test value"'
    assert val_block.value == "test value"
    assert val_block.quote == '"'
    assert val_block.type == BlockTypes.VALUE


@mark.parametrize(
    "content",
    [
        "test value",
        "'test value",
        "test value'",
        '"test value',
        'test value"',
        "'test value\"",
    ],
    ids=[
        "no_quotes",
        "single_quote_start",
        "single_quote_end",
        "double_quote_start",
        "double_quote_end",
        "mixed_quote",
    ],
)
def test_syntax_error(content):
    with raises(ValBlockSyntaxError, match=rf".*{content}*"):
        ValBlock(content=content)


def test_render():
    val_block = ValBlock(content="'test value'")
    rendered_value = val_block.render(Kernel(), KernelArguments())
    assert rendered_value == "test value"


def test_escaping():
    val_block = ValBlock(content="'f\\'oo'")
    rendered_value = val_block.render(Kernel(), KernelArguments())
    assert rendered_value == "f\\'oo"


def test_escaping2():
    val_block = ValBlock(content=r"'f\'oo'")
    rendered_value = val_block.render(Kernel(), KernelArguments())
    assert rendered_value == r"f\'oo"
