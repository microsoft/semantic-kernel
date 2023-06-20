// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Reflection;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.SkillDefinition;
using Microsoft.SemanticKernel.TemplateEngine;
using Microsoft.SemanticKernel.TemplateEngine.Blocks;
using Moq;
using SemanticKernel.UnitTests.XunitHelpers;
using Xunit;
using Xunit.Abstractions;

namespace SemanticKernel.UnitTests.TemplateEngine;

public sealed class PromptTemplateEngineTests
{
    private readonly PromptTemplateEngine _target;
    private readonly ContextVariables _variables;
    private readonly Mock<IReadOnlySkillCollection> _skills;
    private readonly ITestOutputHelper _logger;

    public PromptTemplateEngineTests(ITestOutputHelper testOutputHelper)
    {
        this._logger = testOutputHelper;
        this._target = new PromptTemplateEngine(TestConsoleLogger.Log);
        this._variables = new ContextVariables(Guid.NewGuid().ToString("X"));
        this._skills = new Mock<IReadOnlySkillCollection>();
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
    public async Task ItRendersCodeUsingInputAsync()
    {
        // Arrange
        string MyFunctionAsync(SKContext cx)
        {
            this._logger.WriteLine("MyFunction call received, input: {0}", cx.Variables.Input);
            return $"F({cx.Variables.Input})";
        }

        ISKFunction func = SKFunction.FromNativeMethod(Method(MyFunctionAsync), this);
        Assert.NotNull(func);

        this._variables.Update("INPUT-BAR");
        var template = "foo-{{function}}-baz";
        {
            ISKFunction? outFunc = func;
            this._skills.Setup(x => x.TryGetFunction("function", out outFunc)).Returns(true);
        }
        this._skills.Setup(x => x.GetFunction("function")).Returns(func);
        var context = this.MockContext();

        // Act
        var result = await this._target.RenderAsync(template, context);

        // Assert
        Assert.Equal("foo-F(INPUT-BAR)-baz", result);
    }

    [Fact]
    public async Task ItRendersCodeUsingVariablesAsync()
    {
        // Arrange
        string MyFunctionAsync(SKContext cx)
        {
            this._logger.WriteLine("MyFunction call received, input: {0}", cx.Variables.Input);
            return $"F({cx.Variables.Input})";
        }

        ISKFunction func = SKFunction.FromNativeMethod(Method(MyFunctionAsync), this);
        Assert.NotNull(func);

        this._variables.Set("myVar", "BAR");
        var template = "foo-{{function $myVar}}-baz";
        {
            ISKFunction? outFunc = func;
            this._skills.Setup(x => x.TryGetFunction("function", out outFunc)).Returns(true);
        }
        this._skills.Setup(x => x.GetFunction("function")).Returns(func);
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
        Task<string> MyFunctionAsync(SKContext cx)
        {
            // Input value should be "BAR" because the variable $myVar is passed in
            this._logger.WriteLine("MyFunction call received, input: {0}", cx.Variables.Input);
            return Task.FromResult(cx.Variables.Input.Value);
        }

        ISKFunction func = SKFunction.FromNativeMethod(Method(MyFunctionAsync), this);
        Assert.NotNull(func);

        this._variables.Set("myVar", "BAR");

        var template = "foo-{{function $myVar}}-baz";
        {
            ISKFunction? outFunc = func;
            this._skills.Setup(x => x.TryGetFunction("function", out outFunc)).Returns(true);
        }
        this._skills.Setup(x => x.GetFunction("function")).Returns(func);
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
            skills: this._skills.Object,
            logger: TestConsoleLogger.Log);
    }
}
