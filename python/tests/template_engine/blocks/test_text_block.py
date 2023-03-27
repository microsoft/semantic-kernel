# Copyright (c) Microsoft. All rights reserved.

from logging import Logger

from pytest import raises

from semantic_kernel.orchestration.context_variables import ContextVariables
from semantic_kernel.template_engine_v2.blocks.block_types import BlockTypes
from semantic_kernel.template_engine_v2.blocks.text_block import TextBlock


def test_init():
    text_block = TextBlock(text="test text", log=Logger("test_logger"))
    assert text_block.content == "test text"
    assert isinstance(text_block.log, Logger)


def test_init_with_just_start_index():
    text_block = TextBlock(text="test text", start_index=2, log=Logger("test_logger"))
    assert text_block.content == "st text"
    assert isinstance(text_block.log, Logger)


def test_init_with_just_stop_index():
    text_block = TextBlock(text="test text", stop_index=2, log=Logger("test_logger"))
    assert text_block.content == "te"
    assert isinstance(text_block.log, Logger)


def test_init_with_start_index_greater_than_stop_index():
    with raises(ValueError):
        TextBlock(
            text="test text", start_index=2, stop_index=1, log=Logger("test_logger")
        )


def test_init_with_start_stop_indices():
    text_block = TextBlock(
        text="test text", start_index=0, stop_index=4, log=Logger("test_logger")
    )
    assert text_block.content == "test"
    assert isinstance(text_block.log, Logger)


def test_init_with_start_index_less_than_zero():
    with raises(ValueError):
        TextBlock(
            text="test text", start_index=-1, stop_index=1, log=Logger("test_logger")
        )


def test_init_with_negative_stop_index():
    text_block = TextBlock(text="test text", stop_index=-1, log=Logger("test_logger"))
    assert text_block.content == "test tex"


def test_type_property():
    text_block = TextBlock(text="test text")
    assert text_block.type == BlockTypes.TEXT


def test_is_valid():
    text_block = TextBlock(text="test text")
    is_valid, error_msg = text_block.is_valid()
    assert is_valid
    assert error_msg == ""


def test_render():
    text_block = TextBlock(text="test text")
    rendered_value = text_block.render(ContextVariables())
    assert rendered_value == "test text"
