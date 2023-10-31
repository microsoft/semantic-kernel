// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Globalization;
using System.Linq;
using System.Reflection;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.Services;
using Moq;
using Xunit;

namespace SemanticKernel.UnitTests.Functions;

public sealed class SKFunctionTests2
{
    private readonly Mock<ILoggerFactory> _logger;
    private readonly Mock<IReadOnlyFunctionCollection> _functions;
    private readonly Mock<IKernel> _kernel;

    private static string s_expected = string.Empty;
    private static string s_actual = string.Empty;

    public SKFunctionTests2()
    {
        this._logger = new Mock<ILoggerFactory>();
        this._functions = new Mock<IReadOnlyFunctionCollection>();
        this._kernel = new Mock<IKernel>();

        s_expected = Guid.NewGuid().ToString("D");
    }

    [Fact]
    public async Task ItSupportsStaticVoidVoidAsync()
    {
        // Arrange
        static void Test()
        {
            s_actual = s_expected;
        }

        var context = this.MockContext("");

        // Act
        var function = SKFunction.FromNativeMethod(Method(Test), loggerFactory: this._logger.Object);
        Assert.NotNull(function);

        await function.InvokeAsync(context);

        // Assert
        Assert.Equal(s_expected, s_actual);
    }

    [Fact]
    public async Task ItSupportsStaticVoidStringAsync()
    {
        // Arrange
        static string Test()
        {
            s_actual = s_expected;
            return s_expected;
        }

        var context = this.MockContext("");

        // Act
        var function = SKFunction.FromNativeMethod(Method(Test), loggerFactory: this._logger.Object);
        Assert.NotNull(function);

        FunctionResult result = await function.InvokeAsync(context);

        // Assert
        Assert.Equal(s_expected, s_actual);
        Assert.Equal(s_expected, context.Result);
        Assert.Equal(s_expected, result.GetValue<string>());
    }

    [Fact]
    public async Task ItSupportsStaticVoidTaskStringAsync()
    {
        // Arrange
        static Task<string> Test()
        {
            s_actual = s_expected;
            return Task.FromResult(s_expected);
        }

        var context = this.MockContext("");

        // Act
        var function = SKFunction.FromNativeMethod(Method(Test), loggerFactory: this._logger.Object);
        Assert.NotNull(function);

        FunctionResult result = await function.InvokeAsync(context);

        // Assert
        Assert.Equal(s_expected, s_actual);
        Assert.Equal(s_expected, context.Result);
        Assert.Equal(s_expected, result.GetValue<string>());
    }

    [Fact]
    public async Task ItSupportsStaticVoidValueTaskStringAsync()
    {
        // Arrange
        static async ValueTask<string> Test()
        {
            s_actual = s_expected;
            await Task.Delay(1);
            return s_expected;
        }

        var context = this.MockContext("");

        // Act
        var function = SKFunction.FromNativeMethod(Method(Test), loggerFactory: this._logger.Object);
        Assert.NotNull(function);

        FunctionResult result = await function.InvokeAsync(context);

        // Assert
        Assert.Equal(s_expected, s_actual);
        Assert.Equal(s_expected, context.Result);
        Assert.Equal(s_expected, result.GetValue<string>());
    }

    [Fact]
    public async Task ItSupportsStaticContextVoidAsync()
    {
        // Arrange
        static void Test(SKContext context)
        {
            s_actual = s_expected;
            context.Variables["canary"] = s_expected;
        }

        var context = this.MockContext("xy");
        context.Variables["someVar"] = "qz";

        // Act
        var function = SKFunction.FromNativeMethod(Method(Test), loggerFactory: this._logger.Object);
        Assert.NotNull(function);

        await function.InvokeAsync(context);

        // Assert
        Assert.Equal(s_expected, s_actual);
        Assert.Equal(s_expected, context.Variables["canary"]);
    }

