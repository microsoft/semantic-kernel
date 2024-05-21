# Copyright (c) Microsoft. All rights reserved.


import pytest

from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.kernel import Kernel
from semantic_kernel.template_engine.blocks.block_types import BlockTypes
from semantic_kernel.template_engine.blocks.text_block import TextBlock


def test_init():
    text_block = TextBlock.from_text(text="test text")
    assert text_block.content == "test text"


def test_init_with_just_start_index():
    text_block = TextBlock.from_text(text="test text", start_index=2)
    assert text_block.content == "st text"


def test_init_with_just_stop_index():
    text_block = TextBlock.from_text(text="test text", stop_index=2)
    assert text_block.content == "te"


def test_init_with_start_index_greater_than_stop_index():
    with pytest.raises(ValueError):
        TextBlock.from_text(text="test text", start_index=2, stop_index=1)


def test_init_with_start_stop_indices():
    text_block = TextBlock.from_text(text="test text", start_index=0, stop_index=4)
    assert text_block.content == "test"


def test_init_with_start_index_less_than_zero():
    with pytest.raises(ValueError):
        TextBlock.from_text(text="test text", start_index=-1, stop_index=1)


def test_init_with_negative_stop_index():
    text_block = TextBlock.from_text(text="test text", stop_index=-1)
    assert text_block.content == "test tex"


def test_type_property():
    text_block = TextBlock.from_text(text="test text")
    assert text_block.type == BlockTypes.TEXT


def test_render():
    text_block = TextBlock.from_text(text="test text")
    rendered_value = text_block.render(Kernel(), KernelArguments())
    assert rendered_value == "test text"


@pytest.mark.parametrize(
    ("input_", "output"),
    [
        (None, ""),
        ("", ""),
        (" ", " "),
        ("  ", "  "),
        ("   ", "   "),
        (" \n", " \n"),
        (" \t", " \t"),
        (" \r", " \r"),
    ],
    ids=["None", "empty", "space", "two_spaces", "three_spaces", "space_newline", "space_tab", "space_carriage_return"],
)
def test_preserves_empty_values(input_, output):
    assert output == TextBlock.from_text(text=input_).content


@pytest.mark.parametrize(
    ("input_", "output"),
    [
        (None, ""),
        ("", ""),
        (" ", " "),
        ("  ", "  "),
        ("   ", "   "),
        (" \n", " \n"),
        (" \t", " \t"),
        (" \r", " \r"),
        ("test", "test"),
        (" \nabc", " \nabc"),
        ("'x'", "'x'"),
        ('"x"', '"x"'),
        ("\"'x'\"", "\"'x'\""),
    ],
)
def test_renders_the_content_as_it(input_, output):
    assert TextBlock.from_text(text=input_).render() == output
