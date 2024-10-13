<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
=======
<<<<<<< main
>>>>>>> origin/main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< main
<<<<<<< div
>>>>>>> main
=======
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> origin/main
>>>>>>> head
# Copyright (c) Microsoft. All rights reserved.

from pytest import mark, raises

from semantic_kernel.exceptions import (
    CodeBlockRenderException,
    CodeBlockSyntaxError,
    CodeBlockTokenError,
    FunctionIdBlockSyntaxError,
    NamedArgBlockSyntaxError,
    ValBlockSyntaxError,
    VarBlockSyntaxError,
)
from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.functions.kernel_function_decorator import kernel_function
from semantic_kernel.functions.kernel_function_from_method import (
    KernelFunctionFromMethod,
)
from semantic_kernel.functions.kernel_plugin import KernelPlugin
from semantic_kernel.kernel import Kernel
<<<<<<< div
<<<<<<< div
=======
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
=======
=======
>>>>>>> origin/main
=======
=======
<<<<<<< main
=======
=======
>>>>>>> Stashed changes
=======
<<<<<<< main
=======
<<<<<<< div
=======
>>>>>>> main
=======
>>>>>>> head
=======
>>>>>>> Stashed changes
from pytest import mark, raises

from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.functions.kernel_function import KernelFunction
from semantic_kernel.functions.kernel_parameter_metadata import KernelParameterMetadata
from semantic_kernel.functions.kernel_plugin import KernelPlugin
from semantic_kernel.functions.kernel_plugin_collection import (
    KernelPluginCollection,
)
from semantic_kernel.kernel import Kernel
from semantic_kernel.template_engine.blocks.block_errors import (
    CodeBlockRenderError,
    CodeBlockSyntaxError,
    CodeBlockTokenError,
    FunctionIdBlockSyntaxError,
    NamedArgBlockSyntaxError,
    ValBlockSyntaxError,
    VarBlockSyntaxError,
)
>>>>>>> ms/small_fixes
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
>>>>>>> origin/main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< div
>>>>>>> main
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> origin/main
>>>>>>> head
from semantic_kernel.template_engine.blocks.block_types import BlockTypes
from semantic_kernel.template_engine.blocks.code_block import CodeBlock
from semantic_kernel.template_engine.blocks.function_id_block import FunctionIdBlock
from semantic_kernel.template_engine.blocks.named_arg_block import NamedArgBlock
from semantic_kernel.template_engine.blocks.val_block import ValBlock
from semantic_kernel.template_engine.blocks.var_block import VarBlock


def test_init():
    target = CodeBlock(
        content="plugin.function 'value'  arg1=$arg1",
    )
    assert len(target.tokens) == 3
    assert target.tokens[0] == FunctionIdBlock(content="plugin.function")
    assert target.tokens[1] == ValBlock(content="'value'")
    assert target.tokens[2] == NamedArgBlock(content="arg1=$arg1")
    assert target.type == BlockTypes.CODE
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream


class TestCodeBlockRendering:
    @mark.asyncio
    async def test_it_throws_if_a_plugins_are_empty(self, kernel: Kernel):
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main

=======
=======
<<<<<<< div
>>>>>>> main
=======
>>>>>>> origin/main
=======
<<<<<<< main

=======
>>>>>>> Stashed changes
=======
<<<<<<< main

=======
>>>>>>> Stashed changes
>>>>>>> head
<<<<<<< main


class TestCodeBlockRendering:
    @mark.asyncio
    async def test_it_throws_if_a_plugins_are_empty(self, kernel: Kernel):
=======


class TestCodeBlockRendering:
    def setup_method(self):
        self.kernel = Kernel()
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
=======

    @mark.asyncio
    async def test_it_throws_if_a_plugins_are_empty(self):
        target = CodeBlock(
            content="functionName",
        )
        assert target.tokens[0].type == BlockTypes.FUNCTION_ID
        with raises(CodeBlockRenderError, match="Plugin collection not set in kernel"):
            await target.render_code(self.kernel, KernelArguments())
<<<<<<< div
>>>>>>> main
=======
>>>>>>> origin/main
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> head

    @mark.asyncio
    async def test_it_throws_if_a_plugins_are_empty(self):
        target = CodeBlock(
            content="functionName",
        )
        assert target.tokens[0].type == BlockTypes.FUNCTION_ID
        with raises(CodeBlockRenderError, match="Plugin collection not set in kernel"):
            await target.render_code(self.kernel, KernelArguments())
>>>>>>> origin/main

class TestCodeBlockRendering:
    @mark.asyncio
<<<<<<< main
    async def test_it_throws_if_a_plugins_are_empty(self, kernel: Kernel):
=======
    async def test_it_throws_if_a_function_doesnt_exist(self):
