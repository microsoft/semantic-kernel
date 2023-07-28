// Copyright (c) Microsoft. All rights reserved.

using System;
using System.ComponentModel;
using System.Globalization;
using System.Reflection;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.SkillDefinition;
using Moq;
using Xunit;

namespace SemanticKernel.UnitTests.SkillDefinition;

public sealed class SKFunctionTests2
{
    private readonly Mock<ILogger> _logger;
    private readonly Mock<IReadOnlySkillCollection> _skills;

    private static string s_expected = string.Empty;
    private static string s_actual = string.Empty;

    public SKFunctionTests2()
    {
        this._logger = new Mock<ILogger>();
        this._skills = new Mock<IReadOnlySkillCollection>();

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
        var function = SKFunction.FromNativeMethod(Method(Test), logger: this._logger.Object);
        Assert.NotNull(function);
        SKContext result = await function.InvokeAsync(context);

        // Assert
        Assert.False(result.ErrorOccurred);
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
        var function = SKFunction.FromNativeMethod(Method(Test), logger: this._logger.Object);
        Assert.NotNull(function);
        SKContext result = await function.InvokeAsync(context);

        // Assert
        Assert.False(result.ErrorOccurred);
        Assert.Equal(s_expected, s_actual);
        Assert.Equal(s_expected, result.Result);
        Assert.Equal(s_expected, context.Result);
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
        var function = SKFunction.FromNativeMethod(Method(Test), logger: this._logger.Object);
        Assert.NotNull(function);
        SKContext result = await function.InvokeAsync(context);

        // Assert
        Assert.False(result.ErrorOccurred);
        Assert.Equal(s_expected, s_actual);
        Assert.Equal(s_expected, context.Result);
        Assert.Equal(s_expected, result.Result);
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
        var function = SKFunction.FromNativeMethod(Method(Test), logger: this._logger.Object);
        Assert.NotNull(function);
        SKContext result = await function.InvokeAsync(context);

        // Assert
        Assert.False(result.ErrorOccurred);
        Assert.Equal(s_expected, s_actual);
        Assert.Equal(s_expected, context.Result);
        Assert.Equal(s_expected, result.Result);
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
        var function = SKFunction.FromNativeMethod(Method(Test), logger: this._logger.Object);
        Assert.NotNull(function);
        SKContext result = await function.InvokeAsync(context);

        // Assert
        Assert.False(result.ErrorOccurred);
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
        var function = SKFunction.FromNativeMethod(Method(Test), logger: this._logger.Object);
        Assert.NotNull(function);
        SKContext result = await function.InvokeAsync(context);

        // Assert
        Assert.False(result.ErrorOccurred);
        Assert.Equal(s_expected, s_actual);
        Assert.Equal("abc", context.Result);
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
        var function = SKFunction.FromNativeMethod(Method(method), method.Target, logger: this._logger.Object);
        Assert.NotNull(function);
        SKContext result = await function.InvokeAsync(context);

        // Assert
        Assert.False(result.ErrorOccurred);
        Assert.Equal(1, invocationCount);
        Assert.Equal(s_expected, s_actual);
        Assert.Equal("abc", context.Result);
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
        var function = SKFunction.FromNativeMethod(Method(method), method.Target, logger: this._logger.Object);
        Assert.NotNull(function);
        SKContext result = await function.InvokeAsync(context);

        // Assert
        Assert.False(result.ErrorOccurred);
        Assert.Equal(1, invocationCount);
        Assert.Equal(s_expected, s_actual);
        Assert.Equal(s_actual, context.Result);
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
        var function = SKFunction.FromNativeMethod(Method(method), method.Target, logger: this._logger.Object);
        Assert.NotNull(function);
        SKContext result = await function.InvokeAsync(context);

        // Assert
        Assert.False(result.ErrorOccurred);
        Assert.Equal(1, invocationCount);
        Assert.Equal(s_expected, s_actual);
        Assert.Equal(s_expected, context.Variables["canary"]);
        Assert.Equal("foo", context.Result);
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
        var function = SKFunction.FromNativeMethod(Method(method), method.Target, logger: this._logger.Object);
        Assert.NotNull(function);
        SKContext result = await function.InvokeAsync(context);

        // Assert
        Assert.False(result.ErrorOccurred);
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
        var function = SKFunction.FromNativeMethod(Method(method), method.Target, logger: this._logger.Object);
        Assert.NotNull(function);
        SKContext result = await function.InvokeAsync(context);

        // Assert
        Assert.False(result.ErrorOccurred);
        Assert.Equal(1, invocationCount);
        Assert.Equal(s_expected, s_actual);
        Assert.Equal("foo-bar", context.Result);
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
        var function = SKFunction.FromNativeMethod(Method(method), method.Target, logger: this._logger.Object);
        Assert.NotNull(function);
        SKContext result = await function.InvokeAsync(context);

        // Assert
        Assert.False(result.ErrorOccurred);
        Assert.Equal(1, invocationCount);
        Assert.Equal(s_expected, s_actual);
        Assert.Equal("hello there", context.Result);
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
        var function = SKFunction.FromNativeMethod(Method(method), method.Target, logger: this._logger.Object);
        Assert.NotNull(function);
        SKContext result = await function.InvokeAsync(context);

        // Assert
        Assert.False(result.ErrorOccurred);
        Assert.Equal(1, invocationCount);
        Assert.Equal(s_expected, s_actual);
        Assert.Equal(s_expected, context.Variables["canary"]);
        Assert.Equal("x y z", context.Result);
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
        var function = SKFunction.FromNativeMethod(Method(method), method.Target, logger: this._logger.Object);
        Assert.NotNull(function);
        SKContext result = await function.InvokeAsync(context);

        // Assert
        Assert.False(result.ErrorOccurred);
        Assert.Equal(1, invocationCount);
        Assert.Equal(s_expected, s_actual);
        Assert.Equal(s_expected, context.Variables["canary"]);
        Assert.Equal("x y z", context.Result);
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
        var function = SKFunction.FromNativeMethod(Method(Test), logger: this._logger.Object);
        Assert.NotNull(function);
        SKContext result = await function.InvokeAsync(context);

        // Assert
        Assert.False(result.ErrorOccurred);
        Assert.Equal(s_expected, s_actual);
        Assert.Equal(s_expected, context.Variables["canary"]);
        Assert.Equal("new data", context.Result);
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
        var function = SKFunction.FromNativeMethod(Method(Test), logger: this._logger.Object);
        Assert.NotNull(function);
        SKContext result = await function.InvokeAsync(context);

        // Assert
        Assert.False(result.ErrorOccurred);
        Assert.Equal(s_expected, s_actual);
        Assert.Equal(s_expected, context.Variables["canary"]);
        Assert.Equal("new data", context.Result);
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

            // This value should overwrite "x y z". Contexts are merged.
            var newContext = new SKContext(
                new ContextVariables(input),
                skills: new Mock<IReadOnlySkillCollection>().Object);

            newContext.Variables.Update("new data");
            newContext.Variables["canary2"] = "222";

            return Task.FromResult(newContext);
        }

