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
using Moq;
using Xunit;

namespace SemanticKernel.UnitTests.Functions;

public sealed class SKFunctionTests2
{
    private readonly Kernel _kernel;
    private readonly Mock<ILoggerFactory> _logger;

    private static string s_expected = string.Empty;
    private static string s_actual = string.Empty;

    public SKFunctionTests2()
    {
        this._kernel = KernelBuilder.Create();
        this._logger = new Mock<ILoggerFactory>();

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

        var variables = new ContextVariables(string.Empty);

        // Act
        var function = SKFunctionFactory.CreateFromMethod(Method(Test), loggerFactory: this._logger.Object);
        Assert.NotNull(function);

        await function.InvokeAsync(this._kernel, variables);

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

        var variables = new ContextVariables(string.Empty);

        // Act
        var function = SKFunctionFactory.CreateFromMethod(Method(Test), loggerFactory: this._logger.Object);
        Assert.NotNull(function);

        FunctionResult result = await function.InvokeAsync(this._kernel, variables);

        // Assert
        Assert.Equal(s_expected, s_actual);
        Assert.Equal(s_expected, variables.Input);
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

        var variables = new ContextVariables(string.Empty);

        // Act
        var function = SKFunctionFactory.CreateFromMethod(Method(Test), loggerFactory: this._logger.Object);
        Assert.NotNull(function);

        FunctionResult result = await function.InvokeAsync(this._kernel, variables);

        // Assert
        Assert.Equal(s_expected, s_actual);
        Assert.Equal(s_expected, variables.Input);
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

        var variables = new ContextVariables(string.Empty);

        // Act
        var function = SKFunctionFactory.CreateFromMethod(Method(Test), loggerFactory: this._logger.Object);
        Assert.NotNull(function);

        FunctionResult result = await function.InvokeAsync(this._kernel, variables);

        // Assert
        Assert.Equal(s_expected, s_actual);
        Assert.Equal(s_expected, variables.Input);
        Assert.Equal(s_expected, result.GetValue<string>());
    }

    [Fact]
    public async Task ItSupportsStaticContextVoidAsync()
    {
        // Arrange
        static void Test(ContextVariables localVariables)
        {
            s_actual = s_expected;
            localVariables["canary"] = s_expected;
        }

        var variables = new ContextVariables("xy");
        variables["someVar"] = "qz";

        // Act
        var function = SKFunctionFactory.CreateFromMethod(Method(Test), loggerFactory: this._logger.Object);
        Assert.NotNull(function);

        await function.InvokeAsync(this._kernel, variables);

        // Assert
        Assert.Equal(s_expected, s_actual);
        Assert.Equal(s_expected, variables["canary"]);
    }

    [Fact]
    public async Task ItSupportsStaticContextStringAsync()
    {
        // Arrange
        static string Test(ContextVariables localVariables)
        {
            s_actual = localVariables["someVar"];
            return "abc";
        }

        var variables = new ContextVariables(string.Empty);
        variables["someVar"] = s_expected;

        // Act
        var function = SKFunctionFactory.CreateFromMethod(Method(Test), loggerFactory: this._logger.Object);
        Assert.NotNull(function);

        var result = await function.InvokeAsync(this._kernel, variables);

        // Assert
        Assert.Equal(s_expected, s_actual);
        Assert.Equal("abc", variables.Input);
        Assert.Equal("abc", result.GetValue<string>());
    }

    [Fact]
    public async Task ItSupportsInstanceContextStringNullableAsync()
    {
        // Arrange
        int invocationCount = 0;

        string? Test(ContextVariables localVariables)
        {
            invocationCount++;
            s_actual = localVariables["someVar"];
            return "abc";
        }

        var variables = new ContextVariables(string.Empty);
        variables["someVar"] = s_expected;

        // Act
        Func<ContextVariables, string?> method = Test;
        var function = SKFunctionFactory.CreateFromMethod(Method(method), method.Target, loggerFactory: this._logger.Object);
        Assert.NotNull(function);

        var result = await function.InvokeAsync(this._kernel, variables);

        // Assert
        Assert.Equal(1, invocationCount);
        Assert.Equal(s_expected, s_actual);
        Assert.Equal("abc", variables.Input);
        Assert.Equal("abc", result.GetValue<string>());
    }

