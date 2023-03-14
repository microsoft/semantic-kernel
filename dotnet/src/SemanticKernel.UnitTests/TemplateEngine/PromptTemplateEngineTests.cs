// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Reflection;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Memory;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.SkillDefinition;
using Microsoft.SemanticKernel.TemplateEngine;
using Microsoft.SemanticKernel.TemplateEngine.Blocks;
using Moq;
using SemanticKernel.UnitTests.XunitHelpers;
using Xunit;

namespace SemanticKernel.UnitTests.TemplateEngine;

public sealed class PromptTemplateEngineTests
{
    private readonly IPromptTemplateEngine _target;
    private readonly ContextVariables _variables;
    private readonly Mock<IReadOnlySkillCollection> _skills;
    private readonly ILogger _logger;

    public PromptTemplateEngineTests()
    {
        this._logger = ConsoleLogger.Log;
        this._target = new PromptTemplateEngine(this._logger);
        this._variables = new ContextVariables(Guid.NewGuid().ToString("X"));
        this._skills = new Mock<IReadOnlySkillCollection>();
    }

    [Fact]
    public void ItTokenizesEdgeCases1()
    {
        // Arrange
        var template = "}}{{{ {$a}}}} {{b}}x}}";

        // Act
        var blocks = this._target.ExtractBlocks(template, false);

        // Assert
        Assert.Equal(5, blocks.Count);

        Assert.Equal("}}{", blocks[0].Content);
        Assert.Equal(BlockTypes.Text, blocks[0].Type);

        Assert.Equal("{$a", blocks[1].Content);
        Assert.Equal(BlockTypes.Code, blocks[1].Type);

        Assert.Equal("}} ", blocks[2].Content);
        Assert.Equal(BlockTypes.Text, blocks[2].Type);

        Assert.Equal("b", blocks[3].Content);
        Assert.Equal(BlockTypes.Code, blocks[3].Type);

        Assert.Equal("x}}", blocks[4].Content);
        Assert.Equal(BlockTypes.Text, blocks[4].Type);
    }

    [Fact]
    public void ItTokenizesEdgeCases2()
    {
        // Arrange
        var template = "}}{{{{$a}}}} {{b}}$x}}";

        // Act
        var blocks = this._target.ExtractBlocks(template);

        // Assert
        Assert.Equal(5, blocks.Count);

        Assert.Equal("}}{{", blocks[0].Content);
        Assert.Equal(BlockTypes.Text, blocks[0].Type);

        Assert.Equal("$a", blocks[1].Content);
        Assert.Equal(BlockTypes.Variable, blocks[1].Type);

        Assert.Equal("}} ", blocks[2].Content);
        Assert.Equal(BlockTypes.Text, blocks[2].Type);

        Assert.Equal("b", blocks[3].Content);
        Assert.Equal(BlockTypes.Code, blocks[3].Type);

        Assert.Equal("$x}}", blocks[4].Content);
        Assert.Equal(BlockTypes.Text, blocks[4].Type);
    }

    [Fact]
    public void ItTokenizesAClassicPrompt()
    {
        // Arrange
        var template = "this is a {{ $prompt }} with {{$some}} variables " +
                       "and {{function $calls}} that {{ also $use $variables }}";

        // Act
        var blocks = this._target.ExtractBlocks(template, true);

        // Assert
        Assert.Equal(8, blocks.Count);

        Assert.Equal("this is a ", blocks[0].Content);
        Assert.Equal(BlockTypes.Text, blocks[0].Type);

        Assert.Equal("$prompt", blocks[1].Content);
        Assert.Equal(BlockTypes.Variable, blocks[1].Type);

        Assert.Equal(" with ", blocks[2].Content);
        Assert.Equal(BlockTypes.Text, blocks[2].Type);

        Assert.Equal("$some", blocks[3].Content);
        Assert.Equal(BlockTypes.Variable, blocks[3].Type);

        Assert.Equal(" variables and ", blocks[4].Content);
        Assert.Equal(BlockTypes.Text, blocks[4].Type);

        Assert.Equal("function $calls", blocks[5].Content);
        Assert.Equal(BlockTypes.Code, blocks[5].Type);

        Assert.Equal(" that ", blocks[6].Content);
        Assert.Equal(BlockTypes.Text, blocks[6].Type);

        Assert.Equal("also $use $variables", blocks[7].Content);
        Assert.Equal(BlockTypes.Code, blocks[7].Type);
    }

    [Theory]
    [InlineData(null, 1)]
    [InlineData("", 1)]
    [InlineData("}}{{a}} {{b}}x", 5)]
    [InlineData("}}{{ -a}} {{b}}x", 5)]
    [InlineData("}}{{ -a\n}} {{b}}x", 5)]
    [InlineData("}}{{ -a\n} } {{b}}x", 3)]
    public void ItTokenizesTheRightTokenCount(string? template, int blockCount)
    {
        // Act
        var blocks = this._target.ExtractBlocks(template, false);

        // Assert
        Assert.Equal(blockCount, blocks.Count);
    }

