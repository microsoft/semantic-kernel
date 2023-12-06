// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Globalization;
using System.Reflection;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.TemplateEngine.Blocks;
using SemanticKernel.UnitTests.XunitHelpers;
using Xunit;
using Xunit.Abstractions;

namespace SemanticKernel.UnitTests.PromptTemplate;

public sealed class KernelPromptTemplateTests
{
    private const string DateFormat = "M/d/yyyy";
    private readonly KernelPromptTemplateFactory _factory;
    private readonly KernelArguments _arguments;
    private readonly ITestOutputHelper _logger;
    private readonly Kernel _kernel;

    public KernelPromptTemplateTests(ITestOutputHelper testOutputHelper)
    {
        this._logger = testOutputHelper;
        this._factory = new KernelPromptTemplateFactory(TestConsoleLogger.LoggerFactory);
        this._arguments = new KernelArguments(Guid.NewGuid().ToString("X"));
        this._kernel = new Kernel();
    }

    [Fact]
    public async Task ItRendersVariablesValuesAndFunctionsAsync()
    {
        // Arrange
        var template = "This {{$x11}} {{$a}}{{$missing}} test template {{p.bar $b}} and {{p.food c='argument \"c\"' d = $d}}";

        this._kernel.Plugins.Add(new KernelPlugin("p", new[]
        {
            KernelFunctionFactory.CreateFromMethod((string input) => "with function that accepts " + input, "bar"),
            KernelFunctionFactory.CreateFromMethod((string c, string d) => "another one with " + c + d, "food"),
        }));

        var target = (KernelPromptTemplate)this._factory.Create(new PromptTemplateConfig(template));

        // Arrange
        this._arguments["x11"] = "is";
        this._arguments["a"] = "a";
        this._arguments["b"] = "the positional argument 'input'";
        this._arguments["d"] = " and 'd'";

        // Act
        var renderedPrompt = await target.RenderAsync(this._kernel, this._arguments);

        // Assert
        Assert.Equal("This is a test template with function that accepts the positional argument 'input' and another one with argument \"c\" and 'd'", renderedPrompt);
    }

    [Fact]
    public async Task ItThrowsExceptionIfTemplateReferencesFunctionThatIsNotRegisteredAsync()
    {
        // Arrange
        var template = "This is a test template that references not registered function {{foo}}";

        //No plugins/functions are registered with the API - this._kernel.Plugins.Add(new KernelPlugin(...));

        var target = (KernelPromptTemplate)this._factory.Create(new PromptTemplateConfig(template));

        // Act and assert
        await Assert.ThrowsAsync<KeyNotFoundException>(async () => await target.RenderAsync(this._kernel, this._arguments));
    }

    [Fact]
    public async Task ItInsertsEmptyStringIfNoArgumentProvidedForVariableAsync()
    {
        // Arrange
        var template = "This is a test template that references variable that does not have argument {{$foo}}.";

        var target = (KernelPromptTemplate)this._factory.Create(new PromptTemplateConfig(template));

        // Act
        var result = await target.RenderAsync(this._kernel, this._arguments);

        // Assert
        Assert.NotNull(result);
        Assert.Equal("This is a test template that references variable that does not have argument .", result);
    }

    [Fact]
    public async Task ItCallsMethodWithEmptyStringAsArgumentIfNoArgumentProvidedForMethodParameterAsync()
    {
        // Arrange
        string Foo(string input) { return "Result is " + input; }

        this._kernel.Plugins.Add(new KernelPlugin("p", new[] { KernelFunctionFactory.CreateFromMethod(Method(Foo), this, "bar") }));

        var template = "This is a test template that references variable that does not have argument. {{p.bar $foo}}.";

        var target = (KernelPromptTemplate)this._factory.Create(new PromptTemplateConfig(template));

        // Act
        var result = await target.RenderAsync(this._kernel, this._arguments); // rendering without arguments

        // Assert
        Assert.NotNull(result);
        Assert.Equal("This is a test template that references variable that does not have argument. Result is .", result); // There's a space between the last "is" and the full stop.
    }