    [Fact]
    public async Task ItSupportsInstanceContextTaskStringAsync()
    {
        // Arrange
        int invocationCount = 0;

        Task<string> Test(ContextVariables localVariables)
        {
            invocationCount++;
            s_actual = s_expected;
            localVariables["canary"] = s_expected;
            return Task.FromResult(s_expected);
        }

        var variables = new ContextVariables(string.Empty);

        // Act
        Func<ContextVariables, Task<string>> method = Test;
        var function = SKFunctionFactory.CreateFromMethod(Method(method), method.Target, loggerFactory: this._logger.Object);
        Assert.NotNull(function);

        var result = await function.InvokeAsync(this._kernel, variables);

        // Assert
        Assert.Equal(1, invocationCount);
        Assert.Equal(s_expected, s_actual);
        Assert.Equal(s_actual, variables.Input);
        Assert.Equal(s_actual, result.GetValue<string>());
        Assert.Equal(s_expected, variables["canary"]);
    }

    [Fact]
    public async Task ItSupportsInstanceContextTaskContextAsync()
    {
        // Arrange
        int invocationCount = 0;

        async Task TestAsync(ContextVariables localVariables)
        {
            await Task.Delay(0);
            invocationCount++;
            s_actual = s_expected;
            localVariables.Update("foo");
            localVariables["canary"] = s_expected;
        }

        var variables = new ContextVariables(string.Empty);

        // Act
        Func<ContextVariables, Task> method = TestAsync;
        var function = SKFunctionFactory.CreateFromMethod(Method(method), method.Target, loggerFactory: this._logger.Object);
        Assert.NotNull(function);

        var result = await function.InvokeAsync(this._kernel, variables);

        // Assert
        Assert.Equal(1, invocationCount);
        Assert.Equal(s_expected, s_actual);
        Assert.Equal(s_expected, variables["canary"]);
        Assert.Equal("foo", variables.Input);
        Assert.Null(result.GetValue<string>());
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

        var variables = new ContextVariables(".blah");

        // Act
        Action<string> method = Test;
        var function = SKFunctionFactory.CreateFromMethod(Method(method), method.Target, loggerFactory: this._logger.Object);
        Assert.NotNull(function);

        await function.InvokeAsync(this._kernel, variables);

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

        var variables = new ContextVariables(string.Empty);

        // Act
        Func<string, string> method = Test;
        var function = SKFunctionFactory.CreateFromMethod(Method(method), method.Target, loggerFactory: this._logger.Object);
        Assert.NotNull(function);

        var result = await function.InvokeAsync(this._kernel, variables);

        // Assert
        Assert.Equal(1, invocationCount);
        Assert.Equal(s_expected, s_actual);
        Assert.Equal("foo-bar", variables.Input);
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

        var variables = new ContextVariables(string.Empty);

        // Act
        Func<string, Task<string>> method = Test;
        var function = SKFunctionFactory.CreateFromMethod(Method(method), method.Target, loggerFactory: this._logger.Object);
        Assert.NotNull(function);

        var result = await function.InvokeAsync(this._kernel, variables);

        // Assert
        Assert.Equal(1, invocationCount);
        Assert.Equal(s_expected, s_actual);
        Assert.Equal("hello there", variables.Input);
        Assert.Equal("hello there", result.GetValue<string>());
    }

    [Fact]
    public async Task ItSupportsInstanceStringContextVoidAsync()
    {
        // Arrange
        int invocationCount = 0;

        void Test(string input, ContextVariables localVariables)
        {
            invocationCount++;
            s_actual = s_expected;
            localVariables.Update("x y z");
            localVariables["canary"] = s_expected;
        }

        var variables = new ContextVariables(string.Empty);

        // Act
        Action<string, ContextVariables> method = Test;
        var function = SKFunctionFactory.CreateFromMethod(Method(method), method.Target, loggerFactory: this._logger.Object);
        Assert.NotNull(function);

        var result = await function.InvokeAsync(this._kernel, variables);

        // Assert
        Assert.Equal(1, invocationCount);
        Assert.Equal(s_expected, s_actual);
        Assert.Equal(s_expected, variables["canary"]);
        Assert.Equal("x y z", variables.Input);
        Assert.Null(result.GetValue<string>());
    }

    [Fact]
    public async Task ItSupportsInstanceKernelVoidAsync()
    {
        // Arrange
        int invocationCount = 0;
        Kernel? actualKernel = null;

        void Test(Kernel kernel)
        {
            invocationCount++;
            actualKernel = kernel;
        }

        var variables = new ContextVariables(string.Empty);

        // Act
        Action<Kernel> method = Test;
        var function = SKFunctionFactory.CreateFromMethod(Method(method), method.Target);
        Assert.NotNull(function);

        var result = await function.InvokeAsync(this._kernel, variables);

        // Assert
        Assert.Equal(1, invocationCount);
        Assert.Equal(this._kernel, actualKernel);
        Assert.Null(result.GetValue<string>());
    }

