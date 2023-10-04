// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Globalization;
using System.Reflection;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Diagnostics;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.TemplateEngine.Prompt;
using Microsoft.SemanticKernel.TemplateEngine.Prompt.Blocks;
using Moq;
using SemanticKernel.Extensions.UnitTests.XunitHelpers;
using Xunit;
using Xunit.Abstractions;

namespace SemanticKernel.Extensions.UnitTests.TemplateEngine.Prompt;

public sealed class PromptTemplateEngineTests
{
    private const string DateFormat = "M/d/yyyy";
    private readonly PromptTemplateEngine _target;
    private readonly ContextVariables _variables;
    private readonly Mock<IReadOnlyFunctionCollection> _functions;
    private readonly ITestOutputHelper _logger;
    private readonly Mock<IKernel> _kernel;
    private readonly Mock<IFunctionRunner> _functionRunner;

    public PromptTemplateEngineTests(ITestOutputHelper testOutputHelper)
    {
        this._logger = testOutputHelper;
        this._target = new PromptTemplateEngine(TestConsoleLogger.LoggerFactory);
        this._variables = new ContextVariables(Guid.NewGuid().ToString("X"));
        this._functions = new Mock<IReadOnlyFunctionCollection>();
        this._kernel = new Mock<IKernel>();
        this._functionRunner = new Mock<IFunctionRunner>();
    }

    [Fact]
    public void ItRendersVariables()
    {
        // Arrange
        var template = "{$x11} This {$a} is {$_a} a {{$x11}} test {{$x11}} " +
                       "template {{foo}}{{bar $a}}{{baz $_a}}{{yay $x11}}{{food a='b' c = $d}}";

        // Act
        var blocks = this._target.ExtractBlocks(template);
        var updatedBlocks = this._target.RenderVariables(blocks, this._variables);

        // Assert
        Assert.Equal(10, blocks.Count);
        Assert.Equal(10, updatedBlocks.Count);

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

        Assert.Equal("food a='b' c = $d", blocks[9].Content);
        Assert.Equal("food a='b' c = $d", updatedBlocks[9].Content);
        Assert.Equal(BlockTypes.Code, blocks[9].Type);
        Assert.Equal(BlockTypes.Code, updatedBlocks[9].Type);

        // Arrange
        this._variables.Set("x11", "x11 value");
        this._variables.Set("a", "a value");
        this._variables.Set("_a", "_a value");
        this._variables.Set("c", "c value");
        this._variables.Set("d", "d value");

        // Act
        blocks = this._target.ExtractBlocks(template);
        updatedBlocks = this._target.RenderVariables(blocks, this._variables);

        // Assert
        Assert.Equal(10, blocks.Count);
        Assert.Equal(10, updatedBlocks.Count);

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

        Assert.Equal("food a='b' c = $d", blocks[9].Content);
        Assert.Equal("food a='b' c = $d", updatedBlocks[9].Content);
        Assert.Equal(BlockTypes.Code, blocks[9].Type);
        Assert.Equal(BlockTypes.Code, updatedBlocks[9].Type);
    }

    [Fact]
    public async Task ItRendersCodeUsingInputAsync()
    {
        // Arrange
        string MyFunctionAsync(SKContext context)
        {
            this._logger.WriteLine("MyFunction call received, input: {0}", context.Variables.Input);
            return $"F({context.Variables.Input})";
        }

        ISKFunction func = SKFunction.FromNativeMethod(Method(MyFunctionAsync), this);
        Assert.NotNull(func);

        this._variables.Update("INPUT-BAR");
        var template = "foo-{{function}}-baz";
        {
            ISKFunction? outFunc = func;
            this._functions.Setup(x => x.TryGetFunction("function", out outFunc)).Returns(true);
        }
        this._functions.Setup(x => x.GetFunction("function")).Returns(func);
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
        string MyFunctionAsync(SKContext context)
        {
            this._logger.WriteLine("MyFunction call received, input: {0}", context.Variables.Input);
            return $"F({context.Variables.Input})";
        }

        ISKFunction func = SKFunction.FromNativeMethod(Method(MyFunctionAsync), this);
        Assert.NotNull(func);

        this._variables.Set("myVar", "BAR");
        var template = "foo-{{function $myVar}}-baz";
        {
            ISKFunction? outFunc = func;
            this._functions.Setup(x => x.TryGetFunction("function", out outFunc)).Returns(true);
        }
        this._functions.Setup(x => x.GetFunction("function")).Returns(func);
        var context = this.MockContext();

        // Act
        var result = await this._target.RenderAsync(template, context);

        // Assert
        Assert.Equal("foo-F(BAR)-baz", result);
    }