>>>>>>> ms/small_fixes
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
>>>>>>> origin/main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< div
>>>>>>> main
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> origin/main
>>>>>>> head
        target = CodeBlock(
            content="functionName",
        )
        assert target.tokens[0].type == BlockTypes.FUNCTION_ID
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
=======
<<<<<<< main
>>>>>>> origin/main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> origin/main
=======
>>>>>>> Stashed changes
=======
<<<<<<< main
=======
<<<<<<< main
>>>>>>> origin/main
>>>>>>> Stashed changes
<<<<<<< div
=======
<<<<<<< main
>>>>>>> main
=======
>>>>>>> head
        with raises(
            CodeBlockRenderException, match="Function `functionName` not found"
        ):
            await target.render_code(kernel, KernelArguments())
<<<<<<< div
<<<<<<< div
=======
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
<<<<<<< main
>>>>>>> Stashed changes
<<<<<<< Updated upstream
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes

    @mark.asyncio
    async def test_it_throws_if_a_function_doesnt_exist(self, kernel: Kernel):
        target = CodeBlock(
            content="functionName",
        )
        assert target.tokens[0].type == BlockTypes.FUNCTION_ID
        kernel.add_plugin(KernelPlugin(name="test", functions=[]))
        with raises(
            CodeBlockRenderException, match="Function `functionName` not found"
        ):
            await target.render_code(kernel, KernelArguments())

    @mark.asyncio
    async def test_it_throws_if_a_function_call_throws(self, kernel: Kernel):
        @kernel_function(name="funcName")
        def invoke():
            raise Exception("function exception")

        function = KernelFunctionFromMethod(
            method=invoke,
            plugin_name="pluginName",
        )

        kernel.add_function(plugin_name="test", function=function)

        target = CodeBlock(
            content="test.funcName",
        )

        with raises(CodeBlockRenderException, match="test.funcName"):
            await target.render_code(kernel, KernelArguments())

    @mark.asyncio
    async def test_it_renders_code_block_consisting_of_just_a_var_block1(
        self, kernel: Kernel
    ):
        code_block = CodeBlock(
            content="$var",
        )
        result = await code_block.render_code(kernel, KernelArguments(var="foo"))
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======

    @mark.asyncio
    async def test_it_throws_if_a_function_doesnt_exist(self, kernel: Kernel):
=======
        self.kernel.plugins = KernelPluginCollection()
        dkp = KernelPlugin(name="test", functions=[])
        self.kernel.plugins.add(dkp)
        with raises(CodeBlockRenderError, match="Function `functionName` not found"):
            await target.render_code(self.kernel, KernelArguments())

    @mark.asyncio
    async def test_it_throws_if_a_function_call_throws(self):
        def invoke():
            raise Exception("error")

        function = KernelFunction(
            function_name="funcName",
            plugin_name="pluginName",
            description="",
            function=invoke,
            parameters=[],
            return_parameter=None,
            is_prompt=False,
        )

        dkp = KernelPlugin(name="test", functions=[function])
        plugins = KernelPluginCollection()
        plugins.add(dkp)
        kernel = Kernel()
        kernel.plugins = plugins

<<<<<<< div
=======
<<<<<<< Updated upstream
=======
>>>>>>> Stashed changes
>>>>>>> head
=======

    @mark.asyncio
    async def test_it_throws_if_a_function_doesnt_exist(self, kernel: Kernel):
=======
        self.kernel.plugins = KernelPluginCollection()
        dkp = KernelPlugin(name="test", functions=[])
        self.kernel.plugins.add(dkp)
        with raises(CodeBlockRenderError, match="Function `functionName` not found"):
            await target.render_code(self.kernel, KernelArguments())

    @mark.asyncio
    async def test_it_throws_if_a_function_call_throws(self):
        def invoke():
            raise Exception("error")

        function = KernelFunction(
            function_name="funcName",
            plugin_name="pluginName",
            description="",
            function=invoke,
            parameters=[],
            return_parameter=None,
            is_prompt=False,
        )

        dkp = KernelPlugin(name="test", functions=[function])
        plugins = KernelPluginCollection()
        plugins.add(dkp)
        kernel = Kernel()
        kernel.plugins = plugins

<<<<<<< div
>>>>>>> main
=======
<<<<<<< Updated upstream
>>>>>>> origin/main
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> head
>>>>>>> ms/small_fixes
        target = CodeBlock(
            content="functionName",
        )
        assert target.tokens[0].type == BlockTypes.FUNCTION_ID
        kernel.add_plugin(KernelPlugin(name="test", functions=[]))
        with raises(
            CodeBlockRenderException, match="Function `functionName` not found"
        ):
            await target.render_code(kernel, KernelArguments())

<<<<<<< main
    @mark.asyncio
    async def test_it_throws_if_a_function_call_throws(self, kernel: Kernel):
        @kernel_function(name="funcName")
        def invoke():
            raise Exception("function exception")

        function = KernelFunctionFromMethod(
            method=invoke,
            plugin_name="pluginName",
        )

        kernel.add_function(plugin_name="test", function=function)

        target = CodeBlock(
            content="test.funcName",
        )

        with raises(CodeBlockRenderException, match="test.funcName"):
            await target.render_code(kernel, KernelArguments())

    @mark.asyncio
    async def test_it_renders_code_block_consisting_of_just_a_var_block1(
        self, kernel: Kernel
    ):
        code_block = CodeBlock(
            content="$var",
        )
        result = await code_block.render_code(kernel, KernelArguments(var="foo"))
