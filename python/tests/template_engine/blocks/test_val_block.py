# Copyright (c) Microsoft. All rights reserved.

from logging import Logger

from pytest import raises

from semantic_kernel.orchestration.context_variables import ContextVariables
from semantic_kernel.template_engine_v2.blocks.block_types import BlockTypes
from semantic_kernel.template_engine_v2.blocks.val_block import ValBlock


class TestValBlock:
    def test_init(self):
        val_block = ValBlock(content="'test value'", log=Logger("test_logger"))
        assert val_block.content == "'test value'"
        assert isinstance(val_block.log, Logger)

    def test_type_property(self):
        val_block = ValBlock(content="'test value'")
        assert val_block.type == BlockTypes.VALUE

    def test_is_valid(self):
        val_block = ValBlock(content="'test value'")
        is_valid, error_msg = val_block.is_valid()
        assert is_valid
        assert error_msg == ""

    def test_is_valid_invalid_quotes(self):
        val_block = ValBlock(content="'test value\"")
        is_valid, error_msg = val_block.is_valid()
        assert not is_valid
        assert (
            error_msg
            == "A value must be defined using either single quotes or double quotes, not both"
        )

    def test_is_valid_no_quotes(self):
        val_block = ValBlock(content="test value")
        is_valid, error_msg = val_block.is_valid()
        assert not is_valid
        assert (
            error_msg
            == "A value must be wrapped in either single quotes or double quotes"
        )

    def test_is_valid_wrong_quotes(self):
        val_block = ValBlock(content="!test value!")
        is_valid, error_msg = val_block.is_valid()
        assert not is_valid
        assert (
            error_msg
            == "A value must be wrapped in either single quotes or double quotes"
        )

    def test_render(self):
        val_block = ValBlock(content="'test value'")
        rendered_value = val_block.render(ContextVariables())
        assert rendered_value == "test value"

    def test_has_val_prefix(self):
        assert ValBlock.has_val_prefix("'test value'")
        assert ValBlock.has_val_prefix('"test value"')
        assert not ValBlock.has_val_prefix("test value")
        assert not ValBlock.has_val_prefix(None)

    def test_init_value_error(self):
        with raises(ValueError):
            ValBlock(content="")