    [Fact]
    public async Task ItRendersCodeUsingInputAsync()
    {
        // Arrange
        string MyFunctionAsync(string input)
        {
            this._logger.WriteLine("MyFunction call received, input: {0}", input);
            return $"F({input})";
        }

        var func = KernelFunctionFactory.CreateFromMethod(Method(MyFunctionAsync), this, "function");

        this._kernel.Plugins.Add(new KernelPlugin("plugin", new[] { func }));

        this._arguments[KernelArguments.InputParameterName] = "INPUT-BAR";
        var template = "foo-{{plugin.function}}-baz";
        var target = (KernelPromptTemplate)this._factory.Create(new PromptTemplateConfig(template));

        // Act
        var result = await target.RenderAsync(this._kernel, this._arguments);

        // Assert
        Assert.Equal("foo-F(INPUT-BAR)-baz", result);
    }

    [Fact]
    public async Task ItRendersCodeUsingVariablesAsync()
    {
        // Arrange
        string MyFunctionAsync(string input)
        {
            this._logger.WriteLine("MyFunction call received, input: {0}", input);
            return $"F({input})";
        }

        var func = KernelFunctionFactory.CreateFromMethod(Method(MyFunctionAsync), this, "function");

        this._kernel.Plugins.Add(new KernelPlugin("plugin", new[] { func }));

        this._arguments["myVar"] = "BAR";
        var template = "foo-{{plugin.function $myVar}}-baz";
        var target = (KernelPromptTemplate)this._factory.Create(new PromptTemplateConfig(template));

        // Act
        var result = await target.RenderAsync(this._kernel, this._arguments);

        // Assert
        Assert.Equal("foo-F(BAR)-baz", result);
    }

    [Fact]
    public async Task ItRendersCodeUsingNamedVariablesAsync()
    {
        // Arrange
        string MyFunctionAsync(
            [Description("Name")] string input,
            [Description("Age")] int age,
            [Description("Slogan")] string slogan,
            [Description("Date")] DateTime date)
        {
            var dateStr = date.ToString(DateFormat, CultureInfo.InvariantCulture);
            this._logger.WriteLine("MyFunction call received, name: {0}, age: {1}, slogan: {2}, date: {3}", input, age, slogan, date);
            return $"[{dateStr}] {input} ({age}): \"{slogan}\"";
        }

        var func = KernelFunctionFactory.CreateFromMethod(Method(MyFunctionAsync), this, "function");

        this._kernel.Plugins.Add(new KernelPlugin("plugin", new[] { func }));

        this._arguments[KernelArguments.InputParameterName] = "Mario";
        this._arguments["someDate"] = "2023-08-25T00:00:00";
        var template = "foo-{{plugin.function input=$input age='42' slogan='Let\\'s-a go!' date=$someDate}}-baz";
        var target = (KernelPromptTemplate)this._factory.Create(new PromptTemplateConfig(template));

        // Act
        var result = await target.RenderAsync(this._kernel, this._arguments);

        // Assert
        Assert.Equal("foo-[8/25/2023] Mario (42): \"Let's-a go!\"-baz", result);
    }

    [Fact]
    public async Task ItHandlesSyntaxErrorsAsync()
    {
        this._arguments[KernelArguments.InputParameterName] = "Mario";
        this._arguments["someDate"] = "2023-08-25T00:00:00";
        var template = "foo-{{function input=$input age=42 slogan='Let\\'s-a go!' date=$someDate}}-baz";
        var target = (KernelPromptTemplate)this._factory.Create(new PromptTemplateConfig(template));

        // Act
        var result = await Assert.ThrowsAsync<KernelException>(() => target.RenderAsync(this._kernel, this._arguments));
        Assert.Equal($"Named argument values need to be prefixed with a quote or {Symbols.VarPrefix}.", result.Message);
    }

    [Fact]
    public async Task ItRendersCodeUsingImplicitInputAndNamedVariablesAsync()
    {
        // Arrange
        string MyFunctionAsync(
            [Description("Input")] string input,
            [Description("Age")] int age,
            [Description("Slogan")] string slogan,
            [Description("Date")] DateTime date)
        {
            this._logger.WriteLine("MyFunction call received, name: {0}, age: {1}, slogan: {2}, date: {3}", input, age, slogan, date);
            var dateStr = date.ToString(DateFormat, CultureInfo.InvariantCulture);
            return $"[{dateStr}] {input} ({age}): \"{slogan}\"";
        }

        KernelFunction func = KernelFunctionFactory.CreateFromMethod(Method(MyFunctionAsync), this, "function");

        this._kernel.Plugins.Add(new KernelPlugin("plugin", new[] { func }));

        this._arguments[KernelArguments.InputParameterName] = "Mario";
        this._arguments["someDate"] = "2023-08-25T00:00:00";

        var template = "foo-{{plugin.function $input age='42' slogan='Let\\'s-a go!' date=$someDate}}-baz";
        var target = (KernelPromptTemplate)this._factory.Create(new PromptTemplateConfig(template));

        // Act
        var result = await target.RenderAsync(this._kernel, this._arguments);

        // Assert
        Assert.Equal("foo-[8/25/2023] Mario (42): \"Let's-a go!\"-baz", result);
    }