=======
        with raises(CodeBlockRenderError):
            await target.render_code(kernel, KernelArguments())

    @mark.asyncio
    async def test_it_renders_code_block_consisting_of_just_a_var_block1(self):
        code_block = CodeBlock(
            content="$var",
        )
        result = await code_block.render_code(self.kernel, KernelArguments(var="foo"))
>>>>>>> ms/small_fixes
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
>>>>>>> origin/main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< div
>>>>>>> main
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> origin/main
>>>>>>> head

        assert result == "foo"

    @mark.asyncio
<<<<<<< div
<<<<<<< div
=======
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
=======
<<<<<<< main
>>>>>>> origin/main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> origin/main
=======
>>>>>>> Stashed changes
=======
<<<<<<< main
=======
<<<<<<< main
>>>>>>> origin/main
>>>>>>> Stashed changes
<<<<<<< div
=======
<<<<<<< main
>>>>>>> main
=======
>>>>>>> head
    async def test_it_renders_code_block_consisting_of_just_a_val_block1(
        self, kernel: Kernel
    ):
        code_block = CodeBlock(
            content="'ciao'",
        )
        result = await code_block.render_code(kernel, KernelArguments())
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
=======
<<<<<<< div
=======
>>>>>>> main
=======
>>>>>>> head
=======
>>>>>>> origin/main
=======
=======
<<<<<<< main
=======
=======
>>>>>>> Stashed changes
=======
<<<<<<< main
=======
=======
>>>>>>> Stashed changes
    async def test_it_renders_code_block_consisting_of_just_a_val_block1(self):
        code_block = CodeBlock(
            content="'ciao'",
        )
        result = await code_block.render_code(self.kernel, KernelArguments())
>>>>>>> ms/small_fixes
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
>>>>>>> origin/main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< div
>>>>>>> main
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> origin/main
>>>>>>> head

        assert result == "ciao"

    @mark.asyncio
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
    async def test_it_invokes_function_cloning_all_variables(self, kernel: Kernel):
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
    async def test_it_invokes_function_cloning_all_variables(self, kernel: Kernel):
=======
=======
<<<<<<< div
>>>>>>> main
=======
>>>>>>> origin/main
=======
<<<<<<< main
    async def test_it_invokes_function_cloning_all_variables(self, kernel: Kernel):
=======
>>>>>>> Stashed changes
=======
<<<<<<< main
    async def test_it_invokes_function_cloning_all_variables(self, kernel: Kernel):
=======
>>>>>>> Stashed changes
>>>>>>> head
<<<<<<< main
    async def test_it_invokes_function_cloning_all_variables(self, kernel: Kernel):
=======
    async def test_it_invokes_function_cloning_all_variables(self):
>>>>>>> ms/small_fixes
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
>>>>>>> origin/main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< div
>>>>>>> main
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> origin/main
>>>>>>> head
        # Set up initial context variables
        arguments = KernelArguments(input="zero", var1="uno", var2="due")

        # Create a FunctionIdBlock with the function name
        func_id = FunctionIdBlock(content="test.funcName")

        # Set up a canary dictionary to track changes in the context variables
        canary = {"input": "", "var1": "", "var2": ""}

        # Define the function to be invoked, which modifies the canary
        # and context variables
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
        @kernel_function(name="funcName")
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
        @kernel_function(name="funcName")
=======
=======
<<<<<<< div
>>>>>>> main
=======
>>>>>>> origin/main
=======
<<<<<<< main
        @kernel_function(name="funcName")
=======
>>>>>>> Stashed changes
=======
<<<<<<< main
        @kernel_function(name="funcName")
=======
>>>>>>> Stashed changes
>>>>>>> head
<<<<<<< main
        @kernel_function(name="funcName")
=======
>>>>>>> ms/small_fixes
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
>>>>>>> origin/main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< div
>>>>>>> main
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> origin/main
>>>>>>> head
        def invoke(arguments: KernelArguments):
            nonlocal canary
            canary["input"] = arguments["input"]
            canary["var1"] = arguments["var1"]
            canary["var2"] = arguments["var2"]

            arguments["input"] = "overridden"
            arguments["var1"] = "overridden"
            arguments["var2"] = "overridden"

        # Create an KernelFunction with the invoke function as its delegate
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< Updated upstream
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
        function = KernelFunctionFromMethod(
            method=invoke,
            plugin_name="pluginName",
        )

        kernel.add_plugin(KernelPlugin(name="test", functions=[function]))
