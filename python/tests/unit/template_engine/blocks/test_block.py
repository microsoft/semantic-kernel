# Copyright (c) Microsoft. All rights reserved.

from pydantic import ValidationError
from pytest import raises

from semantic_kernel.template_engine.blocks.block import Block


def test_init():
    block = Block(content="test content")
    assert block.content == "test content"


def test_is_empty_not_implemented():
    block = Block(content="test content")
    block.content = ""
    with raises(NotImplementedError):
        block.is_valid()


def test_no_content():
    with raises(ValidationError):
        Block()


def test_is_valid_not_implemented():
    block = Block(content="")
    with raises(NotImplementedError):
        block.is_valid()
