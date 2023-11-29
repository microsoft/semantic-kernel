// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Services;
using Microsoft.SemanticKernel.TemplateEngine.Blocks;
using Moq;
using Xunit;

namespace SemanticKernel.UnitTests.TemplateEngine.Blocks;

public class CodeBlockTests
{
    private readonly ILoggerFactory _logger = NullLoggerFactory.Instance;
    private readonly Kernel _kernel = new(new Mock<IAIServiceProvider>().Object);

    [Fact]
    public async Task ItThrowsIfAFunctionDoesntExistAsync()
    {
        // Arrange
        var arguments = new Dictionary<string, string>();
        var target = new CodeBlock("functionName", this._logger);

        // Act & Assert
        await Assert.ThrowsAsync<KeyNotFoundException>(() => target.RenderCodeAsync(this._kernel, arguments));
    }

    [Fact]
    public async Task ItThrowsIfAFunctionCallThrowsAsync()
    {
        // Arrange
        var arguments = new Dictionary<string, string>();

        static void method() => throw new FormatException("error");
        var function = KernelFunctionFactory.CreateFromMethod(method, "function", "description");

        this._kernel.Plugins.Add(new KernelPlugin("plugin", new[] { function }));

        var target = new CodeBlock("plugin.function", this._logger);

        // Act & Assert
        await Assert.ThrowsAsync<FormatException>(() => target.RenderCodeAsync(this._kernel, arguments));
    }

    [Fact]
    public void ItHasTheCorrectType()
    {
        // Act
        var target = new CodeBlock("", NullLoggerFactory.Instance);

        // Assert
        Assert.Equal(BlockTypes.Code, target.Type);
    }

    [Fact]
    public void ItTrimsSpaces()
    {
        // Act + Assert
        Assert.Equal("aa", new CodeBlock("  aa  ", NullLoggerFactory.Instance).Content);
    }

    [Fact]
    public void ItChecksValidityOfInternalBlocks()
    {
        // Arrange
        var validBlock1 = new FunctionIdBlock("x");
        var validBlock2 = new ValBlock("''");
        var invalidBlock = new VarBlock("");

        // Act
        var codeBlock1 = new CodeBlock(new List<Block> { validBlock1, validBlock2 }, "", NullLoggerFactory.Instance);
        var codeBlock2 = new CodeBlock(new List<Block> { validBlock1, invalidBlock }, "", NullLoggerFactory.Instance);

        // Assert
        Assert.True(codeBlock1.IsValid(out _));
        Assert.False(codeBlock2.IsValid(out _));
    }

    [Fact]
    public void ItRequiresAValidFunctionCall()
    {
        // Arrange
        var funcId = new FunctionIdBlock("funcName");
        var valBlock = new ValBlock("'value'");
        var varBlock = new VarBlock("$var");
        var namedArgBlock = new NamedArgBlock("varName='foo'");

        // Act
        var codeBlock1 = new CodeBlock(new List<Block> { funcId, valBlock }, "", NullLoggerFactory.Instance);
        var codeBlock2 = new CodeBlock(new List<Block> { funcId, varBlock }, "", NullLoggerFactory.Instance);
        var codeBlock3 = new CodeBlock(new List<Block> { funcId, funcId }, "", NullLoggerFactory.Instance);
        var codeBlock4 = new CodeBlock(new List<Block> { funcId, varBlock, varBlock }, "", NullLoggerFactory.Instance);
        var codeBlock5 = new CodeBlock(new List<Block> { funcId, varBlock, namedArgBlock }, "", NullLoggerFactory.Instance);
        var codeBlock6 = new CodeBlock(new List<Block> { varBlock, valBlock }, "", NullLoggerFactory.Instance);
        var codeBlock7 = new CodeBlock(new List<Block> { namedArgBlock }, "", NullLoggerFactory.Instance);

        // Assert
        Assert.True(codeBlock1.IsValid(out _));
        Assert.True(codeBlock2.IsValid(out _));

        // Assert - Can't pass a function to a function
        Assert.False(codeBlock3.IsValid(out var errorMessage3));
        Assert.Equal("The first arg of a function must be a quoted string, variable or named argument", errorMessage3);

        // Assert - Can't pass more than one unnamed param
        Assert.False(codeBlock4.IsValid(out var errorMessage4));
        Assert.Equal("Functions only support named arguments after the first argument. Argument 2 is not named.", errorMessage4);

        // Assert - Can pass one unnamed param and named args
        Assert.True(codeBlock5.IsValid(out var errorMessage5));
        Assert.Empty(errorMessage5);

        // Assert - Can't use > 1 block if not a function call
        Assert.False(codeBlock6.IsValid(out var errorMessage6));
        Assert.Equal("Unexpected second token found: 'value'", errorMessage6);

        // Assert - Can't use a named argument without a function block
        Assert.False(codeBlock7.IsValid(out var errorMessage7));
        Assert.Equal("Unexpected named argument found. Expected function name first.", errorMessage7);
    }

