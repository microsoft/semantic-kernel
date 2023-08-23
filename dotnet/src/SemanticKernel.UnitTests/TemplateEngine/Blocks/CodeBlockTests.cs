// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel.AI.TextCompletion;
using Microsoft.SemanticKernel.Diagnostics;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.SkillDefinition;
using Microsoft.SemanticKernel.TemplateEngine.Blocks;
using Moq;
using Xunit;

namespace SemanticKernel.UnitTests.TemplateEngine.Blocks;

public class CodeBlockTests
{
    private readonly Mock<IReadOnlySkillCollection> _skills;
    private readonly ILoggerFactory _logger = NullLoggerFactory.Instance;

    public CodeBlockTests()
    {
        this._skills = new Mock<IReadOnlySkillCollection>();
    }

    [Fact]
    public async Task ItThrowsIfAFunctionDoesntExistAsync()
    {
        // Arrange
        var context = new SKContext(skills: this._skills.Object, loggerFactory: this._logger);
        this._skills.Setup(x => x.TryGetFunction("functionName", out It.Ref<ISKFunction?>.IsAny)).Returns(false);
        var target = new CodeBlock("functionName", this._logger);

        // Act & Assert
        await Assert.ThrowsAsync<SKException>(async () => await target.RenderCodeAsync(context));
    }

    [Fact]
    public async Task ItThrowsIfAFunctionCallThrowsAsync()
    {
        // Arrange
        var context = new SKContext(skills: this._skills.Object, loggerFactory: this._logger);
        var function = new Mock<ISKFunction>();
        function
            .Setup(x => x.InvokeAsync(It.IsAny<SKContext>(), It.IsAny<CompleteRequestSettings?>(), It.IsAny<CancellationToken>()))
            .Throws(new RuntimeWrappedException("error"));
        ISKFunction? outFunc = function.Object;
        this._skills.Setup(x => x.TryGetFunction("functionName", out outFunc)).Returns(true);
        this._skills.Setup(x => x.GetFunction("functionName")).Returns(function.Object);
        var target = new CodeBlock("functionName", this._logger);

        // Act & Assert
        await Assert.ThrowsAsync<SKException>(async () => await target.RenderCodeAsync(context));
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

        // Act
        var codeBlock1 = new CodeBlock(new List<Block> { funcId, valBlock }, "", NullLoggerFactory.Instance);
        var codeBlock2 = new CodeBlock(new List<Block> { funcId, varBlock }, "", NullLoggerFactory.Instance);
        var codeBlock3 = new CodeBlock(new List<Block> { funcId, funcId }, "", NullLoggerFactory.Instance);
        var codeBlock4 = new CodeBlock(new List<Block> { funcId, varBlock, varBlock }, "", NullLoggerFactory.Instance);

        // Assert
        Assert.True(codeBlock1.IsValid(out _));
        Assert.True(codeBlock2.IsValid(out _));

        // Assert - Can't pass a function to a function
        Assert.False(codeBlock3.IsValid(out _));

        // Assert - Can't pass more than one param
        Assert.False(codeBlock4.IsValid(out _));
    }

    [Fact]
    public async Task ItRendersCodeBlockConsistingOfJustAVarBlock1Async()
    {
        // Arrange
        var variables = new ContextVariables { ["varName"] = "foo" };
        var context = new SKContext(variables);

        // Act
        var codeBlock = new CodeBlock("$varName", NullLoggerFactory.Instance);
        var result = await codeBlock.RenderCodeAsync(context);

        // Assert
        Assert.Equal("foo", result);
    }

    [Fact]
    public async Task ItRendersCodeBlockConsistingOfJustAVarBlock2Async()
    {
        // Arrange
        var variables = new ContextVariables { ["varName"] = "bar" };
        var context = new SKContext(variables);
        var varBlock = new VarBlock("$varName");

        // Act
        var codeBlock = new CodeBlock(new List<Block> { varBlock }, "", NullLoggerFactory.Instance);
        var result = await codeBlock.RenderCodeAsync(context);

        // Assert
        Assert.Equal("bar", result);
    }

    [Fact]
    public async Task ItRendersCodeBlockConsistingOfJustAValBlock1Async()
    {
        // Arrange
        var context = new SKContext();

        // Act
        var codeBlock = new CodeBlock("'ciao'", NullLoggerFactory.Instance);
        var result = await codeBlock.RenderCodeAsync(context);

        // Assert
        Assert.Equal("ciao", result);
    }