=======
<<<<<<< main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
=======
>>>>>>> Stashed changes
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< main
<<<<<<< div
>>>>>>> main
=======
>>>>>>> origin/main
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> head
        function = KernelFunctionFromMethod(
            method=invoke,
            plugin_name="pluginName",
        )

        kernel.add_plugin(KernelPlugin(name="test", functions=[function]))
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< div
>>>>>>> main
=======
>>>>>>> origin/main
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> head
=======
        function = KernelFunction(
            function_name="funcName",
            plugin_name="pluginName",
            description="",
            function=invoke,
            parameters=[KernelParameterMetadata(name="arguments", description="", default_value=None, required=True)],
            return_parameter=None,
            is_prompt=False,
        )

        dkp = KernelPlugin(name="test", functions=[function])
        kernel = Kernel()
        kernel.plugins.add(dkp)
>>>>>>> ms/small_fixes
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
>>>>>>> origin/main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< div
>>>>>>> main
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> origin/main
>>>>>>> head

        # Create a CodeBlock with the FunctionIdBlock and render it with the context
        code_block = CodeBlock(
            tokens=[func_id],
            content="",
        )
        await code_block.render_code(kernel, arguments)

        # Check that the canary values match the original context variables
        assert canary["input"] == "zero"
        assert canary["var1"] == "uno"
        assert canary["var2"] == "due"

        # Check that the original context variables were not modified
        assert arguments["input"] == "zero"
        assert arguments["var1"] == "uno"
        assert arguments["var2"] == "due"

    @mark.asyncio
    async def test_it_invokes_function_with_custom_variable(self, kernel: Kernel):
        # Define custom variable name and value
        VAR_NAME = "varName"
        VAR_VALUE = "varValue"

        # Set up initial context variables
        arguments = KernelArguments()
        arguments[VAR_NAME] = VAR_VALUE

        # Create a FunctionIdBlock with the function name and a
        # VarBlock with the custom variable
        func_id = FunctionIdBlock(content="test.funcName")
        var_block = VarBlock(content=f"${VAR_NAME}")

        # Set up a canary variable to track changes in the context input
        canary = ""

        # Define the function to be invoked, which modifies the canary variable
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
        @kernel_function(name="funcName")
        def invoke(arguments: "KernelArguments"):
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< Updated upstream
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
        @kernel_function(name="funcName")
        def invoke(arguments: "KernelArguments"):
=======
<<<<<<< div
=======
>>>>>>> main
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
>>>>>>> origin/main
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> head
<<<<<<< main
        @kernel_function(name="funcName")
        def invoke(arguments: "KernelArguments"):
=======
        def invoke(arguments):
>>>>>>> ms/small_fixes
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
>>>>>>> origin/main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< div
>>>>>>> main
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> origin/main
>>>>>>> head
            nonlocal canary
            canary = arguments["varName"]
            return arguments["varName"]

        # Create an KernelFunction with the invoke function as its delegate
<<<<<<< div
<<<<<<< div
=======
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
        function = KernelFunctionFromMethod(
            method=invoke,
            plugin_name="pluginName",
        )

        kernel.add_plugin(KernelPlugin(name="test", functions=[function]))
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
>>>>>>> Stashed changes
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< Updated upstream
=======
<<<<<<< div
>>>>>>> main
=======
>>>>>>> origin/main
=======
=======
>>>>>>> Stashed changes
=======
=======
>>>>>>> Stashed changes
>>>>>>> head
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
        function = KernelFunctionFromMethod(
            method=invoke,
            plugin_name="pluginName",
        )

        kernel.add_plugin(KernelPlugin(name="test", functions=[function]))
=======
        function = KernelFunction(
            function=invoke,
            plugin_name="pluginName",
            function_name="funcName",
            description="",
            parameters=[KernelParameterMetadata(name="arguments", description="", default_value=None, required=True)],
            return_parameter=None,
            is_prompt=False,
        )

        dkp = KernelPlugin(name="test", functions=[function])
        kernel = Kernel()
        kernel.plugins.add(dkp)
>>>>>>> ms/small_fixes
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
>>>>>>> origin/main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< div
>>>>>>> main
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> origin/main
>>>>>>> head

        # Create a CodeBlock with the FunctionIdBlock and VarBlock,
        # and render it with the context
        code_block = CodeBlock(
            tokens=[func_id, var_block],
            content="",
        )
        result = await code_block.render_code(kernel, arguments)

        # Check that the result matches the custom variable value
        assert result == VAR_VALUE
        # Check that the canary value matches the custom variable value
        assert canary == VAR_VALUE

    @mark.asyncio
    async def test_it_invokes_function_with_custom_value(self, kernel: Kernel):
        # Define a value to be used in the test
        VALUE = "value"

        # Create a FunctionIdBlock with the function name and a ValBlock with the value
        func_id = FunctionIdBlock(content="test.funcName")
        val_block = ValBlock(content=f"'{VALUE}'")

        # Set up a canary variable to track changes in the context input
        canary = ""

        # Define the function to be invoked, which modifies the canary variable
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
        @kernel_function(name="funcName")
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
        @kernel_function(name="funcName")
