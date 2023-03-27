from pytest import raises, mark
from unittest.mock import Mock
from logging import Logger

from semantic_kernel.template_engine_v2.blocks.code_block import CodeBlock
from semantic_kernel.template_engine_v2.blocks.block_types import BlockTypes
from semantic_kernel.template_engine_v2.blocks.function_id_block import FunctionIdBlock
from semantic_kernel.template_engine_v2.blocks.var_block import VarBlock
from semantic_kernel.template_engine_v2.blocks.val_block import ValBlock
from semantic_kernel.orchestration.context_variables import ContextVariables
from semantic_kernel.orchestration.sk_context import SKContext
from semantic_kernel.memory.null_memory import NullMemory
from semantic_kernel.skill_definition.read_only_skill_collection_base import (
    ReadOnlySkillCollectionBase,
)
from semantic_kernel.orchestration.sk_function_base import SKFunctionBase


class TestCodeBlock:
    def setup_method(self):
        self.skills = Mock(spec=ReadOnlySkillCollectionBase)
        self.log = Mock(spec=Logger)

    @mark.asyncio
    async def test_it_throws_if_a_function_doesnt_exist(self):
        context = SKContext(
            ContextVariables(),
            memory=NullMemory(),
            skill_collection=self.skills,
            logger=self.log,
        )
        # Make it so our self.skills mock's `has_function` method returns False
        self.skills.has_function.return_value = False
        target = CodeBlock(content="functionName", log=self.log)

        with raises(ValueError):
            await target.render_code_async(context)

    @mark.asyncio
    async def test_it_throws_if_a_function_call_throws(self):
        context = SKContext(
            ContextVariables(),
            memory=NullMemory(),
            skill_collection=self.skills,
            logger=self.log,
        )
        function = Mock(spec=SKFunctionBase)
        function.invoke_async.side_effect = Exception("error")
        self.skills.has_function.return_value = True
        self.skills.get_function.return_value = function
        target = CodeBlock(content="functionName", log=self.log)

        with raises(ValueError):
            await target.render_code_async(context)

    def test_it_has_the_correct_type(self):
        target = CodeBlock(content="", log=self.log)
        assert target.type == BlockTypes.CODE

    def test_it_trims_spaces(self):
        assert CodeBlock(content="  aa  ", log=self.log).content == "aa"

    def test_it_checks_validity_of_internal_blocks(self):
        valid_block1 = FunctionIdBlock(content="x")
        valid_block2 = ValBlock(content="''")
        invalid_block = VarBlock(content="!notvalid")

        code_block1 = CodeBlock(
            tokens=[valid_block1, valid_block2], content="", log=self.log
        )
        code_block2 = CodeBlock(
            tokens=[valid_block1, invalid_block], content="", log=self.log
        )

        is_valid1, _ = code_block1.is_valid()
        is_valid2, _ = code_block2.is_valid()

        assert is_valid1
        assert not is_valid2

    def test_it_requires_a_valid_function_call(self):
        func_id = FunctionIdBlock(content="funcName")
        val_block = ValBlock(content="'value'")
        var_block = VarBlock(content="$var")

        code_block1 = CodeBlock(tokens=[func_id, val_block], content="", log=self.log)
        code_block2 = CodeBlock(tokens=[func_id, var_block], content="", log=self.log)
        code_block3 = CodeBlock(tokens=[func_id, func_id], content="", log=self.log)
        code_block4 = CodeBlock(
            tokens=[func_id, var_block, var_block], content="", log=self.log
        )

        is_valid1, _ = code_block1.is_valid()
        is_valid2, _ = code_block2.is_valid()
        is_valid3, _ = code_block3.is_valid()
        is_valid4, _ = code_block4.is_valid()

        assert is_valid1
        assert is_valid2
        assert not is_valid3
        assert not is_valid4

    @mark.asyncio
    async def test_it_renders_code_block_consisting_of_just_a_var_block1(self):
        variables = ContextVariables()
        variables["varName"] = "foo"
        context = SKContext(
            variables, memory=NullMemory(), skill_collection=None, logger=self.log
        )

        code_block = CodeBlock(content="$varName", log=self.log)
        result = await code_block.render_code_async(context)

        assert result == "foo"

    @mark.asyncio
    async def test_it_renders_code_block_consisting_of_just_a_var_block2(self):
        variables = ContextVariables()
        variables["varName"] = "bar"
        context = SKContext(
            variables, memory=NullMemory(), skill_collection=None, logger=self.log
        )
        var_block = VarBlock(content="$varName")

        code_block = CodeBlock(tokens=[var_block], content="", log=self.log)
        result = await code_block.render_code_async(context)

        assert result == "bar"

    @mark.asyncio
    async def test_it_renders_code_block_consisting_of_just_a_val_block1(self):
        context = SKContext(
            ContextVariables(),
            memory=NullMemory(),
            skill_collection=None,
            logger=self.log,
        )

        code_block = CodeBlock(content="'ciao'", log=self.log)
        result = await code_block.render_code_async(context)

        assert result == "ciao"

    @mark.asyncio
    async def test_it_renders_code_block_consisting_of_just_a_val_block2(self):
        context = SKContext(
            ContextVariables(),
            memory=NullMemory(),
            skill_collection=None,
            logger=self.log,
        )
        val_block = ValBlock(content="'arrivederci'")

        code_block = CodeBlock(tokens=[val_block], content="", log=self.log)
        result = await code_block.render_code_async(context)

        assert result == "arrivederci"

    @mark.asyncio
    async def test_it_invokes_function_cloning_all_variables(self):
        FUNC = "funcName"

        variables = ContextVariables()
        variables["input"] = "zero"
        variables["var1"] = "uno"
        variables["var2"] = "due"
        context = SKContext(
            variables,
            memory=NullMemory(),
            skill_collection=self.skills,
            logger=self.log,
        )
        func_id = FunctionIdBlock(content=FUNC)

        canary = {"input": "", "var1": "", "var2": ""}
        function = Mock(spec=SKFunctionBase)

        async def invoke_async(input, ctx, settings, log):
            nonlocal canary
            canary["input"] = ctx["input"]
            canary["var1"] = ctx["var1"]
            canary["var2"] = ctx["var2"]

            ctx["input"] = "overridden"
            ctx["var1"] = "overridden"
            ctx["var2"] = "overridden"

        function.invoke_async.side_effect = invoke_async

        self.skills.has_function.return_value = True
        self.skills.get_function.return_value = function

        code_block = CodeBlock(tokens=[func_id], content="", log=self.log)
        await code_block.render_code_async(context)

        assert canary["input"] == "zero"
        assert canary["var1"] == "uno"
        assert canary["var2"] == "due"

        assert variables["input"] == "zero"
        assert variables["var1"] == "uno"
        assert variables["var2"] == "due"

    @mark.asyncio
    async def test_it_invokes_function_with_custom_variable(self):
        FUNC = "funcName"
        VAR = "varName"
        VAR_VALUE = "varValue"

        variables = ContextVariables()
        variables[VAR] = VAR_VALUE
        context = SKContext(
            variables,
            memory=NullMemory(),
            skill_collection=self.skills,
            logger=self.log,
        )
        func_id = FunctionIdBlock(content=FUNC)
        var_block = VarBlock(content=f"${VAR}")

        canary = ""

        function = Mock(spec=SKFunctionBase)

        async def invoke_async(ctx):
            nonlocal canary
            canary = ctx["input"]

        function.invoke_async.side_effect = invoke_async

        self.skills.has_function.return_value = True
        self.skills.get_function.return_value = function

        code_block = CodeBlock(tokens=[func_id, var_block], content="", log=self.log)
        result = await code_block.render_code_async(context)

        assert result == VAR_VALUE
        assert canary == VAR_VALUE

    @mark.asyncio
    async def test_it_invokes_function_with_custom_value(self):
        FUNC = "funcName"
        VALUE = "value"

        context = SKContext(
            ContextVariables(),
            memory=NullMemory(),
            skill_collection=self.skills,
            logger=self.log,
        )
        func_id = FunctionIdBlock(content=FUNC)
        val_block = ValBlock(content=f"'{VALUE}'")

        canary = ""

        function = Mock(spec=SKFunctionBase)

        async def invoke_async(ctx):
            nonlocal canary
            canary = ctx["input"]

        function.invoke_async.side_effect = invoke_async

        self.skills.has_function.return_value = True
        self.skills.get_function.return_value = function

        code_block = CodeBlock(tokens=[func_id, val_block], content="", log=self.log)
        result = await code_block.render_code_async(context)

        assert result == VALUE
        assert canary == VALUE