    [Fact]
    public void ItRendersVariables()
    {
        // Arrange
        var template = "{$x11} This {$a} is {$_a} a {{$x11}} test {{$x11}} " +
                       "template {{foo}}{{bar $a}}{{baz $_a}}{{yay $x11}}";

        // Act
        var blocks = this._target.ExtractBlocks(template);
        var updatedBlocks = this._target.RenderVariables(blocks, this._variables);

        // Assert
        Assert.Equal(9, blocks.Count);
        Assert.Equal(9, updatedBlocks.Count);

        Assert.Equal("$x11", blocks[1].Content);
        Assert.Equal("", updatedBlocks[1].Content);
        Assert.Equal(BlockTypes.Variable, blocks[1].Type);
        Assert.Equal(BlockTypes.Text, updatedBlocks[1].Type);

        Assert.Equal("$x11", blocks[3].Content);
        Assert.Equal("", updatedBlocks[3].Content);
        Assert.Equal(BlockTypes.Variable, blocks[3].Type);
        Assert.Equal(BlockTypes.Text, updatedBlocks[3].Type);

        Assert.Equal("foo", blocks[5].Content);
        Assert.Equal("foo", updatedBlocks[5].Content);
        Assert.Equal(BlockTypes.Code, blocks[5].Type);
        Assert.Equal(BlockTypes.Code, updatedBlocks[5].Type);

        Assert.Equal("bar $a", blocks[6].Content);
        Assert.Equal("bar $a", updatedBlocks[6].Content);
        Assert.Equal(BlockTypes.Code, blocks[6].Type);
        Assert.Equal(BlockTypes.Code, updatedBlocks[6].Type);

        Assert.Equal("baz $_a", blocks[7].Content);
        Assert.Equal("baz $_a", updatedBlocks[7].Content);
        Assert.Equal(BlockTypes.Code, blocks[7].Type);
        Assert.Equal(BlockTypes.Code, updatedBlocks[7].Type);

        Assert.Equal("yay $x11", blocks[8].Content);
        Assert.Equal("yay $x11", updatedBlocks[8].Content);
        Assert.Equal(BlockTypes.Code, blocks[8].Type);
        Assert.Equal(BlockTypes.Code, updatedBlocks[8].Type);

        // Arrange
        this._variables.Set("x11", "x11 value");
        this._variables.Set("a", "a value");
        this._variables.Set("_a", "_a value");

        // Act
        blocks = this._target.ExtractBlocks(template);
        updatedBlocks = this._target.RenderVariables(blocks, this._variables);

        // Assert
        Assert.Equal(9, blocks.Count);
        Assert.Equal(9, updatedBlocks.Count);

        Assert.Equal("$x11", blocks[1].Content);
        Assert.Equal("x11 value", updatedBlocks[1].Content);
        Assert.Equal(BlockTypes.Variable, blocks[1].Type);
        Assert.Equal(BlockTypes.Text, updatedBlocks[1].Type);

        Assert.Equal("$x11", blocks[3].Content);
        Assert.Equal("x11 value", updatedBlocks[3].Content);
        Assert.Equal(BlockTypes.Variable, blocks[3].Type);
        Assert.Equal(BlockTypes.Text, updatedBlocks[3].Type);

        Assert.Equal("foo", blocks[5].Content);
        Assert.Equal("foo", updatedBlocks[5].Content);
        Assert.Equal(BlockTypes.Code, blocks[5].Type);
        Assert.Equal(BlockTypes.Code, updatedBlocks[5].Type);

        Assert.Equal("bar $a", blocks[6].Content);
        Assert.Equal("bar $a", updatedBlocks[6].Content);
        Assert.Equal(BlockTypes.Code, blocks[6].Type);
        Assert.Equal(BlockTypes.Code, updatedBlocks[6].Type);

        Assert.Equal("baz $_a", blocks[7].Content);
        Assert.Equal("baz $_a", updatedBlocks[7].Content);
        Assert.Equal(BlockTypes.Code, blocks[7].Type);
        Assert.Equal(BlockTypes.Code, updatedBlocks[7].Type);

        Assert.Equal("yay $x11", blocks[8].Content);
        Assert.Equal("yay $x11", updatedBlocks[8].Content);
        Assert.Equal(BlockTypes.Code, blocks[8].Type);
        Assert.Equal(BlockTypes.Code, updatedBlocks[8].Type);
    }

