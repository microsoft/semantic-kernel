// Copyright (c) Microsoft. All rights reserved.

using System;
using System.ComponentModel;
using System.Linq;
using System.Reflection;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.Services;
using Moq;
using Xunit;

namespace SemanticKernel.UnitTests.Functions;

public sealed class KernelFunctionTests3
{
    private readonly Kernel _kernel = new(new Mock<IAIServiceProvider>().Object);

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

        KernelFunction[] functions = new KernelBuilder().Build().ImportPluginFromObject(pluginInstance).ToArray();

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
        Assert.Equal(4, count);
    }

    [Fact]
    public async Task ItCanImportNativeFunctionsAsync()
    {
        // Arrange
        var variables = new ContextVariables();
        variables["done"] = "NO";

        // Note: the function doesn't have any SK attributes
        async Task ExecuteAsync(ContextVariables contextIn)
        {
            Assert.Equal("NO", contextIn["done"]);
            contextIn["canary"] = "YES";

            await Task.Delay(0);
        }

        // Act
        KernelFunction function = KernelFunctionFactory.CreateFromMethod(
            method: ExecuteAsync,
            parameters: null,
            description: "description",
            functionName: "functionName");

        FunctionResult result = await function.InvokeAsync(this._kernel, variables);

        // Assert
        Assert.Equal("YES", variables["canary"]);
        Assert.Equal("YES", result.Variables["canary"]);
    }

    [Fact]
    public async Task ItCanImportNativeFunctionsWithExternalReferencesAsync()
    {
        // Arrange
        var variables = new ContextVariables();
        variables["done"] = "NO";

        // Note: This is an important edge case that affects the function signature and how delegates
        //       are handled internally: the function references an external variable and cannot be static.
        //       This scenario is used for gRPC functions.
        string variableOutsideTheFunction = "foo";

        async Task ExecuteAsync(ContextVariables variables)
        {
            string referenceToExternalVariable = variableOutsideTheFunction;
            variables["canary"] = "YES";

            await Task.Delay(0);
        }

        // Act. Note: this will throw an exception if SKFunction doesn't handle the function type.
        KernelFunction function = KernelFunctionFactory.CreateFromMethod(
            method: ExecuteAsync,
            description: "description",
            functionName: "functionName");

        FunctionResult result = await function.InvokeAsync(this._kernel, variables);

        // Assert
        Assert.Equal("YES", variables["canary"]);
    }

    private sealed class InvalidPlugin
    {
        [KernelFunction]
        public void Invalid1([KernelFunctionName("input"), Description("The x parameter")] string x, [KernelFunctionName("input"), Description("The y parameter")] string y)
        {
        }

        [KernelFunction]
        public void Invalid2(string y, CustomUnknownType n)
        {
        }

        [KernelFunction]
        public void Invalid3(ContextVariables context1, ContextVariables context2)
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
        public void Type04(ContextVariables context)
        {
        }

        [KernelFunction]
        public void Type04Nullable(ContextVariables? variables)
        {
        }

        [KernelFunction]
        public string Type05(ContextVariables context)
        {
            return "";
        }

        [KernelFunction]
        public string? Type05Nullable(ContextVariables? variables)
        {
            return null;
        }

        [KernelFunction]
        public async Task<string> Type06Async(ContextVariables context)
        {
            await Task.Delay(0);
            return "";
        }

        [KernelFunction]
        public async Task Type07Async(ContextVariables context)
        {
            await Task.Delay(0);
        }

        [KernelFunction]
        public void Type08(string input)
        {
        }

        [KernelFunction]
        public void Type08Nullable(string? input)
        {
        }

        [KernelFunction]
        public string Type09(string input)
        {
            return "";
        }

        [KernelFunction]
        public string? Type09Nullable(string? input = null)
        {
            return "";
        }

        [KernelFunction]
        public async Task<string> Type10Async(string input)
        {
            await Task.Delay(0);
            return "";
        }

        [KernelFunction]
        public async Task<string?> Type10NullableAsync(string? input)
        {
            await Task.Delay(0);
            return "";
        }

        [KernelFunction]
        public void Type11(string input, ContextVariables context)
        {
        }

        [KernelFunction]
        public void Type11Nullable(string? input = null, ContextVariables? variables = null)
        {
        }

        [KernelFunction]
        public string Type12(string input, ContextVariables context)
        {
            return "";
        }

        [KernelFunction]
        public async Task<string> Type13Async(string input, ContextVariables context)
        {
            await Task.Delay(0);
            return "";
        }

        [KernelFunction]
        public async Task Type14Async(string input, ContextVariables context)
        {
            await Task.Delay(0);
        }

        [KernelFunction]
        public async Task Type15Async(string input)
        {
            await Task.Delay(0);
        }

        [KernelFunction]
        public async Task Type16Async(ContextVariables context)
        {
            await Task.Delay(0);
        }

        [KernelFunction]
        public async Task Type17Async(string input, ContextVariables context)
        {
            await Task.Delay(0);
        }

        [KernelFunction]
        public async Task Type18Async()
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
        public async ValueTask ReturnsValueTaskContextAsync(ContextVariables context)
        {
            await Task.Delay(0);
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