    [Fact]
    public async Task ItRendersCodeBlockConsistingOfJustAValBlock2Async()
    {
        // Arrange
        var context = new SKContext();
        var valBlock = new ValBlock("'arrivederci'");

        // Act
        var codeBlock = new CodeBlock(new List<Block> { valBlock }, "", NullLoggerFactory.Instance);
        var result = await codeBlock.RenderCodeAsync(context);

        // Assert
        Assert.Equal("arrivederci", result);
    }

    [Fact]
    public async Task ItInvokesFunctionCloningAllVariablesAsync()
    {
        // Arrange
        const string Func = "funcName";

        var variables = new ContextVariables { ["input"] = "zero", ["var1"] = "uno", ["var2"] = "due" };
        var context = new SKContext(variables, skills: this._skills.Object);
        var funcId = new FunctionIdBlock(Func);

        var canary0 = string.Empty;
        var canary1 = string.Empty;
        var canary2 = string.Empty;
        var function = new Mock<ISKFunction>();
        function
            .Setup(x => x.InvokeAsync(It.IsAny<SKContext>(), It.IsAny<CompleteRequestSettings?>(), It.IsAny<CancellationToken>()))
            .Callback<SKContext, CompleteRequestSettings?, CancellationToken>((context, _, _) =>
            {
                canary0 = context!.Variables["input"];
                canary1 = context.Variables["var1"];
                canary2 = context.Variables["var2"];

                context.Variables["input"] = "overridden";
                context.Variables["var1"] = "overridden";
                context.Variables["var2"] = "overridden";
            })
            .ReturnsAsync((SKContext inputcontext, CompleteRequestSettings _, CancellationToken _) => inputcontext);

        ISKFunction? outFunc = function.Object;
        this._skills.Setup(x => x.TryGetFunction(Func, out outFunc)).Returns(true);
        this._skills.Setup(x => x.GetFunction(Func)).Returns(function.Object);

        // Act
        var codeBlock = new CodeBlock(new List<Block> { funcId }, "", NullLoggerFactory.Instance);
        string result = await codeBlock.RenderCodeAsync(context);

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
        const string Func = "funcName";
        const string Var = "varName";
        const string VarValue = "varValue";

        var variables = new ContextVariables { [Var] = VarValue };
        var context = new SKContext(variables, skills: this._skills.Object);
        var funcId = new FunctionIdBlock(Func);
        var varBlock = new VarBlock($"${Var}");

        var canary = string.Empty;
        var function = new Mock<ISKFunction>();
        function
            .Setup(x => x.InvokeAsync(It.IsAny<SKContext>(), It.IsAny<CompleteRequestSettings?>(), It.IsAny<CancellationToken>()))
            .Callback<SKContext, CompleteRequestSettings?, CancellationToken>((context, _, _) =>
            {
                canary = context!.Variables["input"];
            })
            .ReturnsAsync((SKContext inputcontext, CompleteRequestSettings _, CancellationToken _) => inputcontext);

        ISKFunction? outFunc = function.Object;
        this._skills.Setup(x => x.TryGetFunction(Func, out outFunc)).Returns(true);
        this._skills.Setup(x => x.GetFunction(Func)).Returns(function.Object);

        // Act
        var codeBlock = new CodeBlock(new List<Block> { funcId, varBlock }, "", NullLoggerFactory.Instance);
        string result = await codeBlock.RenderCodeAsync(context);

        // Assert
        Assert.Equal(VarValue, result);
        Assert.Equal(VarValue, canary);
    }

    [Fact]
    public async Task ItInvokesFunctionWithCustomValueAsync()
    {
        // Arrange
        const string Func = "funcName";
        const string Value = "value";

        var context = new SKContext(skills: this._skills.Object);
        var funcId = new FunctionIdBlock(Func);
        var valBlock = new ValBlock($"'{Value}'");

        var canary = string.Empty;
        var function = new Mock<ISKFunction>();
        function
            .Setup(x => x.InvokeAsync(It.IsAny<SKContext>(), It.IsAny<CompleteRequestSettings?>(), It.IsAny<CancellationToken>()))
            .Callback<SKContext, CompleteRequestSettings?, CancellationToken>((context, _, _) =>
            {
                canary = context!.Variables["input"];
            })
            .ReturnsAsync((SKContext inputcontext, CompleteRequestSettings _, CancellationToken _) => inputcontext);

        ISKFunction? outFunc = function.Object;
        this._skills.Setup(x => x.TryGetFunction(Func, out outFunc)).Returns(true);
        this._skills.Setup(x => x.GetFunction(Func)).Returns(function.Object);

        // Act
        var codeBlock = new CodeBlock(new List<Block> { funcId, valBlock }, "", NullLoggerFactory.Instance);
        string result = await codeBlock.RenderCodeAsync(context);

        // Assert
        Assert.Equal(Value, result);
        Assert.Equal(Value, canary);
    }
}