    [Fact]
    public async Task ItSupportsInstanceContextStringVoidAsync()
    {
        // Arrange
        int invocationCount = 0;

        void Test(ContextVariables localVariables, string input)
        {
            invocationCount++;
            s_actual = s_expected;
            localVariables.Update("x y z");
            localVariables["canary"] = s_expected;
        }

        var variables = new ContextVariables(string.Empty);

        // Act
        Action<ContextVariables, string> method = Test;
        var function = SKFunctionFactory.CreateFromMethod(Method(method), method.Target, loggerFactory: this._logger.Object);
        Assert.NotNull(function);

        var result = await function.InvokeAsync(this._kernel, variables);

        // Assert
        Assert.Equal(1, invocationCount);
        Assert.Equal(s_expected, s_actual);
        Assert.Equal(s_expected, variables["canary"]);
        Assert.Equal("x y z", variables.Input);
        Assert.Null(result.GetValue<string>());
    }

    [Fact]
    public async Task ItSupportsStaticStringContextStringAsync()
    {
        // Arrange
        static string Test(string input, ContextVariables localVariables)
        {
            s_actual = s_expected;
            localVariables["canary"] = s_expected;
            localVariables.Update("x y z");
            // This value should overwrite "x y z"
            return "new data";
        }

        var variables = new ContextVariables(string.Empty);

        // Act
        var function = SKFunctionFactory.CreateFromMethod(Method(Test), loggerFactory: this._logger.Object);
        Assert.NotNull(function);

        var result = await function.InvokeAsync(this._kernel, variables);

        // Assert
        Assert.Equal(s_expected, s_actual);
        Assert.Equal(s_expected, variables["canary"]);
        Assert.Equal("new data", variables.Input);
        Assert.Equal("new data", result.GetValue<string>());
    }

    [Fact]
    public async Task ItSupportsStaticStringContextTaskStringAsync()
    {
        // Arrange
        static Task<string> Test(string input, ContextVariables localVariables)
        {
            s_actual = s_expected;
            localVariables["canary"] = s_expected;
            localVariables.Update("x y z");
            // This value should overwrite "x y z"
            return Task.FromResult("new data");
        }

        var variables = new ContextVariables(string.Empty);
        // Act
        var function = SKFunctionFactory.CreateFromMethod(Method(Test), loggerFactory: this._logger.Object);
        Assert.NotNull(function);

        var result = await function.InvokeAsync(this._kernel, variables);

        // Assert
        Assert.Equal(s_expected, s_actual);
        Assert.Equal(s_expected, variables["canary"]);
        Assert.Equal("new data", variables.Input);
        Assert.Equal("new data", result.GetValue<string>());
    }

    [Fact]
    public async Task ItSupportsStaticContextValueTaskContextAsync()
    {
        // Arrange
        static ValueTask Test(string input, ContextVariables localVariables)
        {
            localVariables.Update(input + "abc");

            return new ValueTask();
        }

        var variables = new ContextVariables("test");

        // Act
        var function = SKFunctionFactory.CreateFromMethod(Method(Test), loggerFactory: this._logger.Object);
        Assert.NotNull(function);

        FunctionResult result = await function.InvokeAsync(this._kernel, variables);

        // Assert
        Assert.Equal("testabc", variables.Input);
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

        var variables = new ContextVariables(string.Empty);

        // Act
        var function = SKFunctionFactory.CreateFromMethod(Method(TestAsync), loggerFactory: this._logger.Object);
        Assert.NotNull(function);

        await function.InvokeAsync(this._kernel, variables);

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

        var variables = new ContextVariables(string.Empty);

        // Act
        var function = SKFunctionFactory.CreateFromMethod(Method(TestAsync), loggerFactory: this._logger.Object);
        Assert.NotNull(function);

        await function.InvokeAsync(this._kernel, variables);

        // Assert
        Assert.Equal(s_expected, s_actual);
    }