    [Fact]
    public async Task ItSupportsStaticContextStringAsync()
    {
        // Arrange
        static string Test(SKContext context)
        {
            s_actual = context.Variables["someVar"];
            return "abc";
        }

        var context = this.MockContext("");
        context.Variables["someVar"] = s_expected;

        // Act
        var function = SKFunction.FromNativeMethod(Method(Test), loggerFactory: this._logger.Object);
        Assert.NotNull(function);

        var result = await function.InvokeAsync(context);

        // Assert
        Assert.Equal(s_expected, s_actual);
        Assert.Equal("abc", context.Result);
        Assert.Equal("abc", result.GetValue<string>());
    }

    [Fact]
    public async Task ItSupportsInstanceContextStringNullableAsync()
    {
        // Arrange
        int invocationCount = 0;

        string? Test(SKContext context)
        {
            invocationCount++;
            s_actual = context.Variables["someVar"];
            return "abc";
        }

        var context = this.MockContext("");
        context.Variables["someVar"] = s_expected;

        // Act
        Func<SKContext, string?> method = Test;
        var function = SKFunction.FromNativeMethod(Method(method), method.Target, loggerFactory: this._logger.Object);
        Assert.NotNull(function);

        var result = await function.InvokeAsync(context);

        // Assert
        Assert.Equal(1, invocationCount);
        Assert.Equal(s_expected, s_actual);
        Assert.Equal("abc", context.Result);
        Assert.Equal("abc", result.GetValue<string>());
    }

    [Fact]
    public async Task ItSupportsInstanceContextTaskStringAsync()
    {
        // Arrange
        int invocationCount = 0;

        Task<string> Test(SKContext context)
        {
            invocationCount++;
            s_actual = s_expected;
            context.Variables["canary"] = s_expected;
            return Task.FromResult(s_expected);
        }

        var context = this.MockContext("");

        // Act
        Func<SKContext, Task<string>> method = Test;
        var function = SKFunction.FromNativeMethod(Method(method), method.Target, loggerFactory: this._logger.Object);
        Assert.NotNull(function);

        var result = await function.InvokeAsync(context);

        // Assert
        Assert.Equal(1, invocationCount);
        Assert.Equal(s_expected, s_actual);
        Assert.Equal(s_actual, context.Result);
        Assert.Equal(s_actual, result.GetValue<string>());
        Assert.Equal(s_expected, context.Variables["canary"]);
    }

    [Fact]
    public async Task ItSupportsInstanceContextTaskContextAsync()
    {
        // Arrange
        int invocationCount = 0;

        async Task<SKContext> TestAsync(SKContext context)
        {
            await Task.Delay(0);
            invocationCount++;
            s_actual = s_expected;
            context.Variables.Update("foo");
            context.Variables["canary"] = s_expected;
            return context;
        }

        var context = this.MockContext("");

        // Act
        Func<SKContext, Task<SKContext>> method = TestAsync;
        var function = SKFunction.FromNativeMethod(Method(method), method.Target, loggerFactory: this._logger.Object);
        Assert.NotNull(function);

        var result = await function.InvokeAsync(context);

        // Assert
        Assert.Equal(1, invocationCount);
        Assert.Equal(s_expected, s_actual);
        Assert.Equal(s_expected, context.Variables["canary"]);
        Assert.Equal("foo", context.Result);
        Assert.Equal("foo", result.GetValue<string>());
    }

    [Fact]
    public async Task ItSupportsInstanceStringVoidAsync()
    {
        // Arrange
        int invocationCount = 0;

        void Test(string input)
        {
            invocationCount++;
            s_actual = s_expected + input;
        }

        var context = this.MockContext(".blah");

        // Act
        Action<string> method = Test;
        var function = SKFunction.FromNativeMethod(Method(method), method.Target, loggerFactory: this._logger.Object);
        Assert.NotNull(function);

        await function.InvokeAsync(context);

        // Assert
        Assert.Equal(1, invocationCount);
        Assert.Equal(s_expected + ".blah", s_actual);
    }

