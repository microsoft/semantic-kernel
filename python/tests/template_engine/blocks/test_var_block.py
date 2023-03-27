# Copyright (c) Microsoft. All rights reserved.

from pytest import raises
from logging import Logger

from semantic_kernel.template_engine_v2.blocks.var_block import VarBlock
from semantic_kernel.template_engine_v2.blocks.block_types import BlockTypes
from semantic_kernel.template_engine_v2.blocks.symbols import Symbols
from semantic_kernel.orchestration.context_variables import ContextVariables


class TestVarBlock:
    def test_init(self):
        var_block = VarBlock(content="$test_var", log=Logger("test_logger"))
        assert var_block.content == "$test_var"
        assert isinstance(var_block.log, Logger)

    def test_type_property(self):
        var_block = VarBlock(content="$test_var")
        assert var_block.type == BlockTypes.VARIABLE

    def test_is_valid(self):
        var_block = VarBlock(content="$test_var")
        is_valid, error_msg = var_block.is_valid()
        assert is_valid
        assert error_msg == ""

    def test_is_valid_no_prefix(self):
        var_block = VarBlock(content="test_var")
        is_valid, error_msg = var_block.is_valid()
        assert not is_valid
        assert (
            error_msg == f"A variable must start with the symbol {Symbols.VAR_PREFIX}"
        )

    def test_is_valid_invalid_characters(self):
        var_block = VarBlock(content="$test-var")
        is_valid, error_msg = var_block.is_valid()
        assert not is_valid
        assert (
            error_msg == "The variable name 'test-var' contains invalid characters. "
            "Only alphanumeric chars and underscore are allowed."
        )

    def test_render(self):
        var_block = VarBlock(content="$test_var")
        context_variables = ContextVariables()
        context_variables.set("test_var", "test_value")
        rendered_value = var_block.render(context_variables)
        assert rendered_value == "test_value"

    def test_render_variable_not_found(self):
        var_block = VarBlock(content="$test_var")
        context_variables = ContextVariables()
        rendered_value = var_block.render(context_variables)
        assert rendered_value == ""

    def test_init_value_error(self):
        with raises(ValueError):
            VarBlock(content="")