    [Fact]
    public async Task ItSupportsStaticContextTaskAsync()
    {
        // Arrange
        static Task TestAsync(ContextVariables localVariables)
        {
            s_actual = s_expected;
            localVariables["canary"] = s_expected;
            localVariables.Update("x y z");
            return Task.CompletedTask;
        }

        var variables = new ContextVariables(string.Empty);

        // Act
        var function = SKFunctionFactory.CreateFromMethod(Method(TestAsync), loggerFactory: this._logger.Object);
        Assert.NotNull(function);

        var result = await function.InvokeAsync(this._kernel, variables);

        // Assert
        Assert.Equal(s_expected, s_actual);
        Assert.Equal(s_expected, variables["canary"]);
        Assert.Equal("x y z", variables.Input);
        Assert.Null(result.GetValue<string>());
    }

    [Fact]
    public async Task ItSupportsStaticStringContextTaskAsync()
    {
        // Arrange
        static Task TestAsync(string input, ContextVariables localVariables)
        {
            s_actual = s_expected;
            localVariables["canary"] = s_expected;
            localVariables.Update(input + "x y z");
            return Task.CompletedTask;
        }

        var variables = new ContextVariables("input:");

        // Act
        var function = SKFunctionFactory.CreateFromMethod(Method(TestAsync), loggerFactory: this._logger.Object);
        Assert.NotNull(function);

        var result = await function.InvokeAsync(this._kernel, variables);

        // Assert
        Assert.Equal(s_expected, s_actual);
        Assert.Equal(s_expected, variables["canary"]);
        Assert.Equal("input:x y z", variables.Input);
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

        var variables = new ContextVariables(string.Empty);

        // Act
        var function = SKFunctionFactory.CreateFromMethod(Method(TestAsync), loggerFactory: this._logger.Object);
        Assert.NotNull(function);

        await function.InvokeAsync(this._kernel, variables);

        // Assert
        Assert.Equal(s_expected, s_actual);
    }

    [Fact]
    public async Task ItSupportsUsingNamedInputValueFromContextAsync()
    {
        static string Test(string input) => "Result: " + input;

        var variables = new ContextVariables("input value");

        // Act
        var function = SKFunctionFactory.CreateFromMethod(Method(Test));
        Assert.NotNull(function);

        FunctionResult result = await function.InvokeAsync(this._kernel, variables);

        // Assert
        Assert.Equal("Result: input value", variables.Input);
    }

    [Fact]
    public async Task ItSupportsUsingNonNamedInputValueFromContextAsync()
    {
        static string Test(string other) => "Result: " + other;

        var variables = new ContextVariables("input value");

        // Act
        var function = SKFunctionFactory.CreateFromMethod(Method(Test));
        Assert.NotNull(function);

        FunctionResult result = await function.InvokeAsync(this._kernel, variables);

        // Assert
        Assert.Equal("Result: input value", variables.Input);
    }

    [Fact]
    public async Task ItSupportsUsingNonNamedInputValueFromContextEvenWhenThereAreMultipleParametersAsync()
    {
        static string Test(int something, long orother) => "Result: " + (something + orother);

        var variables = new ContextVariables("42");
        variables.Set("orother", "8");

        // Act
        var function = SKFunctionFactory.CreateFromMethod(Method(Test));
        Assert.NotNull(function);

        FunctionResult result = await function.InvokeAsync(this._kernel, variables);

        // Assert
        Assert.Equal("Result: 50", variables.Input);
    }

    [Fact]
    public async Task ItSupportsPreferringNamedValueOverInputFromContextAsync()
    {
        static string Test(string other) => "Result: " + other;

        var variables = new ContextVariables("input value");
        variables.Set("other", "other value");

        // Act
        var function = SKFunctionFactory.CreateFromMethod(Method(Test));
        Assert.NotNull(function);

        FunctionResult result = await function.InvokeAsync(this._kernel, variables);

        // Assert
        Assert.Equal("Result: other value", variables.Input);
    }

    [Fact]
    public async Task ItSupportsOverridingNameWithAttributeAsync()
    {
        static string Test([SKName("input"), Description("description")] string other) => "Result: " + other;

        var variables = new ContextVariables("input value");
        variables.Set("other", "other value");

        // Act
        var function = SKFunctionFactory.CreateFromMethod(Method(Test));
        Assert.NotNull(function);

        FunctionResult result = await function.InvokeAsync(this._kernel, variables);

        // Assert
        Assert.Equal("Result: input value", variables.Input);
    }

    [Fact]
    public async Task ItSupportNullDefaultValuesOverInputAsync()
    {
        static string Test(string? input = null, string? other = null) => "Result: " + (other is null);

        var variables = new ContextVariables("input value");

        // Act
        var function = SKFunctionFactory.CreateFromMethod(Method(Test));
        Assert.NotNull(function);

        FunctionResult result = await function.InvokeAsync(this._kernel, variables);

        // Assert
        Assert.Equal("Result: True", variables.Input);
    }