    [Fact]
    public async Task ItSupportsInstanceStringStringAsync()
    {
        // Arrange
        int invocationCount = 0;

        string Test(string input)
        {
            invocationCount++;
            s_actual = s_expected;
            return "foo-bar";
        }

        var context = this.MockContext("");

        // Act
        Func<string, string> method = Test;
        var function = SKFunction.FromNativeMethod(Method(method), method.Target, loggerFactory: this._logger.Object);
        Assert.NotNull(function);

        var result = await function.InvokeAsync(context);

        // Assert
        Assert.Equal(1, invocationCount);
        Assert.Equal(s_expected, s_actual);
        Assert.Equal("foo-bar", context.Result);
        Assert.Equal("foo-bar", result.GetValue<string>());
    }

    [Fact]
    public async Task ItSupportsInstanceStringTaskStringAsync()
    {
        // Arrange
        int invocationCount = 0;

        Task<string> Test(string input)
        {
            invocationCount++;
            s_actual = s_expected;
            return Task.FromResult("hello there");
        }

        var context = this.MockContext("");

        // Act
        Func<string, Task<string>> method = Test;
        var function = SKFunction.FromNativeMethod(Method(method), method.Target, loggerFactory: this._logger.Object);
        Assert.NotNull(function);

        var result = await function.InvokeAsync(context);

        // Assert
        Assert.Equal(1, invocationCount);
        Assert.Equal(s_expected, s_actual);
        Assert.Equal("hello there", context.Result);
        Assert.Equal("hello there", result.GetValue<string>());
    }

    [Fact]
    public async Task ItSupportsInstanceStringContextVoidAsync()
    {
        // Arrange
        int invocationCount = 0;

        void Test(string input, SKContext context)
        {
            invocationCount++;
            s_actual = s_expected;
            context.Variables.Update("x y z");
            context.Variables["canary"] = s_expected;
        }

        var context = this.MockContext("");

        // Act
        Action<string, SKContext> method = Test;
        var function = SKFunction.FromNativeMethod(Method(method), method.Target, loggerFactory: this._logger.Object);
        Assert.NotNull(function);

        var result = await function.InvokeAsync(context);

        // Assert
        Assert.Equal(1, invocationCount);
        Assert.Equal(s_expected, s_actual);
        Assert.Equal(s_expected, context.Variables["canary"]);
        Assert.Equal("x y z", context.Result);
        Assert.Null(result.GetValue<string>());
    }

    [Fact]
    public async Task ItSupportsInstanceContextStringVoidAsync()
    {
        // Arrange
        int invocationCount = 0;

        void Test(SKContext context, string input)
        {
            invocationCount++;
            s_actual = s_expected;
            context.Variables.Update("x y z");
            context.Variables["canary"] = s_expected;
        }

        var context = this.MockContext("");

        // Act
        Action<SKContext, string> method = Test;
        var function = SKFunction.FromNativeMethod(Method(method), method.Target, loggerFactory: this._logger.Object);
        Assert.NotNull(function);

        var result = await function.InvokeAsync(context);

        // Assert
        Assert.Equal(1, invocationCount);
        Assert.Equal(s_expected, s_actual);
        Assert.Equal(s_expected, context.Variables["canary"]);
        Assert.Equal("x y z", context.Result);
        Assert.Null(result.GetValue<string>());
    }

    [Fact]
    public async Task ItSupportsStaticStringContextStringAsync()
    {
        // Arrange
        static string Test(string input, SKContext context)
        {
            s_actual = s_expected;
            context.Variables["canary"] = s_expected;
            context.Variables.Update("x y z");
            // This value should overwrite "x y z"
            return "new data";
        }

        var context = this.MockContext("");

        // Act
        var function = SKFunction.FromNativeMethod(Method(Test), loggerFactory: this._logger.Object);
        Assert.NotNull(function);

        var result = await function.InvokeAsync(context);

        // Assert
        Assert.Equal(s_expected, s_actual);
        Assert.Equal(s_expected, context.Variables["canary"]);
        Assert.Equal("new data", context.Result);
        Assert.Equal("new data", result.GetValue<string>());
    }