    [Fact]
    public async Task ItRendersCodeUsingInputInstanceAsync()
    {
        // Arrange
        [SKFunction("test")]
        [SKFunctionName("test")]
        string MyFunctionAsync(SKContext cx)
        {
            this._logger.LogTrace("MyFunction call received, input: {0}", cx.Variables.Input);
            return $"F({cx.Variables.Input})";
        }

        var func = SKFunction.FromNativeMethod(Method(MyFunctionAsync), this);
        Assert.NotNull(func);

        this._variables.Update("INPUT-BAR");
        var template = "foo-{{function}}-baz";
        this._skills.Setup(x => x.HasNativeFunction("function")).Returns(true);
        this._skills.Setup(x => x.GetNativeFunction("function")).Returns(func);
        var context = this.MockContext();

        // Act
        var result = await this._target.RenderAsync(template, context);

        // Assert
        Assert.Equal("foo-F(INPUT-BAR)-baz", result);
    }

    [Fact]
    public async Task ItRendersCodeUsingInputStaticAsync()
    {
        // Arrange
        [SKFunction("test")]
        [SKFunctionName("test")]
        static string MyFunctionAsync(SKContext cx)
        {
            ConsoleLogger.Log.LogTrace("MyFunction call received, input: {0}", cx.Variables.Input);
            return $"F({cx.Variables.Input})";
        }

        var func = SKFunction.FromNativeMethod(Method(MyFunctionAsync));
        Assert.NotNull(func);

        this._variables.Update("INPUT-BAR");
        var template = "foo-{{function}}-baz";
        this._skills.Setup(x => x.HasNativeFunction("function")).Returns(true);
        this._skills.Setup(x => x.GetNativeFunction("function")).Returns(func);
        var context = this.MockContext();

        // Act
        var result = await this._target.RenderAsync(template, context);

        // Assert
        Assert.Equal("foo-F(INPUT-BAR)-baz", result);
    }

    [Fact]
    public async Task ItRendersCodeUsingVariablesInstanceAsync()
    {
        // Arrange
        [SKFunction("test")]
        [SKFunctionName("test")]
        string MyFunctionAsync(SKContext cx)
        {
            this._logger.LogTrace("MyFunction call received, input: {0}", cx.Variables.Input);
            return $"F({cx.Variables.Input})";
        }

        var func = SKFunction.FromNativeMethod(Method(MyFunctionAsync), this);
        Assert.NotNull(func);

        this._variables.Set("myVar", "BAR");
        var template = "foo-{{function $myVar}}-baz";
        this._skills.Setup(x => x.HasNativeFunction("function")).Returns(true);
        this._skills.Setup(x => x.GetNativeFunction("function")).Returns(func);
        var context = this.MockContext();

        // Act
        var result = await this._target.RenderAsync(template, context);

        // Assert
        Assert.Equal("foo-F(BAR)-baz", result);
    }

    [Fact]
    public async Task ItRendersCodeUsingVariablesStaticAsync()
    {
        // Arrange
        [SKFunction("test")]
        [SKFunctionName("test")]
        static string MyFunctionAsync(SKContext cx)
        {
            ConsoleLogger.Log.LogTrace("MyFunction call received, input: {0}", cx.Variables.Input);
            return $"F({cx.Variables.Input})";
        }

        var func = SKFunction.FromNativeMethod(Method(MyFunctionAsync));
        Assert.NotNull(func);

        this._variables.Set("myVar", "BAR");
        var template = "foo-{{function $myVar}}-baz";
        this._skills.Setup(x => x.HasNativeFunction("function")).Returns(true);
        this._skills.Setup(x => x.GetNativeFunction("function")).Returns(func);
        var context = this.MockContext();

        // Act
        var result = await this._target.RenderAsync(template, context);

        // Assert
        Assert.Equal("foo-F(BAR)-baz", result);
    }

    [Fact]
    public async Task ItRendersAsyncCodeUsingVariablesAsync()
    {
        // Arrange
        [SKFunction("test")]
        [SKFunctionName("test")]
        Task<string> MyFunctionAsync(SKContext cx)
        {
            // Input value should be "BAR" because the variable $myVar is passed in
            this._logger.LogTrace("MyFunction call received, input: {0}", cx.Variables.Input);
            return Task.FromResult(cx.Variables.Input);
        }

        var func = SKFunction.FromNativeMethod(Method(MyFunctionAsync), this);
        Assert.NotNull(func);

        this._variables.Set("myVar", "BAR");
        var template = "foo-{{function $myVar}}-baz";
        this._skills.Setup(x => x.HasNativeFunction("function")).Returns(true);
        this._skills.Setup(x => x.GetNativeFunction("function")).Returns(func);
        var context = this.MockContext();

        // Act
        var result = await this._target.RenderAsync(template, context);

        // Assert
        Assert.Equal("foo-BAR-baz", result);
    }

    private static MethodInfo Method(Delegate method)
    {
        return method.Method;
    }

    private SKContext MockContext()
    {
        return new SKContext(
            this._variables,
            NullMemory.Instance,
            this._skills.Object,
            this._logger);
    }
}
