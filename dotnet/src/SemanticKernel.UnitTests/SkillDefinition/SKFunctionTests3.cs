// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Linq;
using System.Reflection;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.SkillDefinition;
using Xunit;

namespace SemanticKernel.UnitTests.SkillDefinition;

public sealed class SKFunctionTests3
{
    [Fact]
    public void ItDoesntThrowForValidFunctions()
    {
        // Arrange
        var skillInstance = new LocalExampleSkill();
        MethodInfo[] methods = skillInstance.GetType()
            .GetMethods(BindingFlags.Static | BindingFlags.Instance | BindingFlags.Public | BindingFlags.InvokeMethod)
            .Where(m => m.Name is not "GetType" and not "Equals" and not "GetHashCode" and not "ToString")
            .ToArray();

        IEnumerable<ISKFunction> functions = from method in methods select SKFunction.FromNativeMethod(method, skillInstance, "skill");
        List<ISKFunction> result = (from function in functions where function != null select function).ToList();

        // Act - Assert that no exception occurs and functions are not null
        Assert.Equal(26, methods.Length);
        Assert.Equal(26, result.Count);
        foreach (var method in methods)
        {
            ISKFunction? func = SKFunction.FromNativeMethod(method, skillInstance, "skill");
            Assert.NotNull(func);
        }
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
            catch (KernelException e) when (e.ErrorCode == KernelException.ErrorCodes.FunctionTypeNotSupported)
            {
                count++;
            }
        }

        // Assert
        Assert.Equal(2, count);
    }

    [Fact]
    public async Task ItCanImportNativeFunctionsAsync()
    {
        // Arrange
        var context = Kernel.Builder.Build().CreateNewContext();
        context["done"] = "NO";

        // Note: the function doesn't have any SK attributes
        async Task<SKContext> ExecuteAsync(SKContext contextIn)
        {
            Assert.Equal("NO", contextIn["done"]);
            contextIn["canary"] = "YES";

            await Task.Delay(0);
            return contextIn;
        }

        // Act

        ISKFunction function = SKFunction.FromNativeFunction(
            nativeFunction: ExecuteAsync,
            parameters: null,
            description: "description",
            skillName: "skillName",
            functionName: "functionName");

        SKContext result = await function.InvokeAsync(context);

        // Assert
        Assert.Equal("YES", context["canary"]);
        Assert.Equal("YES", result["canary"]);
    }

    [Fact]
    public async Task ItCanImportNativeFunctionsWithExternalReferencesAsync()
    {
        // Arrange
        var context = Kernel.Builder.Build().CreateNewContext();
        context["done"] = "NO";

        // Note: This is an important edge case that affects the function signature and how delegates
        //       are handled internally: the function references an external variable and cannot be static.
        //       This scenario is used for gRPC functions.
        string variableOutsideTheFunction = "foo";

        async Task<SKContext> ExecuteAsync(SKContext contextIn)
        {
            string referenceToExternalVariable = variableOutsideTheFunction;
            contextIn["canary"] = "YES";

            await Task.Delay(0);
            return contextIn;
        }

        // Act. Note: this will throw an exception if SKFunction doesn't handle the function type.
        ISKFunction function = SKFunction.FromNativeFunction(
            nativeFunction: ExecuteAsync,
            description: "description",
            skillName: "skillName",
            functionName: "functionName");

        SKContext result = await function.InvokeAsync(context);

        // Assert
        Assert.Equal("YES", result["canary"]);
    }

    private sealed class InvalidSkill
    {
        [SKFunction("one")]
        public void Invalid1(string x, string y)
        {
        }

        [SKFunction("three")]
        public void Invalid2(string y, int n)
        {
        }
    }

    private sealed class LocalExampleSkill
    {
        [SKFunction("one")]
        public void Type01()
        {
        }

        [SKFunction("two")]
        public string Type02()
        {
            return "";
        }

        [SKFunction("two2")]
        public string? Type02Nullable()
        {
            return null;
        }

        [SKFunction("three")]
        public async Task<string> Type03Async()
        {
            await Task.Delay(0);
            return "";
        }

        [SKFunction("three2")]
        public async Task<string?> Type03NullableAsync()
        {
            await Task.Delay(0);
            return null;
        }

        [SKFunction("four")]
        public void Type04(SKContext context)
        {
        }

        [SKFunction("four2")]
        public void Type04Nullable(SKContext? context)
        {
        }

        [SKFunction("five")]
        public string Type05(SKContext context)
        {
            return "";
        }

        [SKFunction("five2")]
        public string? Type05Nullable(SKContext? context)
        {
            return null;
        }

        [SKFunction("six")]
        public async Task<string> Type06Async(SKContext context)
        {
            await Task.Delay(0);
            return "";
        }

        [SKFunction("seven")]
        public async Task<SKContext> Type07Async(SKContext context)
        {
            await Task.Delay(0);
            return context;
        }

        [SKFunction("eight")]
        public void Type08(string x)
        {
        }

        [SKFunction("eight2")]
        public void Type08Nullable(string? x)
        {
        }

        [SKFunction("nine")]
        public string Type09(string x)
        {
            return "";
        }

        [SKFunction("nine2")]
        public string? Type09Nullable(string? x = null)
        {
            return "";
        }

        [SKFunction("ten")]
        public async Task<string> Type10Async(string x)
        {
            await Task.Delay(0);
            return "";
        }

        [SKFunction("ten2")]
        public async Task<string?> Type10NullableAsync(string? x)
        {
            await Task.Delay(0);
            return "";
        }

        [SKFunction("eleven")]
        public void Type11(string x, SKContext context)
        {
        }

        [SKFunction("eleven2")]
        public void Type11Nullable(string? x = null, SKContext? context = null)
        {
        }

        [SKFunction("twelve")]
        public string Type12(string x, SKContext context)
        {
            return "";
        }

        [SKFunction("thirteen")]
        public async Task<string> Type13Async(string x, SKContext context)
        {
            await Task.Delay(0);
            return "";
        }

        [SKFunction("fourteen")]
        public async Task<SKContext> Type14Async(string x, SKContext context)
        {
            await Task.Delay(0);
            return context;
        }

        [SKFunction("fifteen")]
        public async Task Type15Async(string x)
        {
            await Task.Delay(0);
        }

        [SKFunction("sixteen")]
        public async Task Type16Async(SKContext context)
        {
            await Task.Delay(0);
        }

        [SKFunction("seventeen")]
        public async Task Type17Async(string x, SKContext context)
        {
            await Task.Delay(0);
        }

        [SKFunction("eighteen")]
        public async Task Type18Async()
        {
            await Task.Delay(0);
        }
    }
}
