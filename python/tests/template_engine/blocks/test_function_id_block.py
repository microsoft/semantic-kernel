# Copyright (c) Microsoft. All rights reserved.

from pytest import raises
from logging import Logger

from semantic_kernel.template_engine_v2.blocks.function_id_block import FunctionIdBlock
from semantic_kernel.template_engine_v2.blocks.block_types import BlockTypes
from semantic_kernel.orchestration.context_variables import ContextVariables


class TestFunctionIdBlock:
    def test_init(self):
        function_id_block = FunctionIdBlock(
            content="skill.function", log=Logger("test_logger")
        )
        assert function_id_block.content == "skill.function"
        assert isinstance(function_id_block.log, Logger)

    def test_type_property(self):
        function_id_block = FunctionIdBlock(content="skill.function")
        assert function_id_block.type == BlockTypes.FUNCTION_ID

    def test_is_valid(self):
        function_id_block = FunctionIdBlock(content="skill.function")
        is_valid, error_msg = function_id_block.is_valid()
        assert is_valid
        assert error_msg == ""

    def test_is_valid_empty_identifier(self):
        function_id_block = FunctionIdBlock(content="")
        is_valid, error_msg = function_id_block.is_valid()
        assert not is_valid
        assert error_msg == "The function identifier is empty"

    def test_render(self):
        function_id_block = FunctionIdBlock(content="skill.function")
        rendered_value = function_id_block.render(ContextVariables())
        assert rendered_value == "skill.function"

    def test_init_value_error(self):
        with raises(ValueError):
            FunctionIdBlock(content="skill.nope.function")
