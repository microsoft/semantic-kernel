// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.TemplateEngine.Blocks;
using Microsoft.SemanticKernel.TextGeneration;
using Moq;
using Xunit;

namespace SemanticKernel.UnitTests.TemplateEngine.Blocks;

public class CodeBlockTests
{
    private readonly Kernel _kernel = new();

    [Fact]
    public async Task ItThrowsIfAFunctionDoesntExistAsync()
    {
        // Arrange
        var target = new CodeBlock("functionName");

        // Act & Assert
        await Assert.ThrowsAsync<KeyNotFoundException>(async () => await target.RenderCodeAsync(this._kernel));
    }

    [Fact]
    public async Task ItThrowsIfAFunctionCallThrowsAsync()
    {
        // Arrange
        static void method() => throw new FormatException("error");
        var function = KernelFunctionFactory.CreateFromMethod(method, "function", "description");

        this._kernel.Plugins.Add(KernelPluginFactory.CreateFromFunctions("plugin", "description", new[] { function }));

        var target = new CodeBlock("plugin.function");

        // Act & Assert
        await Assert.ThrowsAsync<FormatException>(async () => await target.RenderCodeAsync(this._kernel));
    }

    [Fact]
    public void ItHasTheCorrectType()
    {
        // Act
        var target = new CodeBlock("");

        // Assert
        Assert.Equal(BlockTypes.Code, target.Type);
    }

    [Fact]
    public void ItTrimsSpaces()
    {
        // Act + Assert
        Assert.Equal("aa", new CodeBlock("  aa  ").Content);
    }

    [Fact]
    public void ItChecksValidityOfInternalBlocks()
    {
        // Arrange
        var validBlock1 = new FunctionIdBlock("x");
        var validBlock2 = new ValBlock("''");
        var invalidBlock = new VarBlock("");

        // Act
        var codeBlock1 = new CodeBlock(new List<Block> { validBlock1, validBlock2 }, "");
        var codeBlock2 = new CodeBlock(new List<Block> { validBlock1, invalidBlock }, "");

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
        var codeBlock1 = new CodeBlock(new List<Block> { funcId, valBlock }, "");
        var codeBlock2 = new CodeBlock(new List<Block> { funcId, varBlock }, "");
        var codeBlock3 = new CodeBlock(new List<Block> { funcId, funcId }, "");
        var codeBlock4 = new CodeBlock(new List<Block> { funcId, varBlock, varBlock }, "");
        var codeBlock5 = new CodeBlock(new List<Block> { funcId, varBlock, namedArgBlock }, "");
        var codeBlock6 = new CodeBlock(new List<Block> { varBlock, valBlock }, "");
        var codeBlock7 = new CodeBlock(new List<Block> { namedArgBlock }, "");

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
        var arguments = new KernelArguments { ["varName"] = "foo" };

        // Act
        var codeBlock = new CodeBlock("$varName");
        var result = await codeBlock.RenderCodeAsync(this._kernel, arguments);

        // Assert
        Assert.Equal("foo", result);
    }

    [Fact]
    public async Task ItRendersCodeBlockConsistingOfJustAVarBlock2Async()
    {
        // Arrange
        var arguments = new KernelArguments { ["varName"] = "bar" };
        var varBlock = new VarBlock("$varName");

        // Act
        var codeBlock = new CodeBlock(new List<Block> { varBlock }, "");
        var result = await codeBlock.RenderCodeAsync(this._kernel, arguments);

        // Assert
        Assert.Equal("bar", result);
    }

    [Fact]
    public async Task ItRendersCodeBlockConsistingOfJustAValBlock1Async()
    {
        // Arrange
        var codeBlock = new CodeBlock("'ciao'");

        // Act
        var result = await codeBlock.RenderCodeAsync(this._kernel);

        // Assert
        Assert.Equal("ciao", result);
    }

