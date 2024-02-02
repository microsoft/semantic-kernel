from unittest.mock import Mock

from pytest import mark, raises

from semantic_kernel.memory.null_memory import NullMemory
from semantic_kernel.orchestration.context_variables import ContextVariables
from semantic_kernel.orchestration.delegate_types import DelegateTypes
from semantic_kernel.orchestration.kernel_context import KernelContext
from semantic_kernel.orchestration.kernel_function import KernelFunction
from semantic_kernel.plugin_definition.kernel_plugin import KernelPlugin
from semantic_kernel.plugin_definition.kernel_plugin_collection import (
    KernelPluginCollection,
)
from semantic_kernel.template_engine.blocks.block_types import BlockTypes
from semantic_kernel.template_engine.blocks.code_block import CodeBlock
from semantic_kernel.template_engine.blocks.function_id_block import FunctionIdBlock
from semantic_kernel.template_engine.blocks.val_block import ValBlock
from semantic_kernel.template_engine.blocks.var_block import VarBlock


class TestCodeBlock:
    def setup_method(self):
        self.plugins = Mock(spec=KernelPluginCollection)

    @mark.asyncio
    async def test_it_throws_if_a_function_doesnt_exist(self):
        context = KernelContext.model_construct(
            variables=ContextVariables(),
            memory=NullMemory(),
            plugins=KernelPluginCollection(),
        )

        target = CodeBlock(
            content="functionName",
        )

        with raises(ValueError):
            await target.render_code(context)

    @mark.asyncio
    async def test_it_throws_if_a_function_call_throws(self):
        def invoke(_):
            raise Exception("error")

        function = KernelFunction(
            delegate_type=DelegateTypes.InKernelContext,
            delegate_function=invoke,
            plugin_name="",
            function_name="funcName",
            description="",
            parameters=[],
            is_semantic=False,
        )

        dkp = KernelPlugin(name="test", functions=[function])
        plugins = KernelPluginCollection()
        plugins.add(dkp)

        # Create a context with the variables, memory, and plugin collection
        context = KernelContext.model_construct(
            variables=ContextVariables(),
            memory=NullMemory(),
            plugins=plugins,
        )

        target = CodeBlock(
            content="functionName",
        )

        with raises(ValueError):
            await target.render_code(context)

    def test_it_has_the_correct_type(self):
        assert (
            CodeBlock(
                content="",
            ).type
            == BlockTypes.CODE
        )

    def test_it_trims_spaces(self):
        assert (
            CodeBlock(
                content="  aa  ",
            ).content
            == "aa"
        )

    def test_it_checks_validity_of_internal_blocks(self):
        valid_block1 = FunctionIdBlock(content="x")

        valid_block2 = ValBlock(content="''")
        invalid_block = VarBlock(content="!notvalid")

        code_block1 = CodeBlock(
            tokens=[valid_block1, valid_block2],
            content="",
        )
        code_block2 = CodeBlock(
            tokens=[valid_block1, invalid_block],
            content="",
        )

        is_valid1, _ = code_block1.is_valid()
        is_valid2, _ = code_block2.is_valid()

        assert is_valid1
        assert not is_valid2

    def test_it_requires_a_valid_function_call(self):
        func_id = FunctionIdBlock(content="funcName")

        val_block = ValBlock(content="'value'")
        var_block = VarBlock(content="$var")

        code_block1 = CodeBlock(
            tokens=[func_id, val_block],
            content="",
        )
        code_block2 = CodeBlock(
            tokens=[func_id, var_block],
            content="",
        )
        code_block3 = CodeBlock(
            tokens=[func_id, func_id],
            content="",
        )
        code_block4 = CodeBlock(
            tokens=[func_id, var_block, var_block],
            content="",
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

        context = KernelContext.model_construct(
            variables=variables,
            memory=NullMemory(),
            plugins=None,
        )

        code_block = CodeBlock(
            content="$varName",
        )
        result = await code_block.render_code(context)

        assert result == "foo"

    @mark.asyncio
    async def test_it_renders_code_block_consisting_of_just_a_var_block2(self):
        variables = ContextVariables()
        variables["varName"] = "bar"

        context = KernelContext.model_construct(
            variables=variables,
            memory=NullMemory(),
            plugins=None,
        )

        code_block = CodeBlock(
            tokens=[VarBlock(content="$varName")],
            content="",
        )
        result = await code_block.render_code(context)

        assert result == "bar"

    @mark.asyncio
    async def test_it_renders_code_block_consisting_of_just_a_val_block1(self):
        context = KernelContext.model_construct(
            variables=ContextVariables(),
            memory=NullMemory(),
            plugins=None,
        )

        code_block = CodeBlock(
            content="'ciao'",
        )
        result = await code_block.render_code(context)

        assert result == "ciao"

    @mark.asyncio
    async def test_it_renders_code_block_consisting_of_just_a_val_block2(self):
        context = KernelContext.model_construct(
            variables=ContextVariables(),
            memory=NullMemory(),
            plugins=None,
        )

        code_block = CodeBlock(
            tokens=[ValBlock(content="'arrivederci'")],
            content="",
        )
        result = await code_block.render_code(context)

        assert result == "arrivederci"

    @mark.asyncio
    async def test_it_invokes_function_cloning_all_variables(self):
        # Set up initial context variables
        variables = ContextVariables()
        variables["input"] = "zero"
        variables["var1"] = "uno"
        variables["var2"] = "due"

        # Create a FunctionIdBlock with the function name
        func_id = FunctionIdBlock(content="funcName")

        # Set up a canary dictionary to track changes in the context variables
        canary = {"input": "", "var1": "", "var2": ""}

        # Define the function to be invoked, which modifies the canary
        # and context variables
        def invoke(ctx):
            nonlocal canary
            canary["input"] = ctx["input"]
            canary["var1"] = ctx["var1"]
            canary["var2"] = ctx["var2"]

            ctx["input"] = "overridden"
            ctx["var1"] = "overridden"
            ctx["var2"] = "overridden"

        # Create an KernelFunction with the invoke function as its delegate
        function = KernelFunction(
            delegate_type=DelegateTypes.InKernelContext,
            delegate_function=invoke,
            plugin_name="",
            function_name="funcName",
            description="",
            parameters=[],
            is_semantic=False,
        )

        dkp = KernelPlugin(name="test", functions=[function])
        plugins = KernelPluginCollection()
        plugins.add(dkp)

        # Create a context with the variables, memory, and plugin collection
        context = KernelContext.model_construct(
            variables=variables,
            memory=NullMemory(),
            plugins=plugins,
        )

        # Create a CodeBlock with the FunctionIdBlock and render it with the context
        code_block = CodeBlock(
            tokens=[func_id],
            content="",
        )
        await code_block.render_code(context)

        # Check that the canary values match the original context variables
        assert canary["input"] == "zero"
        assert canary["var1"] == "uno"
        assert canary["var2"] == "due"

        # Check that the original context variables were not modified
        assert variables["input"] == "zero"
        assert variables["var1"] == "uno"
        assert variables["var2"] == "due"

    @mark.asyncio
    async def test_it_invokes_function_with_custom_variable(self):
        # Define custom variable name and value
        VAR_NAME = "varName"
        VAR_VALUE = "varValue"

        # Set up initial context variables
        variables = ContextVariables()
        variables[VAR_NAME] = VAR_VALUE

        # Create a FunctionIdBlock with the function name and a
        # VarBlock with the custom variable
        func_id = FunctionIdBlock(content="funcName")
        var_block = VarBlock(content=f"${VAR_NAME}")

        # Set up a canary variable to track changes in the context input
        canary = ""

        # Define the function to be invoked, which modifies the canary variable
        def invoke(ctx):
            nonlocal canary
            canary = ctx["input"]

        # Create an KernelFunction with the invoke function as its delegate
        function = KernelFunction(
            delegate_type=DelegateTypes.InKernelContext,
            delegate_function=invoke,
            plugin_name="",
            function_name="funcName",
            description="",
            parameters=[],
            is_semantic=False,
        )

        dkp = KernelPlugin(name="test", functions=[function])
        plugins = KernelPluginCollection()
        plugins.add(dkp)

        # Create a context with the variables, memory, and plugin collection
        context = KernelContext.model_construct(
            variables=variables,
            memory=NullMemory(),
            plugins=plugins,
        )

        # Create a CodeBlock with the FunctionIdBlock and VarBlock,
        # and render it with the context
        code_block = CodeBlock(
            tokens=[func_id, var_block],
            content="",
        )
        result = await code_block.render_code(context)

        # Check that the result matches the custom variable value
        assert result == VAR_VALUE
        # Check that the canary value matches the custom variable value
        assert canary == VAR_VALUE

    @mark.asyncio
    async def test_it_invokes_function_with_custom_value(self):
        # Define a value to be used in the test
        VALUE = "value"

        # Create a FunctionIdBlock with the function name and a ValBlock with the value
        func_id = FunctionIdBlock(content="funcName")
        val_block = ValBlock(content=f"'{VALUE}'")

        # Set up a canary variable to track changes in the context input
        canary = ""

        # Define the function to be invoked, which modifies the canary variable
        def invoke(ctx):
            nonlocal canary
            canary = ctx["input"]

        # Create an KernelFunction with the invoke function as its delegate
        function = KernelFunction(
            delegate_type=DelegateTypes.InKernelContext,
            delegate_function=invoke,
            plugin_name="",
            function_name="funcName",
            description="",
            parameters=[],
            is_semantic=False,
        )

        dkp = KernelPlugin(name="test", functions=[function])
        plugins = KernelPluginCollection()
        plugins.add(dkp)

        # Create a context with empty variables, memory, and plugin collection
        context = KernelContext.model_construct(
            variables=ContextVariables(),
            memory=NullMemory(),
            plugins=plugins,
        )

        # Create a CodeBlock with the FunctionIdBlock and ValBlock,
        # and render it with the context
        code_block = CodeBlock(
            tokens=[func_id, val_block],
            content="",
        )
        result = await code_block.render_code(context)

        # Check that the result matches the value
        assert result == VALUE
        # Check that the canary value matches the value
        assert canary == VALUE