        var oldContext = this.MockContext("");
        oldContext.Variables["legacy"] = "something";

        // Act
        var function = SKFunction.FromNativeMethod(Method(Test), logger: this._logger.Object);
        Assert.NotNull(function);
        SKContext newContext = await function.InvokeAsync(oldContext);

        // Assert
        Assert.False(oldContext.ErrorOccurred);
        Assert.False(newContext.ErrorOccurred);

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
    }

    [Fact]
    public async Task ItSupportsStaticContextValueTaskContextAsync()
    {
        // Arrange
        static ValueTask<SKContext> Test(string input, SKContext context)
        {
            // This value should overwrite "x y z". Contexts are merged.
            var newCx = new SKContext(
                new ContextVariables(input + "abc"),
                skills: new Mock<IReadOnlySkillCollection>().Object);

            return new ValueTask<SKContext>(newCx);
        }

        var oldContext = this.MockContext("test");

        // Act
        var function = SKFunction.FromNativeMethod(Method(Test), logger: this._logger.Object);
        Assert.NotNull(function);
        SKContext newContext = await function.InvokeAsync(oldContext);

        // Assert
        Assert.Equal("testabc", newContext.Variables.Input);
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
        var function = SKFunction.FromNativeMethod(Method(TestAsync), logger: this._logger.Object);
        Assert.NotNull(function);
        SKContext result = await function.InvokeAsync(context);

        // Assert
        Assert.False(result.ErrorOccurred);
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
        var function = SKFunction.FromNativeMethod(Method(TestAsync), logger: this._logger.Object);
        Assert.NotNull(function);
        SKContext result = await function.InvokeAsync(context);

        // Assert
        Assert.False(result.ErrorOccurred);
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
        var function = SKFunction.FromNativeMethod(Method(TestAsync), logger: this._logger.Object);
        Assert.NotNull(function);
        SKContext result = await function.InvokeAsync(context);

        // Assert
        Assert.False(result.ErrorOccurred);
        Assert.Equal(s_expected, s_actual);
        Assert.Equal(s_expected, context.Variables["canary"]);
        Assert.Equal("x y z", context.Result);
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
        var function = SKFunction.FromNativeMethod(Method(TestAsync), logger: this._logger.Object);
        Assert.NotNull(function);
        SKContext result = await function.InvokeAsync(context);

        // Assert
        Assert.False(result.ErrorOccurred);
        Assert.Equal(s_expected, s_actual);
        Assert.Equal(s_expected, context.Variables["canary"]);
        Assert.Equal("input:x y z", context.Result);
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
        var function = SKFunction.FromNativeMethod(Method(TestAsync), logger: this._logger.Object);
        Assert.NotNull(function);
        SKContext result = await function.InvokeAsync(context);

        // Assert
        Assert.False(result.ErrorOccurred);
        Assert.Equal(s_expected, s_actual);
    }

    [Fact]
    public async Task ItSupportsUsingNamedInputValueFromContext()
    {
        static string Test(string input) => "Result: " + input;

        var context = this.MockContext("input value");

        // Act
        var function = SKFunction.FromNativeMethod(Method(Test));
        Assert.NotNull(function);
        SKContext result = await function.InvokeAsync(context);

        // Assert
        Assert.False(result.ErrorOccurred);
        Assert.Equal("Result: input value", result.Variables.Input);
    }

    [Fact]
    public async Task ItSupportsUsingNonNamedInputValueFromContext()
    {
        static string Test(string other) => "Result: " + other;

        var context = this.MockContext("input value");

        // Act
        var function = SKFunction.FromNativeMethod(Method(Test));
        Assert.NotNull(function);
        SKContext result = await function.InvokeAsync(context);

        // Assert
        Assert.False(result.ErrorOccurred);
        Assert.Equal("Result: input value", result.Variables.Input);
    }

    [Fact]
    public async Task ItSupportsUsingNonNamedInputValueFromContextEvenWhenThereAreMultipleParameters()
    {
        static string Test(int something, long orother) => "Result: " + (something + orother);

        var context = this.MockContext("42");
        context.Variables.Set("orother", "8");

        // Act
        var function = SKFunction.FromNativeMethod(Method(Test));
        Assert.NotNull(function);
        SKContext result = await function.InvokeAsync(context);

        // Assert
        Assert.False(result.ErrorOccurred);
        Assert.Equal("Result: 50", result.Variables.Input);
    }

    [Fact]
    public async Task ItSupportsPreferringNamedValueOverInputFromContext()
    {
        static string Test(string other) => "Result: " + other;

        var context = this.MockContext("input value");
        context.Variables.Set("other", "other value");

        // Act
        var function = SKFunction.FromNativeMethod(Method(Test));
        Assert.NotNull(function);
        SKContext result = await function.InvokeAsync(context);

        // Assert
        Assert.False(result.ErrorOccurred);
        Assert.Equal("Result: other value", result.Variables.Input);
    }

    [Fact]
    public async Task ItSupportsOverridingNameWithAttribute()
    {
        static string Test([SKName("input"), Description("description")] string other) => "Result: " + other;

        var context = this.MockContext("input value");
        context.Variables.Set("other", "other value");

        // Act
        var function = SKFunction.FromNativeMethod(Method(Test));
        Assert.NotNull(function);
        SKContext result = await function.InvokeAsync(context);

        // Assert
        Assert.False(result.ErrorOccurred);
        Assert.Equal("Result: input value", result.Variables.Input);
    }

    [Fact]
    public async Task ItSupportNullDefaultValuesOverInput()
    {
        static string Test(string? input = null, string? other = null) => "Result: " + (other is null);

        var context = this.MockContext("input value");

        // Act
        var function = SKFunction.FromNativeMethod(Method(Test));
        Assert.NotNull(function);
        SKContext result = await function.InvokeAsync(context);

        // Assert
        Assert.False(result.ErrorOccurred);
        Assert.Equal("Result: True", result.Variables.Input);
    }

    [Fact]
    public async Task ItSupportsConvertingFromManyTypes()
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
        SKContext result = await function.InvokeAsync(context);

        // Assert
        Assert.False(result.ErrorOccurred);
        Assert.Equal("1 -2 1234 7e08cc00-1d71-4558-81ed-69929499dea1 Thu, 25 May 2023 20:17:30 GMT Monday", result.Variables.Input);
    }

    [Fact]
    public async Task ItSupportsConvertingFromTypeConverterAttributedTypes()
    {
        static int Test(MyCustomType mct) => mct.Value * 2;

        var context = this.MockContext("");
        context.Variables.Set("mct", "42");

        // Act
        var function = SKFunction.FromNativeMethod(Method(Test));
        Assert.NotNull(function);
        SKContext result = await function.InvokeAsync(context);

        // Assert
        Assert.False(result.ErrorOccurred);
        Assert.Equal("84", result.Variables.Input);
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
    public async Task ItSupportsConvertingFromToManyTypes()
    {
        // Arrange
        var context = this.MockContext("1");

        static async Task AssertResult(Delegate d, SKContext context, string expected)
        {
            context = await SKFunction.FromNativeFunction(d, functionName: "Test")!.InvokeAsync(context);
            Assert.False(context.ErrorOccurred);
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
    public async Task ItUsesContextCultureForParsingFormatting()
    {
        // Arrange
        var context = this.MockContext("");
        ISKFunction func = SKFunction.FromNativeFunction((double input) => input * 2, functionName: "Test");

        // Act/Assert

        context.Culture = new CultureInfo("fr-FR");
        context.Variables.Update("12,34"); // tries first to parse with the specified culture
        context = await func.InvokeAsync(context);
        Assert.Equal("24,68", context.Variables.Input);

        context.Culture = new CultureInfo("fr-FR");
        context.Variables.Update("12.34"); // falls back to invariant culture
        context = await func.InvokeAsync(context);
        Assert.Equal("24,68", context.Variables.Input);

        context.Culture = new CultureInfo("en-US");
        context.Variables.Update("12.34"); // works with current culture
        context = await func.InvokeAsync(context);
        Assert.Equal("24.68", context.Variables.Input);

        context.Culture = new CultureInfo("en-US");
        context.Variables.Update("12,34"); // not parsable with current or invariant culture
        context = await func.InvokeAsync(context);
        Assert.True(context.ErrorOccurred);
        Assert.IsType<ArgumentOutOfRangeException>(context.LastException);
    }

    [Fact]
    public async Task ItThrowsWhenItFailsToConvertAnArgument()
    {
        static string Test(Guid g) => g.ToString();

        var context = this.MockContext("");
        context.Variables.Set("g", "7e08cc00-1d71-4558-81ed-69929499dxyz");

        // Act
        var function = SKFunction.FromNativeMethod(Method(Test));
        Assert.NotNull(function);
        SKContext result = await function.InvokeAsync(context);

        // Assert
        AssertExtensions.AssertIsArgumentOutOfRange(result.LastException, "g", context.Variables["g"]);
    }

    private static MethodInfo Method(Delegate method)
    {
        return method.Method;
    }

    private SKContext MockContext(string input)
    {
        return new SKContext(
            new ContextVariables(input),
            skills: this._skills.Object,
            logger: this._logger.Object);
    }
}
