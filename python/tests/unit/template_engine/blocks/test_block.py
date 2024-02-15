# Copyright (c) Microsoft. All rights reserved.

from pytest import raises

from semantic_kernel.template_engine.blocks.block import Block
from semantic_kernel.template_engine.blocks.block_types import BlockTypes


def test_init():
    block = Block(content="test content")
    assert block.content == "test content"


def test_type_property():
    block = Block()
    assert block.type == BlockTypes.UNDEFINED


def test_is_valid_not_implemented():
    block = Block()
    with raises(NotImplementedError):
        block.is_valid()
