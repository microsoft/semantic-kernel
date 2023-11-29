// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.TemplateEngine.Blocks;
using Moq;
using Xunit;

namespace SemanticKernel.UnitTests.TemplateEngine.Blocks;

public class CodeBlockTests
{
    private readonly Kernel _kernel = new(new Mock<IServiceProvider>().Object);

    [Fact]
    public async Task ItThrowsIfAFunctionDoesntExistAsync()
    {
        // Arrange
        var variables = new ContextVariables();
        var target = new CodeBlock("functionName");

        // Act & Assert
        await Assert.ThrowsAsync<KeyNotFoundException>(() => target.RenderCodeAsync(this._kernel, variables));
    }

    [Fact]
    public async Task ItThrowsIfAFunctionCallThrowsAsync()
    {
        // Arrange
        var variables = new ContextVariables();

        static void method() => throw new FormatException("error");
        var function = KernelFunctionFactory.CreateFromMethod(method, "function", "description");

        this._kernel.Plugins.Add(new KernelPlugin("plugin", new[] { function }));

        var target = new CodeBlock("plugin.function");

        // Act & Assert
        await Assert.ThrowsAsync<FormatException>(() => target.RenderCodeAsync(this._kernel, variables));
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
        var variables = new ContextVariables { ["varName"] = "foo" };

        // Act
        var codeBlock = new CodeBlock("$varName");
        var result = await codeBlock.RenderCodeAsync(this._kernel, variables);

        // Assert
        Assert.Equal("foo", result);
    }

    [Fact]
    public async Task ItRendersCodeBlockConsistingOfJustAVarBlock2Async()
    {
        // Arrange
        var variables = new ContextVariables { ["varName"] = "bar" };
        var varBlock = new VarBlock("$varName");

        // Act
        var codeBlock = new CodeBlock(new List<Block> { varBlock }, "");
        var result = await codeBlock.RenderCodeAsync(this._kernel, variables);

        // Assert
        Assert.Equal("bar", result);
    }

    [Fact]
    public async Task ItRendersCodeBlockConsistingOfJustAValBlock1Async()
    {
        // Arrange
        var variables = new ContextVariables();

        // Act
        var codeBlock = new CodeBlock("'ciao'");
        var result = await codeBlock.RenderCodeAsync(this._kernel, variables);

        // Assert
        Assert.Equal("ciao", result);
    }

    [Fact]
    public async Task ItRendersCodeBlockConsistingOfJustAValBlock2Async()
    {
        // Arrange
        var variables = new ContextVariables();
        var valBlock = new ValBlock("'arrivederci'");

        // Act
        var codeBlock = new CodeBlock(new List<Block> { valBlock }, "");
        var result = await codeBlock.RenderCodeAsync(this._kernel, variables);

        // Assert
        Assert.Equal("arrivederci", result);
    }

    [Fact]
    public async Task ItInvokesFunctionCloningAllVariablesAsync()
    {
        // Arrange
        var variables = new ContextVariables { ["input"] = "zero", ["var1"] = "uno", ["var2"] = "due" };
        var funcBlock = new FunctionIdBlock("plugin.function");

        var canary0 = string.Empty;
        var canary1 = string.Empty;
        var canary2 = string.Empty;

        var function = KernelFunctionFactory.CreateFromMethod((ContextVariables localVariables) =>
        {
            canary0 = localVariables["input"];
            canary1 = localVariables["var1"];
            canary2 = localVariables["var2"];

            localVariables["input"] = "overridden";
            localVariables["var1"] = "overridden";
            localVariables["var2"] = "overridden";
        },
        "function");

        this._kernel.Plugins.Add(new KernelPlugin("plugin", new[] { function }));

        // Act
        var codeBlock = new CodeBlock(new List<Block> { funcBlock }, "");
        string result = await codeBlock.RenderCodeAsync(this._kernel, variables);

        // Assert - Values are received
        Assert.Equal("zero", canary0);
        Assert.Equal("uno", canary1);
        Assert.Equal("due", canary2);

        // Assert - Original context is intact
        Assert.Equal("zero", variables["input"]);
        Assert.Equal("uno", variables["var1"]);
        Assert.Equal("due", variables["var2"]);
    }

    [Fact]
    public async Task ItInvokesFunctionWithCustomVariableAsync()
    {
        // Arrange
        const string Var = "varName";
        const string VarValue = "varValue";

        var variables = new ContextVariables { [Var] = VarValue };
        var funcId = new FunctionIdBlock("plugin.function");
        var varBlock = new VarBlock($"${Var}");

        var canary = string.Empty;

        var function = KernelFunctionFactory.CreateFromMethod((ContextVariables localVariables) =>
        {
            canary = localVariables["input"];
        },
        "function");

        this._kernel.Plugins.Add(new KernelPlugin("plugin", new[] { function }));

        // Act
        var codeBlock = new CodeBlock(new List<Block> { funcId, varBlock }, "");
        string result = await codeBlock.RenderCodeAsync(this._kernel, variables);

        // Assert
        Assert.Equal(VarValue, result);
        Assert.Equal(VarValue, canary);
    }

    [Fact]
    public async Task ItInvokesFunctionWithCustomValueAsync()
    {
        // Arrange
        const string Value = "value";

        ContextVariables context = new();
        var funcBlock = new FunctionIdBlock("plugin.function");
        var valBlock = new ValBlock($"'{Value}'");

        var canary = string.Empty;

        var function = KernelFunctionFactory.CreateFromMethod((ContextVariables localVariables) =>
        {
            canary = localVariables["input"];
        },
        "function");

        this._kernel.Plugins.Add(new KernelPlugin("plugin", new[] { function }));

        // Act
        var codeBlock = new CodeBlock(new List<Block> { funcBlock, valBlock }, "");
        string result = await codeBlock.RenderCodeAsync(this._kernel, context);

        // Assert
        Assert.Equal(Value, result);
        Assert.Equal(Value, canary);
    }

    [Fact]
    public async Task ItInvokesFunctionWithNamedArgsAsync()
    {
        // Arrange
        const string Value = "value";
        const string FooValue = "bar";
        const string BobValue = "bob's value";

        var variables = new ContextVariables();
        variables.Set("bob", BobValue);
        variables.Set("input", Value);

        var funcId = new FunctionIdBlock("plugin.function");
        var namedArgBlock1 = new NamedArgBlock($"foo='{FooValue}'");
        var namedArgBlock2 = new NamedArgBlock("baz=$bob");

        var foo = string.Empty;
        var baz = string.Empty;

        var function = KernelFunctionFactory.CreateFromMethod((ContextVariables localVariables) =>
        {
            foo = localVariables["foo"];
            baz = localVariables["baz"];
        },
        "function");

        this._kernel.Plugins.Add(new KernelPlugin("plugin", new[] { function }));

        // Act
        var codeBlock = new CodeBlock(new List<Block> { funcId, namedArgBlock1, namedArgBlock2 }, "");
        string result = await codeBlock.RenderCodeAsync(this._kernel, variables);

        // Assert
        Assert.Equal(FooValue, foo);
        Assert.Equal(BobValue, baz);
        Assert.Equal(Value, result);
    }
}
