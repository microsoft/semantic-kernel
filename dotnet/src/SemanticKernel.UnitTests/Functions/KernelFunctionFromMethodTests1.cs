// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Globalization;
using System.Linq;
using System.Text.Json;
using System.Text.Json.Nodes;
using System.Text.Json.Serialization;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel;
using Moq;
using SemanticKernel.UnitTests.Functions.JsonSerializerContexts;
using Xunit;

namespace SemanticKernel.UnitTests.Functions;

public sealed class KernelFunctionFromMethodTests1
{
    private const string InputParameterName = "input";
    private static readonly KernelFunction s_nopFunction = KernelFunctionFactory.CreateFromMethod(() => { });

    private readonly Kernel _kernel;
    private readonly Mock<ILoggerFactory> _logger;

    private static string s_expected = string.Empty;
    private static string s_actual = string.Empty;

    public KernelFunctionFromMethodTests1()
    {
        this._kernel = new Kernel();
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

        // Act
        var function = KernelFunctionFactory.CreateFromMethod(Test, loggerFactory: this._logger.Object);
        Assert.NotNull(function);

        await function.InvokeAsync(this._kernel);

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

        // Act
        var function = KernelFunctionFactory.CreateFromMethod(Test, loggerFactory: this._logger.Object);
        Assert.NotNull(function);

        FunctionResult result = await function.InvokeAsync(this._kernel);

        // Assert
        Assert.Equal(s_expected, s_actual);
        Assert.Equal(s_expected, result.GetValue<string>());
        Assert.Equal(s_expected, result.ToString());
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

        // Act
        var function = KernelFunctionFactory.CreateFromMethod(Test, loggerFactory: this._logger.Object);
        Assert.NotNull(function);

        FunctionResult result = await function.InvokeAsync(this._kernel);

        // Assert
        Assert.Equal(s_expected, s_actual);
        Assert.Equal(s_expected, result.GetValue<string>());
        Assert.Equal(s_expected, result.ToString());
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

        // Act
        var function = KernelFunctionFactory.CreateFromMethod(Test, loggerFactory: this._logger.Object);
        Assert.NotNull(function);

        FunctionResult result = await function.InvokeAsync(this._kernel);

        // Assert
        Assert.Equal(s_expected, s_actual);
        Assert.Equal(s_expected, result.GetValue<string>());
        Assert.Equal(s_expected, result.ToString());
    }

    [Fact]
    public async Task ItSupportsStaticVoidAsync()
    {
        // Arrange
        static void Test()
        {
            s_actual = s_expected;
        }

        // Act
        var function = KernelFunctionFactory.CreateFromMethod(Test, loggerFactory: this._logger.Object);
        Assert.NotNull(function);

        var result = await function.InvokeAsync(this._kernel);

        // Assert
        Assert.Equal(s_expected, s_actual);
        Assert.Null(result.GetValue<object?>());
        Assert.Empty(result.ToString());
    }

    [Fact]
    public async Task ItSupportsStaticAsync()
    {
        // Arrange
        static string Test(string someVar)
        {
            s_actual = someVar;
            return "abc";
        }

        var arguments = new KernelArguments
        {
            ["someVar"] = s_expected
        };

        // Act
        var function = KernelFunctionFactory.CreateFromMethod(Test, loggerFactory: this._logger.Object);
        Assert.NotNull(function);

        var result = await function.InvokeAsync(this._kernel, arguments);

        // Assert
        Assert.Equal(s_expected, s_actual);
        Assert.Equal("abc", result.GetValue<string>());
        Assert.Equal("abc", result.ToString());
    }

    [Fact]
    public async Task ItSupportsInstanceStringStringNullableAsync()
    {
        // Arrange
        int invocationCount = 0;

        string? Test(string someVar)
        {
            invocationCount++;
            s_actual = someVar;
            return "abc";
        }

        var arguments = new KernelArguments
        {
            ["someVar"] = s_expected
        };

        // Act
        Func<string, string?> method = Test;
        var function = KernelFunctionFactory.CreateFromMethod(method, loggerFactory: this._logger.Object);
        Assert.NotNull(function);

        var result = await function.InvokeAsync(this._kernel, arguments);

        // Assert
        Assert.Equal(1, invocationCount);
        Assert.Equal(s_expected, s_actual);
        Assert.Equal("abc", result.GetValue<string>());
        Assert.Equal("abc", result.ToString());
    }

    [Fact]
    public async Task ItSupportsInstanceStringTaskAsync()
    {
        // Arrange
        int invocationCount = 0;

        async Task TestAsync(string canary)
        {
            await Task.Delay(0);
            invocationCount++;
            s_actual = canary;
        }

        var arguments = new KernelArguments
        {
            ["canary"] = s_expected
        };

        // Act
        Func<string, Task> method = TestAsync;
        var function = KernelFunctionFactory.CreateFromMethod(method, loggerFactory: this._logger.Object);
        Assert.NotNull(function);

        var result = await function.InvokeAsync(this._kernel, arguments);

        // Assert
        Assert.Equal(1, invocationCount);
        Assert.Equal(s_expected, s_actual);
        Assert.Null(result.GetValue<object?>());
        Assert.Empty(result.ToString());
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

        var arguments = new KernelArguments() { [InputParameterName] = ".blah" };

        // Act
        Action<string> method = Test;
        var function = KernelFunctionFactory.CreateFromMethod(method, loggerFactory: this._logger.Object);
        Assert.NotNull(function);

        var result = await function.InvokeAsync(this._kernel, arguments);

        // Assert
        Assert.Equal(1, invocationCount);
        Assert.Equal(s_expected + ".blah", s_actual);
        Assert.Null(result.GetValue<object?>());
        Assert.Empty(result.ToString());
    }

    [Fact]
    public async Task ItSupportsInstanceStringStringAsync()
    {
        // Arrange
        int invocationCount = 0;

        string Test(string input)
        {
            invocationCount++;
            return input;
        }

        var arguments = new KernelArguments() { [InputParameterName] = "foo-bar" };

        // Act
        Func<string, string> method = Test;
        var function = KernelFunctionFactory.CreateFromMethod(method, loggerFactory: this._logger.Object);
        Assert.NotNull(function);

        var result = await function.InvokeAsync(this._kernel, arguments);

        // Assert
        Assert.Equal(1, invocationCount);
        Assert.Equal("foo-bar", result.GetValue<string>());
        Assert.Equal("foo-bar", result.ToString());
    }