    [Fact]
    public async Task ItRendersCodeBlockConsistingOfJustAValBlock2Async()
    {
        // Arrange
        var valBlock = new ValBlock("'arrivederci'");

        // Act
        var codeBlock = new CodeBlock(new List<Block> { valBlock }, "");
        var result = await codeBlock.RenderCodeAsync(this._kernel);

        // Assert
        Assert.Equal("arrivederci", result);
    }

    [Fact]
    public async Task ItInvokesFunctionWithCustomVariableAsync()
    {
        // Arrange
        const string Var = "varName";
        const string VarValue = "varValue";

        var arguments = new KernelArguments { [Var] = VarValue };
        var funcId = new FunctionIdBlock("plugin.function");
        var varBlock = new VarBlock($"${Var}");

        var canary = string.Empty;

        var function = KernelFunctionFactory.CreateFromMethod((string input) =>
        {
            canary = input;
        },
        "function");

        this._kernel.Plugins.Add(KernelPluginFactory.CreateFromFunctions("plugin", "description", new[] { function }));

        // Act
        var codeBlock = new CodeBlock(new List<Block> { funcId, varBlock }, "");
        var result = await codeBlock.RenderCodeAsync(this._kernel, arguments);

        // Assert
        Assert.Null(result);
        Assert.Equal(VarValue, canary);
    }

    [Fact]
    public async Task ItInvokesFunctionWithCustomValueAsync()
    {
        // Arrange
        const string Value = "value";

        var funcBlock = new FunctionIdBlock("plugin.function");
        var valBlock = new ValBlock($"'{Value}'");

        var canary = string.Empty;

        var function = KernelFunctionFactory.CreateFromMethod((string input) =>
        {
            canary = input;
        },
        "function");

        this._kernel.Plugins.Add(KernelPluginFactory.CreateFromFunctions("plugin", "description", new[] { function }));

        // Act
        var codeBlock = new CodeBlock(new List<Block> { funcBlock, valBlock }, "");
        var result = await codeBlock.RenderCodeAsync(this._kernel);

        // Assert
        Assert.Null(result);
        Assert.Equal(Value, canary);
    }

    [Fact]
    public async Task ItInvokesFunctionWithNamedArgsAsync()
    {
        // Arrange
        const string Value = "value";
        const string FooValue = "bar";
        const string BobValue = "bob's value";

        var arguments = new KernelArguments();
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

        this._kernel.Plugins.Add(KernelPluginFactory.CreateFromFunctions("plugin", "description", new[] { function }));

        // Act
        var codeBlock = new CodeBlock(new List<Block> { funcId, namedArgBlock1, namedArgBlock2 }, "");
        var result = await codeBlock.RenderCodeAsync(this._kernel, arguments);

        // Assert
        Assert.Equal(FooValue, actualFoo);
        Assert.Equal(BobValue, actualBaz);
        Assert.Null(result);
    }

    [Fact]
    public async Task ItReturnsArgumentValueAndTypeAsync()
    {
        // Arrange
        object expectedValue = new();
        object? canary = null;

        var funcId = new FunctionIdBlock("p.f");
        var varBlock = new VarBlock("$var");
        var namedArgBlock = new NamedArgBlock("p1=$a1");

        this._kernel.Plugins.Add(KernelPluginFactory.CreateFromFunctions("p", "description", new[] { KernelFunctionFactory.CreateFromMethod((object p1) =>
        {
            canary = p1;
        }, "f") }));

        // Act
        var functionWithPositionedArgument = new CodeBlock(new List<Block> { funcId, varBlock }, "");
        var functionWithNamedArgument = new CodeBlock(new List<Block> { funcId, namedArgBlock }, "");
        var variable = new CodeBlock(new List<Block> { varBlock }, "");

        // Assert function positional argument passed to the the function with no changes
        await functionWithPositionedArgument.RenderCodeAsync(this._kernel, new() { ["p1"] = expectedValue, ["var"] = expectedValue });
        Assert.Same(expectedValue, canary); // Ensuring that the two variables point to the same object, as there is no other way to verify that the argument has not been transformed from object -> string -> object during the process.

        // Assert function named argument passed to the the function with no changes
        await functionWithNamedArgument.RenderCodeAsync(this._kernel, new() { ["p1"] = expectedValue, ["a1"] = expectedValue });
        Assert.Same(expectedValue, canary);

        // Assert argument assigned to a variable with no changes
        await variable.RenderCodeAsync(this._kernel, new() { ["var"] = expectedValue });
        Assert.Same(expectedValue, canary);
    }

