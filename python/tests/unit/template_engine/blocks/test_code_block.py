from pytest import mark, raises

from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.functions.kernel_function import KernelFunction
from semantic_kernel.functions.kernel_parameter_metadata import KernelParameterMetadata
from semantic_kernel.functions.kernel_plugin import KernelPlugin
from semantic_kernel.functions.kernel_plugin_collection import (
    KernelPluginCollection,
)
from semantic_kernel.kernel import Kernel
from semantic_kernel.template_engine.blocks.block_types import BlockTypes
from semantic_kernel.template_engine.blocks.code_block import CodeBlock
from semantic_kernel.template_engine.blocks.function_id_block import FunctionIdBlock
from semantic_kernel.template_engine.blocks.val_block import ValBlock
from semantic_kernel.template_engine.blocks.var_block import VarBlock


class TestCodeBlock:
    def setup_method(self):
        self.kernel = Kernel()

    @mark.asyncio
    async def test_it_throws_if_a_function_doesnt_exist(self):
        target = CodeBlock(
            content="functionName",
        )

        with raises(ValueError):
            await target.render_code(self.kernel, KernelArguments())

    @mark.asyncio
    async def test_it_throws_if_a_function_call_throws(self):
        def invoke():
            raise Exception("error")

        function = KernelFunction(
            function_name="functionName",
            plugin_name="pluginName",
            description="",
            function=invoke,
            parameters=[],
            return_parameter=None,
            is_semantic=False,
        )

        dkp = KernelPlugin(name="test", functions=[function])
        plugins = KernelPluginCollection()
        plugins.add(dkp)
        kernel = Kernel()
        kernel.plugins = plugins

        target = CodeBlock(
            content="functionName",
        )

        with raises(ValueError):
            await target.render_code(kernel, KernelArguments())

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
        valid_block1 = FunctionIdBlock(content="plug.func")

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
        code_block = CodeBlock(
            content="$varName",
        )
        result = await code_block.render_code(self.kernel, KernelArguments(varName="foo"))

        assert result == "foo"

    @mark.asyncio
    async def test_it_renders_code_block_consisting_of_just_a_var_block2(self):
        code_block = CodeBlock(
            tokens=[VarBlock(content="$varName")],
            content="",
        )
        result = await code_block.render_code(self.kernel, KernelArguments(varName="bar"))

        assert result == "bar"

    @mark.asyncio
    async def test_it_renders_code_block_consisting_of_just_a_val_block1(self):
        code_block = CodeBlock(
            content="'ciao'",
        )
        result = await code_block.render_code(self.kernel, KernelArguments())

        assert result == "ciao"

    @mark.asyncio
    async def test_it_renders_code_block_consisting_of_just_a_val_block2(self):
        code_block = CodeBlock(
            tokens=[ValBlock(content="'arrivederci'")],
            content="",
        )
        result = await code_block.render_code(self.kernel, KernelArguments())

        assert result == "arrivederci"

    @mark.asyncio
    async def test_it_invokes_function_cloning_all_variables(self):
        # Set up initial context variables
        arguments = KernelArguments(input="zero", var1="uno", var2="due")

        # Create a FunctionIdBlock with the function name
        func_id = FunctionIdBlock(content="test.funcName")

        # Set up a canary dictionary to track changes in the context variables
        canary = {"input": "", "var1": "", "var2": ""}

        # Define the function to be invoked, which modifies the canary
        # and context variables
        def invoke(arguments: KernelArguments):
            nonlocal canary
            canary["input"] = arguments["input"]
            canary["var1"] = arguments["var1"]
            canary["var2"] = arguments["var2"]

            arguments["input"] = "overridden"
            arguments["var1"] = "overridden"
            arguments["var2"] = "overridden"

        # Create an KernelFunction with the invoke function as its delegate
        function = KernelFunction(
            function_name="funcName",
            plugin_name="pluginName",
            description="",
            function=invoke,
            parameters=[KernelParameterMetadata(name="arguments", description="", default_value=None, required=True)],
            return_parameter=None,
            is_semantic=False,
        )

        dkp = KernelPlugin(name="test", functions=[function])
        kernel = Kernel()
        kernel.plugins.add(dkp)

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
    async def test_it_invokes_function_with_custom_variable(self):
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
        def invoke(arguments):
            nonlocal canary
            canary = arguments["varName"]
            return arguments["varName"]

        # Create an KernelFunction with the invoke function as its delegate
        function = KernelFunction(
            function=invoke,
            plugin_name="pluginName",
            function_name="funcName",
            description="",
            parameters=[KernelParameterMetadata(name="arguments", description="", default_value=None, required=True)],
            return_parameter=None,
            is_semantic=False,
        )

        dkp = KernelPlugin(name="test", functions=[function])
        kernel = Kernel()
        kernel.plugins.add(dkp)

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
    async def test_it_invokes_function_with_custom_value(self):
        # Define a value to be used in the test
        VALUE = "value"

        # Create a FunctionIdBlock with the function name and a ValBlock with the value
        func_id = FunctionIdBlock(content="test.funcName")
        val_block = ValBlock(content=f"'{VALUE}'")

        # Set up a canary variable to track changes in the context input
        canary = ""

        # Define the function to be invoked, which modifies the canary variable
        def invoke(arguments):
            nonlocal canary
            canary = arguments["input"]
            return arguments["input"]

        # Create an KernelFunction with the invoke function as its delegate
        function = KernelFunction(
            function=invoke,
            plugin_name="pluginName",
            function_name="funcName",
            description="",
            parameters=[KernelParameterMetadata(name="arguments", description="", default_value=None, required=True)],
            return_parameter=None,
            is_semantic=False,
        )

        dkp = KernelPlugin(name="test", functions=[function])
        kernel = Kernel()
        kernel.plugins.add(dkp)

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