    [Fact]
    public async Task ItRendersAsyncCodeUsingImmutableVariablesAsync()
    {
        // Arrange
        var template = "{{func1}} {{func2}} {{func3 $myVar}}";
        var target = (KernelPromptTemplate)this._factory.Create(new PromptTemplateConfig(template));
        this._arguments[KernelArguments.InputParameterName] = "A";
        this._arguments["myVar"] = "C";

        string MyFunction1Async(string input)
        {
            return input;
        }
        string MyFunction2Async(string input)
        {
            return "B";
        }
        string MyFunction3Async(string myVar)
        {
            return myVar;
        }

        var functions = new List<KernelFunction>()
        {
            KernelFunctionFactory.CreateFromMethod(Method(MyFunction1Async), this, "func1"),
            KernelFunctionFactory.CreateFromMethod(Method(MyFunction2Async), this, "func2"),
            KernelFunctionFactory.CreateFromMethod(Method(MyFunction3Async), this, "func3")
        };

        this._kernel.Plugins.Add(new KernelPlugin("plugin", functions));

        // Act
        var result = await target.RenderAsync(this._kernel, this._arguments);

        // Assert
        Assert.Equal("A B C", result);
    }

    [Fact]
    public async Task ItRendersAsyncCodeUsingVariablesAsync()
    {
        // Arrange
        Task<string> MyFunctionAsync(string input)
        {
            // Input value should be "BAR" because the variable $myVar is passed in
            this._logger.WriteLine("MyFunction call received, input: {0}", input);
            return Task.FromResult(input);
        }

        KernelFunction func = KernelFunctionFactory.CreateFromMethod(Method(MyFunctionAsync), this, "function");

        this._kernel.Plugins.Add(new KernelPlugin("plugin", new[] { func }));

        this._arguments["myVar"] = "BAR";

        var template = "foo-{{plugin.function $myVar}}-baz";

        var target = (KernelPromptTemplate)this._factory.Create(new PromptTemplateConfig(template));

        // Act
        var result = await target.RenderAsync(this._kernel, this._arguments);

        // Assert
        Assert.Equal("foo-BAR-baz", result);
    }

    [Fact]
    public async Task RenderVarValuesFunctionWithDiffArgTypesAsync()
    {
        // Arrange
        int expected_i = 42;
        double expected_d = 36.6;
        string expected_s = "test";
        Guid expected_g = new("7ac656b1-c917-41c8-9ff5-e8f0eb51fbac");
        DateTime expected_dt = DateTime.ParseExact("05.12.2023 17:52", "dd.MM.yyyy HH:mm", CultureInfo.InvariantCulture);
        DayOfWeek expected_e = DayOfWeek.Monday;

        KernelFunction func = KernelFunctionFactory.CreateFromMethod((string input, Guid g) =>
        {
            Assert.Equal(expected_s, input);
            Assert.Equal(expected_g, g);

            return $"string:{input}, Guid:{g}";
        },
        "f");

        this._kernel.Culture = new CultureInfo("fr-FR"); //In French culture, a comma is used as a decimal separator, and a slash is used as a date separator. See the Assert below.
        this._kernel.Plugins.Add(new KernelPlugin("p", new[] { func }));

        var template = "int:{{$i}}, double:{{$d}}, {{p.f $s g=$g}}, DateTime:{{$dt}}, enum:{{$e}}";

        var target = (KernelPromptTemplate)this._factory.Create(new PromptTemplateConfig(template));

        // Act
        var result = await target.RenderAsync(this._kernel, new()
        {
            ["i"] = expected_i,
            ["d"] = expected_d,
            ["s"] = expected_s,
            ["g"] = expected_g,
            ["dt"] = expected_dt,
            ["e"] = expected_e,
        });

        // Assert
        Assert.Equal("int:42, double:36,6, string:test, Guid:7ac656b1-c917-41c8-9ff5-e8f0eb51fbac, DateTime:05/12/2023 17:52, enum:Monday", result);
    }

    private static MethodInfo Method(Delegate method)
    {
        return method.Method;
    }
}