    [Fact]
    public async Task ItSupportsConvertingFromManyTypesAsync()
    {
        static string Test(int a, long b, decimal c, Guid d, DateTimeOffset e, DayOfWeek? f) =>
            $"{a} {b} {c} {d} {e:R} {f}";

        var variables = new ContextVariables(string.Empty);
        variables.Set("a", "1");
        variables.Set("b", "-2");
        variables.Set("c", "1234");
        variables.Set("d", "7e08cc00-1d71-4558-81ed-69929499dea1");
        variables.Set("e", "Thu, 25 May 2023 20:17:30 GMT");
        variables.Set("f", "Monday");

        // Act
        var function = SKFunctionFactory.CreateFromMethod(Method(Test));
        Assert.NotNull(function);

        FunctionResult result = await function.InvokeAsync(this._kernel, variables);

        // Assert
        Assert.Equal("1 -2 1234 7e08cc00-1d71-4558-81ed-69929499dea1 Thu, 25 May 2023 20:17:30 GMT Monday", variables.Input);
    }

    [Fact]
    public async Task ItSupportsConvertingFromTypeConverterAttributedTypesAsync()
    {
        static int Test(MyCustomType mct) => mct.Value * 2;

        var variables = new ContextVariables(string.Empty);
        variables.Set("mct", "42");

        // Act
        var function = SKFunctionFactory.CreateFromMethod(Method(Test));
        Assert.NotNull(function);

        FunctionResult result = await function.InvokeAsync(this._kernel, variables);

        // Assert
        Assert.Equal("84", variables.Input);
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
        var variables = new ContextVariables("1");

        async Task AssertResult(Delegate d, ContextVariables localVariables, string? expected)
        {
            var result = await SKFunctionFactory.CreateFromMethod(d, functionName: "Test")!.InvokeAsync(this._kernel, variables);

            Assert.Equal(expected, localVariables.Input);
        }

        // Act/Assert
        await AssertResult((sbyte input) => input * 2, variables, "2");
        await AssertResult((byte input) => input * 2, variables, "4");
        await AssertResult((short input) => input * 2, variables, "8");
        await AssertResult((ushort input) => input * 2, variables, "16");
        await AssertResult((int input) => input * 2, variables, "32");
        await AssertResult((uint input) => input * 2, variables, "64");
        await AssertResult((long input) => input * 2, variables, "128");
        await AssertResult((ulong input) => input * 2, variables, "256");
        await AssertResult((float input) => input * 2, variables, "512");
        await AssertResult((double input) => input * 2, variables, "1024");
        await AssertResult((int input) => Task.FromResult(input * 2), variables, "2048");
        await AssertResult((long input) => Task.FromResult(input * 2), variables, "4096");
        await AssertResult((int input) => new ValueTask<int>(input * 2), variables, "8192");
        await AssertResult((long input) => new ValueTask<long>(input * 2), variables, "16384");
        await AssertResult((long? input) => input!.Value * 2, variables, "32768");
        await AssertResult((TimeSpan input) => TimeSpan.FromTicks(input.Ticks * 2), variables, "65536.00:00:00");
        await AssertResult((TimeSpan? input) => (int?)null, variables, "");

        variables.Update("http://example.com/semantic");
        await AssertResult((Uri input) => new Uri(input, "kernel"), variables, "http://example.com/kernel");
    }

    [Fact]
    public async Task ItUsesContextCultureForParsingFormattingAsync()
    {
        // Arrange
        var variables = new ContextVariables(string.Empty);
        KernelFunction func = SKFunctionFactory.CreateFromMethod((double input) => input * 2, functionName: "Test");
        FunctionResult result;

        // Act/Assert

        this._kernel.Culture = new CultureInfo("fr-FR");
        variables.Update("12,34"); // tries first to parse with the specified culture
        result = await func.InvokeAsync(this._kernel, variables);
        Assert.Equal("24,68", variables.Input);

        this._kernel.Culture = new CultureInfo("fr-FR");
        variables.Update("12.34"); // falls back to invariant culture
        result = await func.InvokeAsync(this._kernel, variables);
        Assert.Equal("24,68", variables.Input);

        this._kernel.Culture = new CultureInfo("en-US");
        variables.Update("12.34"); // works with current culture
        result = await func.InvokeAsync(this._kernel, variables);
        Assert.Equal("24.68", variables.Input);

        this._kernel.Culture = new CultureInfo("en-US");
        variables.Update("12,34"); // not parsable with current or invariant culture
        await Assert.ThrowsAsync<ArgumentOutOfRangeException>(() => func.InvokeAsync(this._kernel, variables));
    }