    [Fact]
    public async Task ItSupportsStaticStringContextTaskStringAsync()
    {
        // Arrange
        static Task<string> Test(string input, SKContext context)
        {
            s_actual = s_expected;
            context.Variables["canary"] = s_expected;
            context.Variables.Update("x y z");
            // This value should overwrite "x y z"
            return Task.FromResult("new data");
        }

        var context = this.MockContext("");
        // Act
        var function = SKFunction.FromNativeMethod(Method(Test), loggerFactory: this._logger.Object);
        Assert.NotNull(function);

        var result = await function.InvokeAsync(context);

        // Assert
        Assert.Equal(s_expected, s_actual);
        Assert.Equal(s_expected, context.Variables["canary"]);
        Assert.Equal("new data", context.Result);
        Assert.Equal("new data", result.GetValue<string>());
    }

    [Fact]
    public async Task ItSupportsStaticStringContextTaskContextAsync()
    {
        // Arrange
        static Task<SKContext> Test(string input, SKContext context)
        {
            s_actual = s_expected;
            context.Variables["canary"] = s_expected;
            context.Variables.Update("x y z");

            var newContext = context.Clone();
            newContext.Variables.Clear();

            // This value should overwrite "x y z". Contexts are merged.
            newContext.Variables.Update("new data");
            newContext.Variables["canary2"] = "222";

            return Task.FromResult(newContext);
        }

        var oldContext = this.MockContext("");
        oldContext.Variables["legacy"] = "something";

        // Act
        var function = SKFunction.FromNativeMethod(Method(Test), loggerFactory: this._logger.Object);
        Assert.NotNull(function);

        FunctionResult result = await function.InvokeAsync(oldContext);
        var newContext = result.Context;

        // Assert
        Assert.Equal(s_expected, s_actual);

        Assert.True(oldContext.Variables.ContainsKey("canary"));
        Assert.False(oldContext.Variables.ContainsKey("canary2"));

        Assert.False(newContext.Variables.ContainsKey("canary"));
        Assert.True(newContext.Variables.ContainsKey("canary2"));

        Assert.Equal(s_expected, oldContext.Variables["canary"]);
        Assert.Equal("222", newContext.Variables["canary2"]);

        Assert.True(oldContext.Variables.ContainsKey("legacy"));
        Assert.False(newContext.Variables.ContainsKey("legacy"));

        Assert.Equal("x y z", oldContext.Result);
        Assert.Equal("new data", newContext.Result);

        Assert.Equal("new data", result.GetValue<string>());
    }

    [Fact]
    public async Task ItSupportsStaticContextValueTaskContextAsync()
    {
        // Arrange
        static ValueTask<SKContext> Test(string input, SKContext context)
        {
            // This value should overwrite "x y z". Contexts are merged.
            var newCx = context.Clone();
            newCx.Variables.Update(input + "abc");

            return new ValueTask<SKContext>(newCx);
        }

        var oldContext = this.MockContext("test");

        // Act
        var function = SKFunction.FromNativeMethod(Method(Test), loggerFactory: this._logger.Object);
        Assert.NotNull(function);

        FunctionResult result = await function.InvokeAsync(oldContext);

        // Assert
        Assert.Equal("testabc", result.Context.Variables.Input);
    }

    [Fact]
    public async Task ItSupportsStaticStringTaskAsync()
    {
        // Arrange
        static Task TestAsync(string input)
        {
            s_actual = s_expected;
            return Task.CompletedTask;
        }

        var context = this.MockContext("");

        // Act
        var function = SKFunction.FromNativeMethod(Method(TestAsync), loggerFactory: this._logger.Object);
        Assert.NotNull(function);

        await function.InvokeAsync(context);

        // Assert
        Assert.Equal(s_expected, s_actual);
    }