    [Fact]
    public async Task ItRendersCodeUsingNamedVariablesAsync()
    {
        // Arrange
        string MyFunctionAsync(
            [Description("Name"), SKName("input")] string name,
            [Description("Age"), SKName("age")] int age,
            [Description("Slogan"), SKName("slogan")] string slogan,
            [Description("Date"), SKName("date")] DateTime date)
        {
            var dateStr = date.ToString(PromptTemplateEngineTests.DateFormat, CultureInfo.InvariantCulture);
            this._logger.WriteLine("MyFunction call received, name: {0}, age: {1}, slogan: {2}, date: {3}", name, age, slogan, date);
            return $"[{dateStr}] {name} ({age}): \"{slogan}\"";
        }

        ISKFunction func = SKFunction.FromNativeMethod(Method(MyFunctionAsync), this);
        Assert.NotNull(func);

        this._variables.Set("input", "Mario");
        this._variables.Set("someDate", "2023-08-25T00:00:00");
        var template = "foo-{{function input=$input age='42' slogan='Let\\'s-a go!' date=$someDate}}-baz";
        {
            ISKFunction? outFunc = func;
            this._functions.Setup(x => x.TryGetFunction("function", out outFunc)).Returns(true);
        }
        this._functions.Setup(x => x.GetFunction("function")).Returns(func);
        var context = this.MockContext();

        // Act
        var result = await this._target.RenderAsync(template, context);

        // Assert
        Assert.Equal("foo-[8/25/2023] Mario (42): \"Let's-a go!\"-baz", result);
    }

    [Fact]
    public async Task ItHandlesSyntaxErrorsAsync()
    {
        // Arrange
        string MyFunctionAsync(
            [Description("Name"), SKName("input")] string name,
            [Description("Age"), SKName("age")] int age,
            [Description("Slogan"), SKName("slogan")] string slogan,
            [Description("Date"), SKName("date")] DateTime date)
        {
            var dateStr = date.ToString(PromptTemplateEngineTests.DateFormat, CultureInfo.InvariantCulture);
            this._logger.WriteLine("MyFunction call received, name: {0}, age: {1}, slogan: {2}, date: {3}", name, age, slogan, date);
            return $"[{dateStr}] {name} ({age}): \"{slogan}\"";
        }

        ISKFunction func = SKFunction.FromNativeMethod(Method(MyFunctionAsync), this);
        Assert.NotNull(func);

        this._variables.Set("input", "Mario");
        this._variables.Set("someDate", "2023-08-25T00:00:00");
        var template = "foo-{{function input=$input age=42 slogan='Let\\'s-a go!' date=$someDate}}-baz";
        {
            ISKFunction? outFunc = func;
            this._functions.Setup(x => x.TryGetFunction("function", out outFunc)).Returns(true);
        }
        this._functions.Setup(x => x.GetFunction("function")).Returns(func);
        var context = this.MockContext();

        // Act
        var result = await Assert.ThrowsAsync<SKException>(() => this._target.RenderAsync(template, context));
        Assert.Equal($"Named argument values need to be prefixed with a quote or {Symbols.VarPrefix}.", result.Message);
    }

