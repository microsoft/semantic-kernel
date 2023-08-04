# Copyright (c) Microsoft. All rights reserved.

from logging import Logger

from pytest import raises

from semantic_kernel.orchestration.context_variables import ContextVariables
from semantic_kernel.template_engine.blocks.block_types import BlockTypes
from semantic_kernel.template_engine.blocks.text_block import TextBlock


def test_init():
    text_block = TextBlock.from_text(text="test text", log=Logger("test_logger"))
    assert text_block.content == "test text"
    assert isinstance(text_block.log, Logger)


def test_init_with_just_start_index():
    text_block = TextBlock.from_text(
        text="test text", start_index=2, log=Logger("test_logger")
    )
    assert text_block.content == "st text"
    assert isinstance(text_block.log, Logger)


def test_init_with_just_stop_index():
    text_block = TextBlock.from_text(
        text="test text", stop_index=2, log=Logger("test_logger")
    )
    assert text_block.content == "te"
    assert isinstance(text_block.log, Logger)


def test_init_with_start_index_greater_than_stop_index():
    with raises(ValueError):
        TextBlock.from_text(
            text="test text", start_index=2, stop_index=1, log=Logger("test_logger")
        )


def test_init_with_start_stop_indices():
    text_block = TextBlock.from_text(
        text="test text", start_index=0, stop_index=4, log=Logger("test_logger")
    )
    assert text_block.content == "test"
    assert isinstance(text_block.log, Logger)


def test_init_with_start_index_less_than_zero():
    with raises(ValueError):
        TextBlock.from_text(
            text="test text", start_index=-1, stop_index=1, log=Logger("test_logger")
        )


def test_init_with_negative_stop_index():
    text_block = TextBlock.from_text(
        text="test text", stop_index=-1, log=Logger("test_logger")
    )
    assert text_block.content == "test tex"


def test_type_property():
    text_block = TextBlock.from_text(text="test text")
    assert text_block.type == BlockTypes.TEXT


def test_is_valid():
    text_block = TextBlock.from_text(text="test text")
    is_valid, error_msg = text_block.is_valid()
    assert is_valid
    assert error_msg == ""


def test_render():
    text_block = TextBlock.from_text(text="test text")
    rendered_value = text_block.render(ContextVariables())
    assert rendered_value == "test text"


def test_preserves_empty_values():
    assert "" == TextBlock.from_text(text=None).content
    assert "" == TextBlock.from_text(text="").content
    assert " " == TextBlock.from_text(text=" ").content
    assert "  " == TextBlock.from_text(text="  ").content
    assert " \n" == TextBlock.from_text(text=" \n").content
    assert " \t" == TextBlock.from_text(text=" \t").content
    assert " \r" == TextBlock.from_text(text=" \r").content


def test_is_always_valid():
    assert TextBlock.from_text(text=None).is_valid() == (True, "")
    assert TextBlock.from_text(text="").is_valid() == (True, "")
    assert TextBlock.from_text(text=" ").is_valid() == (True, "")
    assert TextBlock.from_text(text="  ").is_valid() == (True, "")
    assert TextBlock.from_text(text=" \n").is_valid() == (True, "")
    assert TextBlock.from_text(text=" \t").is_valid() == (True, "")
    assert TextBlock.from_text(text=" \r").is_valid() == (True, "")
    assert TextBlock.from_text(text="test").is_valid() == (True, "")
    assert TextBlock.from_text(text=" \nabc").is_valid() == (True, "")


def test_renders_the_content_as_it():
    assert TextBlock.from_text(text=None).render() == ""
    assert TextBlock.from_text(text="").render() == ""
    assert TextBlock.from_text(text=" ").render() == " "
    assert TextBlock.from_text(text="  ").render() == "  "
    assert TextBlock.from_text(text=" \n").render() == " \n"
    assert TextBlock.from_text(text=" \t").render() == " \t"
    assert TextBlock.from_text(text=" \r").render() == " \r"
    assert TextBlock.from_text(text="test").render() == "test"
    assert TextBlock.from_text(text=" \nabc").render() == " \nabc"
    assert TextBlock.from_text(text="'x'").render() == "'x'"
    assert TextBlock.from_text(text='"x"').render() == '"x"'
    assert TextBlock.from_text(text="\"'x'\"").render() == "\"'x'\""
