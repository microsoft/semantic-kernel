// Copyright (c) Microsoft. All rights reserved.

using System;
using System.ComponentModel;
using System.Globalization;
using System.Linq;
using System.Reflection;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Moq;
using Xunit;

namespace SemanticKernel.UnitTests.Functions;

public sealed class KernelFunctionTests3
{
    private readonly Kernel _kernel = new(new Mock<IServiceProvider>().Object);

    [Fact]
    public void ItDoesntThrowForValidFunctionsViaDelegate()
    {
        // Arrange
        var pluginInstance = new LocalExamplePlugin();
        MethodInfo[] methods = pluginInstance.GetType()
            .GetMethods(BindingFlags.Static | BindingFlags.Instance | BindingFlags.Public | BindingFlags.InvokeMethod)
            .Where(m => m.Name is not "GetType" and not "Equals" and not "GetHashCode" and not "ToString")
            .ToArray();

        KernelFunction[] functions = (from method in methods select KernelFunctionFactory.CreateFromMethod(method, pluginInstance, "plugin")).ToArray();

        // Act
        Assert.Equal(methods.Length, functions.Length);
        Assert.All(functions, Assert.NotNull);
    }

    [Fact]
    public void ItDoesNotThrowForValidFunctionsViaPlugin()
    {
        // Arrange
        var pluginInstance = new LocalExamplePlugin();
        MethodInfo[] methods = pluginInstance.GetType()
            .GetMethods(BindingFlags.Static | BindingFlags.Instance | BindingFlags.Public | BindingFlags.InvokeMethod)
            .Where(m => m.Name is not "GetType" and not "Equals" and not "GetHashCode" and not "ToString")
            .ToArray();

        KernelFunction[] functions = KernelPluginFactory.CreateFromObject(pluginInstance).ToArray();

        // Act
        Assert.Equal(methods.Length, functions.Length);
        Assert.All(functions, f => Assert.NotNull(f));
    }

    [Fact]
    public void ItThrowsForInvalidFunctions()
    {
        // Arrange
        var instance = new InvalidPlugin();
        MethodInfo[] methods = instance.GetType()
            .GetMethods(BindingFlags.Static | BindingFlags.Instance | BindingFlags.Public | BindingFlags.InvokeMethod)
            .Where(m => m.Name is not "GetType" and not "Equals" and not "GetHashCode")
            .ToArray();

        // Act - Assert that no exception occurs
        var count = 0;
        foreach (var method in methods)
        {
            try
            {
                KernelFunctionFactory.CreateFromMethod(method, instance, "plugin");
            }
            catch (KernelException)
            {
                count++;
            }
        }

        // Assert
        Assert.Equal(3, count);
    }

    [Fact]
    public async Task ItCanImportNativeFunctionsAsync()
    {
        // Arrange
        var canary = false;

        var arguments = new KernelArguments();
        arguments["done"] = "NO";

        // Note: the function doesn't have any SK attributes
        async Task ExecuteAsync(string done)
        {
            Assert.Equal("NO", done);
            canary = true;
            await Task.Delay(0);
        }

        // Act
        KernelFunction function = KernelFunctionFactory.CreateFromMethod(
            method: ExecuteAsync,
            parameters: null,
            description: "description",
            functionName: "functionName");

        FunctionResult result = await function.InvokeAsync(this._kernel, arguments);

        // Assert
        Assert.True(canary);
        Assert.Null(result.GetValue<object?>());
        Assert.Empty(result.ToString());
    }

    [Fact]
    public async Task ItCanImportNativeFunctionsWithExternalReferencesAsync()
    {
        // Arrange
        var arguments = new KernelArguments();
        arguments["done"] = "NO";

        // Note: This is an important edge case that affects the function signature and how delegates
        //       are handled internally: the function references an external variable and cannot be static.
        //       This scenario is used for gRPC functions.
        string variableOutsideTheFunction = "foo";

        async Task<string> ExecuteAsync(string done)
        {
            string referenceToExternalVariable = variableOutsideTheFunction;
            await Task.Delay(0);
            return referenceToExternalVariable;
        }

        // Act. Note: this will throw an exception if SKFunction doesn't handle the function type.
        KernelFunction function = KernelFunctionFactory.CreateFromMethod(
            method: ExecuteAsync,
            description: "description",
            functionName: "functionName");

        FunctionResult result = await function.InvokeAsync(this._kernel, arguments);

        // Assert
        Assert.Equal(variableOutsideTheFunction, result.GetValue<string>());
        Assert.Equal(variableOutsideTheFunction, result.ToString());
    }

