from pytest import mark, raises

from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.functions.kernel_function_decorator import kernel_function
from semantic_kernel.functions.kernel_function_from_method import KernelFunctionFromMethod
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


class TestCodeBlockRendering:
    def setup_method(self):
        self.kernel = Kernel()

    @mark.asyncio
    async def test_it_throws_if_a_plugins_are_empty(self):
        target = CodeBlock(
            content="functionName",
        )
        assert target.tokens[0].type == BlockTypes.FUNCTION_ID
        with raises(CodeBlockRenderError, match="Plugin collection not set in kernel"):
            await target.render_code(self.kernel, KernelArguments())

    @mark.asyncio
    async def test_it_throws_if_a_function_doesnt_exist(self):
        target = CodeBlock(
            content="functionName",
        )
        assert target.tokens[0].type == BlockTypes.FUNCTION_ID
        self.kernel.plugins = KernelPluginCollection()
        dkp = KernelPlugin(name="test", functions=[])
        self.kernel.plugins.add(dkp)
        with raises(CodeBlockRenderError, match="Function `functionName` not found"):
            await target.render_code(self.kernel, KernelArguments())

    @mark.asyncio
    async def test_it_throws_if_a_function_call_throws(self):
        @kernel_function(name="funcName")
        def invoke():
            raise Exception("error")

        function = KernelFunctionFromMethod(
            method=invoke,
            plugin_name="pluginName",
        )

        dkp = KernelPlugin(name="test", functions=[function])
        plugins = KernelPluginCollection()
        plugins.add(dkp)
        kernel = Kernel()
        kernel.plugins = plugins

        target = CodeBlock(
            content="functionName",
        )

        with raises(CodeBlockRenderError):
            await target.render_code(kernel, KernelArguments())

    @mark.asyncio
    async def test_it_renders_code_block_consisting_of_just_a_var_block1(self):
        code_block = CodeBlock(
            content="$var",
        )
        result = await code_block.render_code(self.kernel, KernelArguments(var="foo"))

        assert result == "foo"

    @mark.asyncio
    async def test_it_renders_code_block_consisting_of_just_a_val_block1(self):
        code_block = CodeBlock(
            content="'ciao'",
        )
        result = await code_block.render_code(self.kernel, KernelArguments())

        assert result == "ciao"

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
        @kernel_function(name="funcName")
        def invoke(arguments: KernelArguments):
            nonlocal canary
            canary["input"] = arguments["input"]
            canary["var1"] = arguments["var1"]
            canary["var2"] = arguments["var2"]

            arguments["input"] = "overridden"
            arguments["var1"] = "overridden"
            arguments["var2"] = "overridden"

        # Create an KernelFunction with the invoke function as its delegate
        function = KernelFunctionFromMethod(
            method=invoke,
            plugin_name="pluginName",
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
        @kernel_function(name="funcName")
        def invoke(arguments: "KernelArguments"):
            nonlocal canary
            canary = arguments["varName"]
            return arguments["varName"]

        # Create an KernelFunction with the invoke function as its delegate
        function = KernelFunctionFromMethod(
            method=invoke,
            plugin_name="pluginName",
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
        @kernel_function(name="funcName")
        def invoke(arguments):
            nonlocal canary
            canary = arguments["input"]
            return arguments["input"]

        # Create an KernelFunction with the invoke function as its delegate
        function = KernelFunctionFromMethod(
            method=invoke,
            plugin_name="pluginName",
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

    @mark.asyncio
    async def test_it_invokes_function_with_multiple_arguments(self):
        # Define a value to be used in the test
        VALUE = "value"

        code_block = CodeBlock(
            content=" ",
            tokens=[
                FunctionIdBlock(content="test.funcName", plugin_name="test", function_name="funcName", validated=True),
                ValBlock(content=f'"{VALUE}"'),
                NamedArgBlock(content="arg1=$arg1"),
                NamedArgBlock(content='arg2="arg2"'),
            ],
        )
        # Set up a canary variable to track changes in the context input
        canary = ""

        # Define the function to be invoked, which modifies the canary variable
        @kernel_function(name="funcName")
        def invoke(input, arg1, arg2):
            nonlocal canary
            canary = f"{input} {arg1} {arg2}"
            return input

        # Create an KernelFunction with the invoke function as its delegate
        function = KernelFunctionFromMethod(
            method=invoke,
            plugin_name="pluginName",
        )

        dkp = KernelPlugin(name="test", functions=[function])
        kernel = Kernel()
        kernel.plugins.add(dkp)

        # Create a CodeBlock with the FunctionIdBlock and ValBlock,
        # and render it with the context
        result = await code_block.render_code(kernel, KernelArguments(arg1="arg1"))

        # Check that the result matches the value
        assert str(result) == VALUE
        # Check that the canary value matches the value
        assert canary == f"{VALUE} arg1 arg2"

    @mark.asyncio
    async def test_it_invokes_function_with_only_named_arguments(self):
        code_block = CodeBlock(
            content=" ",
            tokens=[
                FunctionIdBlock(content="test.funcName", plugin_name="test", function_name="funcName"),
                NamedArgBlock(content="arg1=$arg1"),
                NamedArgBlock(content='arg2="arg2"'),
            ],
        )
        # Set up a canary variable to track changes in the context input
        canary = ""

        # Define the function to be invoked, which modifies the canary variable
        @kernel_function(name="funcName")
        def invoke(arg1, arg2):
            nonlocal canary
            canary = f"{arg1} {arg2}"
            return arg1

        # Create an KernelFunction with the invoke function as its delegate
        function = KernelFunctionFromMethod(
            method=invoke,
            plugin_name="pluginName",
        )

        dkp = KernelPlugin(name="test", functions=[function])
        kernel = Kernel()
        kernel.plugins.add(dkp)

        # Create a CodeBlock with the FunctionIdBlock and ValBlock,
        # and render it with the context
        result = await code_block.render_code(kernel, KernelArguments(arg1="arg1"))

        # Check that the result matches the value
        assert str(result) == "arg1"
        # Check that the canary value matches the value
        assert canary == "arg1 arg2"

    @mark.asyncio
    async def test_it_fails_on_function_without_args(self):
        code_block = CodeBlock(
            content=" ",
            tokens=[
                FunctionIdBlock(content="test.funcName", plugin_name="test", function_name="funcName"),
                NamedArgBlock(content="arg1=$arg1"),
                NamedArgBlock(content='arg2="arg2"'),
            ],
        )

        @kernel_function(name="funcName")
        def invoke():
            return "function without args"

        # Create an KernelFunction with the invoke function as its delegate
        function = KernelFunctionFromMethod(
            method=invoke,
            plugin_name="test",
        )

        dkp = KernelPlugin(name="test", functions=[function])
        kernel = Kernel()
        kernel.plugins.add(dkp)

        # Create a CodeBlock with the FunctionIdBlock and ValBlock,
        # and render it with the context
        with raises(
            CodeBlockRenderError,
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
def test_positional_validation(token0, token0valid, token1, token1valid, token2, token2valid):
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