    [Fact]
    public async Task ItSupportsStaticStringValueTaskAsync()
    {
        // Arrange
        static ValueTask TestAsync(string input)
        {
            s_actual = s_expected;
            return default;
        }

        var context = this.MockContext("");

        // Act
        var function = SKFunction.FromNativeMethod(Method(TestAsync), loggerFactory: this._logger.Object);
        Assert.NotNull(function);

        await function.InvokeAsync(context);

        // Assert
        Assert.Equal(s_expected, s_actual);
    }

    [Fact]
    public async Task ItSupportsStaticContextTaskAsync()
    {
        // Arrange
        static Task TestAsync(SKContext context)
        {
            s_actual = s_expected;
            context.Variables["canary"] = s_expected;
            context.Variables.Update("x y z");
            return Task.CompletedTask;
        }

        var context = this.MockContext("");

        // Act
        var function = SKFunction.FromNativeMethod(Method(TestAsync), loggerFactory: this._logger.Object);
        Assert.NotNull(function);

        var result = await function.InvokeAsync(context);

        // Assert
        Assert.Equal(s_expected, s_actual);
        Assert.Equal(s_expected, context.Variables["canary"]);
        Assert.Equal("x y z", context.Result);
        Assert.Null(result.GetValue<string>());
    }

    [Fact]
    public async Task ItSupportsStaticStringContextTaskAsync()
    {
        // Arrange
        static Task TestAsync(string input, SKContext context)
        {
            s_actual = s_expected;
            context.Variables["canary"] = s_expected;
            context.Variables.Update(input + "x y z");
            return Task.CompletedTask;
        }

        var context = this.MockContext("input:");

        // Act
        var function = SKFunction.FromNativeMethod(Method(TestAsync), loggerFactory: this._logger.Object);
        Assert.NotNull(function);

        var result = await function.InvokeAsync(context);

        // Assert
        Assert.Equal(s_expected, s_actual);
        Assert.Equal(s_expected, context.Variables["canary"]);
        Assert.Equal("input:x y z", context.Result);
        Assert.Null(result.GetValue<string>());
    }

    [Fact]
    public async Task ItSupportsStaticVoidTaskAsync()
    {
        // Arrange
        static Task TestAsync()
        {
            s_actual = s_expected;
            return Task.CompletedTask;
        }

        var context = this.MockContext("");

        // Act
        var function = SKFunction.FromNativeMethod(Method(TestAsync), loggerFactory: this._logger.Object);
        Assert.NotNull(function);

        await function.InvokeAsync(context);

        // Assert
        Assert.Equal(s_expected, s_actual);
    }

    [Fact]
    public async Task ItSupportsUsingNamedInputValueFromContextAsync()
    {
        static string Test(string input) => "Result: " + input;

        var context = this.MockContext("input value");

        // Act
        var function = SKFunction.FromNativeMethod(Method(Test));
        Assert.NotNull(function);

        FunctionResult result = await function.InvokeAsync(context);

        // Assert
        Assert.Equal("Result: input value", result.Context.Variables.Input);
    }

    [Fact]
    public async Task ItSupportsUsingNonNamedInputValueFromContextAsync()
    {
        static string Test(string other) => "Result: " + other;

        var context = this.MockContext("input value");

        // Act
        var function = SKFunction.FromNativeMethod(Method(Test));
        Assert.NotNull(function);

        FunctionResult result = await function.InvokeAsync(context);

        // Assert
        Assert.Equal("Result: input value", result.Context.Variables.Input);
    }

    [Fact]
    public async Task ItSupportsUsingNonNamedInputValueFromContextEvenWhenThereAreMultipleParametersAsync()
    {
        static string Test(int something, long orother) => "Result: " + (something + orother);

        var context = this.MockContext("42");
        context.Variables.Set("orother", "8");

        // Act
        var function = SKFunction.FromNativeMethod(Method(Test));
        Assert.NotNull(function);

        FunctionResult result = await function.InvokeAsync(context);

        // Assert
        Assert.Equal("Result: 50", result.Context.Variables.Input);
    }

