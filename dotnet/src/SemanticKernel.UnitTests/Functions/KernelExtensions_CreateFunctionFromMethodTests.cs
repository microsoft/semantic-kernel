// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Reflection;
using System.Text.Json;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using SemanticKernel.UnitTests.Functions.JsonSerializerContexts;
using Xunit;

namespace SemanticKernel.UnitTests.Functions;

public class KernelExtensionsCreateFunctionFromMethodTests
{
    private readonly Kernel _kernel = new();

    [Theory]
    [ClassData(typeof(TestJsonSerializerOptionsForTestParameterAndReturnTypes))]
    public async Task ItShouldCreateFunctionFromDelegate(JsonSerializerOptions? jsos)
    {
        // Arrange & Act
        KernelFunction function = jsos is not null ?
            function = this._kernel.CreateFunctionFromMethod(MyStaticMethod, jsonSerializerOptions: jsos, functionName: "f1", description: "f1-description") :
            function = this._kernel.CreateFunctionFromMethod(MyStaticMethod, functionName: "f1", description: "f1-description");

        // Assert
        await this.AssertFunction(function);
    }

    [Theory]
    [ClassData(typeof(TestJsonSerializerOptionsForTestParameterAndReturnTypes))]
    public async Task ItShouldCreateFunctionFromMethodInfo(JsonSerializerOptions? jsos)
    {
        // Arrange
        MethodInfo methodInfo = ((Func<TestParameterType, TestReturnType>)MyStaticMethod).Method;

        // Act
        KernelFunction function = jsos is not null ?
            function = KernelFunctionFactory.CreateFromMethod(methodInfo, jsonSerializerOptions: jsos, functionName: "f1", description: "f1-description") :
            function = KernelFunctionFactory.CreateFromMethod(methodInfo, functionName: "f1", description: "f1-description");

        // Assert
        await this.AssertFunction(function);
    }

    private async Task AssertFunction(KernelFunction function)
    {
        Assert.Equal("f1", function.Name);
        Assert.Equal("f1-description", function.Description);

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
