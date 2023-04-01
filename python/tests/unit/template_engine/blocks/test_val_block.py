# Copyright (c) Microsoft. All rights reserved.

from logging import Logger

from semantic_kernel.orchestration.context_variables import ContextVariables
from semantic_kernel.template_engine.blocks.block_types import BlockTypes
from semantic_kernel.template_engine.blocks.val_block import ValBlock


def test_init():
    val_block = ValBlock(content="'test value'", log=Logger("test_logger"))
    assert val_block.content == "'test value'"
    assert isinstance(val_block.log, Logger)


def test_type_property():
    val_block = ValBlock(content="'test value'")
    assert val_block.type == BlockTypes.VALUE


def test_is_valid():
    val_block = ValBlock(content="'test value'")
    is_valid, error_msg = val_block.is_valid()
    assert is_valid
    assert error_msg == ""


def test_is_valid_invalid_quotes():
    val_block = ValBlock(content="'test value\"")
    is_valid, error_msg = val_block.is_valid()
    assert not is_valid
    assert error_msg == (
        "A value must be defined using either single quotes "
        "or double quotes, not both"
    )


def test_is_valid_no_quotes():
    val_block = ValBlock(content="test value")
    is_valid, error_msg = val_block.is_valid()
    assert not is_valid
    assert (
        error_msg == "A value must be wrapped in either single quotes or double quotes"
    )


def test_is_valid_wrong_quotes():
    val_block = ValBlock(content="!test value!")
    is_valid, error_msg = val_block.is_valid()
    assert not is_valid
    assert (
        error_msg == "A value must be wrapped in either single quotes or double quotes"
    )


def test_render():
    val_block = ValBlock(content="'test value'")
    rendered_value = val_block.render(ContextVariables())
    assert rendered_value == "test value"


def test_has_val_prefix():
    assert ValBlock.has_val_prefix("'test value'")
    assert ValBlock.has_val_prefix('"test value"')

    assert not ValBlock.has_val_prefix("test value")
    assert not ValBlock.has_val_prefix(None)


def test_checks_if_value_starts_with_quote():
    assert ValBlock.has_val_prefix("'")
    assert ValBlock.has_val_prefix("'a")
    assert ValBlock.has_val_prefix('"')
    assert ValBlock.has_val_prefix('"b')

    assert not ValBlock.has_val_prefix("d'")
    assert not ValBlock.has_val_prefix('e"')
    assert not ValBlock.has_val_prefix(None)
    assert not ValBlock.has_val_prefix("")
    assert not ValBlock.has_val_prefix("v")
    assert not ValBlock.has_val_prefix("-")


def test_consistent_quotes_required():
    valid_block_1 = ValBlock(content="'test value'")
    valid_block_2 = ValBlock(content='"test value"')
    invalid_block_1 = ValBlock(content="'test value\"")
    invalid_block_2 = ValBlock(content="\"test value'")

    assert valid_block_1.is_valid()[0]
    assert valid_block_2.is_valid()[0]

    assert not invalid_block_1.is_valid()[0]
    assert not invalid_block_2.is_valid()[0]