=======
=======
<<<<<<< div
>>>>>>> main
=======
>>>>>>> origin/main
=======
<<<<<<< main
        @kernel_function(name="funcName")
=======
>>>>>>> Stashed changes
=======
<<<<<<< main
        @kernel_function(name="funcName")
=======
>>>>>>> Stashed changes
>>>>>>> head
<<<<<<< main
        @kernel_function(name="funcName")
=======
>>>>>>> ms/small_fixes
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
>>>>>>> origin/main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< div
>>>>>>> main
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> origin/main
>>>>>>> head
        def invoke(arguments):
            nonlocal canary
            canary = arguments["input"]
            return arguments["input"]

        # Create an KernelFunction with the invoke function as its delegate
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
        function = KernelFunctionFromMethod(
            method=invoke,
            plugin_name="pluginName",
        )

        kernel.add_plugin(KernelPlugin(name="test", functions=[function]))
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
=======
>>>>>>> origin/main
=======
=======
>>>>>>> Stashed changes
=======
=======
<<<<<<< div
>>>>>>> main
=======
>>>>>>> Stashed changes
>>>>>>> head
<<<<<<< main
        function = KernelFunctionFromMethod(
            method=invoke,
            plugin_name="pluginName",
        )

        kernel.add_plugin(KernelPlugin(name="test", functions=[function]))
=======
        function = KernelFunction(
            function=invoke,
            plugin_name="pluginName",
            function_name="funcName",
            description="",
            parameters=[KernelParameterMetadata(name="arguments", description="", default_value=None, required=True)],
            return_parameter=None,
            is_prompt=False,
        )

        dkp = KernelPlugin(name="test", functions=[function])
        kernel = Kernel()
        kernel.plugins.add(dkp)
>>>>>>> ms/small_fixes
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
>>>>>>> origin/main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< div
>>>>>>> main
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> origin/main
>>>>>>> head

        # Create a CodeBlock with the FunctionIdBlock and ValBlock,
        # and render it with the context
        code_block = CodeBlock(
            tokens=[func_id, val_block],
            content="",
        )
        result = await code_block.render_code(kernel, KernelArguments(input="value"))

        # Check that the result matches the value
        assert str(result) == VALUE
        # Check that the canary value matches the value
        assert canary == VALUE

    @mark.asyncio
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
    async def test_it_invokes_function_with_multiple_arguments(self, kernel: Kernel):
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
    async def test_it_invokes_function_with_multiple_arguments(self, kernel: Kernel):
=======
=======
<<<<<<< div
>>>>>>> main
=======
>>>>>>> origin/main
=======
<<<<<<< main
    async def test_it_invokes_function_with_multiple_arguments(self, kernel: Kernel):
=======
>>>>>>> Stashed changes
=======
<<<<<<< main
    async def test_it_invokes_function_with_multiple_arguments(self, kernel: Kernel):
=======
>>>>>>> Stashed changes
>>>>>>> head
<<<<<<< main
    async def test_it_invokes_function_with_multiple_arguments(self, kernel: Kernel):
=======
    async def test_it_invokes_function_with_multiple_arguments(self):
>>>>>>> ms/small_fixes
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
>>>>>>> origin/main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< div
>>>>>>> main
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> origin/main
>>>>>>> head
        # Define a value to be used in the test
        VALUE = "value"

        code_block = CodeBlock(
            content=" ",
            tokens=[
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
=======
<<<<<<< main
>>>>>>> origin/main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< main
<<<<<<< div
>>>>>>> main
=======
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> origin/main
>>>>>>> head
                FunctionIdBlock(
                    content="test.funcName",
                    plugin_name="test",
                    function_name="funcName",
                    validated=True,
                ),
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
=======
=======
                FunctionIdBlock(content="test.funcName", plugin_name="test", function_name="funcName", validated=True),
>>>>>>> ms/small_fixes
>>>>>>> origin/main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
=======
>>>>>>> Stashed changes
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
=======
                FunctionIdBlock(content="test.funcName", plugin_name="test", function_name="funcName", validated=True),
>>>>>>> ms/small_fixes
>>>>>>> origin/main
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< div
=======
=======
                FunctionIdBlock(content="test.funcName", plugin_name="test", function_name="funcName", validated=True),
>>>>>>> ms/small_fixes
>>>>>>> main
=======
>>>>>>> head
                ValBlock(content=f'"{VALUE}"'),
                NamedArgBlock(content="arg1=$arg1"),
                NamedArgBlock(content='arg2="arg2"'),
            ],
        )
        # Set up a canary variable to track changes in the context input
        canary = ""

        # Define the function to be invoked, which modifies the canary variable
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
        @kernel_function(name="funcName")
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
        @kernel_function(name="funcName")
