// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Reflection;
using System.Text.Json;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using SemanticKernel.UnitTests.Functions.JsonSerializerContexts;
using Xunit;

namespace SemanticKernel.UnitTests.Functions;

public class KernelFunctionFactoryCreateFromMethodInfoTests
{
    private readonly Kernel _kernel = new();

    private static readonly MethodInfo s_methodInfo = ((Func<TestParameterType, TestReturnType>)MyStaticMethod).Method;

    [Theory]
    [ClassData(typeof(TestJsonSerializerOptionsForTestParameterAndReturnTypes))]
    public async Task ItShouldCreateFunctionFromMethodInfoUsingOverloadWithFunctionNameAndDescription(JsonSerializerOptions? jsos)
    {
        // Act
        KernelFunction function = jsos is not null ?
            function = KernelFunctionFactory.CreateFromMethod(s_methodInfo, jsonSerializerOptions: jsos, functionName: "f1", description: "f1-description") :
            function = KernelFunctionFactory.CreateFromMethod(s_methodInfo, functionName: "f1", description: "f1-description");

        // Assert
        await this.AssertFunction(function);
    }

    [Theory]
    [ClassData(typeof(TestJsonSerializerOptionsForTestParameterAndReturnTypes))]
    public async Task ItShouldCreateFunctionFromMethodInfoUsingOverloadWithKernelFunctionFromMethodOptions(JsonSerializerOptions? jsos)
    {
        // Arrange
        MethodInfo methodInfo = ((Func<TestParameterType, TestReturnType>)MyStaticMethod).Method;

        // Act
        KernelFunction function = jsos is not null ?
            function = KernelFunctionFactory.CreateFromMethod(methodInfo, target: null, jsonSerializerOptions: jsos, options: new KernelFunctionFromMethodOptions()) :
            function = KernelFunctionFactory.CreateFromMethod(methodInfo, target: null, options: new KernelFunctionFromMethodOptions());

        // Assert
        await this.AssertFunction(function);
    }

    private async Task AssertFunction(KernelFunction function)
    {
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

    private static TestReturnType MyStaticMethod(TestParameterType p1)
    {
        return new TestReturnType() { Result = int.Parse(p1.Value!) };
    }
}