    [Fact]
    public async Task ItThrowsWhenItFailsToConvertAnArgumentAsync()
    {
        static string Test(Guid g) => g.ToString();

        var variables = new ContextVariables(string.Empty);
        variables.Set("g", "7e08cc00-1d71-4558-81ed-69929499dxyz");

        // Act
        var function = SKFunctionFactory.CreateFromMethod(Method(Test));
        Assert.NotNull(function);

        var ex = await Assert.ThrowsAsync<ArgumentOutOfRangeException>(() => function.InvokeAsync(this._kernel, variables));

        //Assert
        AssertExtensions.AssertIsArgumentOutOfRange(ex, "g", variables["g"]);
    }

    [Fact]
    public void ItExposesMetadataFromDelegate()
    {
        [Description("Concat information")]
        static string Test(Guid id, string name, [SKName("old")] int age) => $"{id} {name} {age}";

        // Act
        var function = SKFunctionFactory.CreateFromMethod(Test);

        // Assert
        Assert.Contains("Test", function.Name, StringComparison.Ordinal);
        Assert.Equal("Concat information", function.Description);
        Assert.Equal("id", function.GetMetadata().Parameters[0].Name);
        Assert.Equal("name", function.GetMetadata().Parameters[1].Name);
        Assert.Equal("old", function.GetMetadata().Parameters[2].Name);
    }

    [Fact]
    public void ItExposesMetadataFromMethodInfo()
    {
        [Description("Concat information")]
        static string Test(Guid id, string name, [SKName("old")] int age) => $"{id} {name} {age}";

        // Act
        var function = SKFunctionFactory.CreateFromMethod(Method(Test));

        // Assert
        Assert.Contains("Test", function.Name, StringComparison.Ordinal);
        Assert.Equal("Concat information", function.Description);
        Assert.Equal("id", function.GetMetadata().Parameters[0].Name);
        Assert.Equal("name", function.GetMetadata().Parameters[1].Name);
        Assert.Equal("old", function.GetMetadata().Parameters[2].Name);
    }

    [Fact]
    public async Task ItCanReturnBasicTypesAsync()
    {
        // Arrange
        static int TestInt(int number) => number;
        static double TestDouble(double number) => number;
        static string TestString(string str) => str;
        static bool TestBool(bool flag) => flag;

        var function1 = SKFunctionFactory.CreateFromMethod(Method(TestInt));
        var function2 = SKFunctionFactory.CreateFromMethod(Method(TestDouble));
        var function3 = SKFunctionFactory.CreateFromMethod(Method(TestString));
        var function4 = SKFunctionFactory.CreateFromMethod(Method(TestBool));

        // Act
        FunctionResult result1 = await function1.InvokeAsync(this._kernel, new ContextVariables("42"));
        FunctionResult result2 = await function2.InvokeAsync(this._kernel, new ContextVariables("3.14"));
        FunctionResult result3 = await function3.InvokeAsync(this._kernel, new ContextVariables("test-string"));
        FunctionResult result4 = await function4.InvokeAsync(this._kernel, new ContextVariables("true"));

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

        var variables = new ContextVariables(string.Empty);
        variables.Set("instance", "42");

        var function = SKFunctionFactory.CreateFromMethod(Method(TestCustomType));

        // Act
        FunctionResult result = await function.InvokeAsync(this._kernel, variables);

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

        var function = SKFunctionFactory.CreateFromMethod(Method(TestAsyncEnumerableTypeAsync));

        // Act
        FunctionResult result = await function.InvokeAsync(this._kernel, new ContextVariables(string.Empty));

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

    [Fact]
    public async Task ItPropagatesOriginalExceptionTypeAsync()
    {
        // Arrange
        var variables = new ContextVariables(string.Empty);
        Exception expected = new FormatException("expected");
        KernelFunction func = SKFunctionFactory.CreateFromMethod(() => { throw expected; });

        // Act
        Exception actual = await Record.ExceptionAsync(() => func.InvokeAsync(this._kernel, variables));

        // Assert
        Assert.Same(expected, actual);
    }

    private static MethodInfo Method(Delegate method)
    {
        return method.Method;
    }
}