=======
=======
<<<<<<< div
>>>>>>> main
=======
>>>>>>> origin/main
=======
<<<<<<< main
        @kernel_function(name="funcName")
=======
>>>>>>> Stashed changes
=======
<<<<<<< main
        @kernel_function(name="funcName")
=======
>>>>>>> Stashed changes
>>>>>>> head
<<<<<<< main
        @kernel_function(name="funcName")
=======
>>>>>>> ms/small_fixes
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
>>>>>>> origin/main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< div
>>>>>>> main
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> origin/main
>>>>>>> head
        def invoke(input, arg1, arg2):
            nonlocal canary
            canary = f"{input} {arg1} {arg2}"
            return input

        # Create an KernelFunction with the invoke function as its delegate
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
=======
<<<<<<< main
>>>>>>> origin/main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< main
<<<<<<< div
>>>>>>> main
=======
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> origin/main
>>>>>>> head
        function = KernelFunctionFromMethod(
            method=invoke,
            plugin_name="pluginName",
        )

        kernel.add_plugin(KernelPlugin(name="test", functions=[function]))
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
=======
<<<<<<< div
=======
>>>>>>> main
=======
>>>>>>> head
=======
>>>>>>> origin/main
=======
=======
<<<<<<< main
=======
=======
>>>>>>> Stashed changes
=======
<<<<<<< main
=======
=======
>>>>>>> Stashed changes
        function = KernelFunction(
            function=invoke,
            plugin_name="pluginName",
            function_name="funcName",
            description="",
            parameters=[
                KernelParameterMetadata(name="input", description="", default_value=None, required=True),
                KernelParameterMetadata(name="arg1", description="", default_value=None, required=True),
                KernelParameterMetadata(name="arg2", description="", default_value=None, required=True),
            ],
            return_parameter=None,
            is_prompt=False,
        )

        dkp = KernelPlugin(name="test", functions=[function])
        kernel = Kernel()
        kernel.plugins.add(dkp)
>>>>>>> ms/small_fixes
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
>>>>>>> origin/main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< div
>>>>>>> main
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> origin/main
>>>>>>> head

        # Create a CodeBlock with the FunctionIdBlock and ValBlock,
        # and render it with the context
        result = await code_block.render_code(kernel, KernelArguments(arg1="arg1"))

        # Check that the result matches the value
        assert str(result) == VALUE
        # Check that the canary value matches the value
        assert canary == f"{VALUE} arg1 arg2"

    @mark.asyncio