    private sealed class InvalidPlugin
    {
        [KernelFunction]
        public void Invalid1([KernelName("input"), Description("The x parameter")] string x, [KernelName("input"), Description("The y parameter")] string y)
        {
        }

        [KernelFunction]
        public void Invalid2(string y, CustomUnknownType n)
        {
        }

        [KernelFunction]
        public void Invalid4(CancellationToken ct1, CancellationToken ct2)
        {
        }

        public struct CustomUnknownType { }
    }

    private sealed class LocalExamplePlugin
    {
        [KernelFunction]
        public void Type01()
        {
        }

        [KernelFunction]
        public string Type02()
        {
            return "";
        }

        [KernelFunction]
        public string? Type02Nullable()
        {
            return null;
        }

        [KernelFunction]
        public async Task<string> Type03Async()
        {
            await Task.Delay(0);
            return "";
        }

        [KernelFunction]
        public async Task<string?> Type03NullableAsync()
        {
            await Task.Delay(0);
            return null;
        }

        [KernelFunction]
        public void Type04(string input)
        {
        }

        [KernelFunction]
        public void Type04Nullable(string? input)
        {
        }

        [KernelFunction]
        public string Type05(string input)
        {
            return "";
        }

        [KernelFunction]
        public string? Type05Nullable(string? input = null)
        {
            return "";
        }

        [KernelFunction]
        public async Task<string> Type06Async(string input)
        {
            await Task.Delay(0);
            return "";
        }

        [KernelFunction]
        public async Task<string?> Type06NullableAsync(string? input)
        {
            await Task.Delay(0);
            return "";
        }

        [KernelFunction]
        public async Task Type07Async(string input)
        {
            await Task.Delay(0);
        }

        [KernelFunction]
        public async Task Type08Async()
        {
            await Task.Delay(0);
        }

        [KernelFunction]
        public async ValueTask ReturnsValueTaskAsync()
        {
            await Task.Delay(0);
        }

        [KernelFunction]
        public async ValueTask<string> ReturnsValueTaskStringAsync()
        {
            await Task.Delay(0);
            return "hello world";
        }

        [KernelFunction]
        public FunctionResult ReturnsFunctionResult()
        {
            return new FunctionResult("fake-function-name", "fake-result", CultureInfo.InvariantCulture);
        }

        [KernelFunction]
        public async Task<FunctionResult> ReturnsTaskFunctionResultAsync()
        {
            await Task.Delay(0);
            return new FunctionResult("fake-function-name", "fake-result", CultureInfo.InvariantCulture);
        }

        [KernelFunction]
        public async ValueTask<FunctionResult> ReturnsValueTaskFunctionResultAsync()
        {
            await Task.Delay(0);
            return new FunctionResult("fake-function-name", "fake-result", CultureInfo.InvariantCulture);
        }

        [KernelFunction]
        public string WithPrimitives(
            byte a1,
            byte? b1,
            sbyte c1,
            sbyte? d1,
            short e1,
            short? f1,
            ushort g1,
            ushort? h1,
            int i1,
            int? j1,
            uint k1,
            uint? l1,
            long m1,
            long? n1,
            ulong o1,
            ulong? p1,
            float q1,
            float? r1,
            double s1,
            double? t1,
            decimal u1,
            decimal? v1,
            char w1,
            char? x1,
            bool y1,
            bool? z1,
            DateTime a2,
            DateTime? b2,
            DateTimeOffset c2,
            DateTimeOffset? d2,
            TimeSpan e2,
            TimeSpan? f2,
            Guid g2,
            Guid? h2,
            DayOfWeek i2,
            DayOfWeek? j2,
            Uri k2,
            string l2)
        {
            return string.Empty;
        }
    }
}