    [Fact]
    public async Task ItSupportsPreferringNamedValueOverInputFromContextAsync()
    {
        static string Test(string other) => "Result: " + other;

        var context = this.MockContext("input value");
        context.Variables.Set("other", "other value");

        // Act
        var function = SKFunction.FromNativeMethod(Method(Test));
        Assert.NotNull(function);

        FunctionResult result = await function.InvokeAsync(context);

        // Assert
        Assert.Equal("Result: other value", result.Context.Variables.Input);
    }

    [Fact]
    public async Task ItSupportsOverridingNameWithAttributeAsync()
    {
        static string Test([SKName("input"), Description("description")] string other) => "Result: " + other;

        var context = this.MockContext("input value");
        context.Variables.Set("other", "other value");

        // Act
        var function = SKFunction.FromNativeMethod(Method(Test));
        Assert.NotNull(function);

        FunctionResult result = await function.InvokeAsync(context);

        // Assert
        Assert.Equal("Result: input value", result.Context.Variables.Input);
    }

    [Fact]
    public async Task ItSupportNullDefaultValuesOverInputAsync()
    {
        static string Test(string? input = null, string? other = null) => "Result: " + (other is null);

        var context = this.MockContext("input value");

        // Act
        var function = SKFunction.FromNativeMethod(Method(Test));
        Assert.NotNull(function);

        FunctionResult result = await function.InvokeAsync(context);

        // Assert
        Assert.Equal("Result: True", result.Context.Variables.Input);
    }

    [Fact]
    public async Task ItSupportsConvertingFromManyTypesAsync()
    {
        static string Test(int a, long b, decimal c, Guid d, DateTimeOffset e, DayOfWeek? f) =>
            $"{a} {b} {c} {d} {e:R} {f}";

        var context = this.MockContext("");
        context.Variables.Set("a", "1");
        context.Variables.Set("b", "-2");
        context.Variables.Set("c", "1234");
        context.Variables.Set("d", "7e08cc00-1d71-4558-81ed-69929499dea1");
        context.Variables.Set("e", "Thu, 25 May 2023 20:17:30 GMT");
        context.Variables.Set("f", "Monday");

        // Act
        var function = SKFunction.FromNativeMethod(Method(Test));
        Assert.NotNull(function);

        FunctionResult result = await function.InvokeAsync(context);

        // Assert
        Assert.Equal("1 -2 1234 7e08cc00-1d71-4558-81ed-69929499dea1 Thu, 25 May 2023 20:17:30 GMT Monday", result.Context.Variables.Input);
    }

    [Fact]
    public async Task ItSupportsConvertingFromTypeConverterAttributedTypesAsync()
    {
        static int Test(MyCustomType mct) => mct.Value * 2;

        var context = this.MockContext("");
        context.Variables.Set("mct", "42");

        // Act
        var function = SKFunction.FromNativeMethod(Method(Test));
        Assert.NotNull(function);

        FunctionResult result = await function.InvokeAsync(context);

        // Assert
        Assert.Equal("84", result.Context.Variables.Input);
    }

    [TypeConverter(typeof(MyCustomTypeConverter))]
    private sealed class MyCustomType
    {
        public int Value { get; set; }
    }

#pragma warning disable CA1812 // Instantiated by reflection
    private sealed class MyCustomTypeConverter : TypeConverter
    {
        public override bool CanConvertFrom(ITypeDescriptorContext? context, Type sourceType) =>
            sourceType == typeof(string);
        public override object? ConvertFrom(ITypeDescriptorContext? context, CultureInfo? culture, object value) =>
            new MyCustomType { Value = int.Parse((string)value, culture) };
    }
#pragma warning restore CA1812

