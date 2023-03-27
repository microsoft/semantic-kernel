# Copyright (c) Microsoft. All rights reserved.

from pytest import raises
from logging import Logger

from semantic_kernel.template_engine_v2.blocks.block import Block
from semantic_kernel.template_engine_v2.blocks.block_types import BlockTypes
from semantic_kernel.utils.null_logger import NullLogger


class TestBlock:
    def test_init(self):
        block = Block(content="test content", log=NullLogger())
        assert block.content == "test content"
        assert isinstance(block.log, Logger)

    def test_type_property(self):
        block = Block()
        assert block.type == BlockTypes.UNDEFINED

    def test_is_valid_not_implemented(self):
        block = Block()
        with raises(NotImplementedError):
            block.is_valid()