    [Fact]
    public async Task ItDoesNotMutateOriginalArgumentsAsync()
    {
        // Arrange
        const string Value = "value";
        const string FooValue = "bar";
        const string BobValue = "bob's value";

        var arguments = new KernelArguments();
        arguments["bob"] = BobValue;
        arguments["input"] = Value;

        var funcId = new FunctionIdBlock("plugin.function");
        var namedArgBlock1 = new NamedArgBlock($"foo='{FooValue}'");
        var namedArgBlock2 = new NamedArgBlock("baz=$bob");

        var function = KernelFunctionFactory.CreateFromMethod((string foo, string baz) => { }, "function");

        this._kernel.Plugins.Add(KernelPluginFactory.CreateFromFunctions("plugin", "description", new[] { function }));

        // Act
        var codeBlock = new CodeBlock(new List<Block> { funcId, namedArgBlock1, namedArgBlock2 }, "");
        await codeBlock.RenderCodeAsync(this._kernel, arguments);

        // Assert
        Assert.Equal(2, arguments.Count);
    }

    [Theory]
    [InlineData(1)]
    [InlineData(2)]
    public async Task ItThrowsWhenArgumentsAreProvidedToAParameterlessFunctionAsync(int numberOfArguments)
    {
        // Arrange
        const string Value = "value";
        const string FooValue = "foo's value";
        const string BobValue = "bob's value";

        var arguments = new KernelArguments();
        arguments["bob"] = BobValue;
        arguments["input"] = Value;

        var blockList = new List<Block>
        {
            new FunctionIdBlock("plugin.function"),
            new ValBlock($"'{FooValue}'")
        };

        if (numberOfArguments == 2)
        {
            blockList.Add(new NamedArgBlock("foo=$foo"));
        }

        var actualFoo = string.Empty;
        var actualBaz = string.Empty;

        var function = KernelFunctionFactory.CreateFromMethod(() => { }, "function");

        this._kernel.Plugins.Add(KernelPluginFactory.CreateFromFunctions("plugin", "description", new[] { function }));

        // Act
        var codeBlock = new CodeBlock(blockList, "");
        var exception = await Assert.ThrowsAsync<ArgumentException>(async () => await codeBlock.RenderCodeAsync(this._kernel, arguments));
        Assert.Contains($"does not take any arguments but it is being called in the template with {numberOfArguments} arguments.", exception.Message, StringComparison.OrdinalIgnoreCase);
    }

    [Theory]
    [InlineData("x11")]
    [InlineData("firstParameter")]
    [InlineData("anything")]
    public async Task ItCallsPromptFunctionWithPositionalTargetFirstArgumentRegardlessOfNameAsync(string parameterName)
    {
        const string FooValue = "foo's value";
        var mockTextContent = new TextContent("Result");
        var mockTextCompletion = new Mock<ITextGenerationService>();
        mockTextCompletion.Setup(m => m.GetTextContentsAsync(It.IsAny<string>(), It.IsAny<PromptExecutionSettings>(), It.IsAny<Kernel>(), It.IsAny<CancellationToken>())).ReturnsAsync(new List<TextContent> { mockTextContent });

        var builder = Kernel.CreateBuilder();
        builder.Services.AddSingleton<ITextGenerationService>(mockTextCompletion.Object);
        var kernel = builder.Build();

        var blockList = new List<Block>
        {
            new FunctionIdBlock("Plugin1.Function1"),
            new ValBlock($"'{FooValue}'")
        };

        kernel.Plugins.Add(
            KernelPluginFactory.CreateFromFunctions("Plugin1", functions: new[]
                {
                    kernel.CreateFunctionFromPrompt(
                        promptTemplate: $"\"This {{{{${parameterName}}}}}",
                        functionName: "Function1")
                }
            )
        );

        kernel.PromptRendering += (object? sender, PromptRenderingEventArgs e) =>
        {
            Assert.Equal(FooValue, e.Arguments[parameterName]);
        };

        kernel.FunctionInvoking += (object? sender, FunctionInvokingEventArgs e) =>
        {
            Assert.Equal(FooValue, e.Arguments[parameterName]);
        };

        var codeBlock = new CodeBlock(blockList, "");
        await codeBlock.RenderCodeAsync(kernel);
    }