    [Fact]
    public async Task ItSupportsConvertingFromToManyTypesAsync()
    {
        // Arrange
        var context = this.MockContext("1");

        static async Task AssertResult(Delegate d, SKContext context, string expected)
        {
            var result = await SKFunction.FromNativeFunction(d, functionName: "Test")!.InvokeAsync(context);
            context = result.Context;

            Assert.Equal(expected, context.Variables.Input);
        }

        // Act/Assert
        await AssertResult((sbyte input) => input * 2, context, "2");
        await AssertResult((byte input) => input * 2, context, "4");
        await AssertResult((short input) => input * 2, context, "8");
        await AssertResult((ushort input) => input * 2, context, "16");
        await AssertResult((int input) => input * 2, context, "32");
        await AssertResult((uint input) => input * 2, context, "64");
        await AssertResult((long input) => input * 2, context, "128");
        await AssertResult((ulong input) => input * 2, context, "256");
        await AssertResult((float input) => input * 2, context, "512");
        await AssertResult((double input) => input * 2, context, "1024");
        await AssertResult((int input) => Task.FromResult(input * 2), context, "2048");
        await AssertResult((long input) => Task.FromResult(input * 2), context, "4096");
        await AssertResult((int input) => ValueTask.FromResult(input * 2), context, "8192");
        await AssertResult((long input) => ValueTask.FromResult(input * 2), context, "16384");
        await AssertResult((long? input) => input!.Value * 2, context, "32768");
        await AssertResult((TimeSpan input) => input * 2, context, "65536.00:00:00");
        await AssertResult((TimeSpan? input) => (int?)null, context, "");

        context.Variables.Update("http://example.com/semantic");
        await AssertResult((Uri input) => new Uri(input, "kernel"), context, "http://example.com/kernel");
    }

    [Fact]
    public async Task ItUsesContextCultureForParsingFormattingAsync()
    {
        // Arrange
        var context = this.MockContext("");
        ISKFunction func = SKFunction.FromNativeFunction((double input) => input * 2, functionName: "Test");
        FunctionResult result;

        // Act/Assert

        context.Culture = new CultureInfo("fr-FR");
        context.Variables.Update("12,34"); // tries first to parse with the specified culture
        result = await func.InvokeAsync(context);
        Assert.Equal("24,68", result.Context.Variables.Input);

        context.Culture = new CultureInfo("fr-FR");
        context.Variables.Update("12.34"); // falls back to invariant culture
        result = await func.InvokeAsync(context);
        Assert.Equal("24,68", result.Context.Variables.Input);

        context.Culture = new CultureInfo("en-US");
        context.Variables.Update("12.34"); // works with current culture
        result = await func.InvokeAsync(context);
        Assert.Equal("24.68", result.Context.Variables.Input);

        context.Culture = new CultureInfo("en-US");
        context.Variables.Update("12,34"); // not parsable with current or invariant culture
        await Assert.ThrowsAsync<ArgumentOutOfRangeException>(() => func.InvokeAsync(context));
    }

    [Fact]
    public async Task ItThrowsWhenItFailsToConvertAnArgumentAsync()
    {
        static string Test(Guid g) => g.ToString();

        var context = this.MockContext("");
        context.Variables.Set("g", "7e08cc00-1d71-4558-81ed-69929499dxyz");

        // Act
        var function = SKFunction.FromNativeMethod(Method(Test));
        Assert.NotNull(function);

        var ex = await Assert.ThrowsAsync<ArgumentOutOfRangeException>(() => function.InvokeAsync(context));

        //Assert
        AssertExtensions.AssertIsArgumentOutOfRange(ex, "g", context.Variables["g"]);
    }

    [Fact]
    public void ItExposesMetadataFromDelegate()
    {
        [Description("Concat information")]
        static string Test(Guid id, string name, [SKName("old")] int age) => $"{id} {name} {age}";

        // Act
        var function = SKFunction.FromNativeFunction(Test);

        // Assert
        Assert.Contains("Test", function.Name, StringComparison.Ordinal);
        Assert.Equal("Concat information", function.Description);
        Assert.Equal("id", function.Describe().Parameters[0].Name);
        Assert.Equal("name", function.Describe().Parameters[1].Name);
        Assert.Equal("old", function.Describe().Parameters[2].Name);
    }