    [Fact]
    public async Task ItSupportsInstanceStringTaskStringAsync()
    {
        // Arrange
        int invocationCount = 0;

        Task<string> Test(string input)
        {
            invocationCount++;
            return Task.FromResult("hello there");
        }

        var arguments = new KernelArguments() { [InputParameterName] = string.Empty };

        // Act
        Func<string, Task<string>> method = Test;
        var function = KernelFunctionFactory.CreateFromMethod(method, loggerFactory: this._logger.Object);
        Assert.NotNull(function);

        var result = await function.InvokeAsync(this._kernel, arguments);

        // Assert
        Assert.Equal(1, invocationCount);
        Assert.Equal("hello there", result.GetValue<string>());
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

        var arguments = new KernelArguments();

        // Act
        Action<Kernel> method = Test;
        var function = KernelFunctionFactory.CreateFromMethod(method);
        Assert.NotNull(function);

        var result = await function.InvokeAsync(this._kernel, arguments);

        // Assert
        Assert.Equal(1, invocationCount);
        Assert.Equal(this._kernel, actualKernel);
        Assert.Null(result.GetValue<object?>());
        Assert.Empty(result.ToString());
    }

    [Fact]
    public async Task ItSupportsStaticStringStringAsync()
    {
        // Arrange
        static string Test(string input)
        {
            s_actual = input;
            return "new data";
        }

        var arguments = new KernelArguments() { [InputParameterName] = s_expected };

        // Act
        var function = KernelFunctionFactory.CreateFromMethod(Test, loggerFactory: this._logger.Object);
        Assert.NotNull(function);

        var result = await function.InvokeAsync(this._kernel, arguments);

        // Assert
        Assert.Equal(s_expected, s_actual);
        Assert.Equal("new data", result.GetValue<string>());
        Assert.Equal("new data", result.ToString());
    }

    [Fact]
    public async Task ItSupportsStaticStringTaskStringAsync()
    {
        // Arrange
        static Task<string> Test(string input)
        {
            s_actual = input;
            return Task.FromResult("new data");
        }

        var arguments = new KernelArguments() { [InputParameterName] = s_expected };

        // Act
        var function = KernelFunctionFactory.CreateFromMethod(Test, loggerFactory: this._logger.Object);
        Assert.NotNull(function);

        var result = await function.InvokeAsync(this._kernel, arguments);

        // Assert
        Assert.Equal(s_expected, s_actual);
        Assert.Equal("new data", result.GetValue<string>());
        Assert.Equal("new data", result.ToString());
    }

    [Fact]
    public async Task ItSupportsStaticValueTaskAsync()
    {
        // Arrange
        s_expected = "testabc";

        static ValueTask Test(string input)
        {
            s_actual = input + "abc";
            return new ValueTask();
        }

        var arguments = new KernelArguments() { [InputParameterName] = "test" };

        // Act
        var function = KernelFunctionFactory.CreateFromMethod(Test, loggerFactory: this._logger.Object);
        Assert.NotNull(function);

        FunctionResult result = await function.InvokeAsync(this._kernel, arguments);

        // Assert
        Assert.Equal(s_expected, s_actual);
        Assert.Null(result.GetValue<object?>());
        Assert.Empty(result.ToString());
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

        var arguments = new KernelArguments() { [InputParameterName] = string.Empty };

        // Act
        var function = KernelFunctionFactory.CreateFromMethod(TestAsync, loggerFactory: this._logger.Object);
        Assert.NotNull(function);

        var result = await function.InvokeAsync(this._kernel, arguments);

        // Assert
        Assert.Equal(s_expected, s_actual);
        Assert.Null(result.GetValue<object?>());
        Assert.Empty(result.ToString());
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

        var arguments = new KernelArguments() { [InputParameterName] = string.Empty };

        // Act
        var function = KernelFunctionFactory.CreateFromMethod(TestAsync, loggerFactory: this._logger.Object);
        Assert.NotNull(function);

        var result = await function.InvokeAsync(this._kernel, arguments);

        // Assert
        Assert.Equal(s_expected, s_actual);
        Assert.Null(result.GetValue<object?>());
        Assert.Empty(result.ToString());
    }

    [Fact]
    public async Task ItSupportsStaticTaskAsync()
    {
        // Arrange
        s_expected = "x y z";

        static Task TestAsync()
        {
            s_actual = s_expected;
            return Task.CompletedTask;
        }

        var arguments = new KernelArguments();

        // Act
        var function = KernelFunctionFactory.CreateFromMethod(TestAsync, loggerFactory: this._logger.Object);
        Assert.NotNull(function);

        var result = await function.InvokeAsync(this._kernel, arguments);

        // Assert
        Assert.Equal(s_expected, s_actual);
        Assert.Null(result.GetValue<object?>());
        Assert.Empty(result.ToString());
    }

    [Fact]
    public async Task ItSupportsStaticStringAsync()
    {
        // Arrange
        s_expected = "x y z";

        static Task TestAsync(string input)
        {
            s_actual = input;
            return Task.CompletedTask;
        }

        var arguments = new KernelArguments() { [InputParameterName] = "x y z" };

        // Act
        var function = KernelFunctionFactory.CreateFromMethod(TestAsync, loggerFactory: this._logger.Object);
        Assert.NotNull(function);

        var result = await function.InvokeAsync(this._kernel, arguments);

        // Assert
        Assert.Equal(s_expected, s_actual);
        Assert.Null(result.GetValue<object?>());
        Assert.Empty(result.ToString());
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

        var arguments = new KernelArguments();

        // Act
        var function = KernelFunctionFactory.CreateFromMethod(TestAsync, loggerFactory: this._logger.Object);
        Assert.NotNull(function);

        var result = await function.InvokeAsync(this._kernel, arguments);

        // Assert
        Assert.Equal(s_expected, s_actual);
        Assert.Null(result.GetValue<object?>());
        Assert.Empty(result.ToString());
    }

    [Fact]
    public async Task ItSupportsUsingNamedInputValueAsync()
    {
        static string Test(string input) => "Result: " + input;

        var arguments = new KernelArguments() { [InputParameterName] = "input value" };

        // Act
        var function = KernelFunctionFactory.CreateFromMethod(Test);
        Assert.NotNull(function);

        FunctionResult result = await function.InvokeAsync(this._kernel, arguments);

        // Assert
        Assert.Equal("Result: input value", result.GetValue<string>());
        Assert.Equal("Result: input value", result.ToString());
    }

    [Fact]
    public async Task ItSupportsPreferringNamedValueOverInputAsync()
    {
        static string Test(string other) => "Result: " + other;

        var arguments = new KernelArguments()
        {
            [InputParameterName] = "input value",
            ["other"] = "other value"
        };

        // Act
        var function = KernelFunctionFactory.CreateFromMethod(Test);
        Assert.NotNull(function);

        FunctionResult result = await function.InvokeAsync(this._kernel, arguments);

        // Assert
        Assert.Equal("Result: other value", result.GetValue<string>());
        Assert.Equal("Result: other value", result.ToString());
    }