<<<<<<< div
<<<<<<< div
=======
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< Updated upstream
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
=======
<<<<<<< main
>>>>>>> origin/main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
>>>>>>> Stashed changes
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> origin/main
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< div
=======
<<<<<<< main
>>>>>>> main
=======
>>>>>>> head
    async def test_it_invokes_function_with_only_named_arguments(self, kernel: Kernel):
        code_block = CodeBlock(
            content=" ",
            tokens=[
                FunctionIdBlock(
                    content="test.funcName",
                    plugin_name="test",
                    function_name="funcName",
                ),
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
=======
>>>>>>> Stashed changes
=======
<<<<<<< div
=======
>>>>>>> main
=======
>>>>>>> head
=======
>>>>>>> origin/main
=======
=======
<<<<<<< main
=======
=======
>>>>>>> Stashed changes
=======
<<<<<<< Updated upstream
=======
>>>>>>> Stashed changes
>>>>>>> Stashed changes
<<<<<<< main
=======
=======
>>>>>>> Stashed changes
    async def test_it_invokes_function_with_only_named_arguments(self):
        code_block = CodeBlock(
            content=" ",
            tokens=[
                FunctionIdBlock(content="test.funcName", plugin_name="test", function_name="funcName"),
>>>>>>> ms/small_fixes
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
>>>>>>> origin/main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< div
>>>>>>> main
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> origin/main
>>>>>>> head
                NamedArgBlock(content="arg1=$arg1"),
                NamedArgBlock(content='arg2="arg2"'),
            ],
        )
        # Set up a canary variable to track changes in the context input
        canary = ""

        # Define the function to be invoked, which modifies the canary variable
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
        @kernel_function(name="funcName")
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
        @kernel_function(name="funcName")
=======
=======
<<<<<<< div
>>>>>>> main
=======
>>>>>>> origin/main
=======
<<<<<<< main
        @kernel_function(name="funcName")
=======
>>>>>>> Stashed changes
=======
<<<<<<< main
        @kernel_function(name="funcName")
=======
>>>>>>> Stashed changes
>>>>>>> head
<<<<<<< main
        @kernel_function(name="funcName")
=======
>>>>>>> ms/small_fixes
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
>>>>>>> origin/main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< div
>>>>>>> main
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> origin/main
>>>>>>> head
        def invoke(arg1, arg2):
            nonlocal canary
            canary = f"{arg1} {arg2}"
            return arg1

        # Create an KernelFunction with the invoke function as its delegate
<<<<<<< div
<<<<<<< div
=======
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
=======
<<<<<<< main
>>>>>>> origin/main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> origin/main
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< div
=======
<<<<<<< main
>>>>>>> main
=======
>>>>>>> head
        function = KernelFunctionFromMethod(
            method=invoke,
            plugin_name="pluginName",
        )

        kernel.add_plugin(KernelPlugin(name="test", functions=[function]))
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
=======
<<<<<<< div
=======
>>>>>>> main
=======
>>>>>>> head
=======
>>>>>>> origin/main
=======
=======
<<<<<<< main
=======
=======
>>>>>>> Stashed changes
=======
<<<<<<< main
=======
=======
>>>>>>> Stashed changes
        function = KernelFunction(
            function=invoke,
            plugin_name="pluginName",
            function_name="funcName",
            description="",
            parameters=[
                KernelParameterMetadata(name="arg1", description="", default_value=None, required=True),
                KernelParameterMetadata(name="arg2", description="", default_value=None, required=True),
            ],
            return_parameter=None,
            is_prompt=False,
        )

        dkp = KernelPlugin(name="test", functions=[function])
        kernel = Kernel()
        kernel.plugins.add(dkp)
>>>>>>> ms/small_fixes
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
>>>>>>> origin/main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< div
>>>>>>> main
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> origin/main
>>>>>>> head

        # Create a CodeBlock with the FunctionIdBlock and ValBlock,
        # and render it with the context
        result = await code_block.render_code(kernel, KernelArguments(arg1="arg1"))

        # Check that the result matches the value
        assert str(result) == "arg1"
        # Check that the canary value matches the value
        assert canary == "arg1 arg2"

    @mark.asyncio
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
=======
<<<<<<< main
>>>>>>> origin/main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< main
<<<<<<< div
>>>>>>> main
=======
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> origin/main
>>>>>>> head
    async def test_it_fails_on_function_without_args(self, kernel: Kernel):
        code_block = CodeBlock(
            content=" ",
            tokens=[
                FunctionIdBlock(
                    content="test.funcName",
                    plugin_name="test",
                    function_name="funcName",
                ),
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
=======
<<<<<<< div
=======
>>>>>>> main
=======
>>>>>>> head
=======
>>>>>>> origin/main
=======
=======
<<<<<<< main
=======
=======
>>>>>>> Stashed changes
=======
<<<<<<< Updated upstream
=======
>>>>>>> Stashed changes
>>>>>>> Stashed changes
<<<<<<< main
=======
=======
>>>>>>> Stashed changes
    async def test_it_fails_on_function_without_args(self):
        code_block = CodeBlock(
            content=" ",
            tokens=[
                FunctionIdBlock(content="test.funcName", plugin_name="test", function_name="funcName"),
>>>>>>> ms/small_fixes
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
>>>>>>> origin/main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< div
>>>>>>> main
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> origin/main
>>>>>>> head
                NamedArgBlock(content="arg1=$arg1"),
                NamedArgBlock(content='arg2="arg2"'),
            ],
        )

<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
        @kernel_function(name="funcName")
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
        @kernel_function(name="funcName")
=======
=======
<<<<<<< div
>>>>>>> main
=======
>>>>>>> origin/main
=======
<<<<<<< main
        @kernel_function(name="funcName")
=======
>>>>>>> Stashed changes
=======
<<<<<<< main
        @kernel_function(name="funcName")
=======
>>>>>>> Stashed changes
>>>>>>> head
<<<<<<< main
        @kernel_function(name="funcName")
=======
>>>>>>> ms/small_fixes
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
>>>>>>> origin/main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< div
>>>>>>> main
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> origin/main
>>>>>>> head
        def invoke():
            return "function without args"

        # Create an KernelFunction with the invoke function as its delegate
<<<<<<< div
<<<<<<< div
=======
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
=======
<<<<<<< main
>>>>>>> origin/main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
=======
>>>>>>> Stashed changes
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> origin/main
=======
>>>>>>> Stashed changes
<<<<<<< div
=======
<<<<<<< main
>>>>>>> main
=======
>>>>>>> head
        function = KernelFunctionFromMethod(
            method=invoke,
            plugin_name="test",
        )

        kernel.add_plugin(KernelPlugin(name="test", functions=[function]))
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
=======
<<<<<<< div
=======
>>>>>>> main
=======
>>>>>>> head
=======
>>>>>>> origin/main
=======
=======
<<<<<<< main
=======
=======
>>>>>>> Stashed changes
=======
<<<<<<< main
=======
=======
>>>>>>> Stashed changes
        function = KernelFunction(
            function=invoke,
            plugin_name="test",
            function_name="funcName",
            description="",
            parameters=[],
            return_parameter=None,
            is_prompt=False,
        )

        dkp = KernelPlugin(name="test", functions=[function])
        kernel = Kernel()
        kernel.plugins.add(dkp)
>>>>>>> ms/small_fixes
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
>>>>>>> origin/main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< div
>>>>>>> main
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> origin/main
>>>>>>> head

        # Create a CodeBlock with the FunctionIdBlock and ValBlock,
        # and render it with the context
        with raises(
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
            CodeBlockRenderException,
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
            CodeBlockRenderException,
=======
=======
<<<<<<< div
>>>>>>> main
=======
>>>>>>> origin/main
=======
<<<<<<< main
            CodeBlockRenderException,
=======
>>>>>>> Stashed changes
=======
<<<<<<< main
            CodeBlockRenderException,
=======
>>>>>>> Stashed changes
>>>>>>> head
<<<<<<< main
            CodeBlockRenderException,
=======
            CodeBlockRenderError,
>>>>>>> ms/small_fixes
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
>>>>>>> origin/main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< div
>>>>>>> main
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> origin/main
>>>>>>> head
            match="Function test.funcName does not take any arguments \
but it is being called in the template with 2 arguments.",
        ):
            await code_block.render_code(kernel, KernelArguments(arg1="arg1"))


@mark.parametrize(
    "token2",
    [
        "",
        "arg2=$arg!2",
        "arg2='va\"l'",
    ],
    ids=[
        "empty",
        "invalid_named_arg",
        "invalid_named_arg_val",
    ],
)
@mark.parametrize(
    "token1",
    [
        "",
        "$var!",
        "\"val'",
        "arg1=$arg!1",
        "arg1='va\"l'",
    ],
    ids=[
        "empty",
        "invalid_var",
        "invalid_val",
        "invalid_named_arg",
        "invalid_named_arg_val",
    ],
)
@mark.parametrize(
    "token0",
    [
        "plugin.func.test",
        "$var!",
        '"va"l"',
    ],
    ids=[
        "invalid_func",
        "invalid_var",
        "invalid_val",
    ],
)
def test_block_validation(token0, token1, token2):
    with raises(
        (
            FunctionIdBlockSyntaxError,
            VarBlockSyntaxError,
            ValBlockSyntaxError,
            NamedArgBlockSyntaxError,
            CodeBlockSyntaxError,
        )
    ):
        CodeBlock(
            content=f"{token0} {token1} {token2}",
        )


@mark.parametrize(
    "token2, token2valid",
    [
        ("", True),
        ("plugin.func", False),
        ("$var", False),
        ('"val"', False),
        ("arg1=$arg1", True),
        ("arg1='val'", True),
    ],
    ids=[
        "empty",
        "func_invalid",
        "invalid_var",
        "invalid_val",
        "valid_named_arg",
        "valid_named_arg_val",
    ],
)
@mark.parametrize(
    "token1, token1valid",
    [
        ("", True),
        ("plugin.func", False),
        ("$var", True),
        ('"val"', True),
        ("arg1=$arg1", True),
        ("arg1='val'", True),
    ],
    ids=[
        "empty",
        "func_invalid",
        "var",
        "val",
        "valid_named_arg",
        "valid_named_arg_val",
    ],
)
@mark.parametrize(
    "token0, token0valid",
    [
        ("func", True),
        ("plugin.func", True),
        ("$var", True),
        ('"val"', True),
        ("arg1=$arg1", False),
        ("arg1='val'", False),
    ],
    ids=[
        "single_name_func",
        "FQN_func",
        "var",
        "val",
        "invalid_named_arg",
        "invalid_named_arg_val",
    ],
)
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
def test_positional_validation(
    token0, token0valid, token1, token1valid, token2, token2valid
):
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< Updated upstream
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
def test_positional_validation(
    token0, token0valid, token1, token1valid, token2, token2valid
):
=======
<<<<<<< div
=======
>>>>>>> main
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
>>>>>>> origin/main
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> head
<<<<<<< main
def test_positional_validation(
    token0, token0valid, token1, token1valid, token2, token2valid
):
=======
def test_positional_validation(token0, token0valid, token1, token1valid, token2, token2valid):
>>>>>>> ms/small_fixes
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
>>>>>>> origin/main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< div
>>>>>>> main
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> origin/main
>>>>>>> head
    if not token1 and not token2valid:
        mark.skipif(f"{token0} {token1} {token2}", reason="Not applicable")
        return
    valid = token0valid and token1valid and token2valid
    if token0 in ["$var", '"val"']:
        valid = True
    content = f"{token0} {token1} {token2}"
    if valid:
        target = CodeBlock(
            content=content,
        )
        assert target.content == content.strip()
    else:
        with raises(CodeBlockTokenError):
            CodeBlock(
                content=content,
            )


@mark.parametrize(
    "case, result",
    [
        (r"{$a", False),
    ],
)
def test_edge_cases(case, result):
    if result:
        target = CodeBlock(
            content=case,
        )
        assert target.content == case
    else:
        with raises(FunctionIdBlockSyntaxError):
            CodeBlock(
                content=case,
            )


def test_no_tokens():
    with raises(CodeBlockTokenError):
        CodeBlock(content="", tokens=[])
