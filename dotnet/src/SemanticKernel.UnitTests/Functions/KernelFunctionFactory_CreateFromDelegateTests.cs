// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using SemanticKernel.UnitTests.Functions.JsonSerializerContexts;
using Xunit;

namespace SemanticKernel.UnitTests.Functions;

public class KernelFunctionFactoryCreateFromDelegateTests
{
    private readonly Kernel _kernel = new();

    [Theory]
    [ClassData(typeof(TestJsonSerializerOptionsForTestParameterAndReturnTypes))]
    public async Task ItShouldCreateFunctionFromDelegateUsingOverloadWithFunctionNameAndDescription(JsonSerializerOptions? jsos)
    {
        // Arrange & Act
        KernelFunction function = jsos is not null ?
            function = KernelFunctionFactory.CreateFromMethod((TestParameterType p1) => new TestReturnType() { Result = int.Parse(p1.Value!) }, jsonSerializerOptions: jsos, functionName: "f1", description: "f1-description") :
            function = KernelFunctionFactory.CreateFromMethod((TestParameterType p1) => new TestReturnType() { Result = int.Parse(p1.Value!) }, functionName: "f1", description: "f1-description");

        // Assert
        await this.AssertFunction(function);
    }

    [Theory]
    [ClassData(typeof(TestJsonSerializerOptionsForTestParameterAndReturnTypes))]
    public async Task ItShouldCreateFunctionFromDelegateUsingOverloadWithKernelFunctionFromMethodOptions(JsonSerializerOptions? jsos)
    {
        // Arrange & Act
        KernelFunction function = jsos is not null ?
            function = KernelFunctionFactory.CreateFromMethod((TestParameterType p1) => new TestReturnType() { Result = int.Parse(p1.Value!) }, jsonSerializerOptions: jsos, options: new KernelFunctionFromMethodOptions()) :
            function = KernelFunctionFactory.CreateFromMethod((TestParameterType p1) => new TestReturnType() { Result = int.Parse(p1.Value!) }, options: new KernelFunctionFromMethodOptions());

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
}