    [Fact]
    public async Task ItCallsPromptFunctionMatchArgumentWithNamedArgsAsync()
    {
        const string FooValue = "foo's value";
        var mockTextContent = new TextContent("Result");
        var mockTextCompletion = new Mock<ITextGenerationService>();
        mockTextCompletion.Setup(m => m.GetTextContentsAsync(It.IsAny<string>(), It.IsAny<PromptExecutionSettings>(), It.IsAny<Kernel>(), It.IsAny<CancellationToken>())).ReturnsAsync(new List<TextContent> { mockTextContent });

        var builder = Kernel.CreateBuilder();
        builder.Services.AddSingleton<ITextGenerationService>(mockTextCompletion.Object);
        var kernel = builder.Build();

        var arguments = new KernelArguments();
        arguments["foo"] = FooValue;

        var blockList = new List<Block>
        {
            new FunctionIdBlock("Plugin1.Function1"),
            new NamedArgBlock("x11=$foo"),
            new NamedArgBlock("x12='new'") // Extra parameters are ignored
        };

        kernel.Plugins.Add(
            KernelPluginFactory.CreateFromFunctions("Plugin1", functions: new[]
                {
                    kernel.CreateFunctionFromPrompt(
                        promptTemplate: "\"This {{$x11}}",
                        functionName: "Function1")
                }
            )
        );

        kernel.PromptRendering += (object? sender, PromptRenderingEventArgs e) =>
        {
            Assert.Equal(FooValue, e.Arguments["foo"]);
            Assert.Equal(FooValue, e.Arguments["x11"]);
        };

        kernel.FunctionInvoking += (object? sender, FunctionInvokingEventArgs e) =>
        {
            Assert.Equal(FooValue, e.Arguments["foo"]);
            Assert.Equal(FooValue, e.Arguments["x11"]);
        };

        var codeBlock = new CodeBlock(blockList, "");
        await codeBlock.RenderCodeAsync(kernel, arguments);
    }

    [Fact]
    public async Task ItThrowsWhenArgumentsAreAmbiguousAsync()
    {
        // Arrange
        const string Value = "value";
        const string FooValue = "foo's value";
        const string BobValue = "bob's value";

        var arguments = new KernelArguments();
        arguments["bob"] = BobValue;
        arguments["input"] = Value;

        var funcId = new FunctionIdBlock("plugin.function");
        var namedArgBlock1 = new ValBlock($"'{FooValue}'");
        var namedArgBlock2 = new NamedArgBlock("foo=$foo");

        var actualFoo = string.Empty;
        var actualBaz = string.Empty;

        var function = KernelFunctionFactory.CreateFromMethod((string foo, string baz) =>
        {
            actualFoo = foo;
            actualBaz = baz;
        },
        "function");

        this._kernel.Plugins.Add(KernelPluginFactory.CreateFromFunctions("plugin", "description", new[] { function }));

        // Act
        var codeBlock = new CodeBlock(new List<Block> { funcId, namedArgBlock1, namedArgBlock2 }, "");
        var exception = await Assert.ThrowsAsync<ArgumentException>(async () => await codeBlock.RenderCodeAsync(this._kernel, arguments));
        Assert.Contains(FooValue, exception.Message, StringComparison.OrdinalIgnoreCase);
    }
}
