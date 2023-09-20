// Copyright (c) Microsoft. All rights reserved.

using System;
using System.ComponentModel;
using System.Linq;
using System.Reflection;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Diagnostics;
using Microsoft.SemanticKernel.Orchestration;
using Xunit;

namespace SemanticKernel.UnitTests.Functions;

public sealed class SKFunctionTests3
{
    [Fact]
    public void ItDoesntThrowForValidFunctionsViaDelegate()
    {
        // Arrange
        var skillInstance = new LocalExampleSkill();
        MethodInfo[] methods = skillInstance.GetType()
            .GetMethods(BindingFlags.Static | BindingFlags.Instance | BindingFlags.Public | BindingFlags.InvokeMethod)
            .Where(m => m.Name is not "GetType" and not "Equals" and not "GetHashCode" and not "ToString")
            .ToArray();

        ISKFunction[] functions = (from method in methods select SKFunction.FromNativeMethod(method, skillInstance, "skill")).ToArray();

        // Act
        Assert.Equal(methods.Length, functions.Length);
        Assert.All(functions, Assert.NotNull);
    }

    [Fact]
    public void ItDoesntThrowForValidFunctionsViaSkill()
    {
        // Arrange
        var skillInstance = new LocalExampleSkill();
        MethodInfo[] methods = skillInstance.GetType()
            .GetMethods(BindingFlags.Static | BindingFlags.Instance | BindingFlags.Public | BindingFlags.InvokeMethod)
            .Where(m => m.Name is not "GetType" and not "Equals" and not "GetHashCode" and not "ToString")
            .ToArray();

        ISKFunction[] functions = Kernel.Builder.Build().ImportFunctions(skillInstance).Select(s => s.Value).ToArray();

        // Act
        Assert.Equal(methods.Length, functions.Length);
        Assert.All(functions, f => Assert.NotNull(f));
    }

    [Fact]
    public void ItThrowsForInvalidFunctions()
    {
        // Arrange
        var instance = new InvalidSkill();
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
                SKFunction.FromNativeMethod(method, instance, "skill");
            }
            catch (SKException)
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
        var context = Kernel.Builder.Build().CreateNewContext();
        context.Variables["done"] = "NO";

        // Note: the function doesn't have any SK attributes
        async Task<SKContext> ExecuteAsync(SKContext contextIn)
        {
            Assert.Equal("NO", contextIn.Variables["done"]);
            contextIn.Variables["canary"] = "YES";

            await Task.Delay(0);
            return contextIn;
        }

        // Act
        ISKFunction function = SKFunction.FromNativeFunction(
            nativeFunction: ExecuteAsync,
            parameters: null,
            description: "description",
            pluginName: "pluginName",
            functionName: "functionName");

        SKContext result = await function.InvokeAsync(context);