    [Fact]
    public async Task ItSupportsOverridingNameWithAttributeAsync()
    {
        static string Test([Description("description")] string input) => "Result: " + input;

        var arguments = new KernelArguments()
        {
            [InputParameterName] = "input value",
            ["other"] = "other value"
        };

        // Act
        var function = KernelFunctionFactory.CreateFromMethod(Test);
        Assert.NotNull(function);

        FunctionResult result = await function.InvokeAsync(this._kernel, arguments);

        // Assert
        Assert.Equal("Result: input value", result.GetValue<string>());
        Assert.Equal("Result: input value", result.ToString());
    }

    [Fact]
    public async Task ItSupportNullDefaultValuesOverInputAsync()
    {
        static string Test(string? input = null, string? other = null) => "Result: " + (other is null);

        var arguments = new KernelArguments() { [InputParameterName] = "input value" };

        // Act
        var function = KernelFunctionFactory.CreateFromMethod(Test);
        Assert.NotNull(function);

        FunctionResult result = await function.InvokeAsync(this._kernel, arguments);

        // Assert
        Assert.Equal("Result: True", result.GetValue<string>());
        Assert.Equal("Result: True", result.ToString());
    }

    [Fact]
    public async Task ItSupportFunctionResultAsync()
    {
        static FunctionResult Test() => new(s_nopFunction, "fake-result", CultureInfo.InvariantCulture);

        // Act
        var function = KernelFunctionFactory.CreateFromMethod(Test);
        Assert.NotNull(function);

        FunctionResult result = await function.InvokeAsync(this._kernel);

        // Assert
        Assert.NotNull(result);
        Assert.Equal("fake-result", result.GetValue<string>());
        Assert.Equal("fake-result", result.ToString());
    }

    [Fact]
    public async Task ItSupportFunctionResultTaskAsync()
    {
        // Arrange
        static Task<FunctionResult> Test()
        {
            var functionResult = new FunctionResult(s_nopFunction, "fake-result", CultureInfo.InvariantCulture);
            return Task.FromResult(functionResult);
        }

        // Act
        var function = KernelFunctionFactory.CreateFromMethod(Test);
        Assert.NotNull(function);

        FunctionResult result = await function.InvokeAsync(this._kernel);

        // Assert
        Assert.NotNull(result);
        Assert.Equal("fake-result", result.GetValue<string>());
        Assert.Equal("fake-result", result.ToString());
    }

    [Fact]
    public async Task ItSupportFunctionResultValueTaskAsync()
    {
        // Arrange
        static ValueTask<FunctionResult> Test()
        {
            var functionResult = new FunctionResult(s_nopFunction, "fake-result", CultureInfo.InvariantCulture);
            return ValueTask.FromResult(functionResult);
        }

        // Act
        var function = KernelFunctionFactory.CreateFromMethod(Test);
        Assert.NotNull(function);

        FunctionResult result = await function.InvokeAsync(this._kernel);

        // Assert
        Assert.NotNull(result);
        Assert.Equal("fake-result", result.GetValue<string>());
        Assert.Equal("fake-result", result.ToString());
    }

    [Fact]
    public async Task ItSupportsConvertingFromManyTypesAsync()
    {
        static string Test(int a, long b, decimal c, Guid d, DateTimeOffset e, DayOfWeek? f) =>
            $"{a} {b} {c} {d} {e:R} {f}";

        var arguments = new KernelArguments
        {
            ["a"] = "1",
            ["b"] = -2,
            ["c"] = "1234",
            ["d"] = Guid.Parse("7e08cc00-1d71-4558-81ed-69929499dea1"),
            ["e"] = "Thu, 25 May 2023 20:17:30 GMT",
            ["f"] = DayOfWeek.Monday
        };

        // Act
        var function = KernelFunctionFactory.CreateFromMethod(Test);
        Assert.NotNull(function);

        FunctionResult result = await function.InvokeAsync(this._kernel, arguments);

        // Assert
        Assert.Equal("1 -2 1234 7e08cc00-1d71-4558-81ed-69929499dea1 Thu, 25 May 2023 20:17:30 GMT Monday", result.GetValue<string>());
        Assert.Equal("1 -2 1234 7e08cc00-1d71-4558-81ed-69929499dea1 Thu, 25 May 2023 20:17:30 GMT Monday", result.ToString());
    }

    [Fact]
    public async Task ItSupportsConvertingFromTypeConverterAttributedTypesAsync()
    {
        static int Test(MyCustomType mct) => mct.Value * 2;

        var arguments = new KernelArguments
        {
            ["mct"] = "42"
        };

        // Act
        var function = KernelFunctionFactory.CreateFromMethod(Test);
        Assert.NotNull(function);

        FunctionResult result = await function.InvokeAsync(this._kernel, arguments);

        // Assert
        Assert.Equal(84, result.GetValue<int>());
        Assert.Equal("84", result.ToString());
    }