    [Fact]
    public async Task ItRendersCodeUsingImplicitInputAndNamedVariablesAsync()
    {
        // Arrange
        string MyFunctionAsync(
            [Description("Input"), SKName("input")] string name,
            [Description("Age"), SKName("age")] int age,
            [Description("Slogan"), SKName("slogan")] string slogan,
            [Description("Date"), SKName("date")] DateTime date)
        {
            this._logger.WriteLine("MyFunction call received, name: {0}, age: {1}, slogan: {2}, date: {3}", name, age, slogan, date);
            var dateStr = date.ToString(PromptTemplateEngineTests.DateFormat, CultureInfo.InvariantCulture);
            return $"[{dateStr}] {name} ({age}): \"{slogan}\"";
        }

        ISKFunction func = SKFunction.FromNativeMethod(Method(MyFunctionAsync), this);
        Assert.NotNull(func);

        this._variables.Set("input", "Mario");
        this._variables.Set("someDate", "2023-08-25T00:00:00");
        var template = "foo-{{function $input age='42' slogan='Let\\'s-a go!' date=$someDate}}-baz";
        {
            ISKFunction? outFunc = func;
            this._functions.Setup(x => x.TryGetFunction("function", out outFunc)).Returns(true);
        }
        this._functions.Setup(x => x.GetFunction("function")).Returns(func);
        var context = this.MockContext();

        // Act
        var result = await this._target.RenderAsync(template, context);

        // Assert
        Assert.Equal("foo-[8/25/2023] Mario (42): \"Let's-a go!\"-baz", result);
    }

    [Fact]
    public async Task ItRendersAsyncCodeUsingVariablesAsync()
    {
        // Arrange
        Task<string> MyFunctionAsync(SKContext context)
        {
            // Input value should be "BAR" because the variable $myVar is passed in
            this._logger.WriteLine("MyFunction call received, input: {0}", context.Variables.Input);
            return Task.FromResult(context.Variables.Input);
        }

        ISKFunction func = SKFunction.FromNativeMethod(Method(MyFunctionAsync), this);
        Assert.NotNull(func);

        this._variables.Set("myVar", "BAR");

        var template = "foo-{{function $myVar}}-baz";
        {
            ISKFunction? outFunc = func;
            this._functions.Setup(x => x.TryGetFunction("function", out outFunc)).Returns(true);
        }
        this._functions.Setup(x => x.GetFunction("function")).Returns(func);
        var context = this.MockContext();

        // Act
        var result = await this._target.RenderAsync(template, context);

        // Assert
        Assert.Equal("foo-BAR-baz", result);
    }

    [Fact]
    public async Task ItRendersAsyncCodeUsingImmutableVariablesAsync()
    {
        // Arrange
        var template = "{{func1}} {{func2}} {{func3 $myVar}}";
        this._variables.Update("BAR");
        this._variables.Set("myVar", "BAZ");

        string MyFunction1Async(SKContext context)
        {
            this._logger.WriteLine("MyFunction1 call received, input: {0}", context.Variables.Input);
            context.Variables.Update("foo");
            return "F(OUTPUT-FOO)";
        }
        string MyFunction2Async(SKContext context)
        {
            // Input value should be "BAR" because the variable $input is immutable in MyFunction1
            this._logger.WriteLine("MyFunction2 call received, input: {0}", context.Variables.Input);
            context.Variables.Set("myVar", "bar");
            return context.Variables.Input;
        }
        string MyFunction3Async(SKContext context)
        {
            // Input value should be "BAZ" because the variable $myVar is immutable in MyFunction2
            this._logger.WriteLine("MyFunction3 call received, input: {0}", context.Variables.Input);
            return context.Variables.TryGetValue("myVar", out string? value) ? value : "";
        }

        var functions = new List<ISKFunction>()
        {
            SKFunction.FromNativeMethod(Method(MyFunction1Async), this, "func1"),
            SKFunction.FromNativeMethod(Method(MyFunction2Async), this, "func2"),
            SKFunction.FromNativeMethod(Method(MyFunction3Async), this, "func3")
        };

        foreach (var func in functions)
        {
            Assert.NotNull(func);
            ISKFunction? outFunc = func;
            this._functions.Setup(x => x.GetFunction(It.Is<string>(s => s == func.PluginName))).Returns(func);
            this._functions.Setup(x => x.TryGetFunction(It.Is<string>(s => s == func.PluginName), out outFunc)).Returns(true);
        }

        // Act
        var result = await this._target.RenderAsync(template, this.MockContext());

        // Assert
        Assert.Equal("F(OUTPUT-FOO) BAR BAZ", result);
    }

    private static MethodInfo Method(Delegate method)
    {
        return method.Method;
    }

    private SKContext MockContext()
    {
        return new SKContext(
            this._functionRunner.Object,
            this._variables,
            this._functions.Object);
    }
}