        // Assert
        Assert.Equal("YES", context.Variables["canary"]);
        Assert.Equal("YES", result.Variables["canary"]);
    }

    [Fact]
    public async Task ItCanImportNativeFunctionsWithExternalReferencesAsync()
    {
        // Arrange
        var context = Kernel.Builder.Build().CreateNewContext();
        context.Variables["done"] = "NO";

        // Note: This is an important edge case that affects the function signature and how delegates
        //       are handled internally: the function references an external variable and cannot be static.
        //       This scenario is used for gRPC functions.
        string variableOutsideTheFunction = "foo";

        async Task<SKContext> ExecuteAsync(SKContext contextIn)
        {
            string referenceToExternalVariable = variableOutsideTheFunction;
            contextIn.Variables["canary"] = "YES";

            await Task.Delay(0);
            return contextIn;
        }

        // Act. Note: this will throw an exception if SKFunction doesn't handle the function type.
        ISKFunction function = SKFunction.FromNativeFunction(
            nativeFunction: ExecuteAsync,
            description: "description",
            pluginName: "pluginName",
            functionName: "functionName");

        SKContext result = await function.InvokeAsync(context);

        // Assert
        Assert.Equal("YES", result.Variables["canary"]);
    }

    private sealed class InvalidSkill
    {
        [SKFunction]
        public void Invalid1([SKName("input"), Description("The x parameter")] string x, [SKName("input"), Description("The y parameter")] string y)
        {
        }

        [SKFunction]
        public void Invalid2(string y, CustomUnknownType n)
        {
        }

        [SKFunction]
        public void Invalid3(SKContext context1, SKContext context2)
        {
        }

        [SKFunction]
        public void Invalid4(CancellationToken ct1, CancellationToken ct2)
        {
        }

        public struct CustomUnknownType { }
    }

    private sealed class LocalExampleSkill
    {
        [SKFunction]
        public void Type01()
        {
        }

        [SKFunction]
        public string Type02()
        {
            return "";
        }

        [SKFunction]
        public string? Type02Nullable()
        {
            return null;
        }

        [SKFunction]
        public async Task<string> Type03Async()
        {
            await Task.Delay(0);
            return "";
        }

        [SKFunction]
        public async Task<string?> Type03NullableAsync()
        {
            await Task.Delay(0);
            return null;
        }

        [SKFunction]
        public void Type04(SKContext context)
        {
        }

        [SKFunction]
        public void Type04Nullable(SKContext? context)
        {
        }

        [SKFunction]
        public string Type05(SKContext context)
        {
            return "";
        }

        [SKFunction]
        public string? Type05Nullable(SKContext? context)
        {
            return null;
        }

        [SKFunction]
        public async Task<string> Type06Async(SKContext context)
        {
            await Task.Delay(0);
            return "";
        }

        [SKFunction]
        public async Task<SKContext> Type07Async(SKContext context)
        {
            await Task.Delay(0);
            return context;
        }

        [SKFunction]
        public void Type08(string input)
        {
        }

        [SKFunction]
        public void Type08Nullable(string? input)
        {
        }

        [SKFunction]
        public string Type09(string input)
        {
            return "";
        }

        [SKFunction]
        public string? Type09Nullable(string? input = null)
        {
            return "";
        }

        [SKFunction]
        public async Task<string> Type10Async(string input)
        {
            await Task.Delay(0);
            return "";
        }

        [SKFunction]
        public async Task<string?> Type10NullableAsync(string? input)
        {
            await Task.Delay(0);
            return "";
        }

        [SKFunction]
        public void Type11(string input, SKContext context)
        {
        }

        [SKFunction]
        public void Type11Nullable(string? input = null, SKContext? context = null)
        {
        }

        [SKFunction]
        public string Type12(string input, SKContext context)
        {
            return "";
        }

        [SKFunction]
        public async Task<string> Type13Async(string input, SKContext context)
        {
            await Task.Delay(0);
            return "";
        }

        [SKFunction]
        public async Task<SKContext> Type14Async(string input, SKContext context)
        {
            await Task.Delay(0);
            return context;
        }

        [SKFunction]
        public async Task Type15Async(string input)
        {
            await Task.Delay(0);
        }

        [SKFunction]
        public async Task Type16Async(SKContext context)
        {
            await Task.Delay(0);
        }

        [SKFunction]
        public async Task Type17Async(string input, SKContext context)
        {
            await Task.Delay(0);
        }

        [SKFunction]
        public async Task Type18Async()
        {
            await Task.Delay(0);
        }

        [SKFunction]
        public async ValueTask ReturnsValueTaskAsync()
        {
            await Task.Delay(0);
        }

        [SKFunction]
        public async ValueTask<string> ReturnsValueTaskStringAsync()
        {
            await Task.Delay(0);
            return "hello world";
        }

        [SKFunction]
        public async ValueTask<SKContext> ReturnsValueTaskContextAsync(SKContext context)
        {
            await Task.Delay(0);
            return context;
        }

        [SKFunction]
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