    [Theory]
    [InlineData((int)0, DayOfWeek.Sunday)]
    [InlineData((uint)1, DayOfWeek.Monday)]
    [InlineData((long)2, DayOfWeek.Tuesday)]
    [InlineData((ulong)3, DayOfWeek.Wednesday)]
    [InlineData((short)4, DayOfWeek.Thursday)]
    [InlineData((ushort)5, DayOfWeek.Friday)]
    [InlineData((byte)6, DayOfWeek.Saturday)]
    [InlineData((sbyte)0, DayOfWeek.Sunday)]
    public async Task ItSupportsConvertingAllIntegerTypesToEnumAsync(object argument, DayOfWeek expected)
    {
        // Arrange
        object? actual = null;

        var function = KernelFunctionFactory.CreateFromMethod((DayOfWeek dow) => actual = dow);

        // Act
        var result = await function.InvokeAsync(this._kernel, new() { ["dow"] = argument });

        // Assert
        Assert.Equal(expected, actual);
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
    public async Task ItSupportsConvertingArgumentsFromStringToManyTypesAsync()
    {
        // Arrange
        var arguments = new KernelArguments() { [InputParameterName] = "1" };

        async Task AssertResult(Delegate d, object? expected, string? expectedString)
        {
            var result = await KernelFunctionFactory.CreateFromMethod(d, functionName: "Test")!.InvokeAsync(this._kernel, arguments);

            Assert.Equal(expected, result.GetValue<object?>());
            Assert.Equal(expectedString, result.ToString());
        }

        // Act/Assert
        await AssertResult((sbyte input) => input * 2, 2, "2");
        await AssertResult((byte input) => input * 2, 2, "2");
        await AssertResult((short input) => input * 2, 2, "2");
        await AssertResult((ushort input) => input * 2, 2, "2");
        await AssertResult((int input) => input * 2, 2, "2");
        await AssertResult((uint input) => input * 2, (uint)2, "2");
        await AssertResult((long input) => input * 2, (long)2, "2");
        await AssertResult((ulong input) => input * 2, (ulong)2, "2");
        await AssertResult((float input) => input * 2, (float)2, "2");
        await AssertResult((double input) => input * 2, (double)2, "2");
        await AssertResult((int input) => Task.FromResult(input * 2), 2, "2");
        await AssertResult((long input) => Task.FromResult(input * 2), (long)2, "2");
        await AssertResult((int input) => new ValueTask<int>(input * 2), 2, "2");
        await AssertResult((long input) => new ValueTask<long>(input * 2), (long)2, "2");
        await AssertResult((long? input) => input!.Value * 2, (long?)2, "2");
        await AssertResult((TimeSpan input) => TimeSpan.FromTicks(input.Ticks * 2), TimeSpan.FromDays(2), "2.00:00:00");
        await AssertResult((TimeSpan? input) => (int?)null, null, "");

        arguments[InputParameterName] = "http://example.com/semantic";
        await AssertResult((Uri input) => new Uri(input, "kernel"), new Uri("http://example.com/kernel"), "http://example.com/kernel");
    }

    [Fact]
    public async Task ItSupportsArgumentsAsIsWithoutConvertingTheirTypeAsync()
    {
        //Arrange
        async Task AssertParameterType<T>(T expected)
        {
            var d = (T actual) =>
            {
                //Check the argument is of the operationCancelled type
                if (actual is not null)
                {
                    Assert.IsType<T>(actual);
                }

                //Check the argument value is the operationCancelled value
                Assert.Equal(expected, actual);
            };

            var arguments = new KernelArguments() { { "actual", (T)expected } };

            await KernelFunctionFactory.CreateFromMethod(d, functionName: "Test")!.InvokeAsync(this._kernel, arguments);
        }

        // Act & Assert
        await AssertParameterType<string?>(null);
        await AssertParameterType<string>("2");
        await AssertParameterType<byte>(2);
        await AssertParameterType<sbyte>(2);
        await AssertParameterType<short>(2);
        await AssertParameterType<ushort>(2);
        await AssertParameterType<int>(2);
        await AssertParameterType<uint>(2);
        await AssertParameterType<long>(2);
        await AssertParameterType<ulong>(2);
        await AssertParameterType<float>(2);
        await AssertParameterType<double>(2);
        await AssertParameterType<decimal>(2);
        await AssertParameterType<char>('w');
        await AssertParameterType<bool>(true);
        await AssertParameterType<DateTime>(DateTime.UtcNow);
        await AssertParameterType<DateTimeOffset>(DateTimeOffset.UtcNow);
        await AssertParameterType<TimeSpan>(TimeSpan.FromMinutes(1));
        await AssertParameterType<Guid>(Guid.NewGuid());
        await AssertParameterType<ConsoleColor>(ConsoleColor.Blue);
        await AssertParameterType<Uri>(new Uri("https://fake-random-test-host/fake-path"));
        await AssertParameterType<object>(new object());
    }

    [Fact]
    public async Task ItSupportsArgumentsImplicitConversionAsync()
    {
        //Arrange
        var arguments = new KernelArguments()
        {
            ["l"] = (int)1,                 //Passed to parameter of type long
            ["i"] = (byte)1,                //Passed to parameter of type int
            ["d"] = (float)1.0,             //Passed to parameter of type double
            ["f"] = (uint)1.0,              //Passed to parameter of type float
            ["g"] = new Guid("35626209-b0ab-458c-bfc4-43e6c7bd13dc"),   //Passed to parameter of type string
            ["dof"] = DayOfWeek.Thursday    //Passed to parameter of type int
        };

        var function = KernelFunctionFactory.CreateFromMethod((long l, int i, double d, float f, string g, int dof) =>
        {
            Assert.Equal(1, l);
            Assert.Equal(1, i);
            Assert.Equal(1.0, d);
            Assert.Equal("35626209-b0ab-458c-bfc4-43e6c7bd13dc", g);
            Assert.Equal(4, dof);
        },
        functionName: "Test");

        // Act & Assert
        await function.InvokeAsync(this._kernel, arguments);
    }

    [Fact]
    public async Task ItSupportsJsonElementArgumentsImplicitConversionAsync()
    {
        //Arrange
        var arguments = new KernelArguments()
        {
            ["l"] = JsonSerializer.Deserialize<JsonElement>((long)1),                 //Passed to parameter of type long
            ["i"] = JsonSerializer.Deserialize<JsonElement>((byte)1),                //Passed to parameter of type int
            ["d"] = JsonSerializer.Deserialize<JsonElement>((float)1.0),             //Passed to parameter of type double
            ["f"] = JsonSerializer.Deserialize<JsonElement>((uint)1.0),              //Passed to parameter of type float
            ["g"] = JsonSerializer.Deserialize<JsonElement>(JsonSerializer.Serialize(new Guid("35626209-b0ab-458c-bfc4-43e6c7bd13dc"))),   //Passed to parameter of type string
            ["dof"] = JsonSerializer.Deserialize<JsonElement>(JsonSerializer.Serialize(DayOfWeek.Thursday)),   //Passed to parameter of type int
            ["b"] = JsonSerializer.Deserialize<JsonElement>(JsonSerializer.Serialize("true")),   //Passed to parameter of type bool
        };

        var function = KernelFunctionFactory.CreateFromMethod((long l, int i, double d, float f, string g, int dof, bool b) =>
        {
            Assert.Equal(1, l);
            Assert.Equal(1, i);
            Assert.Equal(1.0, d);
            Assert.Equal("35626209-b0ab-458c-bfc4-43e6c7bd13dc", g);
            Assert.Equal(4, dof);
            Assert.True(b);
        },
        functionName: "Test");

        await function.InvokeAsync(this._kernel, arguments);
        await function.AsAIFunction().InvokeAsync(new(arguments));
    }

    [Fact]
    public async Task ItSupportsStringJsonElementArgumentsImplicitConversionAsync()
    {
        //Arrange
        var arguments = new KernelArguments()
        {
            ["l"] = JsonSerializer.Deserialize<JsonElement>(JsonSerializer.Serialize("1")),                 //Passed to parameter of type long
            ["i"] = JsonSerializer.Deserialize<JsonElement>(JsonSerializer.Serialize("1")),                //Passed to parameter of type int
            ["d"] = JsonSerializer.Deserialize<JsonElement>(JsonSerializer.Serialize("1.0")),             //Passed to parameter of type double
            ["f"] = JsonSerializer.Deserialize<JsonElement>(JsonSerializer.Serialize("1.0")),              //Passed to parameter of type float
            ["g"] = JsonSerializer.Deserialize<JsonElement>(JsonSerializer.Serialize("35626209-b0ab-458c-bfc4-43e6c7bd13dc")),   //Passed to parameter of type Guid
            ["dof"] = JsonSerializer.Deserialize<JsonElement>(JsonSerializer.Serialize("4")),   //Passed to parameter of type int
            ["b"] = JsonSerializer.Deserialize<JsonElement>(JsonSerializer.Serialize("false")),   //Passed to parameter of type bool
        };

        var function = KernelFunctionFactory.CreateFromMethod((long l, int i, double d, float f, Guid g, int dof, bool b) =>
        {
            Assert.Equal(1, l);
            Assert.Equal(1, i);
            Assert.Equal(1.0, d);
            Assert.Equal(new Guid("35626209-b0ab-458c-bfc4-43e6c7bd13dc"), g);
            Assert.Equal(4, dof);
            Assert.False(b);
        },
        functionName: "Test");

        await function.InvokeAsync(this._kernel, arguments);
        await function.AsAIFunction().InvokeAsync(new(arguments));
    }

    [Fact]
    public async Task ItSupportsParametersWithDefaultValuesAsync()
    {
        //Arrange

        static void Test(int a, long b = 20, string c = "dv", char d = 'w')
        {
            Assert.Equal(10, a);
            Assert.Equal(20, b);
            Assert.Equal("dv", c);
            Assert.Equal('w', d);
        }

        // Act
        var function = KernelFunctionFactory.CreateFromMethod(Test);

        await function.InvokeAsync(this._kernel, arguments: new() { { "a", 10 } }); // Passing value for the 'a' parameter only.
    }

    [Fact]
    public async Task ItShouldMarshalArgumentsOfValueTypeAsync()
    {
        //Scenario #1 - passing int argument to a method that accepts int
        object? actual = null;
        var sut = KernelFunctionFactory.CreateFromMethod((int val) => { actual = val; });
        await sut.InvokeAsync(this._kernel, new() { ["val"] = 5 });
        Assert.Equal(5, actual);

        //Scenario #2 - passing null argument to a method that accepts int
        sut = KernelFunctionFactory.CreateFromMethod((int val) => { actual = val; });
        await Assert.ThrowsAsync<ArgumentOutOfRangeException>(() => sut.InvokeAsync(this._kernel, new() { ["val"] = null }));

        //Scenario #3 - passing int argument to a method that accepts int?
        actual = null;
        sut = KernelFunctionFactory.CreateFromMethod((int? val) => { actual = val; });
        await sut.InvokeAsync(this._kernel, new() { ["val"] = 5 });
        Assert.Equal(5, actual);

        //Scenario #4 - passing null argument to a method that accepts int?
        actual = new();
        sut = KernelFunctionFactory.CreateFromMethod((int? val) => { actual = val; });
        await sut.InvokeAsync(this._kernel, new() { ["val"] = null });
        Assert.Null(actual);
    }

    [Fact]
    public async Task ItShouldMarshalArgumentsOfReferenceTypeAsync()
    {
        //Scenario #1 - passing string argument to a method that accepts string
        object? actual = null;
        var sut = KernelFunctionFactory.CreateFromMethod((string val) => { actual = val; });
        await sut.InvokeAsync(this._kernel, new() { ["val"] = "5" });
        Assert.Equal("5", actual);

        //Scenario #2 - passing null argument to a method that accepts string
        actual = new();
        sut = KernelFunctionFactory.CreateFromMethod((string val) => { actual = val; });
        await sut.InvokeAsync(this._kernel, new() { ["val"] = null });
        Assert.Null(actual);

        //Scenario #3 - passing string argument to a method that accepts string?
        actual = null;
        sut = KernelFunctionFactory.CreateFromMethod((string? val) => { actual = val; });
        await sut.InvokeAsync(this._kernel, new() { ["val"] = "5" });
        Assert.Equal("5", actual);

        //Scenario #4 - passing null argument to a method that accepts string?
        actual = new();
        sut = KernelFunctionFactory.CreateFromMethod((string? val) => { actual = val; });
        await sut.InvokeAsync(this._kernel, new() { ["val"] = null });
        Assert.Null(actual);
    }

    [Fact]
    public async Task ItSupportsGenericArgumentsAndReturnTypesAsync()
    {
        List<string> expected = ["1", "2", "3"];
        KernelArguments input = new() { ["val"] = expected };
        KernelFunction func;
        FunctionResult result;

        func = KernelFunctionFactory.CreateFromMethod((List<string> val) => val);
        result = await func.InvokeAsync(this._kernel, input);
        Assert.Equal(expected, result.Value);

        func = KernelFunctionFactory.CreateFromMethod((List<string> val) => Enumerable.Range(1, 3).Select(i => i.ToString(CultureInfo.InvariantCulture)));
        result = await func.InvokeAsync(this._kernel, input);
        Assert.Equal(expected, result.Value);

        func = KernelFunctionFactory.CreateFromMethod((List<string> val) => Task.FromResult(val));
        result = await func.InvokeAsync(this._kernel, input);
        Assert.Equal(expected, result.Value);

        func = KernelFunctionFactory.CreateFromMethod((List<string> val) => ValueTask.FromResult(val));
        result = await func.InvokeAsync(this._kernel, input);
        Assert.Equal(expected, result.Value);

        func = KernelFunctionFactory.CreateFromMethod((List<string> val) => val.ToAsyncEnumerable());
        result = await func.InvokeAsync(this._kernel, input);
        Assert.Equal(expected, ((IAsyncEnumerable<string>)result.Value!).ToEnumerable());
    }

    [Fact]
    public async Task ItSupportsNullableArgumentsAndReturnTypesAsync()
    {
        KernelFunction func;

        func = KernelFunctionFactory.CreateFromMethod(int? (int? arg) => arg);
        Assert.Equal(42, (await func.InvokeAsync(this._kernel, new() { ["arg"] = 42 })).Value);
        Assert.Null((await func.InvokeAsync(this._kernel, new() { ["arg"] = null })).Value);

        func = KernelFunctionFactory.CreateFromMethod(Task<int?> (int? arg) => Task.FromResult(arg));
        Assert.Equal(42, (await func.InvokeAsync(this._kernel, new() { ["arg"] = 42 })).Value);
        Assert.Null((await func.InvokeAsync(this._kernel, new() { ["arg"] = null })).Value);

        func = KernelFunctionFactory.CreateFromMethod(ValueTask<int?> (int? arg) => ValueTask.FromResult(arg));
        Assert.Equal(42, (await func.InvokeAsync(this._kernel, new() { ["arg"] = 42 })).Value);
        Assert.Null((await func.InvokeAsync(this._kernel, new() { ["arg"] = null })).Value);

        func = KernelFunctionFactory.CreateFromMethod(IEnumerable<int?> (int? arg) => (IEnumerable<int?>)[arg]);
        Assert.Equal(new int?[] { 42 }, (await func.InvokeAsync(this._kernel, new() { ["arg"] = 42 })).Value);
        Assert.Equal(new int?[] { null }, (await func.InvokeAsync(this._kernel, new() { ["arg"] = null })).Value);
    }

    [Fact]
    public async Task ItUsesContextCultureForParsingFormattingAsync()
    {
        // Arrange
        var arguments = new KernelArguments();
        KernelFunction func = KernelFunctionFactory.CreateFromMethod((double input) => input * 2, functionName: "Test");
        FunctionResult result;

        // Act/Assert

        this._kernel.Culture = new CultureInfo("fr-FR");
        arguments[InputParameterName] = "12,34"; // tries first to parse with the specified culture
        result = await func.InvokeAsync(this._kernel, arguments);
        Assert.Equal(24.68, result.GetValue<double>());
        Assert.Equal("24,68", result.ToString());

        this._kernel.Culture = new CultureInfo("fr-FR");
        arguments[InputParameterName] = "12.34"; // falls back to invariant culture
        result = await func.InvokeAsync(this._kernel, arguments);
        Assert.Equal(24.68, result.GetValue<double>());
        Assert.Equal("24,68", result.ToString());

        this._kernel.Culture = new CultureInfo("en-US");
        arguments[InputParameterName] = "12.34"; // works with current culture
        result = await func.InvokeAsync(this._kernel, arguments);
        Assert.Equal(24.68, result.GetValue<double>());
        Assert.Equal("24.68", result.ToString());

        this._kernel.Culture = new CultureInfo("en-US");
        arguments[InputParameterName] = "12,34"; // not parsable with current or invariant culture
        await Assert.ThrowsAsync<ArgumentOutOfRangeException>(() => func.InvokeAsync(this._kernel, arguments));
    }

    [Fact]
    public async Task ItThrowsWhenItFailsToConvertAnArgumentAsync()
    {
        static string Test(Guid g) => g.ToString();

        var arguments = new KernelArguments
        {
            ["g"] = "7e08cc00-1d71-4558-81ed-69929499dxyz"
        };

        // Act
        var function = KernelFunctionFactory.CreateFromMethod(Test);
        Assert.NotNull(function);

        var ex = await Assert.ThrowsAsync<ArgumentOutOfRangeException>(() => function.InvokeAsync(this._kernel, arguments));

        //Assert
        AssertExtensions.AssertIsArgumentOutOfRange(ex, "g", (string?)arguments["g"]!);
    }

    [Fact]
    public void ItExposesMetadataFromDelegate()
    {
        [Description("Concat information")]
        static string Test(Guid id, string name, int old) => $"{id} {name} {old}";

        // Act
        var function = KernelFunctionFactory.CreateFromMethod(Test);

        // Assert
        Assert.Contains("Test", function.Name, StringComparison.Ordinal);
        Assert.Equal("Concat information", function.Description);
        Assert.Equal("id", function.Metadata.Parameters[0].Name);
        Assert.Equal("name", function.Metadata.Parameters[1].Name);
        Assert.Equal("old", function.Metadata.Parameters[2].Name);
    }

    [Fact]
    public void ItExposesMetadataFromMethodInfo()
    {
        [Description("Concat information")]
        static string Test(Guid id, string name, int old) => $"{id} {name} {old}";

        // Act
        var function = KernelFunctionFactory.CreateFromMethod(Test);

        // Assert
        Assert.Contains("Test", function.Name, StringComparison.Ordinal);
        Assert.Equal("Concat information", function.Description);
        Assert.Equal("id", function.Metadata.Parameters[0].Name);
        Assert.Equal("name", function.Metadata.Parameters[1].Name);
        Assert.Equal("old", function.Metadata.Parameters[2].Name);
    }

    [Fact]
    public async Task ItCanReturnBasicTypesAsync()
    {
        // Arrange
        static int TestInt(int number) => number;
        static double TestDouble(double number) => number;
        static string TestString(string str) => str;
        static bool TestBool(bool flag) => flag;

        var function1 = KernelFunctionFactory.CreateFromMethod(TestInt);
        var function2 = KernelFunctionFactory.CreateFromMethod(TestDouble);
        var function3 = KernelFunctionFactory.CreateFromMethod(TestString);
        var function4 = KernelFunctionFactory.CreateFromMethod(TestBool);

        // Act
        FunctionResult result1 = await function1.InvokeAsync(this._kernel, new() { ["number"] = "42" });
        FunctionResult result2 = await function2.InvokeAsync(this._kernel, new() { ["number"] = "3.14" });
        FunctionResult result3 = await function3.InvokeAsync(this._kernel, new() { ["str"] = "test-string" });
        FunctionResult result4 = await function4.InvokeAsync(this._kernel, new() { ["flag"] = "true" });

        // Assert
        Assert.Equal(42, result1.GetValue<int>());
        Assert.Equal("42", result1.ToString());

        Assert.Equal(3.14, result2.GetValue<double>());
        Assert.Equal("3.14", result2.ToString());

        Assert.Equal("test-string", result3.GetValue<string>());
        Assert.Equal("test-string", result3.ToString());

        Assert.True(result4.GetValue<bool>());
        Assert.Equal("True", result4.ToString());
    }

    [Fact]
    public async Task ItCanReturnComplexTypeAsync()
    {
        // Arrange
        static MyCustomType TestCustomType(MyCustomType instance) => instance;

        var arguments = new KernelArguments
        {
            ["instance"] = "42"
        };

        var function = KernelFunctionFactory.CreateFromMethod(TestCustomType);

        // Act
        FunctionResult result = await function.InvokeAsync(this._kernel, arguments);

        var actualInstance = result.GetValue<MyCustomType>();

        // Assert
        Assert.NotNull(actualInstance);
        Assert.Equal(42, result.GetValue<MyCustomType>()?.Value);
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

        var function = KernelFunctionFactory.CreateFromMethod(TestAsyncEnumerableTypeAsync);

        // Act
        FunctionResult result = await function.InvokeAsync(this._kernel);

        // Assert
        Assert.NotNull(result);

        var asyncEnumerableResult = result.GetValue<IAsyncEnumerable<int>>();

        Assert.NotNull(asyncEnumerableResult);

        var assertResult = new List<int>();

        await foreach (var value in asyncEnumerableResult)
        {
            assertResult.Add(value);
        }

        Assert.True(assertResult.SequenceEqual([1, 2, 3]));
    }

    [Fact]
    public async Task ItCanStreamAsyncEnumerableTypeAsync()
    {
        // Arrange
        bool invoked = false;
        async IAsyncEnumerable<int> TestAsyncEnumerableTypeAsync()
        {
            invoked = true;
            for (int i = 0; i < 10; i++)
            {
                await Task.Yield();
                yield return i;
            }
        }
        KernelFunction function = KernelFunctionFactory.CreateFromMethod(TestAsyncEnumerableTypeAsync);

        // Act / Assert
        IAsyncEnumerable<int> enumerable = function.InvokeStreamingAsync<int>(this._kernel);
        Assert.False(invoked);
        IAsyncEnumerator<int> enumerator = enumerable.GetAsyncEnumerator();
        Assert.NotNull(enumerator);
        Assert.False(invoked);
        Assert.True(await enumerator.MoveNextAsync());
        Assert.True(invoked);
        Assert.Equal(0, enumerator.Current);
        for (int i = 1; i < 10; i++)
        {
            Assert.True(await enumerator.MoveNextAsync());
            Assert.Equal(i, enumerator.Current);
        }
        Assert.False(await enumerator.MoveNextAsync());
        await enumerator.DisposeAsync();
    }

    [Fact]
    public async Task ItCanStreamAsyncEnumerablePassthroughAsync()
    {
        // Arrange
        bool invoked = false;
        async IAsyncEnumerable<StreamingMethodContent> TestAsyncEnumerableTypeAsync()
        {
            invoked = true;
            for (int i = 0; i < 10; i++)
            {
                await Task.Yield();
                yield return new StreamingMethodContent(i);
            }
        }
        KernelFunction function = KernelFunctionFactory.CreateFromMethod(TestAsyncEnumerableTypeAsync);

        // Act / Assert
        IAsyncEnumerable<StreamingMethodContent> enumerable = function.InvokeStreamingAsync<StreamingMethodContent>(this._kernel);
        Assert.False(invoked);
        IAsyncEnumerator<StreamingMethodContent> enumerator = enumerable.GetAsyncEnumerator();
        Assert.NotNull(enumerator);
        Assert.False(invoked);
        Assert.True(await enumerator.MoveNextAsync());
        Assert.True(invoked);
        Assert.Equal(0, enumerator.Current.Content);
        for (int i = 1; i < 10; i++)
        {
            Assert.True(await enumerator.MoveNextAsync());
            Assert.Equal(i, enumerator.Current.Content);
        }
        Assert.False(await enumerator.MoveNextAsync());
        await enumerator.DisposeAsync();
    }

    [Fact]
    public async Task ItPropagatesOriginalExceptionTypeAsync()
    {
        // Arrange
        var arguments = new KernelArguments();
        Exception expected = new FormatException("expected");
        KernelFunction func = KernelFunctionFactory.CreateFromMethod(() => { throw expected; });

        // Act
        Exception actual = await Record.ExceptionAsync(() => func.InvokeAsync(this._kernel, arguments));

        // Assert
        Assert.Same(expected, actual);
    }

    [Fact]
    public async Task ItCanDeserializeJsonDocumentAsync()
    {
        // Arrange
        var document = JsonDocument.Parse(@"{""id"":28}");
        CustomTypeForJsonTests? actualArgValue = null;

        var func = KernelFunctionFactory.CreateFromMethod((CustomTypeForJsonTests param) => { actualArgValue = param; });

        // Act
        var res = await func.InvokeAsync(this._kernel, new() { ["param"] = document });

        // Assert
        Assert.NotNull(actualArgValue);
        Assert.Equal(28, actualArgValue.Id);
    }

    [Fact]
    public async Task ItCanDeserializeJsonElementAsync()
    {
        // Arrange
        var element = JsonDocument.Parse(@"{""id"":28}").RootElement;
        CustomTypeForJsonTests? actualArgValue = null;

        var func = KernelFunctionFactory.CreateFromMethod((CustomTypeForJsonTests param) => { actualArgValue = param; });

        // Act
        var res = await func.InvokeAsync(this._kernel, new() { ["param"] = element });

        // Assert
        Assert.NotNull(actualArgValue);
        Assert.Equal(28, actualArgValue.Id);
    }

    [Fact]
    public async Task ItCanDeserializeJsonNodeAsync()
    {
        // Arrange
        var node = JsonNode.Parse(@"{""id"":28}");
        CustomTypeForJsonTests? actualArgValue = null;

        var func = KernelFunctionFactory.CreateFromMethod((CustomTypeForJsonTests param) => { actualArgValue = param; });

        // Act
        var res = await func.InvokeAsync(this._kernel, new() { ["param"] = node });

        // Assert
        Assert.NotNull(actualArgValue);
        Assert.Equal(28, actualArgValue.Id);
    }

    [Fact]
    public async Task ItShouldNotDeserializeIfParameterTypeAndArgumentTypeAreSameAsync()
    {
        // Arrange
        var node = JsonNode.Parse(@"{""id"":28}");
        JsonNode? actualArgValue = null;

        var func = KernelFunctionFactory.CreateFromMethod((JsonNode? param) => { actualArgValue = param; });

        // Act
        var res = await func.InvokeAsync(this._kernel, new() { ["param"] = node });

        // Assert
        Assert.NotNull(actualArgValue);
        Assert.Same(node, actualArgValue);
    }

    [Fact]
    public async Task ItCanDeserializeJsonStringAsync()
    {
        // Arrange
        var jsonString = @"{""id"":28}";
        CustomTypeForJsonTests? actualArgValue = null;

        var func = KernelFunctionFactory.CreateFromMethod((CustomTypeForJsonTests param) => { actualArgValue = param; });

        // Act
        var res = await func.InvokeAsync(this._kernel, new() { ["param"] = jsonString });

        // Assert
        Assert.NotNull(actualArgValue);
        Assert.Equal(28, actualArgValue.Id);
    }

    [Fact]
    public async Task ItCanDeserializeThirdPartyJsonPrimitivesAsync()
    {
        // Arrange
        var thirdPartyJsonPrimitive = new ThirdPartyJsonPrimitive(@"{""id"":28}");
        CustomTypeForJsonTests? actualArgValue = null;

        var func = KernelFunctionFactory.CreateFromMethod((CustomTypeForJsonTests param) => { actualArgValue = param; });

        // Act
        var res = await func.InvokeAsync(this._kernel, new() { ["param"] = thirdPartyJsonPrimitive });

        // Assert
        Assert.NotNull(actualArgValue);
        Assert.Equal(28, actualArgValue.Id);
    }

    [Fact]
    public async Task ItThrowsKernelFunctionCanceledExceptionWhenOperationIsCanceledAsync()
    {
        // Arrange
        var arguments = new KernelArguments();
        var operationCancelled = new OperationCanceledException("OperationCanceledException");
        operationCancelled.Data.Add("Key", "Value");
        KernelFunction func = KernelFunctionFactory.CreateFromMethod(() => { throw operationCancelled; });

        // Act
        Exception actual = await Record.ExceptionAsync(() => func.InvokeAsync(this._kernel, arguments));

        // Assert
        Assert.NotNull(actual);
        Assert.True(actual is KernelFunctionCanceledException);
        Assert.True(actual.Data.Contains("Key"));
        Assert.Equal("Value", actual.Data["Key"]);
    }

    [Theory]
    [ClassData(typeof(TestJsonSerializerOptionsForTestParameterAndReturnTypes))]
    public async Task ItCanBeCloned(JsonSerializerOptions? jsos)
    {
        // Arrange
        var kernel = new Kernel();

        static TestReturnType StaticMethod(TestParameterType p1)
        {
            return new TestReturnType() { Result = int.Parse(p1.Value!) };
        }

        // Arrange & Act
        KernelFunction function = jsos is not null ?
            function = KernelFunctionFromMethod.Create(((Func<TestParameterType, TestReturnType>)StaticMethod).Method, jsonSerializerOptions: jsos, functionName: "f1", description: "f1-description") :
            function = KernelFunctionFromMethod.Create(((Func<TestParameterType, TestReturnType>)StaticMethod).Method, functionName: "f1", description: "f1-description");

        // Act
        function = function.Clone("new-plugin-name");

        // Assert plugin name
        Assert.Equal("new-plugin-name", function.Metadata.PluginName);

        // Assert schema
        Assert.NotEmpty(function.Metadata.Parameters);
        Assert.NotNull(function.Metadata.Parameters[0].Schema);
        Assert.Equal("{\"type\":\"object\",\"properties\":{\"Value\":{\"type\":[\"string\",\"null\"]}}}", function.Metadata.Parameters[0].Schema!.ToString());

        Assert.NotNull(function.Metadata.ReturnParameter);
        Assert.NotNull(function.Metadata.ReturnParameter.Schema);
        Assert.Equal("{\"type\":\"object\",\"properties\":{\"Result\":{\"type\":\"integer\"}}}", function.Metadata.ReturnParameter.Schema!.ToString());

        // Assert invocation
        var invokeResult = await function.InvokeAsync(this._kernel, new() { ["p1"] = """{"Value": "34"}""" }); // Check marshaling logic that deserialize JSON into target type using JSOs
        var result = invokeResult?.GetValue<TestReturnType>();
        Assert.Equal(34, result?.Result);
    }

    [Theory]
    [ClassData(typeof(TestJsonSerializerOptionsForTestParameterAndReturnTypes))]
    public void ItCanCreateFunctionMetadata(JsonSerializerOptions? jsos)
    {
        // Arrange
        static TestReturnType StaticMethod(TestParameterType p1)
        {
            return new TestReturnType() { Result = int.Parse(p1.Value!) };
        }

        // Act
        KernelFunctionMetadata metadata = jsos is not null ?
            KernelFunctionFromMethod.CreateMetadata(((Func<TestParameterType, TestReturnType>)StaticMethod).Method, jsos, functionName: "f1_name", description: "f1-description") :
            KernelFunctionFromMethod.CreateMetadata(((Func<TestParameterType, TestReturnType>)StaticMethod).Method, functionName: "f1_name", description: "f1-description");

        // Assert
        Assert.Equal("f1_name", metadata.Name);
        Assert.Equal("f1-description", metadata.Description);

        Assert.NotEmpty(metadata.Parameters);
        Assert.NotNull(metadata.Parameters[0].Schema);
        Assert.Equal("""{"type":"object","properties":{"Value":{"type":["string","null"]}}}""", metadata.Parameters[0].Schema!.ToString());

        Assert.NotNull(metadata.ReturnParameter);
        Assert.NotNull(metadata.ReturnParameter.Schema);
        Assert.Equal("""{"type":"object","properties":{"Result":{"type":"integer"}}}""", metadata.ReturnParameter.Schema!.ToString());
    }

    [Theory]
    [ClassData(typeof(TestJsonSerializerOptionsForTestParameterAndReturnTypes))]
    public void ItCanCreateFunctionMetadataUsingOverloadWithOptions(JsonSerializerOptions? jsos)
    {
        // Arrange
        static TestReturnType StaticMethod(TestParameterType p1)
        {
            return new TestReturnType() { Result = int.Parse(p1.Value!) };
        }

        KernelFunctionFromMethodOptions options = new()
        {
            FunctionName = "f1_name",
            Description = "f1-description"
        };

        // Act
        KernelFunctionMetadata metadata = jsos is not null ?
            KernelFunctionFromMethod.CreateMetadata(((Func<TestParameterType, TestReturnType>)StaticMethod).Method, jsos, options) :
            KernelFunctionFromMethod.CreateMetadata(((Func<TestParameterType, TestReturnType>)StaticMethod).Method, options);

        // Assert
        Assert.Equal("f1_name", metadata.Name);
        Assert.Equal("f1-description", metadata.Description);

        Assert.NotEmpty(metadata.Parameters);
        Assert.NotNull(metadata.Parameters[0].Schema);
        Assert.Equal("""{"type":"object","properties":{"Value":{"type":["string","null"]}}}""", metadata.Parameters[0].Schema!.ToString());

        Assert.NotNull(metadata.ReturnParameter);
        Assert.NotNull(metadata.ReturnParameter.Schema);
        Assert.Equal("""{"type":"object","properties":{"Result":{"type":"integer"}}}""", metadata.ReturnParameter.Schema!.ToString());
    }

#pragma warning disable CA1812 // Avoid uninstantiated internal classes
    private sealed class CustomTypeForJsonTests
#pragma warning restore CA1812 // Avoid uninstantiated internal classes
    {
        [JsonPropertyName("id")]
        public int Id { get; set; }
    }

    private sealed class ThirdPartyJsonPrimitive(string jsonToReturn)
    {
        public override string ToString() => jsonToReturn;
    }
}