    [Fact]
    public async Task ItRendersCodeBlockConsistingOfJustAVarBlock1Async()
    {
        // Arrange
        var arguments = new Dictionary<string, string> { ["varName"] = "foo" };

        // Act
        var codeBlock = new CodeBlock("$varName", NullLoggerFactory.Instance);
        var result = await codeBlock.RenderCodeAsync(this._kernel, arguments);

        // Assert
        Assert.Equal("foo", result);
    }

    [Fact]
    public async Task ItRendersCodeBlockConsistingOfJustAVarBlock2Async()
    {
        // Arrange
        var arguments = new Dictionary<string, string> { ["varName"] = "bar" };
        var varBlock = new VarBlock("$varName");

        // Act
        var codeBlock = new CodeBlock(new List<Block> { varBlock }, "", NullLoggerFactory.Instance);
        var result = await codeBlock.RenderCodeAsync(this._kernel, arguments);

        // Assert
        Assert.Equal("bar", result);
    }

    [Fact]
    public async Task ItRendersCodeBlockConsistingOfJustAValBlock1Async()
    {
        // Arrange
        var arguments = new Dictionary<string, string>();

        // Act
        var codeBlock = new CodeBlock("'ciao'", NullLoggerFactory.Instance);
        var result = await codeBlock.RenderCodeAsync(this._kernel, arguments);

        // Assert
        Assert.Equal("ciao", result);
    }

    [Fact]
    public async Task ItRendersCodeBlockConsistingOfJustAValBlock2Async()
    {
        // Arrange
        var arguments = new Dictionary<string, string>();
        var valBlock = new ValBlock("'arrivederci'");

        // Act
        var codeBlock = new CodeBlock(new List<Block> { valBlock }, "", NullLoggerFactory.Instance);
        var result = await codeBlock.RenderCodeAsync(this._kernel, arguments);

        // Assert
        Assert.Equal("arrivederci", result);
    }

    [Fact]
    public async Task ItInvokesFunctionWithCustomVariableAsync()
    {
        // Arrange
        const string Var = "varName";
        const string VarValue = "varValue";

        var arguments = new Dictionary<string, string> { [Var] = VarValue };
        var funcId = new FunctionIdBlock("plugin.function");
        var varBlock = new VarBlock($"${Var}");

        var canary = string.Empty;

        var function = KernelFunctionFactory.CreateFromMethod((string input) =>
        {
            canary = input;
        },
        "function");

        this._kernel.Plugins.Add(new KernelPlugin("plugin", new[] { function }));

        // Act
        var codeBlock = new CodeBlock(new List<Block> { funcId, varBlock }, "", NullLoggerFactory.Instance);
        string result = await codeBlock.RenderCodeAsync(this._kernel, arguments);

        // Assert
        Assert.Empty(result);
        Assert.Equal(VarValue, canary);
    }

    [Fact]
    public async Task ItInvokesFunctionWithCustomValueAsync()
    {
        // Arrange
        const string Value = "value";

        var arguments = new Dictionary<string, string>();
        var funcBlock = new FunctionIdBlock("plugin.function");
        var valBlock = new ValBlock($"'{Value}'");

        var canary = string.Empty;

        var function = KernelFunctionFactory.CreateFromMethod((string input) =>
        {
            canary = input;
        },
        "function");

        this._kernel.Plugins.Add(new KernelPlugin("plugin", new[] { function }));

        // Act
        var codeBlock = new CodeBlock(new List<Block> { funcBlock, valBlock }, "", NullLoggerFactory.Instance);
        string result = await codeBlock.RenderCodeAsync(this._kernel, arguments);

        // Assert
        Assert.Empty(result);
        Assert.Equal(Value, canary);
    }

    [Fact]
    public async Task ItInvokesFunctionWithNamedArgsAsync()
    {
        // Arrange
        const string Value = "value";
        const string FooValue = "bar";
        const string BobValue = "bob's value";

        var arguments = new Dictionary<string, string>();
        arguments["bob"] = BobValue;
        arguments["input"] = Value;

        var funcId = new FunctionIdBlock("plugin.function");
        var namedArgBlock1 = new NamedArgBlock($"foo='{FooValue}'");
        var namedArgBlock2 = new NamedArgBlock("baz=$bob");

        var actualFoo = string.Empty;
        var actualBaz = string.Empty;

        var function = KernelFunctionFactory.CreateFromMethod((string foo, string baz) =>
        {
            actualFoo = foo;
            actualBaz = baz;
        },
        "function");

        this._kernel.Plugins.Add(new KernelPlugin("plugin", new[] { function }));

        // Act
        var codeBlock = new CodeBlock(new List<Block> { funcId, namedArgBlock1, namedArgBlock2 }, "", NullLoggerFactory.Instance);
        string result = await codeBlock.RenderCodeAsync(this._kernel, arguments);

        // Assert
        Assert.Equal(FooValue, actualFoo);
        Assert.Equal(BobValue, actualBaz);
        Assert.Empty(result);
    }
}