    [Fact]
    public void ItExposesMetadataFromMethodInfo()
    {
        [Description("Concat information")]
        static string Test(Guid id, string name, [SKName("old")] int age) => $"{id} {name} {age}";

        // Act
        var function = SKFunction.FromNativeMethod(Method(Test));

        // Assert
        Assert.Contains("Test", function.Name, StringComparison.Ordinal);
        Assert.Equal("Concat information", function.Description);
        Assert.Equal("id", function.Describe().Parameters[0].Name);
        Assert.Equal("name", function.Describe().Parameters[1].Name);
        Assert.Equal("old", function.Describe().Parameters[2].Name);
    }

    [Fact]
    public async Task ItCanReturnBasicTypesAsync()
    {
        // Arrange
        static int TestInt(int number) => number;
        static double TestDouble(double number) => number;
        static string TestString(string str) => str;
        static bool TestBool(bool flag) => flag;

        var function1 = SKFunction.FromNativeMethod(Method(TestInt));
        var function2 = SKFunction.FromNativeMethod(Method(TestDouble));
        var function3 = SKFunction.FromNativeMethod(Method(TestString));
        var function4 = SKFunction.FromNativeMethod(Method(TestBool));

        // Act
        FunctionResult result1 = await function1.InvokeAsync(this.MockContext("42"));
        FunctionResult result2 = await function2.InvokeAsync(this.MockContext("3.14"));
        FunctionResult result3 = await function3.InvokeAsync(this.MockContext("test-string"));
        FunctionResult result4 = await function4.InvokeAsync(this.MockContext("true"));

        // Assert
        Assert.Equal(42, result1.GetValue<int>());
        Assert.Equal(3.14, result2.GetValue<double>());
        Assert.Equal("test-string", result3.GetValue<string>());
        Assert.True(result4.GetValue<bool>());
    }

    [Fact]
    public async Task ItCanReturnComplexTypeAsync()
    {
        // Arrange
        static MyCustomType TestCustomType(MyCustomType instance) => instance;

        var context = this.MockContext("");
        context.Variables.Set("instance", "42");

        var function = SKFunction.FromNativeMethod(Method(TestCustomType));

        // Act
        FunctionResult result = await function.InvokeAsync(context);

        var actualInstance = result.GetValue<MyCustomType>();

        // Assert
        Assert.NotNull(actualInstance);
        Assert.Equal(42, actualInstance.Value);
    }

    [Fact]
    public async Task ItCanReturnAsyncEnumerableTypeAsync()
    {
        // Arrange
        static async IAsyncEnumerable<int> TestAsyncEnumerableTypeAsync()
        {
            yield return 1;

            await Task.Delay(50);

            yield return 2;

            await Task.Delay(50);

            yield return 3;
        }

        var function = SKFunction.FromNativeMethod(Method(TestAsyncEnumerableTypeAsync));

        // Act
        FunctionResult result = await function.InvokeAsync(this.MockContext(string.Empty));

        // Assert
        Assert.NotNull(result);

        var asyncEnumerableResult = result.GetValue<IAsyncEnumerable<int>>();

        Assert.NotNull(asyncEnumerableResult);

        var assertResult = new List<int>();

        await foreach (var value in asyncEnumerableResult)
        {
            assertResult.Add(value);
        }

        Assert.True(assertResult.SequenceEqual(new List<int> { 1, 2, 3 }));
    }

    private static MethodInfo Method(Delegate method)
    {
        return method.Method;
    }

    private SKContext MockContext(string input)
    {
        var functionRunner = new Mock<IFunctionRunner>();
        var serviceProvider = new Mock<IAIServiceProvider>();
        var serviceSelector = new Mock<IAIServiceSelector>();

        return new SKContext(
            functionRunner.Object,
            serviceProvider.Object,
            serviceSelector.Object,
            new ContextVariables(input)
        );
    }
}
